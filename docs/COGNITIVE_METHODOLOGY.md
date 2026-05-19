# Cognitive Inference Methodology

This document explains, in plain language, how NeuroPit goes from raw racing telemetry to a number that describes the driver's mental state. It is the source of truth for every weight, every threshold, and every assumption that lives inside the Probabilistic Cognitive Inference Engine.

We chose this approach deliberately. Training a real neural network on synthetic data inside a hackathon window would have produced something that looked like AI on the slide deck but was impossible to defend in a code review. A weighted probabilistic engine is honest about what it knows and what it does not, and it gives IBM Granite something concrete to reason over.

## Reading guide

Each section below covers one cognitive output. Every output has the same four parts.

1. What we are trying to measure.
2. What signals we use.
3. The function, written out so you can rebuild it from scratch.
4. The reasoning behind the weights.

If you ever want to retune a weight, edit this document first, then the code. The audit log captures the active set of weights on every cognitive event, so old race replays still make sense after the constants move.

## 1. Stress Score

What we are trying to measure. A zero to one hundred estimate of mental pressure. High stress is not the same as fast driving. A driver can be fast and calm, fast and overloaded, or slow and panicking. We are after the second case.

Signals used.

- `steering_instability` from `SignalProcessor`.
- `panic_oscillation` from `SignalProcessor`.
- `synthetic_hr` from `BiometricSynthesizer`, used only above a baseline of one hundred forty beats per minute.

Function.

```
steering_term = min(steering_instability * 10, 100)
hr_term       = max(0, synthetic_hr - 140) * 1.5
stress_score  = clamp_0_100(steering_term * 0.40
                          + hr_term     * 0.40
                          + panic_oscillation * 0.20)
```

Reasoning. Forty percent on steering because most stress signatures in publicly available motorsport literature surface through micro corrections of the wheel before they surface anywhere else. Forty percent on heart rate elevation because once the body is committed to a stress response the cardiovascular signal is the most reliable confirmation. Twenty percent on panic oscillation because pure panic is rare. We want it represented but we do not want it to dominate the score on a single noisy lap.

## 2. Confidence Score

What we are trying to measure. A zero to one hundred estimate of driver decisiveness. Confidence collapses before laptimes do, so it is a useful leading indicator for the strategist.

Signals used.

- `throttle_commitment` from `SignalProcessor`.
- `braking_hesitation` from `SignalProcessor`.

Function.

```
throttle_term  = min(throttle_commitment * 5, 100)
hesitation_pen = braking_hesitation * 0.05
confidence_score = clamp_0_100(100 - ((100 - throttle_term) * 0.60
                                     + hesitation_pen))
```

Reasoning. Throttle commitment carries sixty percent of the weight because the decision to commit to throttle out of a corner is the most direct behavioural marker of trust in the car. Braking hesitation is treated as a penalty rather than as a positive signal. We do not want a smooth braker to be punished. We want a pumping braker to be flagged.

## 3. Fatigue Score

What we are trying to measure. A zero to one hundred estimate of cumulative cognitive exhaustion across a session. Fatigue is the only score that explicitly carries state from one window to the next.

Signals used.

- `stress_score` from the same evaluation tick.
- `steering_instability` from `SignalProcessor`.
- A persistent `cumulative_fatigue` value per driver, stored inside the engine.

Function.

```
delta = (stress_score          * 0.0005)
      + (steering_instability  * 0.001)

cumulative_fatigue = cumulative_fatigue + delta
fatigue_score      = min(cumulative_fatigue, 100)
```

Reasoning. The constants are deliberately small. Fatigue should creep upward across a race rather than spike on a single corner. A driver with a sustained stress score in the seventies for thirty minutes of racing reaches a fatigue score of roughly sixty three. That matches the qualitative reports from real drivers in long stints.

## 4. Persona Drift

What we are trying to measure. The discrete behavioural mode the driver is operating in right now. We map continuous cognitive scores into one of six labels.

Decision rules, evaluated in order. The first rule that matches wins.

1. Panic when `stress_score` is above eighty five and `panic_oscillation` is above twenty.
2. Aggressive when `stress_score` is above seventy and `throttle_commitment` is above eighty.
3. Fatigue when `fatigue_score` is above sixty and `confidence_score` is below forty.
4. Defensive when `confidence_score` is below fifty.
5. Flow State when `stress_score` is below forty and `confidence_score` is above eighty.
6. Recovery as the default.

Reasoning. We start with the highest stakes label, Panic, so the strategist sees the right warning even when other modes also apply. Flow State is the rarest label and the rules reflect that. Recovery is the catch all because most of a race is, in fact, recovery between stress events.

## 5. Tunnel Vision

A boolean flag promoted into a probability for downstream consumers.

```
tunnel_vision_prob = 100.0 if stress_score > 85 else 0.0
```

This is intentionally crude in V1. It exists so that the audit log and the dashboard both have a stable field name to read. The first real model that replaces it will keep the same field so nothing downstream needs to change.

## 6. Confidence Band

Every cognitive event ships with a confidence band of `high`, `moderate`, or `unstable`. The band is computed from three inputs.

1. `data_completeness` which is the fraction of expected telemetry fields that were not null in the contributing window.
2. `sensor_agreement` which is the fraction of contributing signals that move in the same direction.
3. `biometric_freshness` which is the time since the last biometric sample.

Rules of thumb. High band when completeness is above ninety percent and agreement is above seventy percent. Moderate band when completeness is above seventy percent. Unstable band otherwise. The exact constants live next to the function in code and are unit tested.

## 7. Why this approach

A weighted probabilistic engine is interpretable. Every score can be defended against a question of the form "why is this number what it is." That matters because the dashboard is going to show this number to a race strategist who has to make a million pound decision. Saying "the model said so" is not an answer. Saying "stress increased because steering instability rose by forty percent and heart rate rose by twelve beats per minute over the previous six laps" is.

The engine is also a stable foundation for the learned models that follow. The features fed into a trained sequence model are exactly the same features that drive these equations. The output schema does not change. The only thing that changes is the function that maps features to scores. That is the right way to evolve a cognitive system.

## 8. Versioning

Every adjustment to the constants above lands in `CHANGELOG.md` against the version that ships them. The audit log writes the active constants alongside the cognitive event so historical replays remain reproducible.

---

NeuroPit · Built by Hriday Vig · IBM AI Builders Challenge 2026 powered by IBM SkillsBuild.
