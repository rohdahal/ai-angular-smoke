# AI‑Driven Angular Test Generator (CI‑First)

This repository demonstrates an automated, **CI‑driven approach to enforcing unit‑test coverage** in Angular projects using a local, open‑source LLM.

Instead of blocking developers with failing coverage gates and manual test writing, the pipeline **detects under‑covered files, generates missing tests automatically, validates them, and iterates until coverage thresholds are met**.

No cloud APIs. No SaaS lock‑in. Fully local and reproducible.

---

## What This Project Does

- Enforces **per‑file line and branch coverage thresholds** (default ≥ 90%)
- Detects missing or under‑covered `.spec.ts` files
- Generates Angular unit tests using an **open‑source coding LLM**
- Validates generated tests by compiling and running `ng test`
- Iterates safely until coverage requirements are satisfied
- Designed to run **locally** or inside a **GitHub Actions workflow**

---

## Why This Exists

Many teams want:
- Fast shipping
- Strong test guarantees
- CI pipelines that guide instead of block

This project explores a middle ground:

> Let CI write the tests *only when needed*, and only for files that actually fail coverage.

---

## Key Design Principles

- **Per‑file coverage enforcement** (not global cheating)
- **Standalone‑component safe** (Angular 15+)
- **Strict TypeScript compatible**
- **No hard‑coded app types** (future‑proof)
- **Local inference** using Ollama
- **Deterministic CI behavior**

---

## How It Works

1. Run Angular tests with coverage enabled
2. Parse `coverage/**/lcov.info`
3. Identify under‑covered source files
4. For each file:
   - Generate or update the corresponding `.spec.ts`
   - Auto‑correct common Angular test pitfalls
   - Compile and run tests
5. Repeat until coverage threshold is met or max iterations are reached

---

## Requirements

### Runtime
- Node.js 18+
- Python 3.9+
- Angular CLI (via `npx`)
- Ollama

### Model
Tested with:
- `qwen2.5-coder:7b-instruct`

```bash
ollama pull qwen2.5-coder:7b-instruct
```

---

## Local Usage

```bash
npm ci
ollama serve
python tools/ai_testgen.py --min 90 --max-iters 10
```

Flags:
- `--min` Minimum required per‑file coverage
- `--max-iters` Maximum number of files to fix per run
- `--model` Ollama model tag

---

## CI Usage (GitHub Actions)

Typical workflow steps:

```yaml
- npm ci
- ollama pull qwen2.5-coder:7b-instruct
- python tools/ai_testgen.py --min 90
```

The script exits non‑zero if coverage requirements are not met.

---

## What This Is Not

- Not a replacement for thoughtful test design
- Not a global coverage cheater
- Not a cloud‑hosted AI service
- Not Angular‑specific in concept

---

## Project Status

This is an **engineering proof‑of‑concept** exploring:
- AI‑assisted CI workflows
- Coverage enforcement without developer friction
- Local LLMs in real build pipelines

---

## License

The Unlicense: This software is released into the public domain and may be used, modified, and distributed for any purpose, with or without attribution.
