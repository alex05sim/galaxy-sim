import numpy as np
from vispy.scene.visuals import Markers

# view_controller.py
from functools import partial

class BodyInteractor:
    def __init__(self, viewer):
        self.viewer = viewer
        # For each body, hook mouse_enter, mouse_leave, mouse_press
        for name, body in zip(viewer.markers.keys(), viewer.bodies):
            marker = viewer.markers[name]
            # bind the body directly into the handler
            marker.events.mouse_move.connect(partial(self._on_hover,   body))
            marker.events.mouse_move.connect(partial(self._on_unhover, body))
            marker.events.mouse_press.connect(partial(self._on_click,   body))

    def _on_hover(self, body, event):
        self.viewer.info_label.text    = body.short_description()
        self.viewer.info_label.visible = True

    def _on_unhover(self, body, event):
        self.viewer.info_label.visible = False

    def _on_click(self, body, event):
        self.viewer.full_info_label.text    = body.full_description()
        self.viewer.full_info_label.visible = True
        ##self.viewer.focus_on(body)
