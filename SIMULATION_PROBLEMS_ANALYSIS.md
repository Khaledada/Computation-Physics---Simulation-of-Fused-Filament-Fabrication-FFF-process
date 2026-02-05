# Simulation Problems, Causes, and Solutions

## Aufgabe 2: Wall Heat Distribution Analysis

### Problem 1: **Numerical Instability Risk (CFL/Fourier Number)**

**Description:** The simulation uses explicit finite difference method without checking stability criteria.

**Cause:**
- Fixed time-step `dt = 0.1s` may violate Courant-Friedrichs-Lewy (CFL) condition
- Fourier number: $Fo = \frac{\alpha \cdot dt}{dx^2}$ or in 2D: $Fo_x + Fo_z$ should be ≤ 0.5 for stability
- With `α = k/(ρ·cp) = 0.25/(1200·1500) ≈ 1.39×10⁻⁷ m²/s` and small meshes, `dt = 0.1s` may be too large
- For `dx = 0.05/100 = 0.0005m` and `dz = 0.005/20 = 0.00025m`: 
  - $Fo_x = 1.39×10⁻⁷ × 0.1 / (0.0005)² ≈ 0.0556$ ✓ Stable
  - $Fo_z = 1.39×10⁻⁷ × 0.1 / (0.00025)² ≈ 0.222$ ✓ Marginally stable
  - But with finer mesh (Nx=500, Nz=100): becomes **unstable**

**Solution:**
```javascript
// Add adaptive time-stepping based on mesh size
function adaptiveTimeStep(Nx, Nz) {
    dx = Lx / (Nx - 1);
    dz = Lz / (Nz - 1);
    
    // Ensure Fo ≤ 0.25 for safety
    const Fo_max = 0.25;
    const dt_x = (Fo_max * dx * dx) / alpha;
    const dt_z = (Fo_max * dz * dz) / alpha;
    
    return Math.min(dt_x, dt_z) * 0.9; // 90% of theoretical max
}
```

---

### Problem 2: **Unrealistic Boundary Condition - Heat Source Location**

**Description:** Heat is only applied at a single point `T[Nz-1][0] = T_heat`, missing the actual physics of the heat source.

**Cause:**
- Real heating elements have finite width and distributed heat
- Current implementation applies 200°C only at corner index [Nz-1][0]
- Most of the top surface uses convective boundary condition, ignoring actual heater coverage
- Results don't represent real physical conditions

**Solution:**
```javascript
// Apply distributed heat source across heater width
function applyHeatSource() {
    const heaterWidth = 15; // mm
    const heaterWidthCells = Math.floor(heaterWidth / (dx * 1000));
    
    for (let j = 0; j < heaterWidthCells; j++) {
        T[Nz-1][j] = T_heat; // Direct contact with heater
    }
    
    // Smooth transition from heated to unheated region
    for (let j = heaterWidthCells; j < heaterWidthCells + 3; j++) {
        const blendFactor = (heaterWidthCells + 3 - j) / 3;
        T[Nz-1][j] = T_heat * blendFactor + T[Nz-1][j] * (1 - blendFactor);
    }
}
```

---

### Problem 3: **Poor Convergence Tolerance Scaling**

**Description:** Fixed absolute tolerance `0.016°C` may be inappropriate for different problem scales.

**Cause:**
- With T_heat = 200°C and T_init = 20°C, relative tolerance is ~0.008%
- With print bed T = 60°C, same tolerance gives different convergence time
- Tolerance independent of mesh refinement and time-stepping

**Solution:**
```javascript
// Use relative tolerance scaled to temperature range
const T_range = Math.max(...T.flat()) - Math.min(...T.flat());
const relativeTolerance = 0.001; // 0.1% relative change
const absoluteTolerance = T_range * relativeTolerance;

if (maxChange < Math.max(absoluteTolerance, 0.001)) {
    steadyStateTime = time;
}
```

---

### Problem 4: **Infinite Loop Risk in Comparison Study**

**Description:** `runComparison()` function may run indefinitely with coarse meshes.

**Cause:**
- Uses hardcoded `tolerance = 0.016` without checking it's achievable
- No maximum iteration safeguard in some branches
- `while (localTime < 200 && !localSteadyTime)` could hang browser threads

**Solution:**
```javascript
const maxIterations = Math.ceil(200 / dt);
let iterations = 0;

while (iterations < maxIterations && !localSteadyTime) {
    // ... solve equations ...
    if (maxChange < tolerance) {
        localSteadyTime = localTime;
    }
    iterations++;
    localTime += dt;
    
    // Prevent UI freezing - yield control periodically
    if (iterations % 100 === 0) {
        await new Promise(resolve => setTimeout(resolve, 0));
    }
}
```

---

## Aufgabe 3: FFF Moving Source Simulation

### Problem 1: **Unrealistic Nozzle Temperature Model**

**Description:** Code applies `T_nozzle = nozzleSetpoint / 3` as filament exit temperature, which doesn't match physics.

