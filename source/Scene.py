import bpy
from typing import List, Callable, Optional

from source.Utils import Utils


class Scene:
    """Scene class: represents the scene."""
    
    start_frame: int = 0
    end_frame: int = 100

    def __init__(self, start_frame: int = 0, end_frame: int = 100) -> None:
        """Initialize the scene with frame range.
        
        Args:
            start_frame: Start frame of the scene
            end_frame: End frame of the scene
        """
        self.start_frame = start_frame
        self.end_frame = end_frame
        bpy.context.scene.frame_start = self.start_frame
        bpy.context.scene.frame_end = self.end_frame

    @staticmethod
    def set_frame_range(start: int, end: int) -> None:
        """Set the frame range.
        
        Args:
            start: Start frame
            end: End frame
        """
        bpy.context.scene.frame_start = start
        bpy.context.scene.frame_end = end

    @staticmethod
    def set_frame(frame: int) -> None:
        """Set the current frame.
        
        Args:
            frame: Frame number to set
        """
        bpy.context.scene.frame_set(frame)

    @staticmethod
    def go_to_first_frame() -> None:
        """Go to the first frame."""
        bpy.context.scene.frame_set(bpy.context.scene.frame_start)

    @staticmethod
    def go_to_last_frame() -> None:
        """Go to the last frame."""
        bpy.context.scene.frame_set(bpy.context.scene.frame_end)

    @staticmethod
    def bake_simulation(
        objects: Optional[List[bpy.types.Mesh]] = None,
        handler: Callable = lambda s: None
    ) -> None:
        """Bake the simulation.
        
        Args:
            objects: List of objects to bake. If None, an empty list is used.
            handler: Handler function to call during baking. Defaults to a no-op lambda.
        """
        if objects is None:
            objects = []
            
        Utils.select_objects(objects)

        bpy.app.handlers.frame_change_pre.append(handler)
        bpy.ops.ptcache.bake_all(bake=True)
        bpy.app.handlers.frame_change_pre.pop(-1)

    @staticmethod
    def apply_simulation(objects: Optional[List[bpy.types.Mesh]] = None) -> None:
        """Applies the simulation and merges all objects.
        
        Args:
            objects: List of objects to apply simulation to. If None, an empty list is used.
        """
        if objects is None:
            objects = []
            
        Scene.go_to_last_frame()
        bpy.ops.object.visual_transform_apply()
        bpy.ops.ptcache.free_bake_all()
        Scene.go_to_first_frame()
        # Utils.apply_transforms(objects[0], location=True, rotation=True, scale=True)

