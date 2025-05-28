
import numpy as np
from typing import List

G = 6.67430e-11  # Gravitational constant
EPSILON = 1e-8 # softening to avoid div by zero

class Body:
    #intlizies body
    def __init__(self, mass: float, position: List[float], velocity: List[float] = None, name: str = None, category: str = None):
        assert mass > 0, f"Mass must be positive, got {mass}"
        self.mass = mass
        self.position = np.array(position, dtype=np.float64)
        self.velocity = np.array(velocity if velocity is not None else [0, 0,0], dtype=np.float64)
        self.acceleration = np.zeros(3, dtype=np.float64)
        self.force = np.zeros(3, dtype=np.float64)

        self.name = name or "Unnamed"
        self.category = category or "generic"


    def __repr__(self):
        return f"Body(name={self.name}, mass = {self.mass:.2e}, pos = {self.position}, velocity = {self.velocity}, accel = {self.acceleration})"

    def __str__(self):
        return f"{self.name} @ {self.position.round(3)}"


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


