import bpy
import os
import shutil
import bmesh
import mathutils
import sys
import argparse
from typing import List, Tuple, Optional


def is_watertight(object: bpy.types.Object, check_self_intersection: bool = True) -> bool:
    """Check if an object is watertight (manifold).
    
    Args:
        object: Blender object to check
        check_self_intersection: Whether to check for self-intersections
        
    Returns:
        True if the object is watertight, False otherwise
    """
    bpy.context.view_layer.objects.active = object

    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_non_manifold(extend=False)
    bm = bmesh.from_edit_mesh(object.data)

    is_watertight = True

    for v in bm.verts:
        if v.select:
            is_watertight = False
            break

    if is_watertight and check_self_intersection:
        bvh_tree = mathutils.bvhtree.BVHTree.FromBMesh(bm, epsilon=0.000001)
        intersections = bvh_tree.overlap(bvh_tree)

        if intersections:
            is_watertight = False

    bpy.ops.object.mode_set(mode='OBJECT')
    return is_watertight


def has_multiple_components(object: bpy.types.Object) -> bool:
    """Check if an object has multiple disconnected components.
    
    Args:
        object: Blender object to check
        
    Returns:
        True if the object has multiple components, False otherwise
    """
    object.select_set(True)
    bpy.context.view_layer.objects.active = object

    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.separate(type='LOOSE')
    bpy.ops.object.mode_set(mode='OBJECT')
    
    # Count selected objects (should be more than 1 if multiple components)
    object_count = len(bpy.context.selected_objects)
    
    return object_count > 1


def check_obj_file(filepath: str, verbose: bool = False) -> bool:
    """Check if an OBJ file represents a valid single-component watertight object.
    
    Args:
        filepath: Path to the OBJ file
        verbose: Whether to print detailed information
        
    Returns:
        True if the object is valid, False otherwise
    """
    bpy.ops.wm.obj_import(filepath=filepath)
    obj = bpy.context.selected_objects[0]

    watertight = is_watertight(obj)
    multiple_components = has_multiple_components(obj)

    if verbose:
        print(f"File at {filepath}")
        print(f"Watertight: {watertight}")
        print(f"Multiple connected components: {multiple_components}")

    return watertight and not multiple_components


def process_folder(directory: str, verbose: bool = False) -> None:
    """Process a folder of 3D objects, filtering out invalid ones.
    
    This function checks each object in the directory to ensure it is:
    1. Watertight (manifold)
    2. A single connected component
    
    Invalid objects are deleted, and valid ones are duplicated for dataset augmentation.
    
    Args:
        directory: Path to the directory containing object folders
        verbose: Whether to print detailed information
    """
    if not os.path.exists(directory):
        raise FileNotFoundError(f"Directory does not exist: {directory}")
        
    count = 0
    folder_names = sorted(os.listdir(directory))
    
    for foldername in folder_names:
        folder_path = os.path.join(directory, foldername)

        if os.path.isdir(folder_path):
            # Remove empty folders
            if not os.listdir(folder_path):
                shutil.rmtree(folder_path)
                if verbose:
                    print(f"Deleted empty folder: {folder_path}")
                continue

            # Find OBJ files
            obj_files = [f for f in os.listdir(folder_path) if f.endswith('.obj')]
            
            if not obj_files:
                if verbose:
                    print(f"No OBJ files found in: {folder_path}")
                continue

            obj_path = os.path.join(folder_path, obj_files[0])

            if not check_obj_file(obj_path, verbose):
                shutil.rmtree(folder_path)
                count += 1
                if verbose:
                    print(f"Deleted invalid folder: {folder_path}")
            else:
                # Duplicate folders for dataset augmentation
                duplicate_folders = True
                if duplicate_folders:
                    for i in range(3):
                        new_folder = f"{folder_path}_{i}"
                        os.makedirs(new_folder, exist_ok=True)
                        shutil.copy(obj_path, os.path.join(new_folder, obj_files[0]))
                        if verbose:
                            print(f"Copied {obj_files[0]} to {new_folder}")
                    shutil.rmtree(folder_path)

            if verbose:
                print("")
                
    if verbose:
        print(f"Deleted {count} invalid folders")


def parse_args() -> Tuple[Optional[str], bool]:
    """Parse command line arguments using argparse.
    
    Returns:
        Tuple of (directory, verbose)
    """
    parser = argparse.ArgumentParser(description="Clean and filter 3D object dataset.")
    parser.add_argument("--path", "-p", type=str, required=True, help="Path to the dataset directory")
    parser.add_argument("--verbose", "-v", action="store_true", help="Print detailed information")
    
    # Parse only the arguments after "--"
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
        
    return args.path, args.verbose
                

if __name__ == "__main__":
    directory, verbose = parse_args()

    # Clear the scene
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    
    if directory:
        process_folder(directory, verbose)
    else:
        print("Error: Directory must be specified with -p flag")
        sys.exit(1)
