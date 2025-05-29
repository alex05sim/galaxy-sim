# solar_system.py
from galaxy_sim.gravity import Body

def load_solar_system():
    return [
        Body(1.989e30, [0, 0, 0], [0, 0, 0], name="Sun", body_type="star", body_subtype="main_sequence"),
        Body(3.285e23, [5.79e10, 0, 0], [0, 47890, 0], name="Mercury", body_type="planet", body_subtype="rocky"),
        Body(4.867e24, [1.08e11, 0, 0], [0, 35040, 0], name="Venus", body_type="planet", body_subtype="rocky"),
        Body(5.972e24, [1.496e11, 0, 0], [0, 29780, 0], name="Earth", body_type="planet", body_subtype="rocky"),
        Body(7.342e22, [1.496e11 + 3.84e8, 0, 0], [0, 29780 + 1022, 0], name="Moon", body_type="moon", body_subtype="rocky"),
        Body(6.39e23, [2.28e11, 0, 0], [0, 24070, 0], name="Mars", body_type="planet", body_subtype="rocky"),
        Body(1.898e27, [7.78e11, 0, 0], [0, 13070, 0], name="Jupiter", body_type="planet", body_subtype="gas_giant"),
        Body(4.8e22, [7.78e11 + 6.71e8, 0, 0], [0, 13070 + 13740, 0], name="Europa", body_type="moon", body_subtype="ice"),
        Body(5.683e26, [1.43e12, 0, 0], [0, 9680, 0], name="Saturn", body_type="planet", body_subtype="gas_giant"),
        Body(1.3452e23, [1.43e12 + 1.22e9, 0, 0], [0, 9680 + 5560, 0], name="Titan", body_type="moon", body_subtype="hazy"),
        Body(8.681e25, [2.87e12, 0, 0], [0, 6800, 0], name="Uranus", body_type="planet", body_subtype="ice_giant"),
        Body(1.024e26, [4.5e12, 0, 0], [0, 5430, 0], name="Neptune", body_type="planet", body_subtype="ice_giant"),
        Body(1.309e22, [5.91e12, 0, 0], [0, 4740, 0], name="Pluto", body_type="dwarf", body_subtype="icy_dwarf"),
    ]
