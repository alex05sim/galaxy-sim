
from galaxy_sim.gravity import Body, update_accelerations, velocity_verlet_step
from galaxy_sim.viewer import OrbitViewer3D
from galaxy_sim.solar_system import load_solar_system

# Setup system
bodies = load_solar_system()
update_accelerations(bodies)

# Viewer
viewer = OrbitViewer3D(bodies)

# Hook up simulation update
def simulate(event):
    for _ in range(10):
        velocity_verlet_step(bodies, dt=1)

viewer.timer.connect(simulate)
viewer.run()
