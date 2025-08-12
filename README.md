# 🚀 N-Body Gravity Simulator & Mission Planner

This is a high-performance, interactive 3D simulation of our solar system, built in Python. It uses the `cupy` library for GPU-accelerated physics calculations and `vispy` for high-performance OpenGL visualization. The orbital data is sourced from NASA's official SPICE kernels, ensuring scientific accuracy.

Beyond being a simple viewer, this project has evolved into a feature-rich **Mission Planner**, allowing you to design and launch your own interplanetary probes and visualize complex orbital maneuvers like gravity assists.

![Galaxy Sim Screenshot](https://i.imgur.com/your_screenshot_url.png)
*(Suggestion: Replace this with a screenshot you've taken, like `image_db486b.png`)*

## ✨ Features

- **GPU-Accelerated Physics:** The core N-body gravity calculations are performed on the GPU using `cupy`, allowing for high-speed simulation of thousands of time steps per second.
- **Accurate Orbital Data:** Planet positions, velocities, and masses are loaded from NASA/JPL SPICE kernels (`de442.bsp`), the same data used for real space missions.
- **Interactive 3D Visualization:** A smooth, interactive 3D view of the solar system built with `vispy`.
- **Full Keyboard Control:**
  - **Camera:** Mouse drag to rotate, scroll wheel to zoom.
  - **Time:** Speed up, slow down, and pause the simulation.
  - **Planet Selection:** Cycle through planets with the arrow keys.
- **Live On-Screen Data:** When a planet is selected, its key orbital statistics (speed, position, distance from Sun) are displayed in real-time.
- **Interactive Probe Launcher:**
  - Select any planet as a launchpad.
  - Visually aim your probe by setting its launch latitude (**W/S**) and angle (**A/D**).
  - Set the launch speed (**+/-**) to control the delta-v of your burn.
- **On-Demand Trajectory Prediction:** Press **'P'** to toggle a high-speed prediction of your probe's trajectory over the next 4 years, allowing you to plan gravity assists.
- **Automated Trajectory Optimization:** Press **'T'** to select a target planet, then press **'O'** to have the simulation automatically search for the best launch parameters to achieve an intercept.
- **Saturn's Rings:** A visually pleasing particle-based ring system for Saturn.

## 🛠️ Setup and Installation

### Prerequisites
- An NVIDIA GPU with CUDA installed.
- Python 3.8+

### Installation
1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/your-username/galaxy-sim.git](https://github.com/your-username/galaxy-sim.git)
    cd galaxy-sim
    ```
2.  **Install Python dependencies:**
    ```bash
    pip install numpy cupy-cudaXX vispy spiceypy
    ```
    *(Note: Replace `cupy-cudaXX` with the version corresponding to your CUDA installation, e.g., `cupy-cuda11x` or `cupy-cuda12x`)*

3.  **Download SPICE Kernels:**
    This simulation requires two data files from the NASA NAIF repository. Download them and place them in the `src/galaxy_sim` directory:
    - **`de442.bsp`**: A large planetary ephemeris file.
    - **`latest_leapseconds.tls`**: The leap seconds kernel.

## ▶️ How to Run

Navigate to the `src/galaxy_sim` directory in your terminal and run the main script:

```bash
python main.py
```

## 🎮 Controls

### General Controls
- **Rotate Camera:** Click and drag the mouse.
- **Zoom:** Use the mouse scroll wheel.
- **Simulation Speed:** `Up Arrow` (faster), `Down Arrow` (slower).
- **Pause/Resume:** `Spacebar`.

### Mission Planning
1.  **Select Launch Planet:** Use the **`Left` / `Right` Arrow Keys** to cycle through the planets. The camera will automatically follow your selection and display its stats.
2.  **Enter Launch Mode:** Selecting a planet automatically enters Launch Mode.
3.  **Aim Probe:**
    - `W` / `S`: Adjust launch latitude (north/south on the planet).
    - `A` / `D`: Adjust launch angle (azimuth).
4.  **Set Speed:** `+` / `-`: Adjust launch delta-v (speed).
5.  **Predict Trajectory:** `P`: Toggle the 4-year trajectory prediction line (green).
6.  **Optimize Trajectory:**
    - `T`: Cycle through available target planets.
    - `O`: Begin an automated search for the best trajectory to the current target.
7.  **Launch:** `L`: Launch the probe!
8.  **Reset View:** `R`: Unfollow all bodies and return to the wide solar system view.
