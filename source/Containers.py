import bpy
from pathlib import Path
import os
import random
import json
from typing import Union, Optional

from source.PhysicsObject import PhysicsObject


class Container(PhysicsObject):
    """Container class: represents a container object in the scene."""
    
    def __init__(self, path: Optional[Union[str, Path]] = None, scaling: tuple = (1, 1, 1)):
        """Initialize a Container object.
        
        Args:
            path: Path to the container files
            scaling: Scaling factors for the container
        """
        super().__init__()
        self.scaling = scaling
        self.pass_index = 12
        self.file_name: str = ""

    def _choose_random_container(self, path: Path, name: Optional[str] = None) -> None:
        """Choose a random container from the given path.
        
        Args:
            path: Path to the containers directory
            name: Name for the container object
        """
        if not path.exists():
            raise FileNotFoundError(f"Container path does not exist: {path}")
            
        folders = [f for f in path.iterdir() if f.is_dir()]
        if not folders:
            raise FileNotFoundError(f"No container folders found in: {path}")
            
        self.file_name = random.choice(folders).name
        container_folder = path / self.file_name
        print("Loading container:", container_folder)
        super().load_from_folder(container_folder, 'OBJ', name=name, pass_index=self.pass_index)

    def load(
        self,
        path: Optional[Union[str, Path]] = None,
        choose_random: bool = True,
        name: Optional[str] = None,
        use_acd: bool = True
    ) -> None:
        """Load a container from the given path.
        
        Args:
            path: Path to the container files
            choose_random: Whether to choose a random container
            name: Name for the container object
            use_acd: Whether to use Approximate Convex Decomposition
        """
        path = Path(path) if path else None
        
        if self._object:
            self.delete()
    
        if choose_random and path:
            self._choose_random_container(path, name=name)
        elif path:
            super().load_from_folder(path, 'OBJ', name=name, pass_index=self.pass_index)
            self.file_name = path.name
        else:
            raise ValueError("Path must be provided")

        if use_acd:
            self.add_rigid_body('CONVEX_HULL', 'PASSIVE', use_margin=True, margin=0.001)
            self.acd(hide_children=True)
        else:
            # Note: Using MESH collision shape may cause objects to stay on top of container
            self.add_rigid_body('MESH', 'PASSIVE', use_margin=True, margin=0.001)
    
    def _compute_volume(self) -> None:
        """Override to load from json file."""
        if not self._path:
            return
            
        for file in self._path.parent.iterdir():
            if file.suffix == '.json':
                with open(file, 'r') as f:
                    data = json.load(f)
                    if data.get('filename') == self._path.name:
                        self._volume = data.get('volume')
                break



