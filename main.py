import open3d as o3d
import open3d.visualization.gui as gui
import open3d.visualization.rendering as rendering
from matplotlib import cm
from matplotlib import pyplot as plt
import matplotlib.colors as mcol
import numpy as np
import os
import subprocess
from pathlib import Path
from PIL import Image

#custom libraries
import resources as res

OUT_LIM_MATPLOT = ['k', 'w', 'r']
POST_PROCESS = ['none', 'smooth', 'sharpen', 'sharpen strong', 'edge (simple)', 'edge (from rgb)']
COLORMAPS = ['coolwarm','Artic', 'Iron', 'Rainbow', 'Greys_r', 'Greys', 'plasma', 'inferno', 'jet',
                              'Spectral_r', 'cividis', 'viridis', 'gnuplot2']
VIEWS = ['th. undistorted', 'RGB crop']

SDK_PATH = Path(res.find('dji/dji_irp.exe'))

img_path = Path(res.find('img/M2EA_IR.JPG'))


class Custom3dView:
    def __init__(self):
        app = gui.Application.instance
        self.window = app.create_window("Open3D - Infrared analyzer", 1920, 1080)
        self.window.set_on_layout(self._on_layout)
        self.widget3d = gui.SceneWidget()
        self.window.add_child(self.widget3d)

        self.info = gui.Label("")
        self.info.visible = False
        self.window.add_child(self.info)

        self.widget3d.scene = rendering.Open3DScene(self.window.renderer)
        self.widget3d.scene.set_background([0, 0, 0, 1])
        self.viewopt = self.widget3d.scene.view
        # self.viewopt.set_ambient_occlusion(True, ssct_enabled=True)

        self.widget3d.enable_scene_caching(True)
        self.widget3d.scene.show_axes(True)
        self.widget3d.scene.scene.set_sun_light(
            [0.45, 0.45, -1],  # direction
            [1, 1, 1],  # color
            100000)  # intensity
        self.widget3d.scene.scene.enable_sun_light(True)
        self.widget3d.scene.scene.enable_indirect_light(True)
        self.widget3d.set_on_sun_direction_changed(self._on_sun_dir)

        self.mat = rendering.MaterialRecord()
        self.mat.shader = "defaultLit"
        self.mat.point_size = 3 * self.window.scaling

        self.mat_maxi = rendering.MaterialRecord()
        self.mat_maxi.shader = "defaultUnlit"
        self.mat_maxi.point_size = 15 * self.window.scaling


        # LAYOUT GUI ELEMENTS
        em = self.window.theme.font_size
        self.layout = gui.Vert(0, gui.Margins(0.25 * em, 0.25 * em, 0.25 * em, 0.25 * em))

        view_ctrls = gui.CollapsableVert("View controls", 0.25 * em,
                                         gui.Margins(em, 0, 0, 0))

        # add button for loading images
        self.load_but = gui.Button('Choose image')
        self.load_but.set_on_clicked(self.on_button_load)

        # add button to reset camera


        # add combo for lit/unlit/depth
        self._shader = gui.Combobox()
        self.materials = ["defaultLit", "defaultUnlit", "normals", "depth"]
        self.materials_name = ['Sun Light', 'No light', 'Normals', 'Depth']
        self._shader.add_item(self.materials_name[0])
        self._shader.add_item(self.materials_name[1])
        self._shader.add_item(self.materials_name[2])
        self._shader.add_item(self.materials_name[3])
        self._shader.set_on_selection_changed(self._on_shader)
        combo_light = gui.Horiz(0, gui.Margins(0.25 * em, 0.25 * em, 0.25 * em, 0.25 * em))
        combo_light.add_child(gui.Label("Rendering"))
        combo_light.add_child(self._shader)

        # add combo for voxel size
        self._voxel = gui.Combobox()

        combo_voxel = gui.Horiz(0, gui.Margins(0.25 * em, 0.25 * em, 0.25 * em, 0.25 * em))
        combo_voxel.add_child(gui.Label("Size of voxels"))
        combo_voxel.add_child(self._voxel)

        # layout
        view_ctrls.add_child(self.load_but)
        view_ctrls.add_child(combo_light)
        view_ctrls.add_child(combo_voxel)
        view_ctrls.add_child(camera_but)
        self.layout.add_child(view_ctrls)
        self.window.add_child(self.layout)


        self.widget3d.set_on_mouse(self._on_mouse_widget3d)
        self.window.set_needs_layout()

    def choose_material(self, is_enabled):
        pass

    def on_button_load(self):
        # choose file
        file_input = gui.FileDialog(gui.FileDialog.OPEN, "Choose file to load",
                                    self.window.theme)

        # file_input.add_filter('.JPG', "JPG files (.JPG)")

        file_input.set_on_cancel(self._on_load_dialog_cancel)

        file_input.set_on_done(self._on_load_dialog_done)

        self.window.show_dialog(file_input)

    def _on_load_dialog_done(self, img_path):
        self.window.close_dialog()
        self.load(img_path)

    def _on_load_dialog_cancel(self):
        self.window.close_dialog()

    def _on_change_colormap(self):
        pass

    def load(self, img_path):
        self.data = process_one_th_picture(img_path)
        self.pc_ir, self.tmax, self.tmin, loc_tmax, loc_tmin, self.factor = surface_from_image(self.data, colormap, n_colors, user_lim_col_low, user_lim_col_high)

        # create all voxel grids
        self.voxel_grids = []
        self.voxel_size = [2, 5, 10, 20]

        for size in self.voxel_size:
            print('yoi')
            voxel_grid = o3d.geometry.VoxelGrid.create_from_point_cloud(self.pc_ir,
                                                                        voxel_size=size)
            self.voxel_grids.append(voxel_grid)


        # show one geometry
        self.widget3d.scene.add_geometry('PC 2', self.voxel_grids[2], self.mat)
        self.current_index = 2


        self.widget3d.scene.show_geometry("Point Cloud IR 0", True)
        self.widget3d.force_redraw()

        self.voxel_name = ["2", "5", "10", "20"]
        self._voxel.add_item(self.voxel_name[0])
        self._voxel.add_item(self.voxel_name[1])
        self._voxel.add_item(self.voxel_name[2])
        self._voxel.add_item(self.voxel_name[3])
        self._voxel.set_on_selection_changed(self._on_voxel)

        # add labels for min and max values
        loc_tmin = np.append(loc_tmin, self.tmin * self.factor)
        loc_tmax = np.append(loc_tmax, self.tmax * self.factor)
        text_max = 'Temp. max.:' + str(round(self.tmax, 2)) + '°C'
        text_min = 'Temp. min.:' + str(round(self.tmin, 2)) + '°C'
        lab_tmin = self.widget3d.add_3d_label(loc_tmin, text_min)
        lab_tmax = self.widget3d.add_3d_label(loc_tmax, text_max)
        lab_color_red = gui.Color(1, 0, 0)
        lab_color_blue = gui.Color(0, 0, 1)

        lab_tmin.color = lab_color_blue
        lab_tmax.color = lab_color_red

        # add points
        pcd_maxi = o3d.geometry.PointCloud()
        array = np.array([loc_tmin, loc_tmax])
        pcd_maxi.points = o3d.utility.Vector3dVector(array)
        color_array = np.array([[0, 0, 1], [1, 0, 0]])
        pcd_maxi.colors = o3d.utility.Vector3dVector(color_array)
        self.widget3d.scene.add_geometry('Max/Min', pcd_maxi, self.mat_maxi)

        self._on_reset_camera()

    def _on_layout(self, layout_context):
        r = self.window.content_rect
        self.widget3d.frame = r
        pref = self.info.calc_preferred_size(layout_context,
                                             gui.Widget.Constraints())

        width = 17 * layout_context.theme.font_size
        height = min(
            r.height,
            self.layout.calc_preferred_size(
                layout_context, gui.Widget.Constraints()).height)

        self.layout.frame = gui.Rect(r.get_right() - width, r.y, width,
                                     height)

        self.info.frame = gui.Rect(r.x,
                                   r.get_bottom() - pref.height, pref.width,
                                   pref.height)

    def _on_voxel(self, name, index):
        print('ok!')
        old_name = f"PC {self.current_index}"
        print(old_name)
        self.widget3d.scene.remove_geometry(old_name)
        self.widget3d.scene.add_geometry(f"PC {index}", self.voxel_grids[index], self.mat)
        self.current_index = index
        print('everything good')
        self.widget3d.force_redraw()

    def _on_shader(self, name, index):
        material = self.materials[index]
        print(material)
        self.mat.shader = material
        self.widget3d.scene.update_material(self.mat)
        self.widget3d.force_redraw()

    def _on_sun_dir(self, sun_dir):
        self.widget3d.scene.scene.set_sun_light(sun_dir, [1, 1, 1], 100000)
        self.widget3d.force_redraw()

    def _on_reset_camera(self):
        # adapt camera
        bounds = self.widget3d.scene.bounding_box
        center = bounds.get_center()
        self.widget3d.setup_camera(30, bounds, center)
        camera = self.widget3d.scene.camera
        self.widget3d.look_at(center, center + [0, 0, 1200], [0, -1, 0])


    def _on_mouse_widget3d(self, event):
        # We could override BUTTON_DOWN without a modifier, but that would
        # interfere with manipulating the scene.
        if event.type == gui.MouseEvent.Type.BUTTON_DOWN and event.is_modifier_down(
                gui.KeyModifier.CTRL):

            def depth_callback(depth_image):
                # Coordinates are expressed in absolute coordinates of the
                # window, but to dereference the image correctly we need them
                # relative to the origin of the widget. Note that even if the
                # scene widget is the only thing in the window, if a menubar
                # exists it also takes up space in the window (except on macOS).
                x = event.x - self.widget3d.frame.x
                y = event.y - self.widget3d.frame.y
                # Note that np.asarray() reverses the axes.
                depth = np.asarray(depth_image)[y, x]

                if depth == 1.0:  # clicked on nothing (i.e. the far plane)
                    text = ""
                    coords = []
                else:
                    world = self.widget3d.scene.camera.unproject(
                        event.x, event.y, depth, self.widget3d.frame.width,
                        self.widget3d.frame.height)
                    text = "({:.3f}, {:.3f}, {:.3f})".format(
                        world[0], world[1], world[2])

                    # add 3D label
                    self.widget3d.add_3d_label(world, '._yeah')

                # This is not called on the main thread, so we need to
                # post to the main thread to safely access UI items.
                def update_label():
                    self.info.text = text
                    self.info.visible = (text != "")
                    # We are sizing the info label to be exactly the right size,
                    # so since the text likely changed width, we need to
                    # re-layout to set the new frame.
                    self.window.set_needs_layout()

                gui.Application.instance.post_to_main_thread(
                    self.window, update_label)

            self.widget3d.scene.scene.render_to_depth_image(depth_callback)

            return gui.Widget.EventCallbackResult.HANDLED
        return gui.Widget.EventCallbackResult.IGNORED


