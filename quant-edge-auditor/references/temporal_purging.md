# Temporal Purging, Embargoing, and Bitemporal Joins

Sports time-series data presents unique leakage risks that standard k-fold cross validation fails to mitigate.

---

## 1. Bitemporal Event Architecture

Every row in an audit dataset must distinguish between two fundamental temporal axes:

1. **Event Time ($T_{\text{event}}$)**: The wall-clock moment the athletic contest occurs (e.g., kickoff, tip-off).
2. **Knowledge Time ($T_{\text{knowledge}}$)**: The exact moment the information reached your computational pipeline or database.

### Strict Causality Invariants
- **Prediction Invariant**:
  $$T_{\text{knowledge}}(\text{Feature}_i) \le T_{\text{decision}} < T_{\text{event}}$$
- **As-Of Joins**: When joining injury reports, weather feeds, or closing market updates, join on:
  $$\text{Feature}.\text{timestamp} \le \text{Decision}.\text{timestamp}$$
  with no forward lookups.

---

## 2. Combinatorially Purged Cross-Validation (CPCV)

In sports betting, games on the same slate (e.g. 1:00 PM Sunday NFL games) share information:
- Correlated weather systems.
- Correlated referee assignments.
- Macro betting sentiment and market maker line rebalancing.

### Purging
Remove from the training set any observations whose informational window overlaps with the test set.

### Embargoing
Following a test set period, enforce an **embargo window** (e.g., 24 to 72 hours) during which subsequent games are barred from training to eliminate auto-regressive momentum and lineup bleed.
