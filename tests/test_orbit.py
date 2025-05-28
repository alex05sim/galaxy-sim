import numpy as np
from galaxy_sim.gravity import Body, update_accelerations, velocity_verlet_step

def test_earth_sun_orbit():
    # Create Sun and Earth
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
        velocity=[0, 29_780, 0],  # near-circular orbit
        name="Earth",
        category="planet"
    )

    bodies = [sun, earth]
    update_accelerations(bodies)

    dt = 60 * 60  # 1 hour
    steps = 24 * 365  # simulate one year
    positions = []

    for step in range(steps):
        velocity_verlet_step(bodies, dt)
        if step % 100 == 0:
            positions.append(earth.position.copy())

    # Validation
    initial_distance = np.linalg.norm(positions[0])
    final_distance = np.linalg.norm(positions[-1])
    drift = abs(final_distance - initial_distance) / initial_distance

    print(f"🌍 Initial distance: {initial_distance:.2e} m")
    print(f"🌍 Final distance:   {final_distance:.2e} m")
    print(f"📉 Drift ratio:      {drift:.5f}")

    assert drift < 0.05, f"Orbit drifted too far: {drift:.2%}"
