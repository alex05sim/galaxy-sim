
import numpy as np

class Body:
    def __init__(self, mass, position, velocity, name = None):
        self.mass = mass
        self.position = np.array(position, dtype=np.float64)
        self.velocity = np.array(velocity, dtype=np.float64)
        self.acceleration = np.array(0, dtype=np.float64)
        self.name = name or "Unnamed"

    def __repr__(self):
        return f"Body(name={self.name}, mass = {self.mass:.2e}, pso = {self.position}, {self.velocity}, {self.acceleration})"