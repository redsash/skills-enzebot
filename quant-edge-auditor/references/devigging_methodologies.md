# Quantitative De-vigging Methodologies: Shin, Power, and Log-Odds

To determine whether a predictive sports model has genuine expected value, raw bookmaker odds must be stripped of overround (the "vig" or "juice") to recover true latent probabilities.

---

## 1. The Longshot Bias & Why Naive Normalization Fails

The simplest approach divides each implied probability $q_i = \frac{1}{O_i}$ by the total bookmaker book sum $\sum q_j$:
$$\pi_i^{\text{naive}} = \frac{q_i}{\sum_{j} q_j}$$

**Failure Mode**: Bookmakers do not distribute overround equally or proportionally across all outcomes. Decades of empirical market literature document the **favorite-longshot bias**: bettors disproportionately over-bet heavy underdogs and longshots (treating them as lottery tickets). Bookmakers balance their books by loading disproportionately higher margins onto longshots, while keeping favorites and high-liquidity lines tighter. Naive proportional normalization severely over-estimates longshot true probability and under-estimates favorite true probability.

---

## 2. Shin's Method (1992, 1993)

Shin modeled bookmaker odds as an equilibrium between two populations:
1. **Uninformed noise bettors** who wager in proportion to true probabilities $\pi_i$.
2. **Informed insiders** who possess perfect information with probability $z \in [0, 1]$.

The bookmaker sets quoted prices $d_i = \frac{1}{q_i}$ to break even against informed traders:
$$q_i = (1 - z)\pi_i + z \frac{\pi_i}{\sum \pi_j}$$

Solving for the true underlying probabilities $\pi_i$ yields:
$$\pi_i = \frac{\sqrt{z^2 + 4(1 - z)\frac{q_i^2}{\sum q_j}} - z}{2(1 - z)}$$

The parameter $z$ (the proportion of informed money) is determined iteratively via numerical root-finding under the constraint that the probabilities sum to unity:
$$\sum_{i=1}^{n} \pi_i(z) = 1$$

### Practical Takeaways
- Shin devigging naturally extracts a higher fair probability for favorites and a lower fair probability for longshots compared to proportional normalization.
- In liquid Pinnacle/Betfair markets, $z$ typically ranges between `0.01` and `0.04`.
- A high $z$ indicates significant market suspicion of private information (e.g., late breaking team news or weather shifts).

---

## 3. The Power Method (Multiplicative Odds)

The power method assumes the bookmaker applies an exponential margin factor $k > 1$ to true probabilities:
$$q_i = \pi_i^{1/k} \implies \pi_i = q_i^k$$

The exponent $k$ is found numerically such that:
$$\sum_{i=1}^{n} q_i^k = 1$$

This method smoothly shifts probability from longshots to favorites without requiring the insider-trading structural model of Shin. In 2-way handicap and total markets, the Power method and Shin method produce near-identical results.

---

## 4. Benchmark Markets vs. Soft Books

When calculating Closing Line Value (CLV):
- **Benchmark Sharp Books**: Always use Shin-devigged odds from **Pinnacle**, **Circa Sports**, or **Betfair Exchange** (net of 2% commission).
- **Execution Books**: Compare the price secured at soft sportsbooks (DraftKings, FanDuel, BetMGM) against the sharp Shin benchmark.
- **CLV Formula**:
  $$\text{CLV} = \frac{O_{\text{placed}}}{O_{\text{benchmark\_shin\_fair}}} - 1$$
