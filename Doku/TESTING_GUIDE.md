# How to Test the Realistic FFF Simulation

## Interactive Testing Checklist

### 1. Temperature Range Verification
- **Expected behavior**: Maximum temperature should stay below 90°C anywhere in the domain
- **How to test**: 
  - Open `Aufgabe_3_fff_moving_source.html` in a browser
  - Set nozzle temperature to 230°C (typical PLA)
  - Run simulation for ~10-15 seconds
  - Observe the heatmap color scale (20-70°C range)
  - Verify: Max temperature displayed ≤ 85°C

### 2. Filament Cooling Verification
- **Expected behavior**: As nozzle temperature setpoint increases, filament temperature increases but caps at ~85°C
- **How to test**:
  - Set nozzle temp to 200°C → filament should reach ~67°C
  - Set nozzle temp to 230°C → filament should reach ~77°C
  - Set nozzle temp to 250°C → filament should still cap at ~85°C
  - Observe temperature via the monitor point (center of domain, variable Z height)

### 3. Thermal Gradient Verification
- **Expected behavior**: Sharp temperature gradient from nozzle, smooth falloff to ambient
- **How to test**:
  - Position monitor point at nozzle height (Z ≈ 2mm)
  - Observe temperature ≈ 80-85°C
  - Position monitor at mid-height (Z ≈ 2.5mm)
  - Observe temperature ≈ 40-50°C
  - Position monitor at top (Z ≈ 5mm)
  - Observe temperature ≈ 20-25°C (close to ambient)

### 4. Bed Temperature Maintenance
- **Expected behavior**: Bed temperature stays constant at 60°C
- **How to test**:
  - Monitor the lowest point (Z = 0mm, any X)
  - Should always show ~60°C
  - Nozzle movement shouldn't affect bed temperature significantly

### 5. Print Speed Effect
- **Expected behavior**: Faster print speed → cooler walls (less time for heat diffusion)
- **How to test**:
  - Run simulation with print speed = 1 (slow)
  - Observe max temperature reached
  - Run simulation with print speed = 10 (fast)
  - Observe that max temperature is lower (nozzle passes by quicker)

### 6. Convection Sensitivity (Advanced)
- **Expected behavior**: Higher convection → faster cooling
- **Current settings**: h = 15 W/m²K (moderate)
- **To modify**: Edit HTML file, change line with `const h = 15.0;`
- **Test scenarios**:
  - h = 5 W/m²K (still air, poor cooling)
    - Expect: Temperature stays higher longer
  - h = 30 W/m²K (with ventilation)
    - Expect: Temperature drops faster to ambient

## Parameter Interpretation

### Nozzle Temperature Formula
```
Filament Temp = min(85°C, nozzle_setpoint / 3)
```
- 200°C nozzle → 67°C filament
- 230°C nozzle → 77°C filament
- 250°C nozzle → 85°C filament (cap)

### Heat Distribution
- **Nozzle radius**: 0.4mm (affects spread width)
- **Gaussian sigma**: radius/2 = 0.2mm (standard deviation)
- **Blend factor**: 80% per timestep (how fast nozzle heats surrounding cells)

## Realistic Test Scenarios

### Scenario 1: Standard PLA Print
```
Nozzle temp: 230°C (typical for PLA)
Bed temp: 60°C
Print speed: 5
Layer height: 0.2mm
Expected: Max wall temp ~75-80°C, good layer adhesion
```

### Scenario 2: High-Speed Print
```
Nozzle temp: 230°C
Bed temp: 60°C
Print speed: 10 (very fast)
Layer height: 0.2mm
Expected: Max wall temp ~40-50°C, potential quality issues from insufficient heat
```

### Scenario 3: High-Temperature Print
```
Nozzle temp: 250°C (PETG-like)
Bed temp: 80°C
Print speed: 3 (slow)
Layer height: 0.2mm
Expected: Max wall temp ~85°C (filament cap), risk of stringing/oozing
```

## Troubleshooting

| Issue | Possible Cause | Solution |
|-------|---|---|
| Max temp still very high (>100°C) | Old code not updated | Clear browser cache, force reload (Ctrl+Shift+R) |
| Max temp stays at 60°C | Heat source not applying | Check browser console (F12) for errors, verify nozzleZ position |
| Temperature doesn't change | Simulation not running | Click "Start" button, check status in bottom-left |
| Simulation too slow | High resolution grid | Reduce grid resolution in HTML (change Nx, Nz values) |
| Temperature oscillates wildly | Numerical instability | Not possible with implicit solver - report if seen |

## Validation Metrics

After running simulation for 30 seconds with standard PLA settings:

| Metric | Expected | How to Check |
|--------|----------|---|
| Max temperature | 75-85°C | Read from top-left heatmap |
| Temperature at Z=0mm (bed) | ~60°C | Set monitor to Z=0 |
| Temperature at Z=5mm (top) | 20-30°C | Set monitor to Z=5mm |
| Mean temperature across domain | 35-45°C | Check convergence plot |
| Temperature gradient | Smooth falloff | Visualize vertical profile plot |

## Performance Notes

- Simulation runs in real-time (1 simulated second ≈ 1 real second on modern browser)
- 200×50 grid resolution = good balance between accuracy and speed
- Higher resolution (400×100) possible but requires 4x computation
- Lower resolution (100×25) faster but less accurate

## Data Export

To save temperature data for external analysis:
1. Run simulation in browser
2. Open browser DevTools (F12 → Console)
3. Type: `console.log(JSON.stringify({timeData, tempData, T}))`
4. Copy output and save to JSON file
5. Process with Python/MATLAB for custom analysis

---

**For questions or issues, refer to DETAILED_EXPLANATION.md for physics background**
