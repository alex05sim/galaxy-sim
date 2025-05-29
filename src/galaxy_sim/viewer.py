import time
from vispy import app, scene
import numpy as np
from vispy.scene import SceneCanvas, visuals
from vispy.scene.cameras import TurntableCamera, PanZoomCamera
from vispy.scene.visuals import Markers
from vispy.scene import Text

class OrbitViewer3D:
    # Class Constant
    CANVAS_SIZE = (1000, 800)
    BG_COLOR = 'black'
    INIT_CAMERA_DISTANCE = 3e11
    FRAME_INTERVAL = 1 / 60

    STAR_COUNT = 500
    STAR_POS_RANGE = 1e13
    STAR_SIZE_RANGE = (1.0, 2.5)
    STAR_COLOR_RANGE = (0.8, 1.0)
    STAR_FREQ_RANGE = (0.5, 1.5)
    STAR_TWINKLE_SPEED = 2
    STAR_ALPHA_MIN = 0.3
    STAR_ALPHA_MAX = 1.0

    TRAIL_COLOR = 'white'
    BODY_MARKER_COLOR = 'blue'
    TRAIL_MARKER_COLOR = 'cyan'


    STYLE_LOOKUP = {
        ("star", "main_sequence"): {"color": "yellow", "size": 18},
        ("planet", "rocky"): {"color": "gray", "size": 10},
        ("planet", "gas_giant"): {"color": "orange", "size": 14},
        ("planet", "ice_giant"): {"color": "cyan", "size": 12},
        ("moon", "rocky"): {"color": "lightgray", "size": 5},
        ("moon", "ice"): {"color": "white", "size": 5},
        ("moon", "hazy"): {"color": "tan", "size": 5},
        ("planet", "dwarf"): {"color": "lightblue", "size": 6},
        ("dwarf", "icy_dwarf"): {"color": "lightblue", "size": 4},
    }

    def __init__(self, bodies, trail_length=300):
        self.bodies = bodies
        self.trail_length = trail_length
        self.positions = {body.name: [body.position.copy()] for body in bodies}

        # Create canvas and view
        self.canvas = SceneCanvas(keys='interactive', show=True,
                                  bgcolor=self.BG_COLOR, size=self.CANVAS_SIZE)
        self.canvas.events.key_press.connect(self.on_key_press)

        # 3D view
        self.view = self.canvas.central_widget.add_view()
        self.view.camera = TurntableCamera(fov=45, elevation=30, azimuth=30)
        self.view.camera.distance = self.INIT_CAMERA_DISTANCE

        # —— ADD THIS: 2D overlay view for HUD ——
        self.ui_view = self.canvas.central_widget.add_view()
        self.ui_view.camera = PanZoomCamera(aspect=1)
        # cover exactly the canvas in pixel units
        self.ui_view.camera.set_range(x=(0, self.CANVAS_SIZE[0]),
                                      y=(0, self.CANVAS_SIZE[1]))
        self.ui_view.interactive = False  # don’t let mouse drag the HUD
        # now create your labels here:
        self.info_label = visuals.Text(
            "", color='white', parent=self.ui_view.scene,
            font_size=10, anchor_x='left', anchor_y='top'
        )
        self.info_label.pos = (10, self.CANVAS_SIZE[1] - 10)
        self.info_label.visible = False

        self.full_info_label = visuals.Text(
            "", color='white', parent=self.ui_view.scene,
            font_size=9, anchor_x='left', anchor_y='top'
        )
        self.full_info_label.pos = (10, self.CANVAS_SIZE[1] - 30)
        self.full_info_label.visible = False

        self.focus_target = None
        self.camera_auto_scale = True
        self.hovered_body = None
        self.selected_body = None

        # Text label for selected object
        self.info_label.pos = (10, self.CANVAS_SIZE[1] - 10)
        self.info_label.visible = False


        self._init_starfield()
        self._init_bodies()

        # Timer for animation
        self.timer = app.Timer(interval=self.FRAME_INTERVAL, connect=self.update_frame, start=True)

    def _init_starfield(self):
        self.num_stars = self.STAR_COUNT
        self.star_positions = np.random.uniform(-self.STAR_POS_RANGE, self.STAR_POS_RANGE, size=(self.num_stars, 3))
        self.star_base_size = np.random.uniform(*self.STAR_SIZE_RANGE, self.num_stars)
        self.star_base_color = np.random.uniform(*self.STAR_COLOR_RANGE, size=(self.num_stars, 3))
        self.star_freq = np.random.uniform(*self.STAR_FREQ_RANGE, self.num_stars)
        self.star_phase = np.random.uniform(0, 2 * np.pi, self.num_stars)

        t = time.time() * self.STAR_TWINKLE_SPEED
        twinkle = 0.5 + 0.5 * np.sin(self.star_freq * t + self.star_phase)
        self.star_alphas = self.STAR_ALPHA_MIN + (self.STAR_ALPHA_MAX - self.STAR_ALPHA_MIN) * twinkle

        star_colors = np.ones((self.num_stars, 4))
        star_colors[:, :3] = self.star_base_color
        star_colors[:, 3] = self.star_alphas

        self.stars = scene.Markers(parent=self.view.scene)
        self.stars.set_data(pos=self.star_positions,
                            size=self.star_base_size,
                            face_color=star_colors,
                            edge_width=0)

    def focus_on(self, body, parent = None):
        self.focus_target = body
        focus_pos = body.position
        if parent:
            focus_pos = (body.position - parent.position) / 2
        self.view.camera.center = focus_pos.tolist()

        if self.camera_auto_scale and parent:
            distance = np.linalg.norm(body.position - parent.position)
            self.view.camera.distance = distance * 3

    def _init_bodies(self):
        self.trails = {}
        self.markers = {}
        for body in self.bodies:
            self.trails[body.name] = scene.Line(pos=np.zeros((self.trail_length, 3)),
                                                color=self.TRAIL_COLOR, method='gl', parent=self.view.scene)
            self.markers[body.name] = Markers(parent=self.view.scene)
            self.markers[body.name].interactive = True

    def update_star_data(self):
        t = time.time() * self.STAR_TWINKLE_SPEED
        twinkle = 0.5 + 0.5 * np.sin(self.star_freq * t + self.star_phase)
        self.star_alphas = self.STAR_ALPHA_MIN + (self.STAR_ALPHA_MAX - self.STAR_ALPHA_MIN) * twinkle

        star_colors = np.ones((self.num_stars, 4))
        star_colors[:, :3] = self.star_base_color
        star_colors[:, 3] = self.star_alphas

        self.stars.set_data(pos=self.star_positions,
                            size=self.star_base_size,
                            face_color=star_colors,
                            edge_width=0)

    def _on_click(self, event):
        clicked = self.get_body_under_cursor(event.pos)
        if clicked:
            self.selected_body = clicked
            self.info_label.text = clicked.name
            self.info_label.visible = True
            self.full_info_label.text = clicked.short_description()
            self.full_info_label.visible = True
    def on_key_press(self, event):
        if self.selected_body:
          if event.key == 'f':
             self.focus_on(self.selected_body)
          elif event.key == 'i':
              self.open_detailed_info(self.selected_body)





    def update_frame(self, event):
        self.update_star_data()


        for body in self.bodies:
            self.positions[body.name].append(body.position.copy())
            if len(self.positions[body.name]) > self.trail_length:
                self.positions[body.name].pop(0)

            trail = np.array(self.positions[body.name])
            self.trails[body.name].set_data(trail)
            self.markers[body.name].set_data(pos=trail[-1:], size=8, face_color=self.TRAIL_MARKER_COLOR)

            if self.selected_body:
                # Project 3D world position to 2D screen coordinates
                pos_3d = self.selected_body.position
                pos_2d = self.canvas.scene.node_transform(self.view.scene).map(pos_3d)
                self.info_label.pos = pos_2d[:2]




    def run(self):
        app.run()
