# Changelog

All notable changes to NeuroPit live here. We follow [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) and the project version moves under [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

The intention is that someone landing on the repository for the first time can scan this file and understand what shipped when, what is in progress, and where to look for the detail.

## [0.1.0] - 2026-05-19

This is the first end to end release of NeuroPit. The system can ingest a real Formula session, infer the driver's cognitive state in near real time, explain that state through IBM Granite or a local stub, project failure probabilities across four horizons, simulate counterfactual race scenarios, and surface every output on a Mission Control dashboard.

### Documentation

- `docs/ARCHITECTURE.md` written in plain language so a new contributor can read the whole system in one sitting.
- `docs/EVENT_TAXONOMY.md` describing every Kafka topic, payload, producer, and consumer.
- `docs/COGNITIVE_METHODOLOGY.md` documenting the weights and reasoning behind the Probabilistic Cognitive Inference Engine.
- `docs/DEMO_RUNBOOK.md` capturing the exact commands and talking points for the live demo.
- `tests/README.md` and `data/knowledge_sources/README.md` describing the test layout and the knowledge ingestion workflow.

### Hardening and shared infrastructure

- Every backend module now reads its broker, database, and replay configuration through `src.backend.config.get_settings` instead of hardcoded localhost strings.
- New `src/backend/common` package containing a versioned cognitive weight registry, the trust and uncertainty layer, the persona drift state machine, and a thread safe JSON Lines audit log writer.
- Cognitive Inference Engine rewritten to use the shared weights, attach a confidence band to every emission, stamp the active weight version onto each record, and append a full audit trail per evaluation.
- Bootstrap script now reads broker, Qdrant, and replay settings from configuration and adds the `explanation-events` topic that the Granite explainability worker subscribes to.

### Testing

- New `tests/unit` suite covering the signal processor, the cognitive weight registry, the persona drift rules, the trust and uncertainty layer, the audit log writer, the cognitive equations, the predictive failure engine, the Ghost Lap AI, the counterfactual simulator, the Granite client, the strategy parliament, the Docling compiler, the FastAPI gateway, and the security helpers.
- The old broker dependent scripts `src/backend/test_phase_2.py` and `src/backend/test_phase_3.py` have moved into `tests/integration` as proper pytest modules marked with the `integration` marker so the default test run no longer requires Redpanda.
- Top level `Makefile` exposing `make test`, `make integration`, `make infra-up`, `make bootstrap`, `make stream`, `make backend`, `make gateway`, and `make frontend` so a new contributor only needs one entry point.

### Forecasting and simulation

- New `src/backend/prediction/failure_engine.py` projecting crash, lock up, spin, failed overtake, concentration collapse, and strategic non compliance probabilities across the five second, one lap, three lap, and full race horizons listed in the PRD.
- New `src/backend/simulation/ghost_lap.py` reconstructing a cognitive normalised lap from per lap stress, fatigue, and panic summaries and exposing a clear per cause lost time breakdown.
- New `src/backend/simulation/counterfactual.py` implementing the five canonical scenarios from PRD section twenty, each carrying a rationale string and the explicit adjustments applied to the baseline lap.

### IBM integration and reasoning

- New `src/backend/reasoning/granite_client.py` that talks to IBM watsonx.ai when credentials are configured and silently falls back to a local templated stub when they are not, so the dashboard always has an explanation to show.
- New `src/backend/reasoning/explainability_worker.py` subscribing to the cognitive state topic and publishing a Granite explanation per evaluation to the explanation events topic.
- New `src/backend/strategy/parliament.py` implementing the seven specialised strategy agents from the PRD with a tally based consensus and a transcript that Granite can synthesise.
- New `src/backend/knowledge/docling_compiler.py` for ingesting PDFs, HTML, Markdown, and plain text from `data/knowledge_sources` into the Qdrant motorsport ontology, with a deterministic hashing fallback when sentence transformers are not installed.
- Reference Langflow definition committed under `orchestration/langflow/neuropit_strategy_flow.json` for visual review of the cognitive strategy pipeline.
- Seed knowledge document under `data/knowledge_sources/neuropit_methodology_seed.md` so the compiler has something to ingest immediately after a fresh checkout.

### Gateway and dashboard

- New FastAPI gateway under `src/backend/api/` exposing healthcheck, ghost lap, counterfactual, parliament, and a single WebSocket fanout that bridges the Kafka cognitive and explanation topics to Mission Control.
- Mission Control dashboard rewritten to consume the WebSocket envelope so the live stress, confidence, fatigue, persona, confidence band, and Granite reasoning panels reflect the actual pipeline rather than synthetic frontend data.
- `run_backend.py` now also boots the predictive failure engine and the explainability worker so a single command brings every backend service online.

### Security and privacy

- New `src/backend/security` package containing JWT token issuance and verification, a role registry covering Team Principal, Race Strategist, Driver Engineer, and Neuro Analyst, and a Fernet based encryption helper for biometric payloads at rest.
- Retention helper that returns whether a biometric record is past its configured retention window, ready to wire into the privacy enforcement loop described in PRD section thirty four.

### Working notes

- These documents are the source of truth. If the code disagrees with them, the documents win and the code needs a fix.
- The OSS community files such as the Code of Conduct, the Contributing guide, the Security policy, and the GitHub issue templates are intentionally postponed and will be added once the core platform stabilises.

## [0.0.1] - 2026-05-19

### Initial scaffolding

- Initial project scaffolding and directory structure.
- Top level `README.md` introducing the Probabilistic Cognitive Inference methodology and the V1 scope.
- Layered backend folders under `src/backend` for `ingestion`, `feature_engineering`, `inference`, and `integration`.
- Next.js Mission Control scaffold under `src/frontend` with a working stress, confidence, and fatigue panel.
- Docker Compose definitions for Redpanda, InfluxDB 2, and Qdrant inside `infrastructure/`.
- FastF1 backed historical race streamer, Kafka producer, and feature extraction pipeline.
- Cognitive Inference Engine and Biometric Synthesiser wired into the event stream.
- Infrastructure bootstrap script that creates the full topic taxonomy and the Qdrant collections.
- Apache 2.0 LICENSE and NOTICE files attributing every third party component used in V1.
