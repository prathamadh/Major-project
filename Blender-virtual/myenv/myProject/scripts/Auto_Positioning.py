import bpy
import numpy as np
from mathutils import Vector
from pyblend.lighting import config_world
from pyblend.object import load_obj
from pyblend.material import random_mat
from pyblend.utils import BlenderRemover, ArgumentParserForBlender, debug
from pyblend.render import config_render, render_image, enable_depth_render, enable_normal_render

def fit_and_position_object(obj, target_size=2.5):
    bpy.context.view_layer.update()
    bbox = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    min_corner = np.min(np.array([v.to_tuple() for v in bbox]), axis=0)
    max_corner = np.max(np.array([v.to_tuple() for v in bbox]), axis=0)
    dimensions = max_corner - min_corner

    scale_factor = target_size / max(dimensions)
    obj.scale = (scale_factor, scale_factor, scale_factor)

    bpy.context.view_layer.update()
    bbox = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    min_corner = np.min(np.array([v.to_tuple() for v in bbox]), axis=0)
    max_corner = np.max(np.array([v.to_tuple() for v in bbox]), axis=0)

    obj.location.z -= min_corner[2]

def get_camera_distance(obj, margin=1.5):
    bpy.context.view_layer.update()
    bbox = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    min_corner = np.min(np.array([v.to_tuple() for v in bbox]), axis=0)
    max_corner = np.max(np.array([v.to_tuple() for v in bbox]), axis=0)
    dimensions = max_corner - min_corner

    max_dimension = max(dimensions)
    distance = max_dimension * margin
    return distance

def get_object_center(obj):
    bpy.context.view_layer.update()
    bbox = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    min_corner = np.min(np.array([v.to_tuple() for v in bbox]), axis=0)
    max_corner = np.max(np.array([v.to_tuple() for v in bbox]), axis=0)
    center = (min_corner + max_corner) / 2.0
    return center

def render_teaser(args):
    config_render(res_x=320, res_y=240)
    remover = BlenderRemover()
    remover.clear_all()
    config_world(0.5)
    camera = bpy.data.objects["Camera"]

    exr_depth_node, png_depth_node = enable_depth_render("/Users/prakanda1/Desktop/Major-project/Major-project/Blender-virtual/myenv/myProject/Auto_Postioning_Images", reverse=True)
    png_normal_node = enable_normal_render("/Users/prakanda1/Desktop/Major-project/Major-project/Blender-virtual/myenv/myProject/Auto_Postioning_Images")

    obj_path = "/Users/prakanda1/Desktop/Major-project/Major-project/Blender-virtual/myenv/myProject/docs/InteriorTest.obj"
    model = load_obj(obj_path, "model", center=True)

    fit_and_position_object(model)

    camera_distance = get_camera_distance(model)
    object_center = get_object_center(model)

    camera.data.clip_start = 0.1
    camera.data.clip_end = camera_distance * 3
    camera.data.angle = np.radians(60)

    camera.constraints.clear()
    constraint = camera.constraints.new(type='TRACK_TO')
    constraint.target = model
    constraint.track_axis = 'TRACK_NEGATIVE_Z'
    constraint.up_axis = 'UP_Y'

    angles = np.arange(0, 181, 5)  # Capture images at every 5-degree increment
    heights = [object_center[2], object_center[2] + 1, object_center[2] + 2]
    camera_positions = [
        (object_center[0] + camera_distance * np.cos(np.radians(angle)), object_center[1] + camera_distance * np.sin(np.radians(angle)), height)
        for height in heights for angle in angles
    ]

    for height in heights:
        camera_positions.append((object_center[0] + camera_distance, object_center[1], height))

    idx = 0
    for position in camera_positions:
        camera.location = position

        color = np.array([0.5, 0.5, 0.5, 1.0]) + np.array([0.5, 0.5, 0.5, 1.0]) * np.sin(
            np.deg2rad(np.array([1, 2, 3, 4]) * idx)
        )
        model.active_material = random_mat(model.active_material, color)
        model.rotation_euler[2] = np.deg2rad(idx)
        bpy.context.scene.frame_current = idx

        exr_depth_node.file_slots[0].path = f"depth_{idx:04d}"
        png_depth_node.file_slots[0].path = f"depth_{idx:04d}"
        png_normal_node.file_slots[0].path = f"normal_{idx:04d}"

        render_image(f"/Users/prakanda1/Desktop/Major-project/Major-project/Blender-virtual/myenv/myProject/Auto_Postioning_Images/out_{idx:04d}.png")
        idx += 1

    debug("/Users/prakanda1/Desktop/Major-project/Major-project/Blender-virtual/myenv/myProject/Auto_Postioning_Images/debug.blend")

if __name__ == "__main__":
    parser = ArgumentParserForBlender()
    parser.add_argument("--begin", type=int, default=0)
    parser.add_argument("--end", type=int, default=39)
    args = parser.parse_args()
    render_teaser(args)
