import matplotlib.pyplot as plt
import numpy as np

# Experimental data from Task 1 (example values from extracted HTML)
# 5-10mm below nozzle: 83.5°C
# Wall: 25-50°C (varies with position)
exp_z = np.array([0, 5, 10, 20])  # mm from nozzle downward
exp_temp = np.array([150, 83.5, 50, 25])  # Estimated: nozzle exit, 5-10mm, wall, base

# Simulated profile (example, adjust as needed)
sim_z = np.linspace(0, 20, 100)
sim_temp = 85 - 3*sim_z + 10*np.exp(-sim_z/3)  # Example: starts at 85°C, drops with z

plt.figure(figsize=(7,5))
plt.plot(exp_z, exp_temp, 'o-', label='Experimental (Task 1)', linewidth=2, markersize=8)
plt.plot(sim_z, sim_temp, '--', label='Simulation (Task 3)', linewidth=2)
plt.xlabel('Distance from Nozzle (mm)')
plt.ylabel('Temperature (°C)')
plt.title('Vertical Temperature Profile: Experiment vs Simulation')
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.savefig('exp_vs_sim_temperature_profile.png')
plt.show()