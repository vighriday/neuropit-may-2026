# Security Policy

## Supported versions

NeuroPit is in active development. Security fixes are applied to the `main` branch and the latest tagged release.

| Version | Supported |
| --- | --- |
| 0.3.x | Yes |
| 0.2.x | Yes |
| 0.1.x | No |
| < 0.1 | No |

## Reporting a vulnerability

Please do not file a public GitHub issue for a security report.

Email Hriday Vig at [vighriday@gmail.com](mailto:vighriday@gmail.com) with the following content.

- A short title that identifies the affected component.
- A reproducible description of the issue, including the exact commit, the configuration, and the steps that triggered the problem.
- Any logs, screenshots, or proof of concept attached.

The maintainer will acknowledge the report within seventy two hours and aim to ship a fix or a documented mitigation within fourteen days for high severity findings.

## Scope

The following surfaces are in scope.

- The cognitive inference engine and every supporting worker under `src/backend/`.
- The FastAPI cognitive gateway and the JWT plus role based access enforcement.
- The Fernet at rest encryption helper for biometric payloads.
- The Mission Control surface under `src/frontend/`.
- The live PPG biometric ingestion path (`/ws/sensor` route on the gateway, and `src/backend/integration/ppg_ingest.py`).
- The per driver persona prior loader (`src/backend/common/priors.py`) and the artifact at `data/persona_priors.json`.

The following are out of scope unless the report identifies a NeuroPit specific misconfiguration.

- IBM watsonx.ai, IBM Granite, IBM Docling, Redpanda, InfluxDB, Qdrant, Langflow, FastAPI, and Next.js themselves. Please report to the upstream projects.

## Defaults

The `.env.example` file ships safe development defaults. Production deployments must rotate `API_JWT_SECRET` and `ENCRYPTION_KEY`. The biometric synthesiser encrypts heart rate, HRV, and respiration payloads at write through the Fernet helper.

## Known posture choices

These are deliberate decisions, not bugs. They are listed here so a security reviewer knows where to look first.

- **Live PPG WebSocket (`/ws/sensor`) is unauthenticated.** The endpoint accepts heart rate samples from a browser on the local network without a JWT. The data never crosses the local network and asking a phone to negotiate JWT before opening the camera would block the demo without raising any meaningful bar. If NeuroPit is deployed in a setting where the local network is not trusted, this route should either be moved behind a JWT step or disabled entirely by removing the `app.websocket("/ws/sensor")` registration in `src/backend/api/gateway.py`.
- **InfluxDB credentials.** Both the admin password and the admin token are mandatory environment variables on the docker compose stack (see `infrastructure/docker-compose.yml`). The stack refuses to start without them. A previous version of the file shipped literal credentials in version control; that mistake is documented in `docs/FAILURE_MODES.md` entry five, and the fix is in commit `6ec3e2e`. The leaked values remain in git history for any commit predating that fix.
- **Persona priors are public data.** `data/persona_priors.json` is generated from publicly available F1 telemetry and contains no personal information. The file is regenerable via `scripts/compute_persona_priors.py`. It is safe to commit.

---

NeuroPit · Built by Hriday Vig · IBM AI Builders Challenge 2026 powered by IBM SkillsBuild.
