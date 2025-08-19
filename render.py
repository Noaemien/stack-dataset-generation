import bpy
from mathutils import Matrix, Vector
import numpy as np
from numpy import cos, sin
import random
import os
import json
import sys
import argparse
from datetime import datetime
from typing import List, Tuple, Optional

# Add current directory to Python path
dir_path = os.path.dirname(bpy.data.filepath)
if dir_path not in sys.path:
    sys.path.append(dir_path)

import source.CameraMatrix as camera_module
from source.Utils import Utils

# Clear existing cameras
Utils.delete_objects_with_prefix("Camera")

# Material lists
floor_mats = [
    "concrete_slab", "factory.door", "factory_black", "factory.white_glossy",
    "factory_floor_black", "factory_floor_white", "factory_plastic", "lead", 
    "paper", "tarp"
]
floor_mats += 10 * ["TexturedFloor"] 

box_mats = ["wood_chest", "wood_02", "Box"]
box_mats += 5 * ["TexturedMat"]

object_mats = ["metal_valve_red"] + 5 * ["metallic-dented"]
plastic_mats = [f"Plastic{'' if i == 0 else f'.{i:03d}'}" for i in range(21)]
object_mats += plastic_mats


def add_cameras(
    thetas: List[float],
    phis: List[float],
    radius: float,
    camera_mats: Optional[List] = None,
    world_mats: Optional[List] = None,
    camera_id: int = 1,
    scaling_factors: Tuple[float, float, float] = (1.0, 1.0, 1.0)
) -> Tuple[List, List]:
    """Add cameras to the scene with specified parameters.
    
    Args:
        thetas: List of theta angles
        phis: List of phi angles
        radius: Camera distance from origin
        camera_mats: List to store camera matrices
        world_mats: List to store world matrices
        camera_id: Starting camera ID
        scaling_factors: Scaling factors for camera positions
        
    Returns:
        Tuple of (camera_mats, world_mats)
    """
    if camera_mats is None:
        camera_mats = []
    if world_mats is None:
        world_mats = []

    random_angle = 0.2 * np.pi / 12

    for theta in thetas:
        for phi0 in phis:
            phi = -3.1415 / 2
            
            print("Camera", camera_id)
            camera_data = bpy.data.cameras.new(name='Camera' + str(camera_id))
            camera_object = bpy.data.objects.new('Camera' + str(camera_id), camera_data)
            bpy.context.scene.collection.objects.link(camera_object)

            rotx = Matrix.Rotation(theta, 4, 'X')
            
            trans_vec = Vector((
                radius * scaling_factors[0] * sin(theta) * cos(phi),
                radius * scaling_factors[1] * sin(theta) * sin(phi),
                radius * cos(theta) 
            ))
            glob_rotz = Matrix.Rotation(phi0, 4, 'Z')
            trans = Matrix.Translation(trans_vec)
            camera_object.matrix_world = glob_rotz @ trans @ rotx

            bpy.ops.object.select_all(action='DESELECT')
            camera_object.select_set(True)
            seed = random.randint(0, 1000)
            if camera_id == 0:
                bpy.ops.object.randomize_transform(
                    random_seed=seed, use_loc=False, 
                    use_scale=False, rot=(0, 0, 0)
                )
            else:
                bpy.ops.object.randomize_transform(
                    random_seed=seed, use_loc=False, 
                    use_scale=False, rot=(random_angle, random_angle, random_angle)
                )
            
            P, K, RT = camera_module.get_3x4_P_matrix_from_blender(camera_object)
            K0 = np.array(K)
            K = np.eye(4)
            K[:3, :3] = K0
            RT0 = np.array(RT)
            RT = np.eye(4)
            RT[:3, :] = RT0
            camera_mats.append(K)
            world_mats.append(np.linalg.inv(RT))
            camera_id += 1

    return camera_mats, world_mats