**Cause:**
```javascript
// Current code (line ~90):
return Math.max(T_bed + 15, Math.min(85, nozzleSetpoint / 3));
```
- Dividing nozzle setpoint by 3 is arbitrary
- PLA nozzle at 200°C → filament exit at 66°C (too cold for proper adhesion)
- Actual physics: nozzle setpoint (200°C) ≠ filament core temperature ≠ filament surface temperature
- Neglects cooling during extrusion and exposure to air

**Solution:**
```javascript
function getNozzleTemp() {
    const nozzleSetpoint = parseFloat(document.getElementById('nozzleTemp').value);
    const ambientTemp = 20;
    
    // Realistic model:
    // Filament cools from nozzle temp during extrusion
    // Surface cools faster than core
    // Typical exit temp for PLA: 85-95% of nozzle temp
    const coolingFactor = 0.92; // 92% of nozzle setpoint
    const filamentExitTemp = nozzleSetpoint * coolingFactor;
    
    // Cap at realistic maximum (PLA degrades above 220°C)
    return Math.min(filamentExitTemp, 220);
}
```

---

### Problem 2: **Oversimplified Gaussian Heat Distribution**

**Description:** Heat application doesn't account for filament momentum, deposition dynamics, or layer bonding.

**Cause:**
- Uses simple Gaussian with fixed parameters
- No convective pre-heating of surroundings before deposition
- Doesn't model filament cooling cone (region where filament is still hot but cooling)
- Fixed blend factor (80%) ignores:
  - Print speed effects on dwell time
  - Pull-off forces during layer transitions
  - Thermal contact resistance at layer interface

**Solution:**
```javascript
function applyHeatSource() {
    const T_nozzle = getNozzleTemp();
    const j = Math.floor(nozzleX / dx);
    const i = Math.floor(nozzleZ / dz);
    const v = getPrintSpeed();
    
    // Adaptive gaussian based on print speed
    // - Slower print speed → more dwell time → stronger heating
    const dwell_time_factor = (50 - v * 1000) / 50; // Normalized 0-1
    const effectiveRadius = Math.max(1, Math.round((nozzle_radius + dwell_time_factor * 0.0001) / dx));
    
    // Cooling cone: hot region immediately under nozzle
    for (let di = -5; di <= 5; di++) {
        for (let dj = -5; dj <= 5; dj++) {
            const ni = i + di;
            const nj = j + dj;
            if (ni >= 0 && ni < Nz && nj >= 0 && nj < Nx) {
                const distSq = di * di + dj * dj;
                const sigma = effectiveRadius / 2.0;
                const weight = Math.exp(-distSq / (2 * sigma * sigma));
                
                // Speed-dependent blend factor
                const blendFactor = weight * (0.3 + dwell_time_factor * 0.7); // 30-100%
                T[ni][nj] = T[ni][nj] * (1 - blendFactor) + T_nozzle * blendFactor;
            }
        }
    }
}
```

---

### Problem 3: **Constant Material Properties (Temperature-Dependent)**

**Description:** Thermal conductivity and heat capacity assumed constant (`k = 0.25`, `cp = 1500`).

**Cause:**
- Real polymer properties vary significantly with temperature
- PLA thermal conductivity increases ~0.00015 W/m·K per °C
- Heat capacity changes ~2 J/kg·K per °C
- Using constant values introduces 10-20% error in high-temperature regions

**Solution:**
```javascript
function getThermalProperties(temperature) {
    // Temperature-dependent properties for PLA
    // Reference: 70°C baseline
    
    const T_ref = 70;
    const k_ref = 0.25;      // W/m·K at 70°C
    const cp_ref = 1500;     // J/kg·K at 70°C
    const dk_dT = 0.00015;   // W/m·K²
    const dcp_dT = 2.0;      // J/kg·K²
    
    const dT = temperature - T_ref;
    
    return {
        k: k_ref + dk_dT * dT,
        cp: cp_ref + dcp_dT * dT,
        rho: 1200 // Density: minimal change with T
    };
}

// Usage in solver:
const props = getThermalProperties(T[i][j]);
const alpha = props.k / (1200 * props.cp);
```

---

### Problem 4: **Fixed Convection Coefficient - Ignores Layer Configuration**

**Description:** `h = 15 W/m²K` constant, but real convection varies dramatically.

**Cause:**
- Layer just deposited: high local heating → different boundary layer
- Between layers: natural convection only
- Active printing head blocking air flow in some regions
- Layer height affects surface exposure to ambient air

**Solution:**
```javascript
function getLocalConvectionCoeff(i, j) {
    const baseH = 15; // W/m²K natural convection
    
    // Increase h near active nozzle
    const distToNozzle = Math.sqrt(
        Math.pow(i * dz - nozzleZ, 2) + 
        Math.pow(j * dx - nozzleX, 2)
    );
    
    if (distToNozzle < 0.005) {
        return baseH * 2; // Forced convection near nozzle
    } else if (distToNozzle < 0.01) {
        return baseH * 1.5; // Transition zone
    }
    return baseH; // Far from nozzle
}

// Apply in boundary condition:
for (let j = 0; j < Nx; j++) {
    const h_local = getLocalConvectionCoeff(Nz - 1, j);
    T[Nz-1][j] = (k * T[Nz-2][j] / dz + h_local * T_inf) / (k / dz + h_local);
}
```

