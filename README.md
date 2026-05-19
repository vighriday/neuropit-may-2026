# NeuroPit - Cognitive Operating System for Motorsport

## Cognitive Inference Methodology

NeuroPit V1 uses a **probabilistic cognitive inference architecture** where cognitive states such as:
* stress,
* fatigue,
* confidence,
* and aggression

are derived from:
* telemetry behavior,
* synthetic physiological signals,
* environmental conditions,
* and race-context variables

through **weighted deterministic inference functions.**

This approach was intentionally selected to maximize explainability, preserve deterministic reasoning, support trustworthy AI principles, and establish a stable foundation for future learned behavioral models.

## Architecture

This is a local-first hybrid cloud infrastructure carefully scoped for a 0 to 1 Zero-to-One vertical slice.

**1. Data Ingestion:** OpenF1 / FastF1 telemetry streams.
**2. Signal Generation:** Telemetry-conditioned synthetic biometrics.
**3. Inference Engine:** Probabilistic cognitive state estimations.
**4. Reasoning & Context:** IBM Docling for Motorsport Ontology (Qdrant mappings), Langflow orchestration, and IBM Granite for explainability.
**5. Streaming & Persistence:** Redpanda (event-bus) and InfluxDB (time-series state).
**6. User Interface:** Next.js Mission Control dashboard.

## Prerequisites & Setup (Before Code Execution)

1. **Python 3.11+ Environment:** Ensure a robust Python virtual environment.
2. **Node.js 20+:** Required for the Next.js Mission Control dashboard.
3. **Docker Engine:** Required to spin up local Redpanda and Langflow instances.
4. **IBM Cloud Account:** Active IBM watsonx.ai API keys for Granite model inference.
5. **InfluxDB Cloud Account:** Free tier bucket setup for `neuropit-telemetry`.
6. **Qdrant Cloud Account:** Free tier cluster setup for ontological embeddings.

*For detailed technical phases, refer to our build plan documentation.*
