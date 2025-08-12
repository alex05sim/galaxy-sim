# engine.py

import cupy as cp
from .gravity import update_accelerations_gpu, Body

class SimulationEngine:
    def __init__(self, bodies: list, initial_et: float):
        self.et = initial_et
        self._set_state_from_bodies(bodies)

    def _set_state_from_bodies(self, bodies: list):
        if not bodies:
            self.positions = cp.array([])
            self.velocities = cp.array([])
            self.masses = cp.array([])
            return
        self.positions = cp.array([b.position for b in bodies], dtype=cp.float64)
        self.velocities = cp.array([b.velocity for b in bodies], dtype=cp.float64)
        self.masses = cp.array([b.mass for b in bodies], dtype=cp.float64)

    def add_body(self, body: Body, all_bodies: list):
        print(f"Adding {body.name} to the simulation engine.")
        self._set_state_from_bodies(all_bodies)

    def step(self, dt: float):
        if self.positions.shape[0] == 0:
            return
        self.et += dt
        a_old = update_accelerations_gpu(self.positions, self.masses)
        self.positions += self.velocities * dt + 0.5 * a_old * dt**2
        a_new = update_accelerations_gpu(self.positions, self.masses)
        self.velocities += 0.5 * (a_old + a_new) * dt

    def get_positions(self):
        return cp.asnumpy(self.positions)

    def get_velocities(self):
        return cp.asnumpy(self.velocities)

    def update_body_objects(self, bodies: list):
        if len(bodies) != self.positions.shape[0]:
            return
        latest_positions = self.get_positions()
        latest_velocities = self.get_velocities()
        for i, body in enumerate(bodies):
            # The body might have been added this frame and not yet be in the engine's list
            if i < len(latest_positions):
                body.position = latest_positions[i]
                body.velocity = latest_velocities[i]