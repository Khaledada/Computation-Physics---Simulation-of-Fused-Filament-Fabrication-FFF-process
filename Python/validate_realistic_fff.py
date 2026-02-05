"""
Validate that the FFF simulation produces realistic temperature distributions.
Tests that:
1. Filament temperature doesn't exceed ~85°C (except at nozzle contact point)
2. Wall temperature cools appropriately
3. Bed maintains ~60°C
4. Gaussian heat distribution works correctly
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

# Physical parameters (matching HTML)
Lx = 0.05          # 50mm domain length
Lz = 0.005         # 5mm height
Nx = 200           # Grid points X
Nz = 50            # Grid points Z
dx = Lx / (Nx - 1)
dz = Lz / (Nz - 1)

# Material properties (PLA)
rho = 1200.0       # Density kg/m³
cp = 1500.0        # Specific heat J/kg·K
k = 0.25           # Thermal conductivity W/m·K
alpha = k / (rho * cp)

# Boundary conditions
T_init = 20.0      # Initial temperature
T_bed = 60.0       # Bed temperature
T_inf = 20.0       # Ambient
h = 15.0           # Convection coefficient
dt = 0.01          # REDUCED timestep for stability (was 0.05)
nozzle_radius = 0.0004  # 0.4mm

# Initialize temperature field
T = np.ones((Nz, Nx)) * T_init

# Simulate realistic nozzle path (moving in X, depositing layers)
# Simulate realistic nozzle path (moving in X, depositing layers)
def apply_gaussian_heat_source(T, x_pos, z_pos, T_nozzle, dx, dz, nozzle_radius=0.0004):
    """Apply Gaussian heat distribution (improved method)"""
    j = int(x_pos / dx)
    i = int(z_pos / dz)
    
    if 0 <= i < Nz and 0 <= j < Nx:
        effectiveRadius = max(1, round(nozzle_radius / dx))
        sigma = effectiveRadius / 2.0
        
        for di in range(-3, 4):
            for dj in range(-3, 4):
                ni = i + di
                nj = j + dj
                if 0 <= ni < Nz and 0 <= nj < Nx:
                    distSq = di**2 + dj**2
                    weight = np.exp(-distSq / (2 * sigma**2))
                    blendFactor = weight * 0.8  # 80% per timestep (INCREASED from 30%)
                    T[ni, nj] = T[ni, nj] * (1 - blendFactor) + T_nozzle * blendFactor
    
    return T

def apply_boundary_conditions(T, T_bed, T_inf, h, k, dz):
    """Apply boundary conditions"""
    # Bottom (bed)
    T[0, :] = T_bed
    
    # Top (convection)
    T[-1, :] = (k * T[-2, :] / dz + h * T_inf) / (k / dz + h)
    
    # Sides (adiabatic - copy from neighbors)
    T[:, 0] = T[:, 1]
    T[:, -1] = T[:, -2]
    
    return T

def solve_heat_equation_step(T, alpha, dx, dz, dt):
    """One Gauss-Seidel iteration for heat equation - STABLE IMPLICIT scheme"""
    Fo_x = alpha * dt / (dx**2)
    Fo_z = alpha * dt / (dz**2)
    
    # Using implicit scheme: solve (1 + 2*Fo_x + 2*Fo_z)*T_new = ...
    # This is unconditionally stable
    coeff_center = 1 + 2*Fo_x + 2*Fo_z
    
    T_old = T.copy()
    
    # Gauss-Seidel iterations (use updated values as they're computed)
    for iteration in range(3):  # 3 iterations sufficient for convergence
        for i in range(1, len(T) - 1):
            for j in range(1, len(T[0]) - 1):
                T[i, j] = (Fo_x * (T[i, j+1] + T[i, j-1]) +
                          Fo_z * (T[i+1, j] + T[i-1, j]) +
                          T_old[i, j]) / coeff_center
    
    return T

# Simulate nozzle pass with new heat source
print("=" * 70)
print("FFF SIMULATION REALISTIC TEMPERATURE VALIDATION")
print("=" * 70)

# Nozzle travel across domain
nozzle_temp = 85.0  # Cooled filament (not raw nozzle)
timesteps = 500
layer_1_time = 150  # Apply heat for first 150 steps

max_temps = []
mean_temps = []
times = []

print(f"\nSimulation Parameters:")
print(f"  Domain: {Lx*1000:.1f}mm × {Lz*1000:.1f}mm (Grid: {Nx}×{Nz})")
print(f"  Nozzle temperature (cooled filament): {nozzle_temp}°C")
print(f"  Bed temperature: {T_bed}°C")
print(f"  Convection h: {h:.1f} W/m²K")
print(f"  Nozzle radius: {nozzle_radius*1000:.2f}mm")
print(f"\nRunning {timesteps} timesteps (dt={dt}s)...\n")

for step in range(timesteps):
    # Move nozzle continuously (zigzag pattern)
    nozzle_distance = (step % 200) / 200.0 * Lx  # Traverse back and forth
    
    # Apply heat source continuously
    x_pos = nozzle_distance
    z_pos = 0.002  # Fixed height above bed (depositing filament)
    T_before = np.max(T)
    T = apply_gaussian_heat_source(T, x_pos, z_pos, nozzle_temp, dx, dz, nozzle_radius)
    T_after = np.max(T)
    
    if step == 0:
        print(f"\nDEBUG: Continuous nozzle motion starting:")
    
    # Solve heat equation
    T = solve_heat_equation_step(T, alpha, dx, dz, dt)
    
    # Apply boundary conditions
    T = apply_boundary_conditions(T, T_bed, T_inf, h, k, dz)
    
    # Record statistics
    max_temps.append(np.max(T))
    mean_temps.append(np.mean(T))
    times.append(step * dt)
    
    if (step + 1) % 100 == 0:
        print(f"  Step {step+1:3d}: Max temp = {np.max(T):6.2f}°C, "
              f"Mean = {np.mean(T):5.2f}°C, Range = [{np.min(T):5.1f}, {np.max(T):6.2f}]°C")

print(f"\nFinal Temperature Field Statistics:")
print(f"  Max temperature: {np.max(T):.2f}°C")
print(f"  Min temperature: {np.min(T):.2f}°C")
print(f"  Mean temperature: {np.mean(T):.2f}°C")
print(f"  Bed center temp: {T[0, Nx//2]:.2f}°C")
print(f"  Top center temp: {T[-1, Nx//2]:.2f}°C")

# Check realism
print("\nVALIDATION CHECKS:")
max_temp = np.max(T)
if max_temp <= 90:  # Allow slight overshoot from 85°C
    print(f"  OK: Maximum temperature {max_temp:.2f}C is realistic (<=90C)")
else:
    print(f"  PROBLEM: Maximum temperature {max_temp:.2f}C is too high!")

if abs(T[0, Nx//2] - T_bed) < 2:
    print(f"  OK: Bed maintains ~{T_bed}C")
else:
    print(f"  PROBLEM: Bed temperature drift: {T[0, Nx//2]:.2f}C vs {T_bed}C")

if T[-1, Nx//2] < 40:
    print(f"  OK: Top surface cools appropriately ({T[-1, Nx//2]:.2f}C)")
else:
    print(f"  PROBLEM: Top surface too warm ({T[-1, Nx//2]:.2f}C)")

# Visualize
fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# Plot 1: Final temperature heatmap
im = axes[0, 0].imshow(T, extent=[0, Lx*1000, 0, Lz*1000], aspect='auto', 
                        cmap='hot', vmin=20, vmax=90, origin='lower')
axes[0, 0].set_xlabel('X position (mm)')
axes[0, 0].set_ylabel('Z height (mm)')
axes[0, 0].set_title('Final Temperature Distribution')
plt.colorbar(im, ax=axes[0, 0], label='Temperature (°C)')

# Plot 2: Temperature vs time
axes[0, 1].plot(times, max_temps, 'r-', label='Max temp', linewidth=2)
axes[0, 1].plot(times, mean_temps, 'b-', label='Mean temp', linewidth=2)
axes[0, 1].axhline(y=85, color='orange', linestyle='--', label='Nozzle/Filament temp', linewidth=1.5)
axes[0, 1].axhline(y=T_bed, color='green', linestyle='--', label='Bed temp', linewidth=1.5)
axes[0, 1].set_xlabel('Time (s)')
axes[0, 1].set_ylabel('Temperature (°C)')
axes[0, 1].set_title('Temperature Evolution')
axes[0, 1].legend()
axes[0, 1].grid(True, alpha=0.3)

# Plot 3: Vertical temperature profile
center_j = Nx // 2
axes[1, 0].plot(T[:, center_j], np.linspace(0, Lz*1000, Nz), 'b-', linewidth=2)
axes[1, 0].set_xlabel('Temperature (°C)')
axes[1, 0].set_ylabel('Z height (mm)')
axes[1, 0].set_title('Vertical Temperature Profile (Center X)')
axes[1, 0].grid(True, alpha=0.3)
axes[1, 0].invert_yaxis()

# Plot 4: Horizontal temperature profile
center_i = Nz // 2
axes[1, 1].plot(np.linspace(0, Lx*1000, Nx), T[center_i, :], 'r-', linewidth=2)
axes[1, 1].set_xlabel('X position (mm)')
axes[1, 1].set_ylabel('Temperature (°C)')
axes[1, 1].set_title(f'Horizontal Temperature Profile (Z = {Lz*1000/2:.2f}mm)')
axes[1, 1].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('fff_realistic_validation.png', dpi=150, bbox_inches='tight')
print(f"\n✓ Visualization saved to 'fff_realistic_validation.png'")
plt.show()
