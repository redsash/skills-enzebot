# Quantitative Edge Auditor (`quant-edge-auditor`)

An enterprise-grade quantitative auditing, statistical verification, and adversarial stress-testing harness for sports prediction and betting models.

---

## 1. Executive Rationale: Deeper, Not Bigger

Retail sports modeling advice (and typical LLM prompt collections) treat model validation as a series of disconnected conversational personas ("Act as a Data Leakage Detective", "Act as a Calibration Expert"). An LLM visually reading CSVs and roleplaying as an auditor provides the illusion of rigor while suffering from three critical failure modes:
1. **The P&L Mirage**: Evaluating backtest ROI instead of Closing Line Value (CLV). In liquid sports markets (NFL, NBA, EPL), historical ROI over a few hundred bets is dominated by noise.
2. **The Multiple Testing Graveyard**: Testing 50 variations of a model and reporting the best backtest without adjusting for the graveyard of discarded trials guarantees false discovery.
3. **Conversational Vibes vs. Mathematical Verification**: Catching lookahead bias, uncalibrated probabilities, and portfolio correlation requires deterministic numerical computation (Shin devigging, Murphy decomposition of Brier, bitemporal joins, block bootstraps), not prose prompts.

`quant-edge-auditor` transforms these isolated personas into an integrated, reproducible, 4-stage adversarial verification engine.

---

## 2. Retail Personas vs. Quantitative Professional Practice

| Retail Persona Prompt | Professional Quantitative Approach | Structural Blindspot in Retail Idea |
| :--- | :--- | :--- |
| **1. Data Leakage Detective** | **Bitemporal Causal Joins (`AS-OF`)**: Structurally enforcing that `knowledge_time <= bet_decision_time` on every row. | Asking an LLM to "inspect injury reports" after the fact is fragile; causal joins must be mathematically impossible to breach. |
| **2. Backtesting Auditor** | **Deflated Sharpe Ratio (DSR) & White's Reality Check**: Penalizing reported performance by the number of discarded trials ($N_{\text{trials}}$). | Standard backtests ignore selection bias across model iterations; a backtest with 100 prior iterations requires a much higher hurdle. |
| **3. Probability Calibration Expert** | **Proper Scoring Rules & Murphy Decomposition**: Decomposing Brier score into *Reliability*, *Resolution*, and *Uncertainty*; equal-frequency quantile ECE. | Arbitrary 5% probability bins mask miscalibration in fat tails; naive calibration ignores the distinction between resolution and reliability. |
| **4. Expected Value Inspector** | **Shin & Power De-vigging against Benchmark Books**: Stripping bookmaker overround using Shin's insider-trading parameter $z$ to recover true market probabilities. | Assuming proportional devigging (dividing by sum of implied probabilities) severely underestimates the longshot bias present in sportsbooks. |
| **5. Model Bias Hunter** | **Combinatorially Purged & Embargoed Cross-Validation (CPCV)**: Slicing prediction errors across orthogonal dimensions while purging overlapping information events. | Naive subgroup analysis creates new multiple-testing hazards; pros use Bonferroni-Holm or Romano-Wolf corrections across sliced dimensions. |
| **6. Correlation Analyzer** | **Copula-based Portfolio Covariance & Stationary Block Bootstrap**: Preserving game-script autocorrelation and covariance in simultaneous bets. | Simple Pearson correlation on outcomes ignores non-linear tail dependence (e.g., game script blowouts impacting multiple props). |
| **7. Model Version Tracker** | **Cryptographic Git-SHA Model Registry & Forward-Walk Ledger**: Enforcing immutable commits and out-of-sample forward tracking. | Version tracking in spreadsheets or comments allows retroactive rule fiddling; only tamper-proof commit ledgers establish true provenance. |
| **8. Performance Stress Tester** | **Adversarial Null Permutation Testing**: Scrambling target outcomes 1,000+ times to prove edge cannot be replicated by random noise ($p < 0.001$). | Parametric stress tests assume normal distributions; financial and sports returns have fat tails and clustering that require block resampling. |

---

## 3. The Rawest Material Required

Top quantitative desks never start from aggregated model output summaries or P&L spreadsheets. They start from:

1. **Raw, Unfiltered Millisecond Tick-Level Odds Logs (L2/L3 Orderbooks)**:
   WebSocket and FIX feed recordings from market-makers (Pinnacle, Circa, Betfair Exchange), capturing every price update, line freeze, spread adjustment, and liquidity volume tick with microsecond timestamps.
2. **Point-in-Time Event-Sourced Wire Feeds**:
   Raw text streams of official league injury wires, Twitter/X breaking news feeds, weather radar sweeps, and referee assignments, stored with immutable database ingestion timestamps (`knowledge_time`).
