# main.py

import os
import spiceypy as spice
from galaxy_sim.engine import SimulationEngine
from galaxy_sim.viewer import OrbitViewer3D
from galaxy_sim.solar_system import load_bodies_from_spice


def main():
    script_dir = os.path.dirname(__file__) if "__file__" in locals() else "."
    spk_path = os.path.join(script_dir, "de442.bsp")
    tls_path = os.path.join(script_dir, "latest_leapseconds.tls")

    try:
        spice.furnsh(tls_path)
        spice.furnsh(spk_path)
        print("✔ SPICE kernels loaded.")
    except Exception as e:
        print(f"✘ ERROR loading SPICE kernels: {e}")
        return

    epoch = "2025-06-01"
    initial_et = spice.str2et(f"{epoch} TDB")
    bodies = load_bodies_from_spice(spk_path, initial_et)
    if not bodies:
        print("✘ No bodies were loaded.")
        spice.kclear()
        return

    engine = SimulationEngine(bodies, initial_et)
    viewer = OrbitViewer3D(bodies, initial_et)

    viewer.canvas.app.engine = engine

    def simulate(event):
        if not viewer.is_paused:
            steps_to_run = int(viewer.time_multiplier)
            if steps_to_run > 0:
                for _ in range(steps_to_run):
                    engine.step(dt=viewer.base_dt)
                engine.update_body_objects(viewer.bodies)

    viewer.timer.connect(simulate)

    print("\n" + "=" * 60)
    print("🚀 N-BODY GRAVITY SIMULATOR & MISSION PLANNER 🚀")
    print("=" * 60)
    print("\n--- Camera & Time Controls ---")
    print("  - Drag Mouse / Scroll Wheel: Rotate & Zoom")
    print("  - Up/Down Arrows / Spacebar: Control Time Speed & Pause")

    print("\n--- Planet Selection ---")
    print("  - Left/Right Arrows: Cycle through planets to select a launch point")

    print("\n--- Gravity Assist Probe Launcher ---")
    print("  - W / S Keys: Adjust launch altitude")
    print("  - A / D Keys: Adjust launch angle")
    print("  - G(+)/H(-) Keys: Adjust launch speed (delta-v)")
    print("  - The yellow line shows your predicted trajectory.")
    print("  - Press 'L' to LAUNCH!")
    print("=" * 60 + "\n")

    viewer.run()

    spice.kclear()
    print("✔ SPICE kernels cleared.")


if __name__ == "__main__":
    main()