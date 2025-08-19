"""
3x4 P matrix from Blender camera

K = Intrinsic properties: (Optical center, focal length, skew, aspect ratio)
RT = Extrinsic properties: (Rotation, Translation)
"""

import bpy
from mathutils import Matrix, Vector
from typing import Tuple


def get_sensor_size(sensor_fit: str, sensor_x: float, sensor_y: float) -> float:
    """Get sensor size based on fit mode.
    
    Args:
        sensor_fit: Sensor fit mode ('VERTICAL', 'HORIZONTAL', 'AUTO')
        sensor_x: Sensor width in mm
        sensor_y: Sensor height in mm
        
    Returns:
        Sensor size in mm
    """
    if sensor_fit == 'VERTICAL':
        return sensor_y
    return sensor_x


def get_sensor_fit(sensor_fit: str, size_x: float, size_y: float) -> str:
    """Determine sensor fit mode.
    
    Args:
        sensor_fit: Current sensor fit mode
        size_x: Image width in pixels
        size_y: Image height in pixels
        
    Returns:
        Determined sensor fit mode
    """
    if sensor_fit == 'AUTO':
        if size_x >= size_y:
            return 'HORIZONTAL'
        else:
            return 'VERTICAL'
    return sensor_fit


def get_calibration_matrix_K_from_blender(camd) -> Matrix:
    """Get intrinsic calibration matrix K from Blender camera.
    
    Args:
        camd: Blender camera data
        
    Returns:
        Intrinsic calibration matrix K
    """
    if camd.type != 'PERSP':
        raise ValueError('Non-perspective cameras not supported')
        
    scene = bpy.context.scene
    f_in_mm = camd.lens
    scale = scene.render.resolution_percentage / 100
    resolution_x_in_px = scale * scene.render.resolution_x
    resolution_y_in_px = scale * scene.render.resolution_y
    sensor_size_in_mm = get_sensor_size(camd.sensor_fit, camd.sensor_width, camd.sensor_height)
    sensor_fit = get_sensor_fit(
        camd.sensor_fit,
        scene.render.pixel_aspect_x * resolution_x_in_px,
        scene.render.pixel_aspect_y * resolution_y_in_px
    )
    pixel_aspect_ratio = scene.render.pixel_aspect_y / scene.render.pixel_aspect_x
    
    if sensor_fit == 'HORIZONTAL':
        view_fac_in_px = resolution_x_in_px
    else:
        view_fac_in_px = pixel_aspect_ratio * resolution_y_in_px
        
    pixel_size_mm_per_px = sensor_size_in_mm / f_in_mm / view_fac_in_px
    s_u = 1 / pixel_size_mm_per_px
    s_v = 1 / pixel_size_mm_per_px / pixel_aspect_ratio

    # Parameters of intrinsic calibration matrix K
    u_0 = resolution_x_in_px / 2 - camd.shift_x * view_fac_in_px
    v_0 = resolution_y_in_px / 2 + camd.shift_y * view_fac_in_px / pixel_aspect_ratio
    skew = 0  # only use rectangular pixels

    K = Matrix(
        ((s_u, skew, u_0),
        (   0,  s_v, v_0),
        (   0,    0,   1))
    )
    return K


def get_3x4_RT_matrix_from_blender(cam) -> Matrix:
    """Get 3x4 extrinsic matrix RT from Blender camera.
    
    Args:
        cam: Blender camera object
        
    Returns:
        Extrinsic matrix RT
    """
    # bcam stands for blender camera
    R_bcam2cv = Matrix(
        ((1, 0,  0),
        (0, 1, 0),
        (0, 0, 1))
    )

    location, rotation = cam.matrix_world.decompose()[0:2]
    R_world2bcam = rotation.to_matrix().transposed()
    T_world2bcam = -1 * R_world2bcam @ location

    R_world2cv = R_bcam2cv @ R_world2bcam
    T_world2cv = R_bcam2cv @ T_world2bcam
    
    RT = Matrix((
        R_world2cv[0][:] + (T_world2cv[0],),
        R_world2cv[1][:] + (T_world2cv[1],),
        R_world2cv[2][:] + (T_world2cv[2],)
    ))
    return RT


def get_3x4_P_matrix_from_blender(cam) -> Tuple[Matrix, Matrix, Matrix]:
    """Get 3x4 projection matrix P from Blender camera.
    
    Args:
        cam: Blender camera object
        
    Returns:
        Tuple of (P, K, RT) matrices
    """
    K = get_calibration_matrix_K_from_blender(cam.data)
    RT = get_3x4_RT_matrix_from_blender(cam)
    P = K @ RT
    return P, K, RT


# Example usage
if __name__ == "__main__":
    # Insert your camera name here
    cam = bpy.data.objects.get('Camera')
    if cam:
        P, K, RT = get_3x4_P_matrix_from_blender(cam)
        print("Projection matrix P:")
        print(P)
        print("Intrinsic matrix K:")
        print(K)
        print("Extrinsic matrix RT:")
        print(RT)