3. **The Backtest Graveyard (Trial Registry)**:
   A complete cryptographic log of every hypothesis, discarded feature, threshold adjustment, and parameter search executed during research.

---

## 4. Specific Methods and Tools

### Mathematical and Econometric Methods
- **Shin's De-vigging Method (1992, 1993)**: Solves for the proportion of insider/informed money $z$ in the market to extract the true underlying distribution $\pi$:
  $$\sum_{i} \sqrt{z^2 + 4(1-z)\frac{\pi_i^2}{\sum \pi_j}} = 1 + z$$
- **Murphy's Brier Score Decomposition (1973)**:
  $$\text{Brier} = \text{Reliability} - \text{Resolution} + \text{Uncertainty}$$
  - $\text{Uncertainty} = \bar{o}(1 - \bar{o})$ (inherent market entropy)
  - $\text{Reliability} = \frac{1}{N}\sum_{k} n_k (f_k - \bar{o}_k)^2$ (calibration penalty, lower is better)
  - $\text{Resolution} = \frac{1}{N}\sum_{k} n_k (\bar{o}_k - \bar{o})^2$ (ability to discriminate outcomes, higher is better)
- **Deflated Sharpe Ratio (Bailey & López de Prado, 2014)**:
  Adjusts the estimated Sharpe ratio for the number of trials tested, sample skewness, and kurtosis to calculate the probability that the observed Sharpe is a statistical fluke:
  $$\text{DSR} \equiv \text{PSR}\left(\sqrt{\mathbb{V}[\{\widehat{\text{SR}}_n\}]}\right)$$
- **Stationary Block Bootstrap (Politis & Romano, 1994)**:
  Resamples historical bet blocks with random block lengths following a geometric distribution to preserve serial and cluster correlation across games.

### Tooling Stack
- `polars` / `duckdb`: High-performance deterministic `AS-OF` joins for bitemporal causality.
- `scipy` / `numpy`: Numerical root-finding for Shin/Power devigging and Murphy decomposition.
- `netcal` / `scikit-learn`: Equal-frequency quantile calibration analysis and reliability diagrams.
- `arch` / `statsmodels`: Econometric hypothesis testing, block bootstrapping, and Deflated Sharpe calculations.
- `pandera` / `pydantic`: Runtime schema validation on input logs.

---

## 5. External Falsification: Proving the Result is Right

To eliminate self-deception and prompt biases, the audit harness evaluates against three external oracles:

1. **Closing Line Value (CLV) Convergence ($t$-stat $> 3.0$)**:
   $$\text{CLV} = \frac{P_{\text{placed}}}{P_{\text{close\_novig}}} - 1$$
   Across $N \ge 1,000$ independent prospective bets, the mean CLV against Pinnacle or Betfair closing prices must be strictly positive with $t > 3.0$. Market-maker closing prices represent millions of dollars of sharp risk and serve as an unbribable reality oracle.
2. **The Permutation Invariance Test (Zero-Edge Null)**:
   When target outcomes are permuted or time-inverted while preserving the feature covariance matrix, the entire pipeline's measured edge must drop to exact zero ($p \approx 0.50$, Sharpe $\le 0$). Any pipeline reporting positive edge on scrambled targets is rejected as leaking data.
3. **Out-of-Distribution Forward Brier Dominance**:
   On prospective games occurring strictly *after* the model's Git SHA was committed, the model's Brier score must be strictly lower than the market-maker's closing un-vigged probability.

---

## 6. Runtime Adaptation: Model & Skill Discovery

The skill executes sub-stages dynamically by inspecting the runtime environment via `scripts/detect_environment.py`:
- **Model Tiers**:
  - `Tier 1: Heavy Reasoning` (e.g. DeepThink / Pro): Allocated to adversarial red-teaming, competing root-cause analysis, and final audit synthesis.
  - `Tier 2: Code Execution & Fast Analysis` (e.g. Medium / Flash): Allocated to script execution, schema validation, and numerical pipeline runs.
  - `Tier 3: Rapid Formatting`: Allocated to raw data transformation and table formatting.
- **Skill Discovery**:
  - Detects if `competing-hypothesis` is available to stress-test rival explanations for apparent edge.
  - Detects if `planning-with-files` is available to maintain multi-step audit logs.
  - Detects if `human-readable` is available to polish the audit synthesis for stakeholders.
- **Self-Contained Fallback**: If external skills or heavy models are unavailable, bundled Python scripts execute all mathematical operations deterministically without degrading audit rigor.
