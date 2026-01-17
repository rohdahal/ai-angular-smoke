#!/usr/bin/env python3

from __future__ import annotations

import argparse
import ast
import subprocess
import textwrap
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional


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


def run_ng_test_quick() -> None:
    # Faster validation run (still compiles and executes tests).
    run(["npx", "ng", "test", "--watch=false"])


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

    import re

    # Best-effort extraction of the exported class name.
    m = re.search(r"export\s+class\s+(\w+)", src)
    class_name = m.group(1) if m else src_path.stem

    # Heuristic: standalone components typically have `imports:` in @Component metadata.
    is_standalone = "@Component" in src and "imports:" in src

    # Collect app-local type names declared in the source file.
    # These names are often not importable from the spec file, so tests should avoid referencing them.
    local_type_names = set(re.findall(r"^\s*(?:export\s+)?type\s+(\w+)\s*=", src, flags=re.M))
    local_type_names |= set(re.findall(r"^\s*(?:export\s+)?interface\s+(\w+)\s*\{", src, flags=re.M))
    local_type_names |= set(re.findall(r"^\s*(?:export\s+)?enum\s+(\w+)\s*\{", src, flags=re.M))

    forbidden_type_names_line = "None" if not local_type_names else ", ".join(sorted(local_type_names))

    system_rules = (
        "You are a senior Angular engineer. "
        "Return ONE complete TypeScript spec file content ONLY. "
        "No markdown, no code fences, no explanations, no diff format, no extra text. "
        "Do not wrap the output in quotes. Do not return JSON. "
        "The first non-empty line MUST be an ES import (start with: import ). "
        "Use Jasmine syntax (describe/it/expect) and Angular TestBed. Do NOT use Jest-only APIs. "
        "Include all required imports (Angular testing utilities and the target under test). "
        "CRITICAL: Do NOT use TestBed 'declarations' at all. Use TestBed 'imports' instead. "
        "If the target is a standalone component, you MUST configure TestBed with imports: [TargetComponent] and create it with TestBed.createComponent(TargetComponent). "
        "Never declare standalone components in any NgModule/TestBed. "
        "Do NOT reference app-local types by name (types/interfaces/enums declared in the SOURCE FILE). "
        "Avoid explicit annotations or casts to those names (no ': LocalType', no 'as LocalType'). "
        "Do NOT use index-signature objects like { [key: string]: any } or Record<string, any>. "
        "When you need test data, derive it from the component instance (e.g., const x = component.someArray[0];) and clone with spread ({...x, field: ...})."
    )

    base_prompt = f"""
SYSTEM:
{system_rules}

CONTEXT:
We enforce >= {min_pct:.0f}% line AND branch coverage per file.
Current: lines={line_pct:.2f}%, branches={branch_pct:.2f}%.
Target class name: {class_name}
Standalone component: {str(is_standalone)}
Forbidden local type names (do not write these identifiers anywhere in the spec): {forbidden_type_names_line}

SOURCE FILE ({src_path.as_posix()}):
{src}

CURRENT SPEC ({spec_path.as_posix()}):
{spec}

TASK:
Return the COMPLETE updated spec file for {spec_path.name}.
"""

    original_spec = spec

    last_error: Optional[str] = None

    for attempt in range(1, 4):
        prompt = base_prompt
        if last_error:
            prompt += f"""

REPAIR INSTRUCTIONS:
The previous output caused the Angular compiler/test run to fail.
Fix the spec so it compiles and tests run.
Remove any invented typed objects and instead use existing component instance data (e.g., component.someArray[0]) and clone via spread.
Avoid index signatures and avoid referencing non-exported app types.

ERROR:
{last_error}
"""
        out = run_ollama(model, prompt).strip()

        # If the model returned the entire file as a single quoted string, unquote it.
        if out and out[0] in ("'", '"') and out[-1] == out[0]:
            try:
                unquoted = ast.literal_eval(out)
                if isinstance(unquoted, str):
                    candidate = unquoted.strip()
                    if "describe(" in candidate or "import " in candidate:
                        out = candidate
            except Exception:
                pass

        # Normalize indentation and strip BOM/zero-width chars.
        out = out.lstrip("\ufeff\u200b\u200c\u200d")
        out = textwrap.dedent(out).rstrip() + "\n"

        # Auto-fix common mistake: using `declarations` instead of `imports`.
        # This avoids the frequent standalone-component error in Angular 15+.
        if "configureTestingModule" in out and "declarations" in out:
            out = re.sub(r"\bdeclarations\b\s*:", "imports:", out)

        # Auto-strip references to app-local type names (often not importable in spec).
        # This keeps the generated spec compiling even if the model adds annotations/casts.
        for tname in sorted(local_type_names, key=len, reverse=True):
            if tname == class_name:
                continue
            # Remove type annotations like `const x: Type = ...` or function returns `): Type`.
            out = re.sub(rf":\s*{re.escape(tname)}\b", "", out)
            # Remove casts like `as Type`.
            out = re.sub(rf"\s+as\s+{re.escape(tname)}\b", "", out)
            # Remove generic usages like `<Type>`.
            out = re.sub(rf"<\s*{re.escape(tname)}\s*>", "", out)

        # Reject markdown fences or commentary.
        if "```" in out or out.lstrip().lower().startswith("here") or "markdown" in out.lower():
            last_error = "Output contained markdown/commentary."
            continue

        # Must look like an Angular Jasmine spec.
        if "describe(" not in out or "it(" not in out or "expect(" not in out:
            last_error = "Output missing describe/it/expect."
            continue

        # Strong signal that TestBed is used.
        if "TestBed" not in out:
            last_error = "Output missing TestBed."
            continue

        # Reject patterns that commonly cause strict TS failures (TS2345/TS4111).
        bad_patterns = [
            "{ [key: string]: any }",
            "[key: string]: any",
            "Record<string, any>",
            "as Record",
        ]
        if any(pat in out for pat in bad_patterns):
            last_error = "Output used forbidden loose typing; derive data from the component instance and clone via spread instead."
            continue

        # (Removed: validation block for referencing local types, now auto-stripped above.)

        # Must not begin with a quote.
        if out.lstrip().startswith(("'", '"')):
            last_error = "Output started with a quote (string literal)."
            continue

        # Must start like a real TS file.
        first = out.lstrip()
        if not first.startswith("import "):
            last_error = "First non-empty line was not an import statement."
            continue

        # Reject any remaining TestBed/module declarations usage.
        if "declarations" in out:
            last_error = "Output still used TestBed declarations. Use imports only (especially for standalone components)."
            continue

        # If the target is standalone, ensure it is included in TestBed imports array.
        if is_standalone:
            m_imports = re.search(r"configureTestingModule\(\s*\{[\s\S]*?imports\s*:\s*\[([^\]]*)\]", out)
            imports_blob = m_imports.group(1) if m_imports else ""
            if class_name not in imports_blob:
                last_error = (
                    f"Standalone target component '{class_name}' must be in TestBed imports array. "
                    "Use: imports: [TargetComponent]"
                )
                continue

        if is_standalone and ("createComponent(" in out) and (class_name not in out.split("createComponent(", 1)[1]):
            last_error = f"Spec attempted to create a different component than the target '{class_name}'."
            continue

        # Write candidate spec, validate compilation by running tests quickly.
        spec_path.parent.mkdir(parents=True, exist_ok=True)
        spec_path.write_text(out, encoding="utf-8")

        try:
            run_ng_test_quick()
            return
        except Exception as e:
            # Capture the error, revert the spec, and retry with error context.
            last_error = str(e)
            spec_path.write_text(original_spec, encoding="utf-8")
            continue

    raise RuntimeError(f"Failed to generate a compiling spec after 3 attempts. Last error:\n{last_error}")


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