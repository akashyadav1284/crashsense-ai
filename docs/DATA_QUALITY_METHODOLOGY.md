# CRASHSENSE AI - Data Quality Methodology

## 1. Quality Scoring Formulation
Every dataset import generates a `DatasetValidationReport` with an objective Quality Score ($Q \in [0.0, 100.0]$):

$$Q = \max\left(0, 100 - \left( 60 \cdot \frac{N_{\text{invalid}}}{N_{\text{total}}} + 30 \cdot \frac{N_{\text{conflict}}}{N_{\text{total}}} + 10 \cdot \frac{N_{\text{dup}}}{N_{\text{total}} + N_{\text{dup}}} + 10 \cdot \frac{N_{\text{unverified}}}{N_{\text{total}}} \right)\right)$$

### Quality Grade Categorization
- **Grade A (EXCELLENT)**: $Q \ge 90.0\%$ (Cryptographically verified hashes, zero schema anomalies).
- **Grade B (ACCEPTABLE)**: $75.0\% \le Q < 90.0\%$ (Minor unverified records, zero non-positive values).
- **Grade C (DEGRADED)**: $50.0\% \le Q < 75.0\%$ (Significant duplicate frequency or missing metadata).
- **REJECTED**: $Q < 50.0\%$ (High failure rate, malformed numbers, unusable for modeling).
