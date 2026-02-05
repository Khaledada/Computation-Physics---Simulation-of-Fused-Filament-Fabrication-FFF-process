import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# Safe-run modifications: fewer Gauss-Seidel iterations and shorter time

# -------------------------------------------------
# 1. Geometry (meters)
# -------------------------------------------------
Lx = 0.05     # 50 mm
Lz = 0.005    # 5 mm

Nx = 100        # change for mesh sensitivity
Nz = 10         # change for mesh sensitivity

dx = Lx / (Nx - 1)
dz = Lz / (Nz - 1)

# -------------------------------------------------
# 2. Material properties
# -------------------------------------------------
rho = 1200.0       # kg/m^3
cp  = 1500.0       # J/(kg K)
k   = 0.25         # W/(m K)

alpha = k / (rho * cp)

# -------------------------------------------------
# 3. Boundary & initial conditions (°C)
# -------------------------------------------------
T_init = 20.0
T_bed  = 60.0
T_heat = 200.0
T_inf  = 20.0

h = 5.0           # convection coefficient W/(m^2 K)

# -------------------------------------------------
# 4. Time settings (reduced for safe run)
# -------------------------------------------------
dt = 0.1           # time step (s)
t_end = 30.0
tolerance = 1e-4

# -------------------------------------------------
# 5. Initialize temperature field
# -------------------------------------------------
T = np.ones((Nz, Nx)) * T_init
time = 0.0

# -------------------------------------------------
# 6. Time loop
# -------------------------------------------------
steady_time = None

while time < t_end:
    T_old = T.copy()

    # --- Iterative implicit solver (Gauss-Seidel) with fewer inner iters
    for _ in range(40):
        for i in range(1, Nz-1):
            for j in range(1, Nx-1):
                T[i, j] = (
                    T_old[i, j]
                    + alpha * dt * (
                        (T[i+1, j] - 2*T[i, j] + T[i-1, j]) / dz**2 +
                        (T[i, j+1] - 2*T[i, j] + T[i, j-1]) / dx**2
                    )
                )

    # -------------------------------------------------
    # 7. Boundary conditions
    # -------------------------------------------------

    # Bottom surface (print bed)
    T[0, :] = T_bed

    # Top surface
    T[-1, 0] = T_heat  # heated element

    for j in range(1, Nx):
        T[-1, j] = (k * T[-2, j] / dz + h * T_inf) / (k / dz + h)

    # Left & right (adiabatic)
    T[:, 0]  = T[:, 1]
    T[:, -1] = T[:, -2]

    # -------------------------------------------------
    # 8. Steady-state check
    # -------------------------------------------------
    max_change = np.max(np.abs(T - T_old))
    if max_change < tolerance:
        print(f"Steady state reached at t = {time:.1f} s")
        break

    time += dt

# -------------------------------------------------
# 9. Post-processing plots
# -------------------------------------------------

# Temperature field
plt.figure(figsize=(8, 2))
plt.imshow(
    T,
    origin='lower',
    extent=[0, Lx * 1000, 0, Lz * 1000],
    aspect='auto',
    cmap='jet',   # 🔵 cold → 🔴 hot
    vmin=20,
    vmax=60
)

plt.colorbar(label='Temperature (°C)')
plt.xlabel('x (mm)')
plt.ylabel('z (mm)')
plt.title('Temperature Distribution')
plt.savefig('temperature_distribution_run.png', dpi=200, bbox_inches='tight')
plt.show()


# Vertical temperature profile at mid-width
mid_x = Nx // 2
plt.figure()
plt.plot(T[:, mid_x], np.linspace(0, Lz*1000, Nz))
plt.xlabel('Temperature (°C)')
plt.ylabel('z (mm)')
plt.title('Vertical Temperature Profile (Mid Width)')
plt.grid()
plt.savefig('vertical_profile_run.png', dpi=200, bbox_inches='tight')
plt.show()

print('Safe run completed, images saved: temperature_distribution_run.png, vertical_profile_run.png')