def read_dji_image(img_in, raw_out, param={'emissivity': 0.95, 'distance': 5, 'humidity': 50, 'reflection': 25}):
    dist = param['distance']
    rh = param['humidity']
    refl_temp = param['reflection']
    em = param['emissivity']

    subprocess.run(
        [str(SDK_PATH), "-s", f"{img_in}", "-a", "measure", "-o", f"{raw_out}", "--measurefmt",
         "float32", "--distance", f"{dist}", "--humidity", f"{rh}", "--reflection", f"{refl_temp}",
         "--emissivity", f"{em}"],
        universal_newlines=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT,
        shell=True
    )

    image = Image.open(img_in)
    exif = image.info['exif']

    return exif


def process_one_th_picture(ir_img_path):
    _, filename = os.path.split(str(ir_img_path))
    new_raw_path = Path(str(ir_img_path)[:-4] + '.raw')

    exif = read_dji_image(str(ir_img_path), str(new_raw_path))

    # read raw dji output
    fd = open(new_raw_path, 'rb')
    rows = 512
    cols = 640
    f = np.fromfile(fd, dtype='<f4', count=rows * cols)
    im = f.reshape((rows, cols))  # notice row, column format
    fd.close()

    # remove raw file
    os.remove(new_raw_path)

    return im


