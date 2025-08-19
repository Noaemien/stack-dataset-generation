import bpy
import numpy as np
from typing import List, Tuple, Optional

from source.Object import Object3D
from source.Utils import Utils
from source.Scene import Scene
from source.BatchPhysicsObject import BatchPhysicsObject


class Delimiter(Object3D):
    """Delimiter class: represents a delimiter object for collision detection."""
    
    def __init__(self, obj: Optional[bpy.types.Mesh] = None, name: Optional[str] = None):
        """Initialize a Delimiter object.
        
        Args:
            obj: Blender mesh object
            name: Name for the delimiter
        """
        super().__init__(obj, name)
        self._type: Optional[str] = None

    def __repr__(self) -> str:
        if self._object:
            location = self._object.location
            return f"Delimiter object at {location}"
        return "Empty Delimiter object"
    
    def create_box(
        self,
        name: str = "Delimiter",
        location: Tuple[float, float, float] = (0, 0, 0),
        size_x: float = 2,
        size_y: float = 2,
        size_z: float = 2
    ) -> None:
        """Create a box delimiter object.
        
        Args:
            name: Name for the delimiter
            location: Location of the delimiter
            size_x: Size in X direction
            size_y: Size in Y direction
            size_z: Size in Z direction
        """
        if self._object is not None:
            raise ValueError("Object already exists")

        bpy.ops.mesh.primitive_cube_add(size=1, location=location)
        bpy.ops.transform.resize(value=(size_x, size_y, size_z))
        Utils.apply_transforms(self._object, True, True, True)
        self._object = bpy.context.selected_objects[0]
        self._object.name = Utils.get_unique_name(name) if name else self._object.name
        self._name = self._object.name

        self._object.hide_render = True
        self._object.hide_viewport = False
        self._object.hide_select = False
        self._object.pass_index = 0
        self._object.display_type = 'WIRE'

        self._type = 'BOX'
    
    def create_convex_hull(
        self,
        obj: Optional[bpy.types.Mesh] = None,
        name: str = "Delimiter_ch"
    ) -> None:
        """Create a convex hull for the object.
        
        Args:
            obj: Object to create convex hull for
            name: Name for the convex hull
        """
        if self._object is not None:
            raise ValueError("Object already exists")
        if obj is None:
            raise ValueError("Object must be provided")
            
        print(f"{obj=}")
        ch = Utils.duplicate_object(obj, name="Delimiter_ch")

        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = ch
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.convex_hull()
        bpy.ops.object.mode_set(mode='OBJECT')

        ch.name = Utils.get_unique_name(name) if name else ch.name
        self._object = ch
        self._name = self._object.name

        self._object.hide_render = True
        self._object.hide_viewport = False
        self._object.hide_select = False
        self._object.pass_index = 0
        self._object.display_type = 'WIRE'

        self._type = 'CONVEX_HULL'

    def check_collision(self, obj: Optional[bpy.types.Mesh] = None) -> bool:
        """Check if the object collides with the delimiter.
        
        Args:
            obj: Object to check collision with
            
        Returns:
            True if collision detected, False otherwise
        """
        if self._object is None:
            raise ValueError("Delimiter object not created")
        if obj is None:
            raise ValueError("Object not provided")

        if self._type == 'BOX':
            # Get bounds for both objects
            bb1 = np.array(Utils.get_object_bounds(self._object))
            bb2 = np.array(Utils.get_object_bounds(obj))
            return self._check_box_collision(bb1, bb2)
        else:
            raise NotImplementedError("Collision check for convex hull not implemented")
        
    def _check_box_collision(self, bb1: np.ndarray, bb2: np.ndarray) -> bool:
        """Check if two bounding boxes collide.
        
        Args:
            bb1: First bounding box
            bb2: Second bounding box
            
        Returns:
            True if collision detected, False otherwise
        """
        # Assumes transform already applied recently!
        bb1_min = np.min(bb1, axis=0)
        bb1_max = np.max(bb1, axis=0)
        bb2_min = np.min(bb2, axis=0)
        bb2_max = np.max(bb2, axis=0)

        # Optimized AABB (axis-aligned bounding box) collision check
        return np.all(bb1_min <= bb2_max) and np.all(bb2_min <= bb1_max)

    def _check_convex_hull_collision(self, obj: Optional[bpy.types.Mesh] = None) -> None:
        """Check collision with convex hull (not implemented).
        
        Args:
            obj: Object to check collision with
        """
        # Implementation pending
        pass
    
    def check_collision_with_batch(
        self,
        batch: Optional[BatchPhysicsObject] = None
    ) -> Optional[List[bpy.types.Mesh]]:
        """Check if objects in batch collide with the delimiter.
        
        Args:
            batch: Batch of objects to check collision with
            
        Returns:
            List of colliding objects or None if no collisions
        """
        if self._object is None:
            raise ValueError("Delimiter object not created")
        if batch is None:
            raise ValueError("Batch not provided")

        colliding_objects = []

        # Apply transforms ONCE before checking collisions
        Utils.apply_transforms(self._object, scale=True, location=True, rotation=True)
        bb1 = np.array(Utils.get_object_bounds(self._object))

        if self._type == 'BOX':
            batch_objects = batch.get_batch()

            # Precompute bounds for batch objects
            transformed_bounds = [np.array(Utils.get_object_bounds(obj)) for obj in batch_objects]

            # Check collisions in a loop with optimized conditions
            for obj, bb2 in zip(batch_objects, transformed_bounds):
                if self._check_box_collision(bb1, bb2):
                    colliding_objects.append(obj)
        else:
            raise NotImplementedError("Collision check for convex hull not implemented")

        return colliding_objects if colliding_objects else None
    
    def get_object_volume(
        self,
        obj: Optional[bpy.types.Mesh] = None,
        keep_intersection: bool = False
    ) -> float:
        """Get the volume of the object contained within the delimiter.
        
        Args:
            obj: Object to calculate volume for
            keep_intersection: Whether to keep the intersection object
            
        Returns:
            Volume of the intersecting part
        """
        if self._object is None:
            raise ValueError("Delimiter object not created")
        if obj is None:
            raise ValueError("Object not provided")

        obj_copy = Utils.duplicate_object(obj, name="obj_copy")
        Utils.boolean(obj_copy, target=self._object, 
                      operation='INTERSECT', solver='FAST')

        volume = Utils.get_object_volume(obj_copy)

        if not keep_intersection:
            bpy.data.objects.remove(obj_copy, do_unlink=True)
        
        return volume


    
