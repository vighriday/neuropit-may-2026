# NeuroPit Architecture

This is the working architecture document for NeuroPit V1. If you are reading this for the first time, start here. If you are about to add a new layer, update this file before you write a line of code. The Master Build Plan in `docs/MASTER_BUILD_PLAN.md` and the platform requirements document in the repo root describe what the system is supposed to do. This document describes how it is actually built.

NeuroPit is a real time cognitive intelligence system for Formula racing. The core idea is simple. Racing teams already measure the car in great detail. They do not measure the driver in any meaningful way. NeuroPit treats the driver as a probabilistic signal that can be inferred from the telemetry the car is already producing, and it does that in a way the team can trust because every output comes with a written explanation.

## What we are building, plainly

A streaming pipeline that ingests racing telemetry, derives a small set of behavioural features per driver, fuses those features with telemetry conditioned synthetic biometrics, scores a handful of cognitive states such as stress, fatigue, and confidence, asks IBM Granite to explain those scores in natural language, and renders the result on a Mission Control dashboard that looks like the pit wall in a real Formula team.

The five things that make NeuroPit different from a normal telemetry dashboard are the cognitive twin, the explainability layer, the uncertainty layer, the persona drift engine, and the audit log that captures every reasoning step. Everything else is plumbing that exists to make those five things possible.

## Principles we will not bend on

1. The pipeline is event driven from end to end. Nothing materialises state outside the stream.
2. The car is measured. The driver is inferred. We do not pretend otherwise.
3. Every cognitive output ships with a confidence band and a written explanation. No exceptions.
4. Local first. The whole stack has to boot on a developer laptop with Docker and free tier cloud accounts.
5. Apache 2.0 from day one. Every third party component is attributed in the NOTICE file.
6. We choose interpretable signal engineering over hastily trained models for V1, and we say so out loud.

## Logical layers

We organise the runtime into five tiers. Each tier owns a small number of layers. Each layer owns a small number of files.

Tier A is acquisition. It contains the data acquisition layer that pulls historical telemetry from OpenF1 and FastF1, and the event streaming layer that fans that telemetry out through Redpanda.

Tier B is signal intelligence. It contains the telemetry processing layer, the feature engineering layer that turns raw frames into behavioural features, and the biometric synthesis layer that produces telemetry conditioned heart rate and HRV estimates.

Tier C is cognitive intelligence. This is the layer the rest of the system exists to serve. It contains the probabilistic cognitive inference engine, the emotional modeling layer, the persona drift engine, the predictive failure layer that lands in Phase 4, and the counterfactual simulation layer that also lands in Phase 4.

Tier D is reasoning and trust. It contains the explainability layer powered by IBM Granite, the trust and uncertainty layer that attaches confidence bands to every cognitive output, the multi agent strategy layer orchestrated through Langflow, and the knowledge and retrieval layer that uses Docling to compile motorsport literature into a Qdrant ontology.

Tier E is the surface. It contains the visualisation layer built in Next.js, the audit layer that writes every cognitive decision to disk, the reporting layer that produces post race intelligence packs, and the historical intelligence layer that lets the team query past sessions through vector search.

## How a frame travels through the system

A telemetry frame begins its life inside `src/backend/ingestion/streamer.py`. The streamer loads a real Formula session from FastF1, merges the car physics with positional data, and replays the session frame by frame at a configurable speed. Each frame is wrapped in a `TelemetryFrame` model and published to the `incoming-telemetry-raw` topic on Redpanda.

Two things happen in parallel from there. The InfluxDB writer in `src/backend/integration/influx_writer.py` persists the raw frame to time series storage so it can be replayed later. The feature extractor in `src/backend/inference/feature_extractor.py` adds the frame to a per driver sliding window and emits a behavioural feature vector to the `telemetry-features` topic every few frames.

The biometric synthesiser in `src/backend/inference/biometric_synthesizer.py` consumes the feature stream and emits telemetry conditioned heart rate, HRV, and respiration estimates to the `biometrics-enriched` topic. The cognitive inference engine in `src/backend/inference/cognitive_engine.py` joins the feature and biometric streams per driver, computes the cognitive twin state, and writes the result to the `cognitive-state-inference` topic along with a persistence row in InfluxDB.

The cognitive event is then picked up by the Granite explanation worker, which generates a short natural language reasoning string and pushes it to the `explanation-events` topic. The FastAPI gateway subscribes to both the cognitive topic and the explanation topic and fans them out over WebSocket to the Mission Control dashboard.

The dashboard never displays a number without its explanation and its confidence band. That is a hard rule.

## Topic taxonomy

Topic names, partition counts, payload shapes, and ownership rules live in `docs/EVENT_TAXONOMY.md`. If the topic list in `src/backend/init_infrastructure.py` disagrees with the taxonomy document, the taxonomy document wins and the code is wrong.

## Cognitive methodology

The exact weights and reasoning behind every cognitive score live in `docs/COGNITIVE_METHODOLOGY.md`. Read that before adjusting the engine.

## Latency targets

The PRD asks for cognitive alerts under three hundred milliseconds. The local stack is built to meet that target. Ingestion to Kafka publish runs at around twenty milliseconds per frame. Feature window processing runs at around sixty milliseconds. Biometric synthesis adds another twenty. Cognitive inference adds forty. The Granite stub adds thirty. The dashboard re renders inside thirty. The cloud Granite call is best effort, around two hundred and fifty milliseconds when it is up, and the stub takes over automatically when it is not.

## Failure handling

Missing telemetry fields drop the confidence band one step instead of guessing. A Kafka outage causes the producer to buffer and flips the dashboard banner to amber. InfluxDB downtime is logged and skipped. Granite cloud outage is invisible because the local stub fills in. Biometric stalls trigger a feature only fallback in the cognitive engine. None of these conditions are allowed to silently lower the displayed score without lowering the displayed confidence first.

## Reproducibility

The whole system should boot from one command. `docker compose up` brings the infrastructure online. `python -m src.backend.init_infrastructure` creates topics and Qdrant collections. `python -m src.backend.ingestion.streamer` plays back the chosen session. Pinned dependencies live in `src/backend/requirements.txt`. Replay seeds live in `.env.example`. The cognitive weights are versioned in `docs/COGNITIVE_METHODOLOGY.md` and stamped onto every audit log row so historical replays still make sense after the constants move.

## Where the roadmap goes from here

Phase 4 adds the predictive failure engine, the Ghost Lap AI, and the counterfactual simulator on top of the same event stream. Phase 5 wires the Strategy Parliament through Langflow and uses Docling to populate the Qdrant ontology. Phase 6 ships the post race intelligence pack. Phase 7 hardens encryption, RBAC, and audit for race day deployment. None of these phases require rewriting the foundation. They subscribe to the same topics this document already describes.
