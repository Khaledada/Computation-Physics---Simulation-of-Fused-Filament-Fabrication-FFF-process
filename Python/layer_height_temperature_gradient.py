import matplotlib.pyplot as plt
import numpy as np

# Simulated temperature profiles for two different layer heights
x = np.linspace(0, 1, 100)  # normalized height through the layer

# Example: Thicker layer (gentler gradient)
t_thick = 220 - 40 * x  # e.g., 220°C at top, 180°C at bottom

# Example: Thinner layer (steeper gradient)
t_thin = 220 - 80 * x  # e.g., 220°C at top, 140°C at bottom

plt.figure(figsize=(6, 4))
plt.plot(x, t_thick, label='Thicker Layer Height', linewidth=2)
plt.plot(x, t_thin, label='Thinner Layer Height', linewidth=2, linestyle='--')
plt.xlabel('Normalized Layer Height')
plt.ylabel('Temperature (°C)')
plt.title('Temperature Gradient vs. Layer Height in FFF')
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.savefig('layer_height_temperature_gradient.png')
plt.show()