def get_custom_cmaps(colormap_name, n_colors):
    colors = [(25, 0, 150), (94, 243, 247), (100, 100, 100), (243, 116, 27), (251, 250, 208)]
    colors_scaled = [np.array(x).astype(np.float32) / 255 for x in colors]
    artic_cmap = mcol.LinearSegmentedColormap.from_list('my_colormap', colors_scaled, N=n_colors)

    colors = [(0, 0, 0), (144, 15, 170), (230, 88, 65), (248, 205, 35), (255, 255, 255)]
    colors_scaled = [np.array(x).astype(np.float32) / 255 for x in colors]
    ironbow_cmap = mcol.LinearSegmentedColormap.from_list('my_colormap', colors_scaled, N=n_colors)

    colors = [(8, 0, 75), (43, 80, 203), (119, 185, 31), (240, 205, 35), (245, 121, 47), (236, 64, 100),
              (240, 222, 203)]
    colors_scaled = [np.array(x).astype(np.float32) / 255 for x in colors]
    rainbow_cmap = mcol.LinearSegmentedColormap.from_list('my_colormap', colors_scaled, N=n_colors)

    if colormap_name == 'Artic':
        out_colormap = artic_cmap
    elif colormap_name == 'Iron':
        out_colormap = ironbow_cmap
    elif colormap_name == 'Rainbow':
        out_colormap = rainbow_cmap

    return out_colormap


