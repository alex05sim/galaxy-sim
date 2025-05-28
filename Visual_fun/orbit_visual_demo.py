import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from galaxy_sim.visualization.orbit_plotter import OrbitPlotter3D
from galaxy_sim.gravity import Body, update_accelerations, velocity_verlet_step



# Init system
sun = Body(
    mass=1.989e30,
    position=[0, 0, 0],
    velocity=[0, 0, 0],
    name="Sun",
    category="star"
)

earth = Body(
    mass=5.972e24,
    position=[1.496e11, 0, 0],
    velocity=[0, 29_780, 0],
    name="Earth",
    category="planet"
)

bodies = [sun, earth]
update_accelerations(bodies)

positions = []
dt = 60 * 60
steps = 24 * 365

for _ in range(steps):
    velocity_verlet_step(bodies, dt)
    positions.append(earth.position.copy())

# Plot
plotter = OrbitPlotter3D("Earth Orbit 3D")
plotter.plot_orbit(positions, label="Earth")
plotter.plot_body([0, 0, 0], label="Sun", color="orange")
plotter.show()