# NeuroPit five-minute demo script

A run order judges or recruiters can follow without you in the room. Assumes the Judge Quickstart in the README has been run and Mission Control is loaded at `http://localhost:3000`.

## Run order

| Time | Surface | Action | What to call out |
| --- | --- | --- | --- |
| 00:00 | Mission Control header | Open `http://localhost:3000`. | Empty pit-wall with the driver selector strip. The stable-link badge sits idle, the heartbeat is ticking. |
| 00:30 | Streamer terminal | `make stream`. | Within ten seconds the cognitive rings populate. The persona band switches from `Flow State` to a working state for at least one driver. |
| 01:00 | Cognitive rings | Point at Stress / Confidence / Fatigue / Panic Probability. | Each ring carries a confidence dot. The trajectory chart below shows the rolling history. |
| 01:45 | Driver selector | Switch the active driver. | The Granite reasoning panel reflows instantly to per-driver scope. No stale text. |
| 02:30 | Reasoning panel | Read one paragraph. | Confirm the `via granite-local` source label. Hover the grounded passages to see the motorsport ontology citations. |
| 03:00 | Prescriptive Engine panel | Point at the cognitive efficiency score and the seconds-left-on-the-table number. Read the primary prescribed action and the triggers that fired. | Projected post-action efficiency is rendered next to the action label. Alternatives are ranked. Guardrail-blocked actions are clearly tagged. |
| 03:45 | What-If drawer | Top-right button. Pick the **Drop HR to calm baseline** preset, hit **Run replay**. | The chart fans baseline vs counterfactual stress and confidence side by side. The divergence summary calls out which axis moved most. This is grounded in audit-log data, not synthetic priors. |
| 04:15 | Audit log | Open any `audit_logs/cognitive-*.jsonl` in a tail. | Point at the score inputs, the weights snapshot, and the model source. Every cognitive evaluation, every prescription, and every what-if replay writes its audit row before the matching Kafka emit. |
| 04:45 | Close | Land the differentiator. | Other systems ask what is happening to the car. NeuroPit infers the human nervous system operating the car, prescribes the next pit-wall action, and lets the strategist defend the call after the fact. |

## What good looks like

- Heartbeat in the header shows a fresh timestamp every two seconds.
- Cognitive rings move smoothly without the persona band oscillating wildly.
- The Granite paragraph mentions the persona, the confidence band, and the actual signals that drove the call.
- The prescription rationale calls out the biggest envelope drift dimension by name.
- The What-If chart shows a visibly different counterfactual curve for at least one of the cognitive fields.

## Troubleshooting

- Rings never populate → check `make backend` and `make stream` are still running.
- Heartbeat keeps ticking but no rings → check the gateway terminal for Kafka broker errors. `docker ps` to confirm Redpanda is up.
- Reasoning panel shows `via stub` instead of `via granite-local` → the local Granite model is still downloading. Run `python scripts/download_granite.py` and wait for it to finish. The dashboard auto-flips to `granite-local` as soon as the next reasoning event picks up the loaded model.
- What-If replay returns a 404 → no audit rows yet for the selected driver. Let the stream run for thirty seconds and try again.

---

NeuroPit · Built by Hriday Vig · IBM AI Builders Challenge 2026 powered by IBM SkillsBuild.
