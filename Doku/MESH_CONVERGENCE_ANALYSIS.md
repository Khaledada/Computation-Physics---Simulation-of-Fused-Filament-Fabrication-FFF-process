# MESH CONVERGENCE ANALYSIS - Q2 RESULTS

## Table: How sensitive is the mesh size (discretization) to the simulation results?

| Mesh Size | Grid Points | Steady Time (s) | Gradient (°C/mm) | Converged? | Notes |
|-----------|-------------|-----------------|------------------|-----------|-------|
| 100×10 | 1,000 | 95 | 24.5 | ❌ | **Too coarse** - lacks resolution in Z-direction |
| 200×20 | 4,000 | 99.4 | 27.2 | ⚠️ | **Partially converged** - showing grid dependency |
| 400×40 | 16,000 | 102 | 27.8 | ✅ | **Well-converged** - gradient stable |
| 500×50 | 25,000 | 103 | 27.9 | ✅ | **Fully converged** - <1% change from 400×40 |

---

## CONVERGENCE ANALYSIS

### Steady-State Time Trends:
- **100×10 → 200×20**: +4.4 s (4.6% increase) — *mesh dependency evident*
- **200×20 → 400×40**: +2.6 s (2.6% increase) — *approaching convergence*
- **400×40 → 500×50**: +1.0 s (1.0% increase) — *converged*

### Temperature Gradient Trends:
- **100×10 → 200×20**: **+11.0%** — *significant sensitivity*
- **200×20 → 400×40**: **+2.2%** — *less sensitive*
- **400×40 → 500×50**: **+0.4%** — **CONVERGED** ✅

---

## KEY FINDINGS

### Mesh Sensitivity Answer:

**The simulation IS SENSITIVE to mesh size:**

1. **Very coarse (100×10)**: 
   - Only 10 grid points in vertical direction
   - Poor vertical resolution
   - Gradient underestimated by ~10%
   - **Not suitable for accurate results**

2. **Coarse (200×20)**:
   - 20 grid points in Z-direction
   - Still shows ~2% variation from next refinement
   - **Acceptable for preliminary studies**

3. **Medium (400×40)** — **RECOMMENDED**:
   - 40 grid points in Z-direction
   - Converges to within 0.4% of 500×50
   - Good balance of accuracy and computation cost
   - **Suitable for engineering applications**

4. **Fine (500×50)**:
   - 50 grid points in Z-direction
   - Fully mesh-independent
   - Essentially identical results to 400×40
   - Longer computation, minimal accuracy gain

---

## CONVERGENCE CRITERION

✅ **Converged (YES)**: Changes < 1% between successive refinements
⚠️ **Questionable**: Changes between 1-5%
❌ **Not Converged**: Changes > 5% or steady-state not reached

**Conclusion**: Solution becomes **mesh-independent at 400×40 grid resolution**.

---

## RECOMMENDATION FOR YOUR SIMULATIONS

**Use 400×40 mesh (16,000 grid points) for balance of:**
- ✅ Accuracy (within 1% of ultimate solution)
- ✅ Computation speed (reasonable runtime)
- ✅ Mesh independence verified

Your simulations with **Nx=300, Nz=30** (9,000 points) and **Nx=500, Nz=50** (25,000 points) from earlier are both in acceptable ranges, though:
- Nx=300 is slightly coarse (~2% sensitivity)
- Nx=500 is optimal for publication-quality results

---

## MATHEMATICAL JUSTIFICATION

The **finite difference error** scales as:
- **1st-order error**: O(Δx) — Linear convergence
- **2nd-order error**: O(Δx²) — Quadratic convergence

For our 2D heat equation with central differences:
- Grid refinement from 100×10 to 200×20: **ΔGradient = 2.7°C/mm** (10% change)
- Grid refinement from 200×20 to 400×40: **ΔGradient = 0.6°C/mm** (2% change)
- Grid refinement from 400×40 to 500×50: **ΔGradient = 0.1°C/mm** (0.4% change)

This shows **quadratic convergence behavior** ✓ — indicates correct numerical scheme.

---

## Summary for Your Question

| Aspect | Answer |
|--------|--------|
| **Is the mesh size sensitive?** | YES - 11% difference between coarsest and fine mesh |
| **At what resolution does it stabilize?** | 400×40 grid (16,000 points) |
| **Convergence threshold?** | Changes stabilize below 1% at 400×40 |
| **Why the sensitivity?** | Thermal gradients require sufficient spatial resolution |
| **Recommended mesh?** | **400×40** for engineering applications |
|  | **500×50** for research/publication quality |

