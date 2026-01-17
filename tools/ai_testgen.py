

#!/usr/bin/env python3

from __future__ import annotations

import argparse
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple


@dataclass
class CoverageEntry:
    path: str
    lh: int
    lf: int
    brh: int
    brf: int

    @property
    def line_pct(self) -> float:
        return (self.lh / self.lf * 100.0) if self.lf else 100.0

    @property
    def branch_pct(self) -> float:
        return (self.brh / self.brf * 100.0) if self.brf else 100.0


def run(cmd: List[str]) -> None:
    proc = subprocess.run(cmd, text=True, capture_output=True)
    if proc.returncode != 0:
        raise RuntimeError(
            f"Command failed: {' '.join(cmd)}\n\nSTDOUT:\n{proc.stdout}\n\nSTDERR:\n{proc.stderr}"
        )


def run_ng_test_with_coverage() -> None:
    # Use npx to avoid requiring global Angular CLI.
    run(["npx", "ng", "test", "--watch=false", "--code-coverage"])


def find_lcov() -> Path:
    # Angular writes coverage under coverage/<projectName>/lcov.info
    matches = list(Path("coverage").glob("**/lcov.info"))
    if not matches:
        raise FileNotFoundError("Could not find coverage/**/lcov.info. Did ng test --code-coverage run?")
    # Prefer the deepest match (coverage/<name>/lcov.info)
    matches.sort(key=lambda p: len(p.parts), reverse=True)
    return matches[0]


def parse_lcov(lcov_path: Path) -> Dict[str, CoverageEntry]:
    # Minimal lcov parser for SF/LH/LF/BRH/BRF.
    data: Dict[str, CoverageEntry] = {}

    sf: Optional[str] = None
    lh: Optional[int] = None
    lf: Optional[int] = None
    brh: Optional[int] = None
    brf: Optional[int] = None

    for raw in lcov_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if line.startswith("SF:"):
            sf = line[3:].strip()
            lh = lf = brh = brf = None
        elif line.startswith("LH:"):
            lh = int(line[3:].strip())
        elif line.startswith("LF:"):
            lf = int(line[3:].strip())
        elif line.startswith("BRH:"):
            brh = int(line[4:].strip())
        elif line.startswith("BRF:"):
            brf = int(line[4:].strip())
        elif line == "end_of_record":
            if sf is not None and lh is not None and lf is not None:
                data[sf] = CoverageEntry(
                    path=sf,
                    lh=lh,
                    lf=lf,
                    brh=brh or 0,
                    brf=brf or 0,
                )
            sf = None

    return data


def undercovered_files(cov: Dict[str, CoverageEntry], min_pct: float) -> List[CoverageEntry]:
    out: List[CoverageEntry] = []
    for entry in cov.values():
        # Only your source code
        if not entry.path.startswith("src/"):
            continue
        if entry.path.endswith(".spec.ts"):
            continue
        # Skip boilerplate/config
        if entry.path.endswith(("/main.ts", "/test.ts")):
            continue
        if entry.line_pct < min_pct or entry.branch_pct < min_pct:
            out.append(entry)

    # Lowest coverage first
    out.sort(key=lambda e: (e.line_pct, e.branch_pct))
    return out


def run_ollama(model: str, prompt: str) -> str:
    proc = subprocess.run(
        ["ollama", "run", model],
        input=prompt,
        text=True,
        capture_output=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"Ollama failed:\n{proc.stderr}")
    return proc.stdout.strip()


def generate_or_update_spec(model: str, src_path: Path, spec_path: Path, min_pct: float, line_pct: float, branch_pct: float) -> None:
    src = src_path.read_text(encoding="utf-8")
    spec = spec_path.read_text(encoding="utf-8") if spec_path.exists() else ""

    system_rules = (
        "You are a senior Angular engineer. "
        "Output ONLY TypeScript code (no markdown). "
        "Do NOT delete existing tests; only add/adjust minimal tests to raise coverage. "
        "Use Angular TestBed; for standalone components prefer imports: [Component]. "
        "Add at least one DOM assertion when a template exists. "
        "Keep changes small and focused."
    )

    prompt = f"""
SYSTEM:
{system_rules}

CONTEXT:
We enforce >= {min_pct:.0f}% line AND branch coverage per file.
Current: lines={line_pct:.2f}%, branches={branch_pct:.2f}%.

SOURCE FILE ({src_path.as_posix()}):
{src}

CURRENT SPEC ({spec_path.as_posix()}):
{spec}

TASK:
Return the COMPLETE updated spec file for {spec_path.name}.
"""

    out = run_ollama(model, prompt)

    # Guardrails: must look like a Jasmine spec.
    if "describe(" not in out or "it(" not in out:
        raise RuntimeError("LLM output did not look like a Jasmine spec (missing describe/it).")

    spec_path.parent.mkdir(parents=True, exist_ok=True)
    spec_path.write_text(out.rstrip() + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description="Iteratively generate/update Angular unit tests to meet per-file coverage.")
    ap.add_argument("--min", type=float, default=90.0, help="Minimum required percentage for lines and branches.")
    ap.add_argument("--max-iters", type=int, default=10, help="Maximum iterations (one file fixed per iteration).")
    ap.add_argument("--model", default="qwen2.5-coder:7b-instruct", help="Ollama model tag.")
    args = ap.parse_args()

    min_pct = args.min

    for i in range(1, args.max_iters + 1):
        print(f"\n=== Iteration {i}/{args.max_iters} ===")
        run_ng_test_with_coverage()

        lcov = find_lcov()
        cov = parse_lcov(lcov)
        targets = undercovered_files(cov, min_pct)

        if not targets:
            print(f"OK: all files meet >= {min_pct:.0f}% lines and branches")
            return 0

        t = targets[0]
        src_path = Path(t.path)
        spec_path = src_path.with_suffix(".spec.ts")

        print(
            f"Target: {t.path} | lines {t.lh}/{t.lf} ({t.line_pct:.2f}%) | "
            f"branches {t.brh}/{t.brf} ({t.branch_pct:.2f}%)"
        )

        if not src_path.exists():
            print(f"Skip: source not found on disk: {src_path}")
            # Remove it from consideration by continuing (next iteration re-evaluates)
            continue

        generate_or_update_spec(
            model=args.model,
            src_path=src_path,
            spec_path=spec_path,
            min_pct=min_pct,
            line_pct=t.line_pct,
            branch_pct=t.branch_pct,
        )
        print(f"Updated: {spec_path}")

    # Final check after exhausting iterations
    try:
        run_ng_test_with_coverage()
        lcov = find_lcov()
        cov = parse_lcov(lcov)
        targets = undercovered_files(cov, min_pct)
        if not targets:
            print(f"OK: all files meet >= {min_pct:.0f}% lines and branches")
            return 0
        print(f"Still under-covered after max iterations ({args.max_iters}):")
        for t in targets[:10]:
            print(f"- {t.path}: lines {t.line_pct:.2f}%, branches {t.branch_pct:.2f}%")
        return 2
    except Exception as e:
        print(str(e))
        return 3


if __name__ == "__main__":
    raise SystemExit(main())