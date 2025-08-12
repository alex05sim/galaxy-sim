# viewer.py

from vispy import app, scene
import numpy as np
import spiceypy
from vispy.scene import SceneCanvas, visuals
from vispy.scene.cameras import TurntableCamera
from .gravity import Probe, Body
from .prediction import run_prediction, evaluate_trajectory


class OrbitViewer3D:
    CANVAS_SIZE = (1600, 900)
    BG_COLOR = 'black'
    RENDER_SCALE = 1e-9
    INIT_CAMERA_DISTANCE = 4000.0
    FRAME_INTERVAL = 1 / 60.0
    STAR_COUNT = 1500
    STAR_DISTANCE_M = 5e12
    STAR_SIZE_RANGE = (1.0, 2.5)

    BODY_VISUALS = {
        'Sun': {'color': (1.0, 0.9, 0.4), 'radius': 35}, 'Mercury': {'color': (0.6, 0.6, 0.6), 'radius': 8},
        'Venus': {'color': (0.9, 0.7, 0.5), 'radius': 12}, 'Earth': {'color': (0.4, 0.6, 1.0), 'radius': 13},
        'Mars': {'color': (1.0, 0.5, 0.3), 'radius': 10}, 'Jupiter': {'color': (0.9, 0.8, 0.6), 'radius': 25},
        'Saturn': {'color': (1.0, 0.9, 0.7), 'radius': 22}, 'Uranus': {'color': (0.6, 0.9, 1.0), 'radius': 18},
        'Neptune': {'color': (0.4, 0.5, 1.0), 'radius': 17}, 'Default': {'color': (0.8, 0.8, 0.8), 'radius': 5},
        'probe': {'color': (1.0, 0.2, 0.2), 'radius': 6}
    }

    def __init__(self, bodies, initial_et, trail_length=2500):
        self.bodies = bodies
        self.planets = sorted([b for b in bodies if b.body_type == 'planet'], key=lambda p: np.linalg.norm(p.position))
        self.initial_et = initial_et
        self.trail_length = trail_length
        self.positions = {body.name: [body.position.copy()] for body in bodies}
        self.sphere_radii = {}

        self.canvas = SceneCanvas(keys='interactive', show=True, bgcolor=self.BG_COLOR, size=self.CANVAS_SIZE)
        self.canvas.events.key_press.connect(self.on_key_press)

        self.view = self.canvas.central_widget.add_view()
        self.view.camera = TurntableCamera(fov=45, elevation=30, azimuth=45, distance=self.INIT_CAMERA_DISTANCE)

        self.ui_view = self.canvas.central_widget.add_view()
        self.ui_view.camera = scene.PanZoomCamera(aspect=1)
        self.ui_view.camera.set_range(x=(0, self.CANVAS_SIZE[0]), y=(0, self.CANVAS_SIZE[1]))
        self.ui_view.interactive = False

        self.time_label = visuals.Text("", color='white', parent=self.ui_view.scene,
                                       pos=(self.CANVAS_SIZE[0] - 10, self.CANVAS_SIZE[1] - 20), anchor_x='right')
        self.launch_ui_label = visuals.Text("", color='yellow', parent=self.ui_view.scene,
                                            pos=(self.CANVAS_SIZE[0] / 2, 30), anchor_x='center', font_size=14)
        self.planet_stats_label = visuals.Text("", color='white', parent=self.ui_view.scene,
                                               pos=(15, self.CANVAS_SIZE[1] - 50), anchor_y='top', font_size=10)

        self.is_paused = False
        self.time_multiplier = 20.0
        self.base_dt = 3600 * 6
        self.follow_target = None
        self.follow_target_idx = -1

        self.launch_mode_active = False
        self.launch_angle = 90.0
        self.launch_altitude_angle = 0.0
        self.launch_altitude = 5e7
        self.launch_speed_dv = 12000.0
        self.probe_count = 0
        self.prediction_dirty = True
        self.show_prediction = False
        self.target_planet_idx = -1
        self.optimizing = False
        self.best_params = None

        self._init_starfield();
        self._init_visuals()
        self.timer = app.Timer(interval=self.FRAME_INTERVAL, connect=self.update_frame, start=True)

    def _init_starfield(self):
        star_positions_m = np.random.uniform(-self.STAR_DISTANCE_M, self.STAR_DISTANCE_M, size=(self.STAR_COUNT, 3))
        self.stars = scene.Markers(parent=self.view.scene, pos=star_positions_m * self.RENDER_SCALE,
                                   size=np.random.uniform(1.0, 2.5, self.STAR_COUNT), face_color='white')

    def _init_visuals(self):
        self.trails = {};
        self.spheres = {}
        for body in self.bodies: self._create_visuals_for_body(body)
        self.targeting_line = scene.Line(parent=self.view.scene, color='cyan', width=2)
        self.launch_origin_marker = scene.Markers(parent=self.view.scene, face_color='white', size=8)
        self.prediction_path_visual = scene.Line(parent=self.view.scene, color=(0, 1, 0.5, 0.7), width=3,
                                                 connect='strip', method='gl')

    def _create_visuals_for_body(self, body):
        props = self.BODY_VISUALS.get(body.name, self.BODY_VISUALS.get(body.body_type, self.BODY_VISUALS['Default']))
        self.sphere_radii[body.name] = props['radius']

        # --- THE FINAL FIX: Set shading to None to ensure planets are always visible with their correct color ---
        self.spheres[body.name] = visuals.Sphere(radius=props['radius'], rows=30, cols=30, method='latitude',
                                                 parent=self.view.scene, color=props['color'], shading=None)

        self.spheres[body.name].transform = scene.transforms.MatrixTransform()
        self.trails[body.name] = scene.Line(parent=self.view.scene, width=1.5, method='gl')


    def on_key_press(self, event):
        if event.key is None: return
        parameter_changed = False
        if event.key == 'Left':
            self.follow_target_idx = (self.follow_target_idx - 1 + len(self.planets)) % len(
                self.planets); self.follow_target = self.planets[
                self.follow_target_idx]; self.view.camera.distance = 1500; parameter_changed = True
        elif event.key == 'Right':
            self.follow_target_idx = (self.follow_target_idx + 1) % len(self.planets); self.follow_target = \
            self.planets[self.follow_target_idx]; self.view.camera.distance = 1500; parameter_changed = True

        if self.launch_mode_active:
            if event.key.name.upper() == 'A':
                self.launch_angle -= 5.0; parameter_changed = True
            elif event.key.name.upper() == 'D':
                self.launch_angle += 5.0; parameter_changed = True
            elif event.key.name.upper() == 'W':
                self.launch_altitude_angle = min(90, self.launch_altitude_angle + 5.0); parameter_changed = True
            elif event.key.name.upper() == 'S':
                self.launch_altitude_angle = max(-90, self.launch_altitude_angle - 5.0); parameter_changed = True
            elif event.key.name == 'Plus':
                self.launch_speed_dv += 500.0; parameter_changed = True
            elif event.key.name == 'Minus':
                self.launch_speed_dv = max(1000.0, self.launch_speed_dv - 500.0); parameter_changed = True
            elif event.key.name.upper() == 'L':
                self.launch_probe()
            elif event.key.name.upper() == 'P':
                self.show_prediction = not self.show_prediction; parameter_changed = True
            elif event.key.name.upper() == 'T':
                self.target_planet_idx = (self.target_planet_idx + 1) % len(self.planets)
                if self.planets[self.target_planet_idx] == self.follow_target:
                    self.target_planet_idx = (self.target_planet_idx + 1) % len(self.planets)
                parameter_changed = True
            elif event.key.name.upper() == 'O':
                self.optimizing = True; self.best_params = None

        if event.key == 'Up':
            self.time_multiplier = min(self.time_multiplier * 2, 2 ** 10)
        elif event.key == 'Down':
            self.time_multiplier = max(self.time_multiplier / 2, 1)
        elif event.key == 'Space':
            self.is_paused = not self.is_paused
        elif event.key.name.upper() == 'R':
            self.follow_target = None; self.follow_target_idx = -1; self.view.camera.distance = self.INIT_CAMERA_DISTANCE; parameter_changed = True

        if parameter_changed: self.prediction_dirty = True

    def launch_probe(self):
        if not self.follow_target: return
        self.probe_count += 1;
        launch_body = self.follow_target
        launch_dir, launch_pos = self._get_launch_vectors(launch_body)
        probe_vel = launch_body.velocity + launch_dir * self.launch_speed_dv
        new_probe = Probe(name=f"Probe-{self.probe_count}", position=launch_pos, velocity=probe_vel,
                          parent=launch_body.name)
        self.bodies.append(new_probe);
        self._create_visuals_for_body(new_probe);
        self.positions[new_probe.name] = [new_probe.position]
        self.canvas.app.engine.add_body(new_probe, self.bodies)
        print(f"🚀 LAUNCHED {new_probe.name} from {launch_body.name}!")
        self.follow_target = new_probe

    def _update_prediction_path(self):
        if not self.launch_mode_active or not self.show_prediction:
            self.prediction_path_visual.visible = False;
            return

        self.prediction_path_visual.visible = True
        self.launch_ui_label.text = "Calculating trajectory..."

        launch_body = self.follow_target
        launch_dir, launch_pos = self._get_launch_vectors(launch_body)
        probe_vel = launch_body.velocity + launch_dir * self.launch_speed_dv
        ghost_probe = Probe(name="ghost", position=launch_pos, velocity=probe_vel)

        non_probe_bodies = [b for b in self.bodies if not isinstance(b, Probe)]
        path = run_prediction(non_probe_bodies, ghost_probe, duration_days=365 * 4, dt=self.base_dt)
        self.prediction_path_visual.set_data(pos=path * self.RENDER_SCALE, color=(0, 1, 0.5, 0.7))
        self.prediction_dirty = False

    def _optimize_trajectory(self):
        if not self.launch_mode_active or self.target_planet_idx < 0:
            self.optimizing = False;
            return

        target_planet = self.planets[self.target_planet_idx]
        self.launch_ui_label.text = f"Optimizing trajectory to {target_planet.name}..."

        best_dist = float('inf')
        if self.best_params: best_dist = self.best_params['dist']

        for _ in range(20):
            angle = self.launch_angle + np.random.uniform(-20, 20)
            speed = self.launch_speed_dv + np.random.uniform(-1500, 1500)

            launch_dir, launch_pos = self._get_launch_vectors(self.follow_target, angle=angle)
            probe_vel = self.follow_target.velocity + launch_dir * speed
            ghost_probe = Probe(name="ghost", position=launch_pos, velocity=probe_vel)

            non_probe_bodies = [b for b in self.bodies if not isinstance(b, Probe)]
            path = run_prediction(non_probe_bodies, ghost_probe, duration_days=365 * 4, dt=self.base_dt)
            dist = evaluate_trajectory(path, target_planet, non_probe_bodies, self.base_dt)

            if dist < best_dist:
                best_dist = dist
                self.best_params = {'angle': angle, 'speed': speed, 'path': path, 'dist': dist}

        self.launch_angle = self.best_params['angle']
        self.launch_speed_dv = self.best_params['speed']
        self.prediction_path_visual.set_data(pos=self.best_params['path'] * self.RENDER_SCALE, color=(0, 1, 0.5, 0.7))
        self.prediction_path_visual.visible = True
        self.optimizing = False;
        self.prediction_dirty = False

    def update_frame(self, event):
        if not hasattr(self.canvas.app, 'engine'): return
        current_et = self.canvas.app.engine.et
        date_str = spiceypy.et2utc(current_et, "C", 3)

        self.launch_mode_active = self.follow_target and self.follow_target.body_type == 'planet'

        if self.is_paused:
            self.time_label.text = f"{date_str} (PAUSED)"
            if self.launch_mode_active:
                if self.optimizing:
                    self._optimize_trajectory()
                elif self.prediction_dirty and self.show_prediction:
                    self._update_prediction_path()
                self._update_launch_ui()
            return

        self.time_label.text = f"{date_str} | Speed: {self.time_multiplier:.0f}x"

        if self.launch_mode_active:
            if self.optimizing:
                self._optimize_trajectory()
            elif self.prediction_dirty and self.show_prediction:
                self._update_prediction_path()
            self._update_launch_ui()
        else:
            self.launch_ui_label.text = "";
            self.targeting_line.visible = False;
            self.prediction_path_visual.visible = False
            self.launch_origin_marker.visible = False;
            self.target_planet_idx = -1;
            self.optimizing = False

        if self.follow_target:
            self.view.camera.center = self.follow_target.position * self.RENDER_SCALE
            self.planet_stats_label.text = self.follow_target.full_description()
            self.planet_stats_label.visible = True
        else:
            self.view.camera.center = [0, 0, 0]
            self.planet_stats_label.visible = False

        for body in self.bodies:
            if body.name not in self.spheres: continue

            self.positions[body.name].append(body.position.copy())
            if len(self.positions[body.name]) > self.trail_length: self.positions[body.name].pop(0)

            trail_scaled = np.array(self.positions[body.name]) * self.RENDER_SCALE
            self.spheres[body.name].transform.translate = trail_scaled[-1]

            props = self.BODY_VISUALS.get(body.name,
                                          self.BODY_VISUALS.get(body.body_type, self.BODY_VISUALS['Default']))
            base_color = props['color']
            colors = np.tile(base_color, (len(trail_scaled), 1));
            colors = np.append(colors, np.linspace(0.0, 0.9, len(trail_scaled))[:, np.newaxis], axis=1)
            self.trails[body.name].set_data(pos=trail_scaled, color=colors)

    def _get_launch_vectors(self, launch_body, angle=None, alt_angle=None):
        angle_rad = np.deg2rad(angle if angle is not None else self.launch_angle)
        alt_angle_rad = np.deg2rad(alt_angle if alt_angle is not None else self.launch_altitude_angle)
        dir_xy = np.array([np.cos(angle_rad), np.sin(angle_rad), 0])
        rot_axis = np.array([-np.sin(angle_rad), np.cos(angle_rad), 0])

        launch_dir = dir_xy * np.cos(alt_angle_rad) + np.cross(rot_axis, dir_xy) * np.sin(alt_angle_rad)
        launch_pos = launch_body.position + launch_dir * self.launch_altitude
        return launch_dir, launch_pos

    def _update_launch_ui(self):
        target_name = self.planets[self.target_planet_idx].name if self.target_planet_idx >= 0 else "None"
        if self.optimizing:
            self.launch_ui_label.text = f"OPTIMIZING TRAJECTORY to {target_name}... (this may take a moment)"
        elif self.prediction_dirty and self.show_prediction:
            self.launch_ui_label.text = "Calculating trajectory..."
        else:
            self.launch_ui_label.text = f"AIMING: {self.follow_target.name} | TARGET: {target_name} | LAT: {self.launch_altitude_angle:.0f}° | ANGLE: {self.launch_angle:.0f}° | Δv: {self.launch_speed_dv / 1000:.1f} km/s"

        launch_dir, launch_pos = self._get_launch_vectors(self.follow_target)
        line_start = launch_pos * self.RENDER_SCALE
        line_length = 30 + (self.launch_speed_dv / 1000) * 2.5
        line_end = line_start + launch_dir * line_length
        self.targeting_line.set_data(pos=np.vstack([line_start, line_end]), color='cyan');
        self.targeting_line.visible = True
        self.launch_origin_marker.set_data(pos=np.array([line_start]), size=8);
        self.launch_origin_marker.visible = True

    def run(self):
        if hasattr(self.canvas.app, 'engine'): self.canvas.app.engine = self.canvas.app.engine
        app.run()