def generate_transform_json(
    camera_mats: List,
    world_mats: List,
    folder_path: str = ""
) -> None:
    """Generate transforms.json file for NeRF training.
    
    Args:
        camera_mats: List of camera matrices
        world_mats: List of world matrices
        folder_path: Path to save the JSON file
    """
    if not camera_mats:
        raise ValueError("No camera matrices provided")
        
    intrinsic_matrix = camera_mats[0]
    transform = {}
    transform["camera_model"] = "OPENCV"
    transform["fl_x"] = intrinsic_matrix[0][0]
    transform["fl_y"] = intrinsic_matrix[1][1]
    transform["cx"] = intrinsic_matrix[0][2]
    transform["cy"] = intrinsic_matrix[1][2]
    transform["w"] = bpy.data.scenes["Scene"].render.resolution_x
    transform["h"] = bpy.data.scenes["Scene"].render.resolution_y
    transform["k1"] = 0
    transform["k2"] = 0
    transform["k3"] = 0
    transform["k4"] = 0
    transform["p1"] = 0
    transform["p2"] = 0
    
    frame = []
    for i in range(len(world_mats)):
        frame_i = {}
        filename = str(i + 1)
        while len(filename) < 4:
            filename = "0" + filename
        filename = "RGB" + filename
        frame_i["file_path"] = os.path.join("RGB", filename + ".png") 
        frame_i["transform_matrix"] = world_mats[i].tolist()
        frame.append(frame_i)
    transform["frames"] = frame

    json_path = os.path.join(folder_path, "transforms.json")
    with open(json_path, "w") as f:
        json.dump(transform, f, indent=4)

    print("Saved transforms.json")


def render_cameras(folder_path: str, single_cam: bool) -> List[str]:
    """Render images from all cameras.
    
    Args:
        folder_path: Path to save rendered images
        single_cam: Whether to render only the first camera
        
    Returns:
        List of image paths
    """
    img_paths = []

    cameras = [obj for obj in bpy.data.objects if obj.type == 'CAMERA']
    for i, cam in enumerate(cameras):
        print("Render", cam.name)
        cam_id = cam.name[6:]  # Remove "Camera" prefix
        
        if int(cam_id) == 0:
            bpy.data.scenes["Scene"].node_tree.nodes["map_range"].inputs[1].default_value = 1.4
            bpy.data.scenes["Scene"].node_tree.nodes["map_range"].inputs[2].default_value = 2.5
        else:
            if single_cam:
                break
            bpy.data.scenes["Scene"].node_tree.nodes["map_range"].inputs[1].default_value = 2.5
            bpy.data.scenes["Scene"].node_tree.nodes["map_range"].inputs[2].default_value = 4

        bpy.context.scene.frame_set(int(cam_id))
        bpy.context.scene.camera = cam
        filename = str(cam_id)
        while len(filename) < 4:
            filename = "0" + filename
        filename = "RGB" + filename

        # Set output paths
        depth_path = os.path.join(folder_path, "Depth")
        depth_normalized_path = os.path.join(folder_path, "DepthNormalized")
        normal_path = os.path.join(folder_path, "Normal")
        mask_ground_path = os.path.join(folder_path, "MaskGround")
        mask_object_path = os.path.join(folder_path, "MaskObject")
        mask_box_path = os.path.join(folder_path, "MaskBox")
        rgb_folder = os.path.join(folder_path, "RGB")
        
        bpy.data.scenes["Scene"].node_tree.nodes["depth_out"].base_path = depth_path
        bpy.data.scenes["Scene"].node_tree.nodes["depth_normalized_out"].base_path = depth_normalized_path
        bpy.data.scenes["Scene"].node_tree.nodes["normal_out"].base_path = normal_path
        bpy.data.scenes["Scene"].node_tree.nodes["mask_ground_out"].base_path = mask_ground_path
        bpy.data.scenes["Scene"].node_tree.nodes["mask_object_out"].base_path = mask_object_path
        bpy.data.scenes["Scene"].node_tree.nodes["mask_box_out"].base_path = mask_box_path
        
        img_path = os.path.join(rgb_folder, filename)
        img_paths.append(img_path)

        # Render
        bpy.context.scene.render.filepath = img_path
        bpy.ops.render.render(write_still=True)
        bpy.context.scene.render.filepath = folder_path
        
    return img_paths


