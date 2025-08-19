import bpy
from pathlib import Path
import math
import random
from typing import List, Tuple, Optional

from source.PhysicsObject import PhysicsObject
from source.Utils import Utils
from source.Scene import Scene


class BatchPhysicsObject(PhysicsObject):
    """BatchPhysicsObject class: represents a batch of PhysicsObject instances."""
    
    def __init__(self):
        super().__init__()
        self._batch: List[bpy.types.Mesh] = []

    def __repr__(self) -> str:
        return f"Base object: {super().__repr__()}, batch {self._batch}"

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
        super().load_from_folder(
            folder, obj_type, name, location,
            pass_index, set_origin, origin_type, decimate,
            rescale, rescale_max_dimension
        )
        if self._object:
            self._object.hide_render = True
            self.add_rigid_body('CONVEX_HULL', 'PASSIVE', use_margin=True, margin=0.001)
        # self.acd()  # ACD support for batch objects pending implementation

    def _add_batch(
        self,
        count_x: int = 5,
        count_y: int = 5,
        count_z: int = 5,
        offset_x: float = 0.2,
        offset_y: float = 0.2,
        offset_z: float = 0.2,
        start_location: Tuple[float, float, float] = (0, 0, 0),
        name: str = "Instance",
        randomise_rotation: bool = True
    ) -> int:
        """Add a batch of objects to the scene.
        
        Args:
            count_x: Number of objects in X direction
            count_y: Number of objects in Y direction
            count_z: Number of objects in Z direction
            offset_x: Offset between objects in X direction
            offset_y: Offset between objects in Y direction
            offset_z: Offset between objects in Z direction
            start_location: Starting location for the batch
            name: Name for the batch objects
            randomise_rotation: Whether to randomize rotation
            
        Returns:
            Number of objects generated
        """
        if not self._object:
            raise ValueError("Base object not loaded")

        Scene.go_to_first_frame()
        Utils.set_origin(self._object, origin_type='ORIGIN_GEOMETRY')
        obj = Utils.duplicate_object(self._object, name=name, location=start_location)
        
        if obj.rigid_body:
            obj.rigid_body.type = 'ACTIVE'

        Utils.array(obj, count=count_x, offset=(offset_x, 0, 0)) 
        Utils.array(obj, count=count_y, offset=(0, offset_z, 0))
        Utils.array(obj, count=count_z, offset=(0, 0, offset_y))

        self._batch += Utils.separate_loose_parts(obj)

        bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
        if randomise_rotation:
            seed = random.randint(0, 1000)
            bpy.ops.object.randomize_transform(
                random_seed=seed, use_loc=False, 
                use_scale=False, rot=(math.pi, math.pi, math.pi)
            )
            
        n_generated = count_x * count_y * count_z
        return n_generated
            
    def get_batch(self) -> List[bpy.types.Mesh]:
        """Get the batch of objects.
        
        Returns:
            List of objects in the batch
        """
        return self._batch

    def join_batch(self) -> None:
        """Join all objects in the batch into a single object."""
        if self._batch:
            Utils.join_objects(self._batch)
            self._batch = self._batch[:1]

    def copy_rigidbody_to_batch(self) -> None:
        """Copy the rigid body settings from the base object to the batch objects."""
        if not self._batch:
            raise ValueError("Batch is empty")
        if not self._object:
            raise ValueError("Base object not loaded")

        Scene.go_to_first_frame()

        bpy.ops.object.select_all(action='DESELECT')

        # Copy to first object
        self._batch[0].select_set(True)
        bpy.context.view_layer.objects.active = self._object
        bpy.ops.rigidbody.object_settings_copy()
        if self._batch[0].rigid_body:
            self._batch[0].rigid_body.type = 'ACTIVE'

        # Copy to the rest
        bpy.ops.object.select_all(action='DESELECT')
        Utils.select_objects(self._batch)
        bpy.ops.rigidbody.object_settings_copy()
        Utils.set_origin(self._object, origin_type='ORIGIN_GEOMETRY')

    def remove_from_batch(self, objs: Optional[List[bpy.types.Mesh]] = None) -> None:
        """Remove objects from the batch.
        
        Args:
            objs: List of objects to remove from the batch
        """
        if objs:
            for obj in objs:
                if obj in self._batch:
                    self._batch.remove(obj)
                    bpy.data.objects.remove(obj, do_unlink=True)

        
    


