# prediction.py

import numpy as np
import copy
from .gravity import Body, G, EPSILON


def gravitational_force_cpu(target, source):
    """CPU-based force calculation for the predictor."""
    r_vector = source.position - target.position
    distance = np.linalg.norm(r_vector)
    if distance < EPSILON:
        return np.zeros(3)
    unit_vector = r_vector / distance
    force_magnitude = G * source.mass * target.mass / (distance ** 2)
    return force_magnitude * unit_vector


def velocity_verlet_step_cpu(bodies, dt):
    """A single step of the Velocity-Verlet integrator running on the CPU."""
    accelerations = []
    for body1 in bodies:
        net_force = np.zeros(3)
        for body2 in bodies:
            if body1 is body2: continue
            net_force += gravitational_force_cpu(body1, body2)
        accelerations.append(net_force / body1.mass)

    new_positions = []
    for i, body in enumerate(bodies):
        new_pos = body.position + body.velocity * dt + 0.5 * accelerations[i] * dt ** 2
        new_positions.append(new_pos)

    new_accelerations = []
    temp_bodies = [copy.copy(b) for b in bodies]
    for i, body in enumerate(temp_bodies):
        body.position = new_positions[i]

    for body1 in temp_bodies:
        net_force = np.zeros(3)
        for body2 in temp_bodies:
            if body1 is body2: continue
            net_force += gravitational_force_cpu(body1, body2)
        new_accelerations.append(net_force / body1.mass)

    for i, body in enumerate(bodies):
        body.velocity += 0.5 * (accelerations[i] + new_accelerations[i]) * dt
        body.position = new_positions[i]


def run_prediction(bodies: list, probe: Body, duration_days: int, dt: float) -> np.ndarray:
    """Runs a temporary, in-memory simulation to predict a probe's trajectory."""
    sim_bodies = copy.deepcopy(bodies)
    sim_probe = copy.deepcopy(probe)

    all_sim_bodies = sim_bodies + [sim_probe]

    num_steps = int(duration_days * 86400 / dt)
    path = np.zeros((num_steps, 3))

    for i in range(num_steps):
        velocity_verlet_step_cpu(all_sim_bodies, dt)
        path[i] = sim_probe.position

        if np.linalg.norm(sim_probe.position) > 2e13:
            path[i:] = sim_probe.position
            break
    return path


def evaluate_trajectory(path: np.ndarray, target_body: Body, bodies: list, dt: float) -> float:
    """Calculates the closest approach of a trajectory to a target body."""
    sim_bodies = copy.deepcopy(bodies)
    target_sim = next((b for b in sim_bodies if b.name == target_body.name), None)
    if not target_sim: return float('inf')

    target_path = np.zeros_like(path)
    for i in range(len(path)):
        target_path[i] = target_sim.position

        # Update target's position based on gravity from all other major bodies
        net_force = np.zeros(3)
        for other_body in sim_bodies:
            if other_body is target_sim: continue
            net_force += gravitational_force_cpu(target_sim, other_body)

        accel = net_force / target_sim.mass
        target_sim.velocity += accel * dt
        target_sim.position += target_sim.velocity * dt

    distances = np.linalg.norm(path - target_path, axis=1)
    return np.min(distances)