def setup_plastic_materials() -> None:
    """Setup plastic materials with random colors."""
    base_material_name = "Plastic"
    if base_material_name not in bpy.data.materials:
        print(f"Material '{base_material_name}' not found!")
        return

    base_material = bpy.data.materials[base_material_name]

    # Create copies of the Plastic material up to Plastic.020
    range_h0 = random.uniform(0, 1)
    range_h1 = random.uniform(range_h0, range_h0 + 1)
    range_s0 = random.uniform(0, 1)
    range_s1 = random.uniform(range_s0, 1) 
    range_v0 = random.uniform(0, 1)
    range_v1 = random.uniform(range_v0, 1)

    for i in range(21):
        material_name = f"Plastic{'' if i == 0 else f'.{i:03d}'}"

        if material_name not in bpy.data.materials:
            new_material = base_material.copy()
            new_material.name = material_name

        material = bpy.data.materials[material_name]
        if material.node_tree:
            for node in material.node_tree.nodes:
                if node.type == "BSDF_PRINCIPLED":  
                    h = random.uniform(range_h0, range_h1)  
                    s = random.uniform(range_s0, range_s1)  
                    v = random.uniform(range_v0, range_v1)  
                    
                    import colorsys
                    r, g, b = colorsys.hsv_to_rgb(h, s, v)
                    node.inputs["Base Color"].default_value = (r, g, b, 1)  


def import_obj_fbx(folder_path: str, file: str, different_materials: bool = False) -> None:
    """Import OBJ/FBX file and apply materials.
    
    Args:
        folder_path: Path to the folder containing the file
        file: Name of the file to import
        different_materials: Whether to apply different materials to components
    """
    bpy.ops.object.select_all(action='DESELECT')

    file_path = os.path.join(folder_path, file)
    bpy.ops.import_scene.fbx(filepath=file_path)
    imported_objects = bpy.context.selected_objects
    if not imported_objects:
        raise ValueError(f"No objects imported from {file_path}")
        
    obj = imported_objects[0]  
    obj.name = "Subject"

    setup_plastic_materials() 
    if different_materials:  # Apply different materials to each component
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.separate(type='LOOSE') 
        bpy.ops.object.mode_set(mode='OBJECT')

        components = [o for o in bpy.context.selected_objects if o != obj]

        for comp in components:
            random_material = random.choice(plastic_mats) 
            Utils.apply_material(comp, random_material)

        for comp in components:
            comp.pass_index = 10
    else: 
        random_material = random.choice(object_mats)
        Utils.apply_material(obj, random_material)

        obj.pass_index = 10


def import_container_fbx(folder_path: str, file: str, box_mat: str) -> None:
    """Import container FBX file and apply material.
    
    Args:
        folder_path: Path to the folder containing the file
        file: Name of the file to import
        box_mat: Material to apply to the container
    """
    bpy.ops.object.select_all(action='DESELECT')

    file_path = os.path.join(folder_path, file)
    print("LOADING", file_path)
    bpy.ops.import_scene.fbx(filepath=file_path)
    imported_objects = bpy.context.selected_objects
    if not imported_objects:
        raise ValueError(f"No objects imported from {file_path}")
        
    obj = imported_objects[0]
    obj.name = "Container"

    Utils.apply_material(obj, box_mat)
    obj.pass_index = 12
    
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.shade_smooth()


