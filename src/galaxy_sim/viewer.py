import time
from vispy import app, scene
import numpy as np
from vispy.scene import SceneCanvas, visuals
from vispy.scene.cameras import TurntableCamera, PanZoomCamera
from vispy.scene.visuals import Markers
from vispy.scene import Text

from galaxy_sim.gravity import velocity_verlet_step, G


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

        self.orbit_lines = []
        self.projected_orbits = {}

        self.show_orbits = False

        self.bodies = bodies
        self.trail_length = 5000
        self.positions = {body.name: [body.position.copy()] for body in bodies}
        self.body_colors = {body.name: self.get_body_color(body) for body in self.bodies}

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

        self.full_info_label = visuals.Text(
            "", color='white', parent=self.ui_view.scene,
            font_size=9, anchor_x='left', anchor_y='top'
        )
        self.full_info_label.pos = (0, self.CANVAS_SIZE[1] - 100)
        self.full_info_label.visible = False

        self.focus_target = None
        self.camera_auto_scale = True
        self.hovered_body = None
        self.selected_body = None

        self._init_starfield()
        self._init_bodies()

        # Timer for animation
        self.timer = app.Timer(interval=self.FRAME_INTERVAL, connect=self.update_frame, start=True)

        self.steps_to_run = 0
        self.sim_time = 0

        self.time_label = visuals.Text(
            "", color='white', parent=self.ui_view.scene,
            font_size=9, anchor_x='right', anchor_y='top'
        )
        self.time_label.pos = (self.CANVAS_SIZE[0] - 10, self.CANVAS_SIZE[1] - 10)
        self.time_label.visible = True

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
        self.body_colors = {body.name: self.get_body_color(body) for body in self.bodies}

        for body in self.bodies:
            # Initialize the trail for each body
            self.trails[body.name] = scene.Line(
                pos=np.zeros((self.trail_length, 3)),
                color=self.TRAIL_COLOR,
                method='gl',
                parent=self.view.scene
            )

            # Create a marker with color based on body name/type
            color = OrbitViewer3D.get_body_color(body)
            self.markers[body.name] = scene.Markers(parent=self.view.scene)
            self.markers[body.name].set_data(
                pos=np.array([body.position]),
                size=12,
                face_color=color
            )
            self.markers[body.name].interactive = True


    def _on_click(self, event):
        clicked = self.get_body_under_cursor(event.pos)
        if clicked:
            self.selected_body = clicked
            self.info_label.text = clicked.name
            self.info_label.visible = True
            self.full_info_label.text = clicked.short_description()
            self.full_info_label.visible = True

    def on_key_press(self, event):
        if event.key == 'Up':
            self.time_multiplier *= 2
        elif event.key == 'Down':
            self.time_multiplier = max(0.25, self.time_multiplier / 2)
        elif hasattr(event.key, 'name') and event.key.name.upper() == 'P':
            self.toggle_projected_orbits()

        print(f"⏱ Time multiplier: {self.time_multiplier:.2f}x")



        if self.selected_body:
            if event.key == 'f':
                self.focus_on(self.selected_body)
            elif event.key == 'i':
                self.open_detailed_info(self.selected_body)
                

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

    def update_frame(self, event):
      ##  self.update_star_data()
        self.time_label.text = f"Sim Time: {self.sim_time / 86400:.2f} days\nSpeed: {self.time_multiplier:.2f}x"

        for body in self.bodies:
            self.positions[body.name].append(body.position.copy())
            if len(self.positions[body.name]) > self.trail_length:
                self.positions[body.name].pop(0)

            trail = np.array(self.positions[body.name])
            self.trails[body.name].set_data(trail)
            self.markers[body.name].set_data(pos=trail[-1:], size=8, face_color=self.body_colors[body.name])




        from galaxy_sim.gravity import kinetic_energy, potential_energy

        KE = sum(kinetic_energy(b) for b in self.bodies)
        PE = sum(
            potential_energy(b1, b2)
            for i, b1 in enumerate(self.bodies)
            for b2 in self.bodies[i + 1:]

        )
        ##print(f"Total Energy: {KE + PE:.3e}")

    def _compute_orbit_path(self, body, steps=500, total_time=None):
        if total_time is None:
            total_time = body.orbital_period  # Use default only when available

        dt = total_time / steps
        pos = body.position.copy()
        vel = body.velocity.copy()
        path = []

        sun_pos = np.zeros(3)  # Assume sun at origin

        for _ in range(steps):
            r = pos - sun_pos
            acc = -G * 1.989e30 * r / np.linalg.norm(r) ** 3  # Only sun gravity
            vel += acc * dt
            pos += vel * dt
            path.append(pos.copy())

        return np.array(path)

    def draw_projected_orbit(self, body, steps=500):
        if body.name.lower() == "sun" or body.orbital_period is None:
            return  # skip Sun or bodies without defined orbital periods

        orbit_radius = np.linalg.norm(body.position)
        orbit_plane_normal = np.cross(body.position, body.velocity)
        orbit_plane_normal /= np.linalg.norm(orbit_plane_normal)

        # Create orthonormal basis
        x_axis = body.position / np.linalg.norm(body.position)
        y_axis = np.cross(orbit_plane_normal, x_axis)
        y_axis /= np.linalg.norm(y_axis)

        # Parametric circle in orbit plane
        angles = np.linspace(0, 2 * np.pi, steps)
        path = [orbit_radius * (np.cos(a) * x_axis + np.sin(a) * y_axis) for a in angles]
        path = np.array(path)

        color = self.body_colors.get(body.name, (0.7, 0.7, 0.7, 1.0))
        orbit_line = scene.Line(pos=path, color=color, width=1.0, parent=self.view.scene)
        self.projected_orbits[body.name] = orbit_line

    def draw_all_projected_orbits(self):
        for body in self.bodies:
            self.draw_projected_orbit(body)

    def toggle_projected_orbits(self):
        if self.show_orbits:
            # Remove existing orbit visuals
            for orbit in self.projected_orbits.values():
                orbit.parent = None
            self.projected_orbits.clear()
            self.show_orbits = False
        else:
            self.draw_all_projected_orbits()
            self.show_orbits = True

    @staticmethod
    def get_body_color(body):
        name = body.name.lower()

        if "sun" in name:
            return (1.0, 1.0, 0.0, 1.0)  # Yellow
        elif "mercury" in name:
            return (0.55, 0.57, 0.67, 1.0)  # Grayish
        elif "venus" in name:
            return (0.9, 0.7, 0.4, 1.0)  # Pale yellowish
        elif "earth" in name:
            return (0.0, 0.5, 1.0, 1.0)  # Blue
        elif "moon" in name:
            return (0.8, 0.8, 0.8, 1.0)  # Light gray
        elif "mars" in name:
            return (1.0, 0.3, 0.0, 1.0)  # Reddish-orange
        elif "jupiter" in name:
            return (0.8, 0.6, 0.4, 1.0)  # Tan with bands
        elif "saturn" in name:
            return (0.9, 0.8, 0.5, 1.0)  # Pale gold
        elif "uranus" in name:
            return (0.5, 0.8, 0.9, 1.0)  # Light blue-cyan
        elif "neptune" in name:
            return (0.3, 0.4, 0.8, 1.0)  # Deep blue
        elif "pluto" in name:
            return (0.8, 0.7, 0.6, 1.0)  # Brown-gray
        elif body.body_type == "star":
            return (1.0, 1.0, 0.6, 1.0)  # Generic star color
        elif body.body_type == "planet":
            return (0.6, 0.6, 0.8, 1.0)  # Default planet color
        else:
            return (1.0, 1.0, 1.0, 1.0)  # Default white



    def run(self):
        app.run()
