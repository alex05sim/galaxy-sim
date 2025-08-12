# prediction.py

import numpy as np
import copy
from .gravity import Body, G, EPSILON


def gravitational_force_cpu(target_pos, source_mass, source_pos):
    """A simplified, faster force calculation for the predictor."""
    r_vector = source_pos - target_pos
    distance_sq = np.dot(r_vector, r_vector)
    if distance_sq < EPSILON:
        return np.zeros(3)

    distance = np.sqrt(distance_sq)
    force_magnitude = G * source_mass / distance_sq
    force_vector = force_magnitude * (r_vector / distance)
    return force_vector


def run_prediction(bodies: list, probe: Body, duration_days: int, dt: float) -> np.ndarray:
    """
    Runs a fast, in-memory simulation to predict a probe's trajectory.
    It assumes the planets themselves follow their main course (Keplerian orbits),
    which is a valid and fast approximation for this kind of tool.
    """
    # Create copies of the simulation objects so we don't affect the main simulation
    sim_bodies = copy.deepcopy(bodies)
    sim_probe = copy.deepcopy(probe)

    num_steps = int(duration_days * 86400 / dt)
    path = np.zeros((num_steps, 3))

    for i in range(num_steps):
        # Calculate the total acceleration on the probe from all celestial bodies
        total_accel = np.zeros(3)
        for body in sim_bodies:
            total_accel += gravitational_force_cpu(sim_probe.position, body.mass, body.position)

        # Update probe's velocity and position using Euler integration
        sim_probe.velocity += total_accel * dt
        sim_probe.position += sim_probe.velocity * dt
        path[i] = sim_probe.position

        # Update the positions of the planets for the next step.
        # This uses their current velocity, which is a good approximation for a prediction.
        for body in sim_bodies:
            body.position += body.velocity * dt

        # Stop early if the probe flies too far away
        if np.linalg.norm(sim_probe.position) > 2e13:
            path[i:] = sim_probe.position
            break

    return path