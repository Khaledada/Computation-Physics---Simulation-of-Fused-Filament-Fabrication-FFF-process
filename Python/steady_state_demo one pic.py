import numpy as np
import matplotlib.pyplot as plt
import time

def run_simulation(Nx=100, Nz=20, bed_temp=60.0, ambient_temp=20.0,
                   Lx=0.1, Lz=0.02, alpha=1e-5, max_time=2000.0,
                   tol=1e-6, record_dt=1.0):
    dx = Lx / (Nx - 1)
    dz = Lz / (Nz - 1)
    dx2 = dx * dx
    dz2 = dz * dz

    # Stability for explicit 2D: dt <= 0.25 * min(dx2,dz2) / alpha
    dt_stable = 0.25 * min(dx2, dz2) / alpha
    dt = min(dt_stable, 0.1)

    T = np.ones((Nz, Nx)) * ambient_temp
    # fix bottom row (bed) to bed_temp (z = bottom)
    T[-1, :] = bed_temp
    # fix left/right/top to ambient for simplicity
    T[0, :] = ambient_temp
    T[:, 0] = ambient_temp
    T[:, -1] = ambient_temp

    # choose probe location: center interior
    ix = Nx // 2
    iz_center = Nz // 2

    times = []
    temps_center = []

    t = 0.0
    next_record = 0.0
    last_max_change = np.inf
    steady_t = None

    it = 0
    start_time = time.time()
    while t < max_time:
        Tn = T.copy()

        # update interior points (simple explicit scheme)
        for j in range(1, Nz - 1):
            for i in range(1, Nx - 1):
                d2Tdx2 = (Tn[j, i+1] - 2*Tn[j, i] + Tn[j, i-1]) / dx2
                d2Tdz2 = (Tn[j+1, i] - 2*Tn[j, i] + Tn[j-1, i]) / dz2
                T[j, i] = Tn[j, i] + alpha * dt * (d2Tdx2 + d2Tdz2)

        # re-apply Dirichlet BCs
        T[-1, :] = bed_temp
        T[0, :] = ambient_temp
        T[:, 0] = ambient_temp
        T[:, -1] = ambient_temp

        max_change = np.max(np.abs(T - Tn))

        if t >= next_record - 1e-12:
            times.append(t)
            temps_center.append(T[iz_center, ix])
            next_record += record_dt

        if max_change < tol:
            # steady state reached
            steady_t = t
            break

        t += dt
        it += 1

    elapsed = time.time() - start_time
    print(f"Simulated to t={t:.3f}s in {it} steps ({elapsed:.2f}s wall time). max_change={max_change:.3e}")

    return np.array(times), np.array(temps_center), T, steady_t


def plot_results(times, temps_center, steady_t=None, out_png='temp_vs_time.png'):
    plt.figure(figsize=(8,4))
    plt.plot(times, temps_center, label='Interior center')
    plt.xlabel('Time (s)')
    plt.ylabel('Temperature (°C)')
    plt.title('Temperature vs Time (interior center)')
    plt.grid(True)
    plt.legend()
    # annotate steady-state time if available
    if steady_t is not None and len(times) > 0:
        # find nearest recorded time index
        idx = int(np.argmin(np.abs(times - steady_t)))
        y_annot = temps_center[idx]
        plt.axvline(steady_t, color='k', linestyle='--', linewidth=1)
        plt.annotate(f'Steady state ≈ {steady_t:.2f}s', xy=(steady_t, y_annot),
                     xytext=(steady_t + 0.05 * (times[-1] - times[0]), y_annot + 0.05 * (temps_center.max() - temps_center.min())),
                     arrowprops=dict(arrowstyle='->', lw=0.8))
    plt.tight_layout()
    plt.savefig(out_png, dpi=150)
    print(f"Saved plot to {out_png}")


def main():
    Nx = 100
    Nz = 20
    bed_temp = 60.0

    times, tc, Tfinal, steady_t = run_simulation(Nx=Nx, Nz=Nz, bed_temp=bed_temp,
                                           ambient_temp=20.0, alpha=1e-5,
                                           max_time=20000.0, tol=1e-7,
                                           record_dt=1.0)

    plot_results(times, tc, steady_t=steady_t)

    # quick check: derivative near end should be ~0
    if len(times) >= 3:
        dt = times[1] - times[0]
        deriv = np.gradient(tc, dt)
        print(f"Last temperature (center): {tc[-1]:.4f} °C; last dT/dt ~ {deriv[-1]:.3e} °C/s")


if __name__ == '__main__':
    main()
