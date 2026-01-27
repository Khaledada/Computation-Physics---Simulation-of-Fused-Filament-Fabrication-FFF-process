import numpy as np
import matplotlib.pyplot as plt

# -------------------------------------------------
# 1. Geometry (meters)
# -------------------------------------------------
Lx = 0.05     # 50 mm
Lz = 0.005    # 5 mm

Nx = 250      # coarser mesh
Nz = 25      # coarser mesh

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

h = 50.0           # convection coefficient W/(m^2 K)

# -------------------------------------------------
# 4. Time settings
# -------------------------------------------------
dt = 0.1           # time step (s)
t_end = 100.0
tolerance = 1.6e-2

# -------------------------------------------------
# 5. Initialize temperature field
# -------------------------------------------------
T = np.ones((Nz, Nx)) * T_init
time = 0.0
steady_state_time = None

# -------------------------------------------------
# 6. Time loop
# -------------------------------------------------
while time < t_end:
    T_old = T.copy()

    # --- Iterative implicit solver (Gauss-Seidel)
    for _ in range(50):  # instead of 200
        for i in range(1, Nz-1):
            for j in range(1, Nx-1):
                # Implicit scheme: (T - T_old)/dt = alpha * (d²T/dz² + d²T/dx²)
                # Rearranged for iteration:
                Fo_z = alpha * dt / dz**2
                Fo_x = alpha * dt / dx**2
                T[i, j] = (T_old[i, j] + Fo_z * (T[i+1, j] + T[i-1, j]) + Fo_x * (T[i, j+1] + T[i, j-1])) / (1 + 2*Fo_z + 2*Fo_x)

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
        steady_state_time = time
        print(f"\n{'='*50}")
        print(f"✓ STEADY STATE REACHED")
        print(f"Steady state time: {steady_state_time:.2f} s")
        print(f"Max change: {max_change:.2e}")
        print(f"{'='*50}\n")
        break
    
    if time % 5 < dt:  # Print every ~5 seconds
        print(f"t = {time:.1f} s, max_change = {max_change:.2e}")

    time += dt

# If loop ends without steady state
if steady_state_time is None:
    print(f"\nTime loop ended at t = {time:.1f} s without reaching steady state")
    print(f"Final max_change = {max_change:.2e} (tolerance = {tolerance:.2e})")

# -------------------------------------------------
# 9. Post-processing plots
# -------------------------------------------------

# Temperature field
plt.figure(figsize=(8, 2))
plt.imshow(T, origin='lower', extent=[0, Lx*1000, 0, Lz*1000], aspect='auto', cmap='jet')   # 🔵 cold → 🔴 hot
plt.colorbar(label='Temperature (°C)')
plt.xlabel(f'x (mm) with Mesh size={Nx}')
plt.ylabel(f'z (mm) with Mesh size={Nz}')
plt.title(f'Temperature Distribution with h = {h} W/m²K')
plt.show()

# Vertical temperature profile at mid-width
mid_x = Nx // 2
plt.figure()
plt.plot(T[:, mid_x], np.linspace(0, Lz*1000, Nz))
plt.xlabel(f'Temperature (°C) with Mesh size={Nx}')
plt.ylabel(f'z (mm) with Mesh size={Nz}')
plt.title(f'Vertical Temperature Profile (Mid Width) with h = {h} W/m²K')
plt.grid()
plt.show()
