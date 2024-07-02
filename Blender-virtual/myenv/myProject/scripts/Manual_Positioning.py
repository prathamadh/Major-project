import bpy
import numpy as np
from mathutils import Vector
from pyblend.lighting import config_world
from pyblend.object import load_obj, create_plane
from pyblend.material import random_mat, set_voronoi_texture
from pyblend.utils import BlenderRemover, ArgumentParserForBlender, debug
from pyblend.render import config_render, render_image, enable_depth_render, enable_normal_render

def fit_and_position_object(obj, target_size=2.5):
    # Calculate the bounding box dimensions of the object
    bpy.context.view_layer.update()
    bbox = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    min_corner = np.min(np.array([v.to_tuple() for v in bbox]), axis=0)
    max_corner = np.max(np.array([v.to_tuple() for v in bbox]), axis=0)
    dimensions = max_corner - min_corner

    # Scale the object to fit within the target size
    scale_factor = target_size / max(dimensions)
    obj.scale = (scale_factor, scale_factor, scale_factor)

    # Update the bounding box after scaling
    bpy.context.view_layer.update()
    bbox = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    min_corner = np.min(np.array([v.to_tuple() for v in bbox]), axis=0)
    max_corner = np.max(np.array([v.to_tuple() for v in bbox]), axis=0)

    # Move the object so that it is above the plane
    obj.location.z -= min_corner[2]

def render_teaser(args):
    # ======== Config ========
    config_render(res_x=320, res_y=240)
    remover = BlenderRemover()
    remover.clear_all()
    config_world(0.5)
    camera = bpy.data.objects["Camera"]

    # Enable depth and normal render passes
    exr_depth_node, png_depth_node = enable_depth_render("/Users/prakanda1/Desktop/Blender-virtual/myenv/PyBlend/mytmp", reverse=True)
    png_normal_node = enable_normal_render("/Users/prakanda1/Desktop/Blender-virtual/myenv/PyBlend/mytmp")

    # ======== Set up scene ========
    plane = create_plane((0, 1, 0), (np.pi / 2, 0, 0), (10, 10, 10), name="plane")
    plane.active_material = set_voronoi_texture(plane.active_material)
    plane = create_plane((0, 0, -1.2), (0, 0, 0), (10, 10, 10), name="plane")

    obj_path = "/Users/prakanda1/Desktop/Blender-virtual/myenv/PyBlend/docs/FinalBaseMesh.obj"
    model = load_obj(obj_path, "model", center=True)

    # Fit and position the object
    fit_and_position_object(model)

    # ======== Camera positions and rotations ========
    camera_positions_rotations = [
        ((0, -10, 3), (72, 0, 0)),
        ((5, -10, 3), (73.4, -5.68, 28.6)),
        ((10, -10, 3), (78.3, 3.94, 45.5)),
        ((15, -10, 3), (80.9, 6.41, 59.7)),
        ((20, -10, 3), (79.5, 2.06, 65)),
        ((11.48, -4.5022, 1.5508), (82.6, 2.91, 73.2)),
        ((11.638, -2.9177, 0.96434), (86.6, 3.47, 81.3)),
        ((-5, -10, 3), (72, 0, -26.2)),
        ((-10, -10, 3), (72, 0, -44.9)),
        ((-15, -10, 3), (79.1, -4.26, -59.2)),
        ((-10.364, -5.4672, 2.1052), (73.3, -1.58, -65.1)),
        ((-12.634, -2.9302, 1.8217), (79.8, -2.93, -78.5)),
        ((-10.614, -1.5011, 1.4917), (82.3, 6.25, -88.7))
    ]

    # ======== Render ========
    idx = 0
    for position, rotation in camera_positions_rotations:
        # Set camera position and rotation
        camera.location = position
        camera.rotation_euler = np.radians(rotation)  # Convert degrees to radians

        # Change material color linearly
        color = np.array([0.5, 0.5, 0.5, 1.0]) + np.array([0.5, 0.5, 0.5, 1.0]) * np.sin(
            np.deg2rad(np.array([1, 2, 3, 4]) * idx)
        )
        model.active_material = random_mat(model.active_material, color)
        model.rotation_euler[2] = np.deg2rad(idx)
        bpy.context.scene.frame_current = idx

        # Set file paths for depth and normal renders
        exr_depth_node.file_slots[0].path = f"depth_"
        png_depth_node.file_slots[0].path = f"depth_"
        png_normal_node.file_slots[0].path = f"normal_"

        # Render the image
        render_image(f"/Users/prakanda1/Desktop/Blender-virtual/myenv/PyBlend/mytmp/out_{idx:04d}.png")
        idx += 1

    # ======== Save blend file ========
    debug("/Users/prakanda1/Desktop/Blender-virtual/myenv/PyBlend/mytmp/debug.blend")

if __name__ == "__main__":
    parser = ArgumentParserForBlender()
    parser.add_argument("--begin", type=int, default=0)
    parser.add_argument("--end", type=int, default=13)  # Total number of camera positions
    args = parser.parse_args()
    render_teaser(args)
