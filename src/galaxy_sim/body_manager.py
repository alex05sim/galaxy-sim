#boody_manager

class BodyManager:
    def __init__(self, bodies: list, viewer):
        self.bodies = {body.name: body for body in bodies}
        self.viewer = viewer
        self.viewer.bodies = list(self.bodies.values())
        self.viewer._init_bodies()

    def add_body(self, body):
        self.bodies[body.name] = body
        self.viewer.bodies = list(self.bodies.values())
        self.viewer._init_bodies()

    def remove_body(self, name):
        if name in self.bodies:
            del self.bodies[name]
            self.viewer.bodies = list(self.bodies.values())
            self.viewer._init_bodies()

    def update_body(self, name, **kwargs):
        if name in self.bodies:
            body = self.bodies[name]
            for key, value in kwargs.items():
                setattr(body, key, value)
