import bpy
from typing import Optional


class Object3D:
    """Object class: represents any form of object in the scene."""
    
    def __init__(self, obj: Optional[bpy.types.Mesh] = None, name: Optional[str] = None):
        """Initialize an Object3D.
        
        Args:
            obj: Blender mesh object
            name: Name of the object
        """
        self._object: Optional[bpy.types.Mesh] = obj
        self._name: Optional[str] = name if name else obj.name if obj else None
    
    def __repr__(self) -> str:
        if self._object:
            location = self._object.location
            return f"Object {self._name}, at {location}"
        return "Empty Object3D"
    
    def delete(self) -> None:
        """Delete the object."""
        if self._object:
            bpy.ops.object.select_all(action='DESELECT')
            self._object.select_set(True)
            bpy.ops.object.delete()
            self._object = None
            self._name = None

    def get_object(self) -> Optional[bpy.types.Mesh]:
        """Return the object.
        
        Returns:
            The Blender mesh object or None
        """
        return self._object
    
        
        