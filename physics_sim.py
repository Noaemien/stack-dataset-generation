import bpy
import os
import sys
import argparse
from pathlib import Path
import random
import numpy as np
import json
from typing import Tuple, List, Optional

# Add current directory to Python path
dir_path = os.path.dirname(bpy.data.filepath)
if dir_path not in sys.path:
    sys.path.append(dir_path)

from source.Containers import Container
from source.BatchPhysicsObject import BatchPhysicsObject
from source.Scene import Scene
from source.Delimiter import Delimiter
from source.Utils import Utils


def clear_scene() -> None:
    """Clear all objects with specific prefixes from the scene."""
    Utils.delete_objects_with_prefix("Instance")
    Utils.delete_objects_with_prefix("BaseObject")
    Utils.delete_objects_with_prefix("Container")
    Utils.delete_objects_with_prefix("Delimiter")
    Utils.delete_objects_with_prefix("obj_copy")
    Utils.delete_objects_with_prefix("coacd")


def init_scene(
    folder_path: Path,
    container: Container,
    scaling: Tuple[float, float, float]
) -> Tuple[Delimiter, Delimiter, Delimiter, Delimiter, Delimiter, BatchPhysicsObject, float]:
    """Initialize the scene with container and delimiters.
    
    Args:
        folder_path: Path to the object folder
        container: Container object
        scaling: Scaling factors for the scene
        
    Returns:
        Tuple of (delimiter_top, delimiter_outer, delimiter_container, delimiter_unitcube, 
                  delimiter_inner, obj, obj_scale)
    """
    if bpy.context.active_object:
        bpy.ops.object.mode_set(mode='OBJECT')

    print(f"Looking for object at {folder_path}")
    if str(folder_path).endswith("_0"):
        container.load("assets/containers/box2", choose_random=False, name="Container", use_acd=True) 
    else:
        container.load("assets/containers", choose_random=True, name="Container", use_acd=True) 

    delimiter_top = Delimiter() 
    # Shouldn't be too large on XY so that it doesn't catch objects balancing on the edge
    if container.file_name.startswith("no_container"):  # A bit lower than normal
        delimiter_top.create_box(name="Delimiter_top", location=(0, 0, 0.55), size_x=0.6, size_y=0.6, size_z=0.1)
    else: 
        delimiter_top.create_box(name="Delimiter_top", location=(0, 0, 1.1), size_x=0.6, size_y=0.6, size_z=0.1)
    
    delimiter_outer = Delimiter()
    delimiter_outer.create_box(name="Delimiter_outer", location=(0, 0, 1), size_x=1*scaling[0], size_y=1*scaling[1], size_z=2)

    delimiter_container = Delimiter()
    delimiter_container.create_convex_hull(container.get_object(), name="Delimiter_Container")

    delimiter_unitcube = Delimiter()
    delimiter_unitcube.create_box(name="Delimiter_unitcube", location=(0, 0, 0.5), size_x=1.0, size_y=1.0, size_z=1.0)

    delimiter_inner = Delimiter()
    delimiter_inner.create_box(name="Delimiter_inner", location=(0, 0, 0.5), size_x=0.5, size_y=0.5, size_z=0.5)

    obj = BatchPhysicsObject()

    obj_scale = np.random.triangular(0.15, 0.2, 0.25)
    if str(folder_path).endswith("_0"):
        obj_scale = 0.2
        
    obj.load_from_folder(
        folder_path, obj_type='OBJ', 
        name="BaseObject", location=(0, 0, -5), rescale=True,
        set_origin=True, origin_type='ORIGIN_GEOMETRY', decimate=True, 
        rescale_max_dimension=obj_scale
    )
    
    return delimiter_top, delimiter_outer, delimiter_container, delimiter_unitcube, delimiter_inner, obj, obj_scale


