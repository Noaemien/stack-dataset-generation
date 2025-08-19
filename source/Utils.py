import bpy
import bmesh
import math
import random
import json
import os
from typing import List, Tuple, Dict, Optional, Union


class Utils:
    """Utility class: contains utility functions for Blender operations."""

    @staticmethod
    def decimate_object(
        obj: bpy.types.Mesh,
        decimate_type: str = 'DISSOLVE',
        ratio: float = 0.1,
        angle_limit: float = 5.7,
        iterations: int = 1
    ) -> None:
        """Decimate the object by the given ratio.
        
        Args:
            obj: The object to decimate
            decimate_type: The type of decimation to perform in ['DISSOLVE', 'UNSUBDIV', 'COLLAPSE']
            ratio: The ratio to decimate by for COLLAPSE
            angle_limit: The angle limit for DISSOLVE in degrees
            iterations: The number of iterations for UNSUBDIV
        """
        decimate_type = decimate_type.upper()
        if decimate_type not in ['DISSOLVE', 'UNSUBDIV', 'COLLAPSE']:
            raise ValueError("Invalid decimate type. Must be one of ['DISSOLVE', 'UNSUBDIV', 'COLLAPSE']")

        name = Utils.get_unique_name("Decimate")

        mod = obj.modifiers.new(name=name, type='DECIMATE')
        mod.decimate_type = decimate_type

        if decimate_type == 'DISSOLVE':
            mod.angle_limit = math.radians(angle_limit)
        elif decimate_type == 'COLLAPSE':
            mod.ratio = ratio
        elif decimate_type == 'UNSUBDIV':
            mod.iterations = iterations

        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_apply(modifier=name)

    @staticmethod
    def array(
        obj: bpy.types.Mesh,
        count: int = 1,
        offset: Tuple[float, float, float] = (0, 0, 0),
        use_relative_offset: bool = False,
        use_constant_offset: bool = True
    ) -> None:
        """Array the object.
        
        Args:
            obj: The object to array
            count: The number of objects to array
            offset: The offset to array by
            use_relative_offset: Whether to use relative offset
            use_constant_offset: Whether to use constant offset
        """
        name = Utils.get_unique_name("Array")

        mod = obj.modifiers.new(name=name, type='ARRAY')
        mod.count = count
        mod.use_relative_offset = use_relative_offset
        mod.use_constant_offset = use_constant_offset
        mod.relative_offset_displace = offset
        mod.constant_offset_displace = offset

        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_apply(modifier=name)

    @staticmethod
    def boolean(
        obj: bpy.types.Mesh,
        target: bpy.types.Mesh,
        operation: str = 'UNION',
        solver: str = 'FAST'
    ) -> None:
        """Perform a boolean operation on the object.
        
        Args:
            obj: The object to boolean
            target: The target object to boolean with
            operation: The boolean operation to perform in ['UNION', 'INTERSECT', 'DIFFERENCE']
            solver: The solver to use in ['FAST', 'EXACT']
        """
        operation = operation.upper()
        if operation not in ['UNION', 'INTERSECT', 'DIFFERENCE']:
            raise ValueError("Invalid boolean operation. Must be one of ['UNION', 'INTERSECT', 'DIFFERENCE']")
        if solver not in ['FAST', 'EXACT']:
            raise ValueError("Invalid boolean solver. Must be one of ['FAST', 'EXACT']")

        name = Utils.get_unique_name("Boolean")

        mod = obj.modifiers.new(name=name, type='BOOLEAN')
        mod.operation = operation
        mod.object = target
        mod.solver = solver

        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_apply(modifier=name)

    @staticmethod
    def rescale(obj: bpy.types.Mesh, scale: float = 0.2) -> None:
        """Rescale object proportionally setting max dimension to scale.
        
        Args:
            obj: The object to rescale
            scale: The scale to rescale max_dim to
        """
        max_dimension = max(obj.dimensions)
        scale_factor = scale / max_dimension
        obj.scale = (
            obj.scale[0] * scale_factor,
            obj.scale[1] * scale_factor,
            obj.scale[2] * scale_factor
        )
        
        Utils.apply_transforms(obj, scale=True)

    @staticmethod
    def apply_transforms(
        obj: bpy.types.Mesh,
        location: bool = False,
        rotation: bool = False,
        scale: bool = False
    ) -> None:
        """Apply all transforms to the object.
        
        Args:
            obj: The object to apply transforms to
            location: Whether to apply location transform
            rotation: Whether to apply rotation transform
            scale: Whether to apply scale transform
        """
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.transform_apply(location=location, rotation=rotation, scale=scale)

    @staticmethod
    def duplicate_object(
        obj: bpy.types.Mesh,
        name: str = '',
        location: Tuple[float, float, float] = (0, 0, 0),
        select_with_children: bool = False
    ) -> bpy.types.Mesh:
        """Duplicate the object.
        
        Args:
            obj: The object to duplicate
            name: The name for the new object
            location: The location for the new object
            select_with_children: Whether to select children of the object
            
        Returns:
            The duplicated object
        """
        bpy.ops.object.select_all(action='DESELECT')

        if select_with_children:
            Utils.select_with_children(obj)
        else:
            obj.select_set(True)
            bpy.context.view_layer.objects.active = obj
            
        bpy.ops.object.duplicate()
        new_obj = bpy.context.selected_objects[0]
        new_obj.location = location
        new_obj.name = Utils.get_unique_name(name) if name else new_obj.name
        return new_obj

    @staticmethod
    def separate_loose_parts(obj: bpy.types.Mesh) -> List[bpy.types.Mesh]:
        """Separate loose parts of the object.
        
        Args:
            obj: The object to separate
            
        Returns:
            List of separated objects including the original object
        """
        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.separate(type='LOOSE')
        bpy.ops.object.mode_set(mode='OBJECT')

        return [obj] + bpy.context.selected_objects

    @staticmethod
    def select_objects(objects: List[bpy.types.Mesh]) -> None:
        """Select the given objects.
        
        Args:
            objects: List of objects to select
        """
        bpy.ops.object.select_all(action='DESELECT')
        for obj in objects:
            obj.select_set(True)
        # Set the first object as the active object
        if objects:
            bpy.context.view_layer.objects.active = objects[0]

    @staticmethod
    def set_origin(obj: bpy.types.Mesh, origin_type: str = 'ORIGIN_GEOMETRY') -> None:
        """Set the origin of the object.
        
        Args:
            obj: The object to set origin for
            origin_type: The type of origin to set
        """
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.origin_set(type=origin_type, center='BOUNDS')

    @staticmethod
    def select_with_children(obj: bpy.types.Mesh) -> None:
        """Select the object and all its children.
        
        Args:
            obj: The object to select with its children
        """
        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.select_grouped(type='CHILDREN_RECURSIVE')
        bpy.context.view_layer.objects.active = obj

    @staticmethod
    def join_objects(objects: List[bpy.types.Mesh]) -> None:
        """Join the given objects.
        
        Args:
            objects: List of objects to join
        """
        if not objects:
            return
            
        Utils.select_objects(objects)
        bpy.context.view_layer.objects.active = objects[0]
        bpy.ops.object.join()

    @staticmethod
    def triangulate_object(obj: bpy.types.Mesh) -> None:
        """Triangulate the object.
        
        Args:
            obj: The object to triangulate
        """
        # Found here: https://blender.stackexchange.com/questions/45698/triangulate-mesh-in-python
        me = obj.data
        bm = bmesh.new()
        bm.from_mesh(me)
        bmesh.ops.triangulate(bm, faces=bm.faces[:])
        bm.to_mesh(me)
        bm.free()

    @staticmethod
    def get_unique_name(name: str) -> str:
        """Get a unique name for the object.
        
        Args:
            name: Base name to make unique
            
        Returns:
            Unique name with random suffix
        """
        return name + '_' + hex(random.getrandbits(32))[2:]

    @staticmethod
    def get_object_volume(obj: bpy.types.Mesh) -> float:
        """Get the volume of the object.
        
        Args:
            obj: The object to calculate volume for
            
        Returns:
            Volume of the object
        """
        bpy.context.view_layer.objects.active = obj
        bm = bmesh.new()
        depsgraph = bpy.context.evaluated_depsgraph_get()
        bm.from_object(obj, depsgraph)
        return bm.calc_volume()

    @staticmethod
    def get_object_bounds(obj: bpy.types.Mesh) -> List:
        """Get the bounds of the object.
        
        Args:
            obj: The object to get bounds for
            
        Returns:
            Object bounds
        """
        return obj.bound_box

    @staticmethod
    def get_object_faces(obj: bpy.types.Mesh) -> List[List[int]]:
        """Get the faces of the object.
        
        Args:
            obj: The object to get faces for
            
        Returns:
            List of faces, each face being a list of vertex indices
        """
        faces = []
        for f in obj.data.polygons:
            face = [idx for idx in f.vertices]
            faces.append(face)
        return faces

    @staticmethod
    def get_object_vertices(obj: bpy.types.Mesh) -> List[List[float]]:
        """Get the vertices of the object.
        
        Args:
            obj: The object to get vertices for
            
        Returns:
            List of vertices, each vertex being a list of coordinates
        """
        return [[v.co[0], v.co[1], v.co[2]] for v in obj.data.vertices]

    @staticmethod
    def delete_objects_with_prefix(prefix: str) -> None:
        """Delete objects with the given prefix.
        
        Args:
            prefix: The prefix to match object names
        """
        # Create a copy of the objects list to avoid modification during iteration
        objects_to_remove = [obj for obj in bpy.data.objects if obj.name.startswith(prefix)]
        for obj in objects_to_remove:
            bpy.data.objects.remove(obj, do_unlink=True)

    @staticmethod
    def select_objects_with_prefix(prefix: str) -> List[bpy.types.Mesh]:
        """Select objects with the given prefix and return them.
        
        Args:
            prefix: The prefix to match object names
            
        Returns:
            List of selected objects
        """
        objects = []
        for obj in bpy.context.scene.objects:
            if obj.name.startswith(prefix):
                obj.select_set(True)
                objects.append(obj)
            else:
                obj.select_set(False)
        return objects

    @staticmethod
    def save_data_json(
        folder_path: str,
        dictionary: Dict,
        name: str = "simulation_results"
    ) -> None:
        """Save dictionary to a JSON file.
        
        Args:
            folder_path: The folder path to save the JSON file
            dictionary: The dictionary to save
            name: The name of the JSON file (default: "simulation_results")
        """
        if folder_path is None:
            raise ValueError("folder_path parameter must be provided")
            
        # Ensure the directory exists
        os.makedirs(folder_path, exist_ok=True)
        
        with open(f"{folder_path}/{name}.json", "w") as f:
            json.dump(dictionary, f, indent=4)

    @staticmethod
    def apply_material(obj: bpy.types.Mesh, material: str) -> None:
        """Apply a material to an object.
        
        Args:
            obj: The object to apply material to
            material: The name of the material to apply
            
        Raises:
            ValueError: If obj or material is None, or if material is not found
            FileNotFoundError: If texture directory or files are not found
        """
        if obj is None or material is None:
            raise ValueError("obj and material parameters must be provided")
            
        # Remove all materials from object
        obj.data.materials.clear()
        bpy.context.view_layer.objects.active = obj
        mat = bpy.data.materials.get(material)

        if mat is None:
            raise ValueError(f"Material '{material}' not found")

        if material in ["TexturedBox", "TexturedFloor"]:
            if mat is None or not mat.use_nodes:
                raise ValueError(f"Material '{material}' not found")
                
            image_node = mat.node_tree.nodes.get("Image Texture")
            if image_node is None or image_node.type != "TEX_IMAGE":
                raise ValueError(f"'Image Texture' node not found or not of type 'TEX_IMAGE' in material '{material}'")

            texture_dir = "assets/" + material
            if not os.path.exists(texture_dir):
                raise FileNotFoundError(f"Texture directory '{texture_dir}' not found")
                
            texture_files = [f for f in os.listdir(texture_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
            if not texture_files:
                raise FileNotFoundError(f"No textures found in {texture_dir}")

            random_texture_path = os.path.join(texture_dir, random.choice(texture_files))
            image_node.image = bpy.data.images.load(random_texture_path)
        
        obj.data.materials.append(mat)