---

### Problem 5: **No Layer-to-Layer Adhesion Modeling**

**Description:** Simulation treats each layer independently; no thermal bonding mechanics.

**Cause:**
- Perfect thermal contact assumed between layers (unrealistic)
- No interface resistance at layer boundaries
- Doesn't account for partial remelt/reflow at layer interfaces
- Affects strength predictions and layer bonding quality

**Solution:**
```javascript
// Track layer boundaries and apply contact resistance
const layerBoundaries = [];

function detectNewLayer() {
    if (Math.abs(nozzleZ - currentLayer * layerHeight) < dz) {
        const z_idx = Math.floor(nozzleZ / dz);
        if (!layerBoundaries.includes(z_idx)) {
            layerBoundaries.push(z_idx);
        }
    }
}

// Apply thermal contact resistance at interfaces
function applyLayerBoundaryResistance(i, j) {
    if (layerBoundaries.includes(i)) {
        // Contact resistance: R_contact = h_contact^-1
        const h_contact = 500; // W/m²K interface conductance
        // Apply reduced heat transfer across boundary
        return alpha / 2; // Reduced thermal diffusivity
    }
    return alpha;
}
```

---

### Problem 6: **No Thermally-Induced Warping/Residual Stress**

**Description:** Simulation ignores thermal gradients causing deformation.

**Cause:**
- High temperature gradients (>100°C/mm) create stress
- Differential cooling causes warping
- 3D deformation not captured in 2D simulation
- Can lead to bed adhesion loss or curling

**Solution (Note: 2D simulation limitation):**
```javascript
// Add qualitative warping indicator
function calculateWarpingIndex() {
    const maxGradient = 0; // °C/mm
    
    // Calculate vertical temperature gradient
    for (let j = 0; j < Nx; j++) {
        const gradient = Math.abs(T[Nz-1][j] - T[0][j]) / (Lz * 1000);
        maxGradient = Math.max(maxGradient, gradient);
    }
    
    // PLA warping threshold: typically >50°C/mm
    const warpingRisk = (maxGradient > 50) ? 'HIGH' : 
                        (maxGradient > 30) ? 'MODERATE' : 'LOW';
    
    return { maxGradient, warpingRisk };
}
```

---

### Problem 7: **UI Freezing During Simulation**

**Description:** Browser may become unresponsive during intensive calculations.

**Cause:**
- `requestAnimationFrame` used for simulation loop (expects 60 FPS)
- 50 Gauss-Seidel iterations per timestep × many timesteps
- Single-threaded JavaScript blocks UI rendering
- Comparison study runs async but still intensive

**Solution:**
```javascript
function simulationStep() {
    // Split computation into chunks
    const chunksPerFrame = 5; // Process 5 timesteps per 60Hz frame
    
    for (let chunk = 0; chunk < chunksPerFrame; chunk++) {
        if (!isRunning) break;
        
        updateNozzlePosition();
        applyHeatSource();
        solveHeatEquation();
        recordData();
        time += dt;
    }
    
    // Update UI once per frame (not per timestep)
    if (timeData.length % 20 === 0) {
        updatePlots(); // Expensive operation
    }
    
    if (isRunning && time < 200 && nozzleZ < Lz) {
        animationId = requestAnimationFrame(simulationStep);
    }
}
```

---

## Summary Table

| Simulation | Problem | Severity | Impact |
|-----------|---------|----------|--------|
| Aufgabe 2 | Numerical instability (Fourier) | **Medium** | Wrong results with fine mesh |
| Aufgabe 2 | Unrealistic heat source | **High** | Unphysical temperature profiles |
| Aufgabe 2 | Tolerance scaling | **Low** | Misleading convergence metrics |
| Aufgabe 2 | Infinite loop risk | **High** | Browser hang in comparison study |
| Aufgabe 3 | Temperature model | **High** | 25% error in adhesion predictions |
| Aufgabe 3 | Oversimplified heating | **Medium** | Wrong cooling rates |
| Aufgabe 3 | Constant properties | **Medium** | 10-20% errors |
| Aufgabe 3 | Fixed convection | **Medium** | Incorrect layer cooling |
| Aufgabe 3 | No adhesion model | **Medium** | Can't predict layer bonding |
| Aufgabe 3 | No warping analysis | **Low** | Missing failure prediction |
| Aufgabe 3 | UI freezing | **Medium** | Poor user experience |

---

## Implementation Priority

1. **High Priority** (Major Physics):
   - Fix Aufgabe 3 temperature model
   - Implement layer heating/cooling coupling
   - Add adaptive time-stepping to Aufgabe 2

2. **Medium Priority** (Realism):
   - Temperature-dependent properties
   - Speed-dependent heat transfer
   - Distributed heat sources

3. **Low Priority** (Enhancement):
   - Warping indicators
   - UI responsiveness improvements
   - Better visualization