def process_object(folder_path: str, file: str, single_cam: bool) -> None:
    """Process a single object for rendering.
    
    This function:
    1. Loads simulation results
    2. Sets up cameras
    3. Imports objects and applies materials
    4. Renders images from multiple viewpoints
    5. Generates transforms.json for NeRF training
    6. Updates simulation results with render metadata
    
    Args:
        folder_path: Path to the object folder
        file: Name of the Instance.fbx file
        single_cam: Whether to render only from the top camera
    """
    json_path = os.path.join(folder_path, "simulation_results.json")
    with open(json_path, "r") as f:
        simulation_data = json.load(f)
    container_scaling = simulation_data["container"]["container_scaling"]
    simulation_data["render"] = {}

    radius = 4
    imax = 6
    jmax = 6
    thetas = [i/imax * np.pi/2 for i in range(1, imax)] 
    phis = [j/jmax * 2 * np.pi for j in range(1, jmax + 1)] 

    bpy.context.view_layer.objects.active = bpy.context.scene.objects[0]
    bpy.ops.object.mode_set(mode='OBJECT')
    
    Utils.delete_objects_with_prefix("Camera")
    camera_mats, world_mats = add_cameras([0], [0], 2.5, camera_id=0)
    if not single_cam:
        camera_mats, world_mats = add_cameras(thetas, phis, radius, scaling_factors=container_scaling)
        
    Utils.delete_objects_with_prefix("Subject")
    different_materials = random.random() > 0.7
    import_obj_fbx(folder_path, file, different_materials)

    Utils.delete_objects_with_prefix("Container")
    if not simulation_data["container"]["file"].startswith("no_container"):
        box_mat = random.choice(box_mats)
        simulation_data["render"]["box_mat"] = box_mat
        import_container_fbx(folder_path, "Container.fbx", box_mat)

    floor_obj = bpy.data.objects.get("Floor")
    if floor_obj:
        floor_mat = random.choice(floor_mats)
        Utils.apply_material(floor_obj, floor_mat)

    render_output_path = os.path.join(folder_path, "MultiView")
    render_cameras(render_output_path, single_cam)
    generate_transform_json(camera_mats, world_mats, render_output_path)
    
    simulation_data["render"]["completion_date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    simulation_data["render"]["floor_mat"] = floor_mat if floor_obj else None
    simulation_data["render"]["different_materials"] = different_materials
    
    with open(json_path, "w") as f:
        json.dump(simulation_data, f, indent=4)


def main(start_idx: int, end_idx: Optional[int], folder_path: str, single_cam: bool) -> None:
    """Main function to process objects for rendering.
    
    Args:
        start_idx: Start index for processing
        end_idx: End index for processing (None for all)
        folder_path: Path to the dataset folder
        single_cam: Whether to render only from the top camera
    """
    subfolders = sorted(next(os.walk(folder_path))[1])

    if end_idx is None or end_idx > len(subfolders):
        end_idx = len(subfolders)
    subfolders_to_process = subfolders[start_idx:end_idx]

    for subfolder in subfolders_to_process:
        current_path = os.path.join(folder_path, subfolder)

        for root, dirs, files in sorted(os.walk(current_path)):
            # Skip if render already exists
            skip_if_recent = True
            if skip_if_recent:
                json_path = os.path.join(folder_path, subfolder, "simulation_results.json")
                if os.path.exists(json_path):
                    try:
                        with open(json_path, "r") as f:
                            simulation_data = json.load(f)
                        if 'render' in simulation_data:
                            print(f"Render exists in {root}, skipping")
                            continue
                    except (json.JSONDecodeError, KeyError):
                        pass  # File corrupted, reprocess

            # Process Instance.fbx files
            for file in files:
                if file == "Instance.fbx":
                    process_object(root, file, single_cam)


def parse_args() -> Tuple[int, Optional[int], str, bool]:
    """Parse command line arguments using argparse.
    
    Returns:
        Tuple of (start_idx, end_idx, folder_path, single_cam)
    """
    parser = argparse.ArgumentParser(description="Render 3D objects from multiple viewpoints.")
    parser.add_argument("--start", "-s", type=int, default=0, help="Start index for processing")
    parser.add_argument("--end", "-e", type=int, help="End index for processing (None for all)")
    parser.add_argument("--path", "-p", type=str, required=True, help="Path to the dataset folder")
    parser.add_argument("--single_cam", action="store_true", help="Render only from the top camera")
    
    # Parse only the arguments after "--"
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
        
    return args.start, args.end, args.path, args.single_cam


if __name__ == "__main__":
    start_idx, end_idx, folder_path, single_cam = parse_args()
    main(start_idx, end_idx, folder_path, single_cam)
