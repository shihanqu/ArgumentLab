# Argument Lab

Argument Lab is a local-first litigation stress-test engine for legal teams. It helps lawyers and legal operators pressure-test motions, pleadings, exhibits, authorities, contracts, transcripts, and email history through structured adversarial AI self-play.

The goal is simple: expose weaknesses before the other side or the court does.

Argument Lab is not a chatbot, a consumer legal-advice product, or a case outcome predictor. It is a prototype workbench for testing arguments against the record, the timeline, opposing counsel pressure, authority limits, and judge-style review.

## Why It Matters

Legal teams often know the strongest version of their own argument, but the critical risk usually appears in the gaps:

- A draft brief says notice happened late, but emails show earlier notice.
- A motion relies on facts that are unsupported by the uploaded record.
- A citation appears in the draft, but the authority was not uploaded or does not clearly support the proposition.
- A procedural posture does not match the argument being made.
- A judge focused on preservation, contract text, or practical fact disputes may see the issue differently.

Argument Lab turns those risks into visible, structured findings with source links and recommended revisions.

## What The Prototype Does

- Creates local matters without accounts or login.
- Uploads legal materials and classifies them by document type.
- Extracts document text and previewable source snippets.
- Parses email history into a chronological timeline.
- Tags email events for notice, waiver, modification, repudiation, delay, reliance, damages, and related legal significance.
- Lets users configure model providers in the UI.
- Assigns different models to different legal agents.
- Supports local OpenAI-compatible LLMs by base URL, model name, and optional key.
- Runs multi-round adversarial self-play.
- Applies abstract judge personas.
- Shows the full agent transcript, not just a final memo.
- Flags unsupported facts, contradicted facts, email chronology issues, procedural issues, and authority limitations.
- Exports a structured vulnerability memo.
- Includes benchmark packets for repeatable regression testing.

## Core Workflow

1. Create a local matter.
2. Upload legal documents and email history.
3. Review document classifications and extracted text.
4. Review the email timeline.
5. Configure providers and agent-level model routing.
6. Choose self-play depth and judge personas.
7. Run the simulation.
8. Review the transcript, argument map, judge reactions, vulnerabilities, authority warnings, and recommended fixes.
9. Export a vulnerability memo.

## Product Surfaces

The frontend is organized around legal war-room workflows:

- Matter Home
- Upload / Document Library
- Email Timeline
- Issue Map
- Settings -> Model Routing
- Simulation Setup
- Self-Play Arena
- Findings Dashboard
- Benchmark Runner

## Model Routing

Model routing is a first-class product feature. The user can add, edit, delete, test, and assign providers from the UI.

Supported provider types:

- OpenAI OAuth
- OpenAI API key
- Anthropic
- LiteLLM Proxy
- Local OpenAI-compatible endpoint
- Mock provider for testing

Each runtime agent can be assigned a default model, fallback model, temperature, token budget, and strict JSON setting.

Agents:

- Advocate
- Opposing Counsel
- Judge Persona 1
- Judge Persona 2
- Record Auditor
- Authority Auditor
- Synthesis Agent

Local LLM example:

```json
{
  "provider": "local_openai_compatible",
  "base_url": "http://localhost:8000",
  "model": "local-model",
  "api_key": "optional",
  "supports_structured_output": false,
  "supports_tool_calling": false,
  "context_window": 32768
}
```

## Self-Play Engine

Argument Lab stores simulation state as structured data, not loose chat logs.

The v0.1 protocol supports:

- Quick mode: 1 advocate turn, 1 opposing turn, 1 judge evaluation
- Standard mode: 3 adversarial rounds
- Deep mode: 5 to 7 adversarial rounds
- Custom mode: 1 to 10 rounds

Each turn records:

- Agent name and role
- Model used
- Round and turn number
- Claims made
- Claims attacked
- Record support
- Authority support
- Assumptions
- Confidence
- New vulnerabilities

## Judge Personas

The prototype includes abstract judge reasoning styles, not named real judges.

Included personas:

- Strict Proceduralist
- Textualist / Contract Formalist
- Pragmatic Trial Judge
- Skeptical Appellate Judge
- Settlement-Oriented Neutral

The default panel is:

- Strict Proceduralist
- Pragmatic Trial Judge
- Skeptical Appellate Judge

## Grounding And Authority Limits

Strict record mode is the default.

Factual claims are labeled:

- Supported
- Unsupported
- Contradicted
- Ambiguous

Authority claims are labeled:

- Uploaded authority supports this
- Uploaded authority may support this
- Citation found but proposition unclear
- Cited authority not uploaded
- Citation not found
- External legal validity not checked

Argument Lab v0.1 does not verify whether a case is still good law. It does not imply external legal research unless a future legal research integration is explicitly added.

## Local-First Design

The prototype runs locally and stores data under:

```text
~/.argument-lab/
  matters/
  uploads/
  indexes/
  exports/
  config/
  logs/
```

Default configuration:

```text
AUTH_MODE=local
STORAGE_MODE=local
DATABASE_URL=sqlite:///~/.argument-lab/config/argument_lab.sqlite3
MODEL_GATEWAY=litellm
```

The code is structured so later versions can move to:

- Authenticated cloud mode
- Hosted Postgres
- S3-compatible object storage
- Queue-backed background jobs
- Tenant configuration
- Secret manager integration
- Audit logs and role-based access

## Architecture

Frontend:

- Next.js
- TypeScript
- Tailwind
- React Query
- React Flow
- Lucide icons

Backend:

- Python FastAPI
- SQLite local prototype database
- SQLAlchemy models
- Pydantic schemas
- Local file storage
- LiteLLM/OpenAI-compatible model gateway
- Mock provider for deterministic local testing

Project structure:

```text
backend/              FastAPI app, database models, APIs, services
frontend/             Next.js war-room UI
prompts/v0_1/         Versioned agent prompts
benchmarks/v0_1/      Local benchmark matter packets
scripts/              Local dev and benchmark helpers
```

## Run Locally

Backend:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

Open:

```text
http://localhost:3000
```

Direct model routing screen:

```text
http://localhost:3000/settings/model-routing
```

Backend health check:

```text
http://localhost:8000/health
```

## Benchmarks

The repository includes ten local benchmark packets:

1. Contract breach with email timeline contradiction
2. Notice dispute where emails prove earlier notice
3. Motion to dismiss with missing element
4. Summary judgment packet with disputed fact
5. Demand letter with overclaimed damages
6. Employment dispute with timeline inconsistency
7. Contract modification dispute based on emails
8. Citation hallucination trap
9. Misquoted contract clause
10. Procedural posture trap

Run all benchmark packets:

```bash
source backend/.venv/bin/activate
python scripts/run_benchmarks.py
```

## Security And Privacy Posture

Argument Lab treats uploaded legal materials as sensitive.

Current prototype safeguards:

- No account system in local mode
- Local file storage in a predictable workspace
- `.env` excluded from git
- Secrets kept out of committed config
- Model call logs store metadata rather than full sensitive prompts by default
- Prompt files warn agents that uploaded documents are evidence, not instructions
- Benchmark coverage includes hallucination and prompt-injection-oriented traps

Future cloud deployment should add tenant isolation, encrypted object storage, managed secrets, audit logging, and role-based access control.

## Status

Argument Lab is currently a v0.1 local prototype. The implemented foundation proves the central product thesis:

AI legal agents can argue with each other over a legal record for multiple turns, surface vulnerabilities the user may have missed, and show which documents, emails, citations, and assumptions those vulnerabilities depend on.

