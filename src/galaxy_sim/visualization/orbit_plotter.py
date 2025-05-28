import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

class OrbitPlotter3D:
    def __init__(self, title="3D Orbit", figsize=(8, 6)):
        self.fig = plt.figure(figsize=figsize)
        self.ax = self.fig.add_subplot(111, projection='3d')
        self.ax.set_title(title)
        self.ax.set_xlabel("X (m)")
        self.ax.set_ylabel("Y (m)")
        self.ax.set_zlabel("Z (m)")
        self.ax.grid(True)

    def plot_orbit(self, positions, label="Orbit", color="blue"):
        positions = np.array(positions)
        x, y, z = positions[:, 0], positions[:, 1], positions[:, 2]
        self.ax.plot(x, y, z, label=label, color=color)

    def plot_body(self, position, label="Body", color="orange", size=300):
        self.ax.scatter(*position, color=color, s=size, label=label)

    def show(self):
        self.ax.legend()
        plt.tight_layout()
        plt.show()
