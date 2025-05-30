
import numpy as np
import cupy as cp
from typing import List


from typing import List

G = 6.67430e-11  # Gravitational constant
EPSILON = 1e-8 # softening to avoid div by zero

class Body:
    #intlizies body
    def __init__(self, mass: float, position: List[float], velocity: List[float] = None, name: str = None,
                 body_type: str = None, body_subtype: str = None):
        assert mass > 0, f"Mass must be positive, got {mass}"
        self.mass = mass
        self.position = np.array(position, dtype=np.float64)
        self.velocity = np.array(velocity if velocity is not None else [0, 0,0], dtype=np.float64)
        self.acceleration = np.zeros(3, dtype=np.float64)
        self.force = np.zeros(3, dtype=np.float64)

        self.name = name or "Unnamed"
        self.body_type = body_type or "generic" #body type
        self.body_subtype = body_subtype or None # detail

    def __repr__(self):
        return f"Body(name={self.name}, mass = {self.mass:.2e}, pos = {self.position}, velocity = {self.velocity}, accel = {self.acceleration})"

    def __str__(self):
        return f"{self.name} @ {self.position.round(3)}"

    def short_description(self):
        return f"{self.name}: {self.body_type} @ {np.linalg.norm(self.position):2e} m"

    def full_description(self):
        return (f"Name: {self.name}\n"
                f"Type: {self.body_type}\n"
                f"Subtype: {self.body_subtype}\n"
                f"Mass: {self.mass:.2e} kg\n"
                f"Position: {self.position}\n"
                f"Velocity: {self.velocity}")


## calculates gravitational force using good old Newton's law
def gravitational_force(target, source):
    r_vector = source.position - target.position
    distance = np.linalg.norm(r_vector) + EPSILON
    unit_vector = r_vector / distance
    force_magnitude = G * source.mass * target.mass / distance ** 2
    force_vector = force_magnitude * unit_vector
    return force_vector

#updates acceleration
def update_accelerations(bodies: List[Body]) -> None:
    for body in bodies:
        net_force = np.zeros(3, dtype=np.float64)
        for other_body in bodies:
            if other_body != body:
                net_force += gravitational_force(body, other_body)
            body.force = net_force.copy()
            body.acceleration = net_force / body.mass


def update_accelerations_gpu(positions, masses):
    N = positions.shape[0]

    # Calculate all pairwise differences r_j - r_i
    r_i = positions[:, cp.newaxis, :]  # shape (N, 1, 3)
    r_j = positions[cp.newaxis, :, :]  # shape (1, N, 3)
    r_ij = r_j - r_i  # shape (N, N, 3)

    # Compute distances with small epsilon for stability
    distances = cp.linalg.norm(r_ij, axis=2) + 1e-10  # shape (N, N)

    # Mask out self-interaction
    mask = ~cp.eye(N, dtype=bool)
    inv_dist3 = cp.where(mask, 1.0 / distances**3, 0.0)  # shape (N, N)

    # Broadcast masses: shape (1, N, 1)
    masses_j = masses[cp.newaxis, :, cp.newaxis]

    # Compute force contributions
    forces = G * r_ij * inv_dist3[:, :, cp.newaxis] * masses_j  # shape (N, N, 3)

    # Sum over all j to get net acceleration for each i
    accels = cp.sum(forces, axis=1)  # shape (N, 3)
    return accels

#updates position and velocity (Verlet integration style)
def velocity_verlet_step(bodies: List[Body], dt: float) -> None:
    old_accelerations = [body.acceleration.copy() for body in bodies]

    for body, old_acc in zip(bodies, old_accelerations):
        body.position += body.velocity * dt + 0.5 * old_acc * dt ** 2

    #Recalculate accelerations with new positions
    update_accelerations(bodies)

    #Update velocities
    for body, old_acc in zip(bodies, old_accelerations):
        body.velocity += 0.5 * (old_acc + body.acceleration) * dt





def velocity_verlet_step_gpu(bodies, dt):
    N = len(bodies)

    # Gather all properties to CuPy arrays
    positions = cp.array([body.position for body in bodies])
    velocities = cp.array([body.velocity for body in bodies])
    accelerations = cp.array([body.acceleration for body in bodies])
    masses = cp.array([body.mass for body in bodies])

    old_accels = accelerations.copy()

    # Update positions
    positions += velocities * dt + 0.5 * old_accels * dt**2

    # Update accelerations with new positions
    accelerations = update_accelerations_gpu(positions, masses)

    # Update velocities
    velocities += 0.5 * (old_accels + accelerations) * dt

    # Push back to CPU
    pos_np = cp.asnumpy(positions)
    vel_np = cp.asnumpy(velocities)
    acc_np = cp.asnumpy(accelerations)

    for i in range(N):
        bodies[i].position = pos_np[i]
        bodies[i].velocity = vel_np[i]
        bodies[i].acceleration = acc_np[i]

#Kinetetic energy
def kinetic_energy(body: Body) -> float:
    return 0.5 * body.mass * np.linalg.norm(body.velocity) ** 2

#Potential_energy
def potential_energy(body1: Body, body2: Body) -> float:
    r = np.linalg.norm(body2.position - body1.position) + EPSILON
    return -G * body1.mass * body2.mass / r


def simulate(bodies: List[Body], dt: float, steps: int):
    for step in range(steps):
        velocity_verlet_step(bodies, dt)


