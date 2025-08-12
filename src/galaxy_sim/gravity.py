# gravity.py

import numpy as np
import cupy as cp
from typing import List

G = 6.67430e-11
EPSILON = 1e-8

class Body:
    def __init__(self, mass: float, position: List[float], velocity: List[float] = None,
                 name: str = None, body_type: str = None, parent: str = None):
        assert mass > 0, f"Mass must be positive, got {mass}"
        self.mass = mass
        self.position = np.array(position, dtype=np.float64)
        self.velocity = np.array(velocity if velocity is not None else [0, 0, 0], dtype=np.float64)
        self.name = name or "Unnamed"
        self.body_type = body_type or "generic"
        self.parent = parent

    def __repr__(self):
        return f"Body(name={self.name})"

    def short_description(self):
        return f"{self.name}: {self.body_type.capitalize()}"

    def full_description(self):
        speed_kms = np.linalg.norm(self.velocity) / 1000
        return (f"Name: {self.name}\n"
                f"Type: {self.body_type.capitalize()}\n"
                f"Mass: {self.mass:.2e} kg\n"
                f"Speed: {speed_kms:.2f} km/s")

class Probe(Body):
    """A specialized Body with very low mass to act as a spacecraft."""
    def __init__(self, **kwargs):
        super().__init__(mass=1.0, body_type='probe', **kwargs)

    def full_description(self):
        speed_kms = np.linalg.norm(self.velocity) / 1000
        parent_str = f"\nLaunched from: {self.parent}" if self.parent else ""
        return (f"Name: {self.name}\n"
                f"Type: {self.body_type.capitalize()}\n"
                f"Speed: {speed_kms:.2f} km/s{parent_str}")

def update_accelerations_gpu(positions, masses):
    N = positions.shape[0]
    positions_cp = cp.array(positions, dtype=cp.float64)
    masses_cp = cp.array(masses, dtype=cp.float64)
    r_i = positions_cp[:, cp.newaxis, :]
    r_j = positions_cp[cp.newaxis, :, :]
    r_ij = r_j - r_i
    distances = cp.linalg.norm(r_ij, axis=2) + EPSILON
    mask = ~cp.eye(N, dtype=bool)
    inv_dist3 = cp.where(mask, 1.0 / distances**3, 0.0)
    masses_j = masses_cp[np.newaxis, :, np.newaxis]
    accels = G * cp.sum(r_ij * inv_dist3[:, :, np.newaxis] * masses_j, axis=1)
    return accels