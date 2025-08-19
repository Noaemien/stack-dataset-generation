import bpy
import bmesh
from pathlib import Path
import numpy as np
from typing import List, Tuple, Optional, Any

from source.Utils import Utils
from source.Object import Object3D


class PhysicsObject(Object3D):
    """Object class: represents any form of object imported in the scene."""
    
    def __init__(self):
        super().__init__()
        self._volume: Optional[float] = None
        self._path: Optional[Path] = None
        self.acd_meshes: List = []

    def __repr__(self) -> str:
        return f"Physics object {self._name}, Volume {self._volume}, path {self._path}"
    
    def __add__(self, other):
        """Add another PhysicsObject to this one.
        
        Args:
            other: Another PhysicsObject to add to this one
            
        Returns:
            This PhysicsObject with the other object joined to it
            
        Raises:
            ValueError: If other is not a PhysicsObject
        """
        if not isinstance(other, PhysicsObject):
            raise ValueError(f"Cannot add object of type {type(other)} to PhysicsObject")
            
        bpy.ops.object.select_all(action='DESELECT')
        self._object.select_set(True)
        other._object.select_set(True)
        bpy.context.view_layer.objects.active = self._object
        bpy.ops.object.join()

        other.delete()

        return self
        
    def __load(
        self,
        path: Path,
        name: Optional[str] = None,
        location: Tuple[float, float, float] = (0, 0, 0),
        pass_index: int = 10,
        set_origin: bool = False,
        origin_type: str = 'ORIGIN_GEOMETRY',
        decimate: bool = False,
        rescale: bool = False,
        rescale_max_dimension: float = 0.2
    ) -> None:
        """Load the object from the given path.
        
        Args:
            path: Path to the object file
            name: Name for the object
            location: Location to place the object
            pass_index: Pass index for rendering
            set_origin: Whether to set the object origin
            origin_type: Type of origin to set
            decimate: Whether to decimate the object
            rescale: Whether to rescale the object
            rescale_max_dimension: Maximum dimension for rescaling
        """
        if self._object:
            self.delete()

        self._path = path

        if path.suffix == '.fbx':
            bpy.ops.import_scene.fbx(filepath=str(path))
        elif path.suffix == '.obj':
            bpy.ops.wm.obj_import(filepath=str(path))
        else:
            raise ValueError(f"Invalid file type: {path.suffix}")
        
        self._object = bpy.context.selected_objects[0]

        if hasattr(self, 'scaling'):
            self._object.scale = self.scaling
            bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

        if set_origin:
            bpy.ops.object.origin_set(type=origin_type, center='BOUNDS')
        if decimate:
            Utils.decimate_object(self._object, decimate_type='DISSOLVE', angle_limit=5.7)
        if rescale:
            Utils.rescale(self._object, rescale_max_dimension)

        self._name = name if name else self._object.name
        self._object.name = self._name
        self._object.location = location
        self._object.pass_index = pass_index

        Utils.apply_transforms(self._object, location=True, rotation=True, scale=True)

        self._compute_volume()
    
    def load_from_folder(
        self,
        folder: Path,
        obj_type: str = 'OBJ',
        name: Optional[str] = None,
        location: Tuple[float, float, float] = (0, 0, 0),
        pass_index: int = 10,
        set_origin: bool = False,
        origin_type: str = 'ORIGIN_GEOMETRY',
        decimate: bool = False,
        rescale: bool = False,
        rescale_max_dimension: float = 0.2
    ) -> None:
        """Load the object from a folder containing the object file.
        
        Args:
            folder: Path to the folder containing the object file
            obj_type: Type of object file ('OBJ', 'FBX', etc.)
            name: Name for the object
            location: Location to place the object
            pass_index: Pass index for rendering
            set_origin: Whether to set the object origin
            origin_type: Type of origin to set
            decimate: Whether to decimate the object
            rescale: Whether to rescale the object
            rescale_max_dimension: Maximum dimension for rescaling
        """
        folder = Path(folder)
        for file in folder.iterdir():
            if file.suffix == f'.{obj_type.lower()}':
                self.__load(
                    file, name, location, pass_index,
                    set_origin, origin_type, decimate, rescale,
                    rescale_max_dimension
                )
                break
        else:
            raise FileNotFoundError(f"No {obj_type} file found in {folder}")

    def delete(self) -> None:
        """Delete the object from the scene."""
        if self._object:
            bpy.data.objects.remove(self._object, do_unlink=True)
        bpy.ops.object.select_all(action='DESELECT')
        self._object = None
        self._volume = None
        self._path = None

    def _compute_volume(self) -> None:
        """Compute the volume of the object."""
        if self._object:
            self._volume = Utils.get_object_volume(self._object)

    def add_rigid_body(
        self,
        collision_shape: str = 'CONVEX_HULL',
        type: str = 'ACTIVE',
        use_margin: bool = True,
        margin: float = 0.001
    ) -> None:
        """Add rigid body physics to the object.
        
        Args:
            collision_shape: Shape of the collision object
            type: Type of rigid body ('ACTIVE', 'PASSIVE')
            use_margin: Whether to use collision margin
            margin: Collision margin value
        """
        bpy.context.view_layer.objects.active = self._object
        bpy.ops.rigidbody.object_add(type=type)
        self._object.rigid_body.collision_shape = collision_shape
        self._object.rigid_body.use_margin = use_margin
        self._object.rigid_body.collision_margin = margin
    
    def get_volume(self) -> Optional[float]:
        """Return the volume of the object.
        
        Returns:
            Volume of the object or None if not computed
        """
        return self._volume
    
    def save_acd_data(self, parts: List, output_file: Path) -> None:
        """Save parts data to a file.
        
        Args:
            parts: List of parts data (vertices and faces)
            output_file: Path to save the data
        """
        data = {}
        for i, (vs, fs) in enumerate(parts):
            data[f'vertices_{i}'] = np.array(vs)
            data[f'faces_{i}'] = np.array(fs)

        np.savez_compressed(output_file, **data)

    def load_acd_data(self, output_file: Path) -> List:
        """Load parts data from a file.
        
        Args:
            output_file: Path to the data file
            
        Returns:
            List of parts data
        """
        loaded_data = np.load(output_file, allow_pickle=True)
        parts = []

        i = 0
        while f'vertices_{i}' in loaded_data:
            vertices = loaded_data[f'vertices_{i}']
            faces = loaded_data[f'faces_{i}']
            parts.append((vertices.tolist(), faces.tolist()))
            i += 1

        return parts

    def acd(self, hide_children: bool = False) -> None:
        """Run Approximate Convex Decomposition on the object.
        
        Args:
            hide_children: Whether to hide child objects after decomposition
        """
        # Define the output path for the ACD file
        if not self._path:
            raise ValueError("Object path is not set")
            
        object_path = Path(self._path)
        output_file = object_path.parent / "acd_data.npz"

        if output_file.exists():
            parts = self.load_acd_data(output_file)
            if hasattr(self, 'scaling'):
                new_parts = []
                for i in range(len(parts)):
                    new_v = np.array(parts[i][0])
                    # Convention change seems necessary (why??)
                    scaling2 = (self.scaling[0], self.scaling[2], self.scaling[1])
                    new_v = new_v * scaling2
                    new_parts.append((new_v, parts[i][1]))
                parts = new_parts
        else:
            Utils.triangulate_object(self._object)

            vertices = np.array(Utils.get_object_vertices(self._object))
            faces = np.array(Utils.get_object_faces(self._object))

            import coacd
            mesh = coacd.Mesh(vertices, faces)
            parts = coacd.run_coacd(mesh, threshold=0.03, mcts_max_depth=7, mcts_nodes=30, mcts_iterations=500)
            
            if not hasattr(self, 'scaling') or self.scaling == (1, 1, 1):
                # Don't save ACD if the mesh was scaled
                self.save_acd_data(parts, output_file)

        children = []

        # Trimesh point data to blender mesh
        for vs, fs in parts:
            bm = bmesh.new()
            mesh = bpy.data.meshes.new(Utils.get_unique_name("coacd_"))
            obj = bpy.data.objects.new(mesh.name, mesh)
            children.append(obj)
            bpy.context.collection.objects.link(obj)
            for v in vs:
                bm.verts.new(v)
            bm.verts.ensure_lookup_table()
            for f in fs:
                bm.faces.new([bm.verts[i] for i in f])
            bm.to_mesh(obj.data)
            bm.free()

        # Set all children to be rigid bodies
        Utils.select_objects(children)
        bpy.context.view_layer.objects.active = self._object
        bpy.ops.rigidbody.object_settings_copy()

        # Set the parent to be the original object
        bpy.ops.object.parent_set(type='OBJECT', keep_transform=False)
        if self._object.rigid_body:
            self._object.rigid_body.collision_shape = 'COMPOUND'

        Utils.select_objects(children)
        if hide_children:
            for c in children:
                c.hide_set(True)

        
