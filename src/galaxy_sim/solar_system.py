# solar_system.py

import spiceypy as spice
import numpy as np
from .gravity import Body

BODY_DATA = {
    'SUN': {'mass': 1.989e30, 'type': 'star'}, 'MERCURY': {'mass': 3.3011e23, 'type': 'planet'},
    'VENUS': {'mass': 4.8675e24, 'type': 'planet'}, 'EARTH': {'mass': 5.972e24, 'type': 'planet'},
    'MOON': {'mass': 7.342e22, 'type': 'moon', 'parent': 'Earth'},
    'MARS BARYCENTER': {'mass': 6.4171e23, 'type': 'planet'},
    'JUPITER BARYCENTER': {'mass': 1.8982e27, 'type': 'planet'},
    'IO': {'mass': 8.9319e22, 'type': 'moon', 'parent': 'Jupiter'},
    'EUROPA': {'mass': 4.7998e22, 'type': 'moon', 'parent': 'Jupiter'},
    'GANYMEDE': {'mass': 1.4819e23, 'type': 'moon', 'parent': 'Jupiter'},
    'CALLISTO': {'mass': 1.0759e22, 'type': 'moon', 'parent': 'Jupiter'},
    'SATURN BARYCENTER': {'mass': 5.6834e26, 'type': 'planet'},
    'TITAN': {'mass': 1.3452e23, 'type': 'moon', 'parent': 'Saturn'},
    'URANUS BARYCENTER': {'mass': 8.6810e25, 'type': 'planet'},
    'NEPTUNE BARYCENTER': {'mass': 1.02413e26, 'type': 'planet'},
    'PLUTO BARYCENTER': {'mass': 1.303e22, 'type': 'planet'},
}


def load_bodies_from_spice(spk_path, et):
    bodies = []
    ids = spice.spkobj(spk_path)

    print(f"Found {len(ids)} objects in the SPK kernel.")

    for body_id in ids:
        name = spice.bodc2n(body_id)
        if name not in BODY_DATA: continue
        try:
            state, _ = spice.spkezr(str(body_id), et, "J2000", "NONE", "0")
        except Exception:
            continue

        pos_m = np.array(state[:3]) * 1000.0;
        vel_m_s = np.array(state[3:]) * 1000.0
        body_info = BODY_DATA[name]
        clean_name = name.replace(' BARYCENTER', '').capitalize()
        parent = body_info.get('parent')
        b = Body(name=clean_name, position=pos_m, velocity=vel_m_s, mass=body_info['mass'], body_type=body_info['type'],
                 parent=parent)
        bodies.append(b)

    print(f"✔ Loaded {len(bodies)} celestial bodies.")
    return bodies