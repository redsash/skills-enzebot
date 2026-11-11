# Multiple Testing Corrections and the Deflated Sharpe Ratio

In sports prediction and quantitative betting, data mining without multiple testing corrections is the primary cause of phantom edges.

---

## 1. The Backtest Graveyard Problem

When a researcher tests $N$ independent strategies, the expected maximum Sharpe ratio $\mathbb{E}[\max_{n} \widehat{\text{SR}}_n]$ from pure random noise grows with $\sqrt{2 \ln N}$:
$$\mathbb{E}[\max_{n} \widehat{\text{SR}}_n] \approx \sqrt{2 \ln N} + \frac{\gamma}{\sqrt{2 \ln N}}$$
where $\gamma \approx 0.5772$ is the Euler-Mascheroni constant.

If a researcher tests 100 variations of qualification rules, an observed Sharpe of 2.0 (or an observed ROI of 15%) is expected under pure noise.

---

## 2. The Deflated Sharpe Ratio (DSR)

Developed by David H. Bailey and Marcos López de Prado (2014), the **Deflated Sharpe Ratio (DSR)** computes the probability that an observed Sharpe ratio $\widehat{\text{SR}}$ exceeds zero after adjusting for:
1. The number of trials tested ($N$).
2. The variance of Sharpe ratios across those trials $\mathbb{V}[\{\widehat{\text{SR}}_n\}]$.
3. The sample length $T$ (number of bets/periods).
4. Non-normality: skewness ($\gamma_3$) and kurtosis ($\gamma_4$) of the return distribution.

$$\text{DSR} = \Phi\left( \frac{\widehat{\text{SR}} - \mathbb{E}[\max_n \widehat{\text{SR}}_n]}{\sqrt{\frac{1 - \gamma_3 \widehat{\text{SR}} + \frac{\gamma_4 - 1}{4}\widehat{\text{SR}}^2}{T - 1}}} \right)$$

### Audit Standard
- $\text{DSR} > 0.95$: Statistically significant edge after controlling for selection bias.
- $\text{DSR} < 0.95$: Rejected; cannot reject the null hypothesis that performance is due to data snooping.

---

## 3. Stepdown Procedures: Romano-Wolf & Hansen's SPA

When slicing models across multiple sub-categories (e.g., examining profitability across 30 different teams or 50 player props):
- Naive $p$-values guarantee false discoveries ($5\%$ of tests will show "significant" bias by pure chance).
- **Romano-Wolf Stepdown**: Controls the Family-Wise Error Rate (FWER) under arbitrary dependence structures using bootstrap iterations.
- **Hansen’s Test for Superior Predictive Ability (SPA)**: Tests whether a benchmark strategy is outperformed by any alternative in a universe of candidate models.
