# CRASHSENSE AI - Statistical Methodology Specification

## 1. Scientific Principles & Memoryless Property
Independent Provably Fair crash games employ SHA-256 seed commitments generated via cryptographically secure pseudorandom number generators (CSPRNG). 

### Methodological Safeguards:
1. **Zero Extrapolation**: Empirical relative frequencies $\hat{p} = \frac{k}{n}$ describe sample observations only. They are never labeled as next-round certainties.
2. **Multiple Hypothesis Testing Correction**: Serial autocorrelation evaluation incorporates Ljung-Box portmanteau tests across multiple lags with Bonferroni-adjusted thresholds where appropriate.
3. **Small Sample Guardrail**: Datasets with $N < 30$ rounds are tagged with sample size warnings and conservative non-parametric confidence bands.

---

## 2. Statistical Formulations

### Empirical Sample Moments
- Sample Mean: $\bar{x} = \frac{1}{n} \sum_{i=1}^n x_i$
- Sample Variance: $s^2 = \frac{1}{n-1} \sum_{i=1}^n (x_i - \bar{x})^2$
- Skewness: Fisher-Pearson coefficient $g_1 = \frac{m_3}{s^3}$
- Kurtosis: Fisher excess kurtosis $g_2 = \frac{m_4}{s^4} - 3$

### Autocorrelation & Ljung-Box Test
For lag $k$:
$$r_k = \frac{\sum_{t=1}^{n-k} (x_t - \bar{x})(x_{t+k} - \bar{x})}{\sum_{t=1}^n (x_t - \bar{x})^2}$$

Portmanteau Ljung-Box statistic:
$$Q = n(n+2) \sum_{k=1}^h \frac{r_k^2}{n-k} \sim \chi^2(h)$$
- **Null Hypothesis ($H_0$)**: The sequence exhibits zero serial autocorrelation (IID randomness).
- **Alternative ($H_1$)**: Significant serial dependence exists.

---

## 3. Wilson Score Confidence Interval
For observed category frequency $\hat{p} = \frac{k}{n}$:
$$CI = \frac{\hat{p} + \frac{z^2}{2n} \pm z \sqrt{\frac{\hat{p}(1-\hat{p})}{n} + \frac{z^2}{4n^2}}}{1 + \frac{z^2}{n}}$$
Where $z = 1.95996$ for 95% confidence.

