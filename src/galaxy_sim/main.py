
from galaxy_sim.gravity import Body, update_accelerations, velocity_verlet_step, velocity_verlet_step_gpu
from galaxy_sim.view_controller import BodyInteractor
from galaxy_sim.viewer import OrbitViewer3D
from galaxy_sim.solar_system import load_solar_system


# Setup system
bodies = load_solar_system()
update_accelerations(bodies)

# Viewer
viewer = OrbitViewer3D(bodies)
viewer.time_multiplier = 1.0
viewer.base_dt = 60 * 60 # second per step

interactor = BodyInteractor(viewer)


# Hook up simulation update
def simulate(event):
    viewer.steps_to_run += viewer.time_multiplier

    # Cap how many we simulate in one frame (avoid freezing)
    max_steps_per_frame = 1000

    steps_this_frame = min(int(viewer.steps_to_run), max_steps_per_frame)
    for _ in range(steps_this_frame):
        velocity_verlet_step_gpu(bodies, dt=viewer.base_dt)
        viewer.sim_time += viewer.base_dt
        viewer.steps_to_run -= 1




viewer.timer.connect(simulate)
viewer.run()

