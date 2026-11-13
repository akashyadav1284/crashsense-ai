# CRASHSENSE AI - Independence Testing & Drift Detection

## 1. Serial Independence Testing
- **Ljung-Box Test**: Tests cumulative lag autocorrelation up to lag $h$.
- **Wald-Wolfowitz Runs Test**: Evaluates whether runs of above/below median outcomes conform to a memoryless Bernoulli sequence.

---

## 2. Distribution Drift Detection
To verify whether an operator's multiplier distribution shifts chronologically:
1. **Two-Sample Kolmogorov-Smirnov Test**:
   $$D = \sup_x |F_1(x) - F_2(x)|$$
   Computes exact asymptotic $p$-value comparing baseline and recent windows.
2. **Population Stability Index (PSI)**:
   $$PSI = \sum_{b=1}^B (T_b - B_b) \cdot \ln\left(\frac{T_b}{B_b}\right)$$
   - $PSI < 0.10$: No distribution drift.
   - $0.10 \le PSI < 0.25$: Moderate drift.
   - $PSI \ge 0.25$: Significant distribution shift.