def process_object(
    folder_path: Path,
    obj_name: str,
    container: Container,
    scaling: Tuple[float, float, float] = (1, 1, 1)
) -> None:
    """Process a single object through physics simulation.
    
    This function:
    1. Clears the scene
    2. Initializes the scene with container and delimiters
    3. Generates batches of objects
    4. Runs physics simulation
    5. Filters objects based on position
    6. Joins remaining objects
    7. Exports results and saves metadata
    
    Args:
        folder_path: Path to the object folder
        obj_name: Name of the object file
        container: Container object
        scaling: Scaling factors for the scene (x, y, z)
    """
    clear_scene()
    delimiter_top, delimiter_outer, delimiter_container, delimiter_unitcube, delimiter_inner, obj, obj_scale = init_scene(folder_path, container, scaling)
    
    # Prepare batch grid parameters
    offset = 0.2
    count_x = int(scaling[0] / offset)
    count_y = int(scaling[1] / offset)
    start_location = (
        -scaling[0] / 2.0 + offset / 2,
        -scaling[1] / 2.0 + offset / 2,  
        scaling[2] + 0.05         # Start just above the container's top
    )

    n_obj_generated = 0
    max_it = 10
    end_log = ""
    success = False
    
    for i in range(max_it):
        rigid_body_world = bpy.context.scene.rigidbody_world
        rigid_body_world.point_cache.frame_start = 0
        rigid_body_world.point_cache.frame_end = 70
        
        n_obj_generated += obj._add_batch(
            start_location=start_location, 
            count_x=count_x, 
            count_y=count_y
        )
        Scene.bake_simulation(obj.get_batch() + [container.get_object()])
        Scene.apply_simulation(obj.get_batch()) 
        
        print(f"Checking if objects are inside the container...")
        objs_in_bounds = delimiter_outer.check_collision_with_batch(obj)
        obj_outside_bounds = [obj_item for obj_item in obj.get_batch() if objs_in_bounds is None or obj_item not in objs_in_bounds]

        # Delete objects outside bounds
        obj.remove_from_batch(obj_outside_bounds)
        print(f"Removing {len(obj_outside_bounds)} objects outside bounds")

        if delimiter_top.check_collision_with_batch(obj):
            print("Simulation done")
            success = True
            end_log = "Top reached"
            break
        elif not str(folder_path).endswith("_0") and random.random() < 0.005:
            # Allow partially filled boxes
            success = True
            end_log = "Partially full scene"
            break    
        elif i == max_it - 1:
            end_log = "Max # batches reached, and still not full"
            if str(folder_path).endswith("_0"):
                success = False
            else:
                success = True
            break

        print(f"Batch {i} done")
       
    n_objects = len(Utils.select_objects_with_prefix("Instance"))
    print("#Objects left in final result:", n_objects, "/", n_obj_generated)

    obj.join_batch()
    bpy.ops.export_scene.fbx(filepath=str(folder_path / "Instance.fbx"), use_selection=True)

    volume_ratio_with_edges = delimiter_unitcube.get_object_volume(obj.get_batch()[0], keep_intersection=True)
    volume_ratio_no_edges = 8 * delimiter_inner.get_object_volume(obj.get_batch()[0], keep_intersection=True)
    print(f"Container volume: {container.get_volume()}")
    print(f"Volume ratio with edges: {volume_ratio_with_edges}")
    print(f"Volume ratio without edges: {volume_ratio_no_edges}")

    Utils.select_objects_with_prefix("Container")
    bpy.ops.export_scene.fbx(filepath=str(folder_path / "Container.fbx"), use_selection=True)

    Utils.select_objects_with_prefix("BaseObject")
    selected_objects = bpy.context.selected_objects
    if len(selected_objects) != 1:
        raise ValueError(f"Expected 1 selected object, got {len(selected_objects)}")
    obj_vol = Utils.get_object_volume(selected_objects[0])    

    # Save data
    value_dict = {
        "n_obj_generated": n_obj_generated,
        "volume_ratio_with_edges": volume_ratio_with_edges,
        "volume_ratio_no_edges": volume_ratio_no_edges,
        "success": success, 
        "end_log": end_log, 
        "obj_origins": n_objects,
        "object": {
            "volume": obj_vol,
            "path": obj_name,
            "scale": obj_scale
        },
        "container": {
            "container_scaling": scaling,
            "file": container.file_name
        }
    }

    Utils.save_data_json(folder_path=str(folder_path), dictionary=value_dict)


def main(start_idx: int, end_idx: Optional[int], folder_path: str) -> None:
    """Main function to process objects through physics simulation.
    
    Args:
        start_idx: Start index for processing
        end_idx: End index for processing (None for all)
        folder_path: Path to the dataset folder
    """
    Scene.set_frame_range(0, 70)

    subfolders = sorted(next(os.walk(folder_path))[1])
    # Ensure end_idx is within the range, defaulting to the end of the subfolders list if not provided
    if end_idx is None or end_idx > len(subfolders):
        end_idx = len(subfolders)
    subfolders_to_process = subfolders[start_idx:end_idx]
    
    # Pre-compute ACD for containers if needed
    PRECOMPUTE_CONTAINERS_ACD = False
    if PRECOMPUTE_CONTAINERS_ACD:
        containers_path = Path("assets/containers")
        if containers_path.exists():
            for folder in sorted(containers_path.iterdir()):
                if folder.is_dir():
                    print(f"Computing ACD for: {folder}")
                    container = Container(folder)
                    container.load(path=folder, use_acd=True, choose_random=False)

    print("Processing subfolders ", subfolders_to_process)
    
    for subfolder in subfolders_to_process:
        current_path = os.path.join(folder_path, subfolder)
        for root, dirs, files in sorted(os.walk(current_path)):
            # Check if simulation already succeeded
            results_file = os.path.join(root, "simulation_results.json")
            if os.path.exists(results_file):
                try:
                    with open(results_file, 'r') as f:
                        data = json.load(f)
                    if data.get("success") is True:
                        print(f"Already successful {root}, skipping...")
                        continue
                except (json.JSONDecodeError, KeyError):
                    pass  # File corrupted or missing success key, reprocess

            # Process OBJ files
            for file in files:
                if file.endswith(".obj"):
                    if current_path.endswith("_0"):
                        random_scaling = (1, 1, 1)
                    else:
                        random_scaling = (
                            np.random.triangular(0.6, 1.0, 1.5), 
                            np.random.triangular(0.5, 1.0, 1.1),  # vertical axis
                            np.random.triangular(0.6, 1.0, 1.5)
                        )
              
                    container = Container("assets/containers", scaling=random_scaling)
                    process_object(
                        folder_path=Path(root), 
                        obj_name=file, 
                        container=container, 
                        scaling=random_scaling
                    )


def parse_args() -> Tuple[int, Optional[int], str]:
    """Parse command line arguments using argparse.
    
    Returns:
        Tuple of (start_idx, end_idx, folder_path)
    """
    parser = argparse.ArgumentParser(description="Run physics simulation on 3D objects.")
    parser.add_argument("--start", "-s", type=int, default=0, help="Start index for processing")
    parser.add_argument("--end", "-e", type=int, help="End index for processing (None for all)")
    parser.add_argument("--path", "-p", type=str, required=True, help="Path to the dataset folder")
    
    # Parse only the arguments after "--"
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
        
    return args.start, args.end, args.path


if __name__ == "__main__":
    # In typical blender fashion, first start by deleting default cube
    Utils.delete_objects_with_prefix("Cube")

    start_idx, end_idx, folder_path = parse_args()
    main(start_idx, end_idx, folder_path)
