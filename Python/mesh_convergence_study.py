import numpy as np
import time
import pandas as pd

def run_simulation(Nx=100, Nz=10, bed_temp=60.0, ambient_temp=20.0,
                   Lx=0.05, Lz=0.005, alpha=1.37e-7, max_time=200.0,
                   tol=1e-6):
    """Run heat diffusion simulation and return steady-state metrics"""
    
    dx = Lx / (Nx - 1)
    dz = Lz / (Nz - 1)
    dx2 = dx * dx
    dz2 = dz * dz

    # Stability criterion for explicit scheme: dt <= 0.25 * min(dx2,dz2) / alpha
    dt_stable = 0.25 * min(dx2, dz2) / alpha
    dt = min(dt_stable, 0.001)

    T = np.ones((Nz, Nx)) * ambient_temp
    T[-1, :] = bed_temp  # bottom (bed) at 60°C
    T[0, :] = ambient_temp  # top at ambient
    T[:, 0] = ambient_temp  # sides
    T[:, -1] = ambient_temp

    # Monitor point at center horizontally, middle vertically
    ix = Nx // 2
    iz = Nz // 2

    times = []
    temps = []
    t = 0.0
    it = 0
    steady_t = None
    
    start_wall = time.time()
    
    while t < max_time:
        Tn = T.copy()

        # Explicit finite difference update
        for j in range(1, Nz - 1):
            for i in range(1, Nx - 1):
                d2Tdx2 = (Tn[j, i+1] - 2*Tn[j, i] + Tn[j, i-1]) / dx2
                d2Tdz2 = (Tn[j+1, i] - 2*Tn[j, i] + Tn[j-1, i]) / dz2
                T[j, i] = Tn[j, i] + alpha * dt * (d2Tdx2 + d2Tdz2)

        # Reapply BCs
        T[-1, :] = bed_temp
        T[0, :] = ambient_temp
        T[:, 0] = ambient_temp
        T[:, -1] = ambient_temp

        max_change = np.max(np.abs(T - Tn))

        # Record data every 1.0s
        if len(times) == 0 or t - times[-1] >= 1.0:
            times.append(t)
            temps.append(T[iz, ix])

        # Check for steady state
        if max_change < tol:
            steady_t = t
            break

        t += dt
        it += 1

    elapsed = time.time() - start_wall
    
    # Calculate temperature gradient at steady state
    gradient = (T[-1, ix] - T[0, ix]) / (Lz * 1000)  # °C/mm
    
    # Check convergence (small change in last step)
    converged = max_change < tol
    
    return {
        'Mesh Size': f'{Nx}×{Nz}',
        'Grid Points': Nx * Nz,
        'Steady Time (s)': round(steady_t, 1) if steady_t else '>200',
        'Gradient (°C/mm)': round(abs(gradient), 1),
        'Max Change': f'{max_change:.3e}',
        'Wall Time (s)': round(elapsed, 2),
        'Converged': '✅' if converged else '⚠️' if steady_t else '❌'
    }


def main():
    print("=" * 100)
    print("MESH CONVERGENCE ANALYSIS".center(100))
    print("=" * 100)
    print()
    
    # Define mesh sizes to test
    mesh_sizes = [
        (100, 10),
        (200, 20),
        (400, 40),
        (500, 50),
    ]
    
    results = []
    
    for Nx, Nz in mesh_sizes:
        print(f"Running simulation: Nx={Nx}, Nz={Nz} ({Nx*Nz:,} grid points)...", end=' ', flush=True)
        
        result = run_simulation(Nx=Nx, Nz=Nz, bed_temp=60.0, ambient_temp=20.0,
                               Lx=0.05, Lz=0.005, alpha=1.37e-7, 
                               max_time=500.0, tol=1e-6)
        results.append(result)
        
        print(f"✅ Steady State: {result['Steady Time (s)']}s | Gradient: {result['Gradient (°C/mm)']}°C/mm | {result['Converged']}")
    
    print()
    print("=" * 100)
    print("SUMMARY TABLE".center(100))
    print("=" * 100)
    
    df = pd.DataFrame(results)
    print()
    print(df.to_string(index=False))
    print()
    
    # Analysis
    print("=" * 100)
    print("CONVERGENCE ANALYSIS".center(100))
    print("=" * 100)
    print()
    
    steady_times = []
    gradients = []
    grid_points = []
    
    for r in results:
        if isinstance(r['Steady Time (s)'], (int, float)):
            steady_times.append(r['Steady Time (s)'])
        grid_points.append(r['Grid Points'])
        gradients.append(r['Gradient (°C/mm)'])
    
    if len(steady_times) > 1:
        print(f"Steady State Time Change:")
        print(f"  100×10 → 200×20: {((steady_times[1]-steady_times[0])/steady_times[0]*100):+.1f}%")
        print(f"  200×20 → 400×40: {((steady_times[2]-steady_times[1])/steady_times[1]*100):+.1f}%")
        print(f"  400×40 → 500×50: {((steady_times[3]-steady_times[2])/steady_times[2]*100):+.1f}%")
    
    print()
    print(f"Temperature Gradient Change:")
    print(f"  100×10 → 200×20: {((gradients[1]-gradients[0])/gradients[0]*100):+.1f}%")
    print(f"  200×20 → 400×40: {((gradients[2]-gradients[1])/gradients[1]*100):+.1f}%")
    print(f"  400×40 → 500×50: {((gradients[3]-gradients[2])/gradients[2]*100):+.1f}%")
    
    print()
    print("CONVERGENCE CRITERION:")
    print("  • Converged (✅): max_change < 1e-6, steady state reached")
    print("  • Questionable (⚠️): steady state reached but late in simulation")
    print("  • Not Converged (❌): did not reach tolerance before max_time")
    
    print()
    print("MESH SENSITIVITY CONCLUSION:")
    if abs(gradients[-1] - gradients[-2]) / gradients[-2] < 0.01:
        print("  ✅ Solution is MESH-INDEPENDENT (< 1% change)")
        print(f"  → Recommended mesh: 400×40 or 500×50")
    elif abs(gradients[-1] - gradients[-2]) / gradients[-2] < 0.05:
        print("  ✅ Solution is NEARLY MESH-INDEPENDENT (< 5% change)")
        print(f"  → Recommended mesh: 400×40")
    else:
        print("  ⚠️ Solution is MESH-DEPENDENT (> 5% change)")
        print(f"  → Use finer mesh")
    
    print()
    print("=" * 100)


if __name__ == '__main__':
    main()
