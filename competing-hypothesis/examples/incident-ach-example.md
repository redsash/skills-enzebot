# Worked Example: Analysis of Competing Hypotheses (Payment 504 Timeouts)

### 1. Focal Question & Candidate Hypotheses
*"What is causing intermittent 504 Gateway Timeouts on the checkout service during peak traffic?"*
- **H1**: Downstream third-party fraud-check webhook rate-limiting or stalling.
- **H2**: Primary PostgreSQL connection pool exhaustion.
- **H3**: Redis session-cache latency spikes stalling request middleware.

### 2. Evidence Assessment
- **E1**: Only checkout routes invoking the synchronous fraud-check webhook return 504; catalog and cart DB routes succeed *(Credibility: High | Diagnosticity: High)*.
- **E2**: DB pool utilization peaks at 85% with zero connection wait timeouts logged *(Credibility: High | Diagnosticity: High)*.
- **E3**: Redis p99 jumped from 2ms to 18ms twice *(Credibility: High | Diagnosticity: Moderate)*.
- **E4**: Checkout pod CPU holds steady at 40% *(Diagnosticity: Low / Nondiagnostic)*.

### 3. ACH Consistency Matrix

| Evidence Item | H1: Fraud Webhook | H2: DB Pool | H3: Redis Latency | Diagnostic Note |
| :--- | :---: | :---: | :---: | :--- |
| **E1**: Non-fraud DB routes unaffected | `++` | `--` | `-` | Shared DB pool / middleware would fail cart writes too |
| **E2**: Zero DB pool wait errors at 85% | `0` | `--` | `0` | Contradicts pool exhaustion |
| **E3**: Two 18ms Redis spikes | `0` | `0` | `+` | 18ms cannot explain 30s 504 gateway timeouts alone |
| **E4**: CPU steady at 40% | `0` | `0` | `0` | Nondiagnostic under all three I/O-bound hypotheses |

### 4. Ranking by Fewest Inconsistencies
1. **Leading (H1 — Fraud Webhook)**: `0` inconsistencies (`-`/`--`).
2. **Eliminated (H3 — Redis)**: `1` inconsistency (`-`); 18ms latency cannot saturate a 30s timeout.
3. **Eliminated (H2 — DB Pool)**: `2` strong inconsistencies (`--`).

### 5. Sensitivity & High-Value Next Probe
- **Key Vulnerability**: E1 relies on gateway route telemetry; if cart routes hit a separate read replica pool, H2 needs re-testing.
- **Next Probe**: Measure outbound TCP/TLS timing to `fraud-api` vs. inspect checkout worker thread pool saturation during peak bursts.

### 6. Assessment & Falsification Trigger
- **Confidence**: High (subject to outbound timing probe).
- **Falsification Trigger**: Outbound `fraud-api` p99 response time under 500ms during active 504 windows disproves H1.