def surface_from_image(data, colormap, n_colors, col_low, col_high):
    if colormap == 'Artic' or colormap == 'Iron' or colormap == 'Rainbow':
        custom_cmap = get_custom_cmaps(colormap, n_colors)
    else:
        custom_cmap = cm.get_cmap(colormap, n_colors)

    custom_cmap.set_over(col_high)
    custom_cmap.set_under(col_low)

    # get extreme values from data
    tmax = np.amax(data)
    tmin = np.amin(data)
    indices_max = np.where(data == tmax)
    indices_min = np.where(data == tmin)

    # Check if there are any occurrences of 'a'
    if len(indices_max[0]) > 0:
        # Get the coordinates of the first occurrence
        loc_tmax = np.array([indices_max[1][0], indices_min[0][0]])

    if len(indices_min[0]) > 0:
        # Get the coordinates of the first occurrence
        loc_tmin = np.array([indices_min[1][0], indices_min[0][0]])

    # normalized data
    thermal_normalized = (data - tmin) / (tmax - tmin)

    thermal_cmap = custom_cmap(thermal_normalized)
    # thermal_cmap = np.uint8(thermal_cmap)
    color_array = thermal_cmap[:, :, [0, 1, 2]]

    # color_array = np.transpose(color_array, (1, 0, 2))
    print(color_array.shape)

    height, width = data.shape

    # Generate the x and y coordinates
    x_coords, y_coords = np.meshgrid(np.arange(width), np.arange(height))

    # Flatten the arrays
    x = x_coords.flatten()
    y = y_coords.flatten()
    z = data.flatten()

    # Create the point cloud using the flattened arrays
    # compute range of temp
    range_temp = tmax-tmin
    # compute how the range scales compared to x/y
    factor = width/range_temp/3
    points = np.column_stack((x, y, z*factor))

    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(points)

    # get colors
    color_array = color_array.reshape(width*height, 3)
    pcd.colors = o3d.utility.Vector3dVector(color_array)

    return pcd, tmax, tmin, loc_tmax, loc_tmin, factor




colormap = COLORMAPS[2]
user_lim_col_low = OUT_LIM_MATPLOT[0]
user_lim_col_high = OUT_LIM_MATPLOT[0]
n_colors = 256

app_vis = gui.Application.instance
app_vis.initialize()

viz = Custom3dView()
app_vis.run()
