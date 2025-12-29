#!/usr/bin/env python3
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple

ROOT = Path(__file__).resolve().parents[1]

PATCH_RE = re.compile(r"^guardian/patches/([0-9a-fA-F-]{36})\.md$")
BRANCH_RE = re.compile(r"^guardian/[0-9a-fA-F-]{36}$")


def _run(cmd: List[str], check: bool = True) -> str:
    result = subprocess.run(
        cmd,
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if check and result.returncode != 0:
        raise SystemExit(
            f"Command failed ({' '.join(cmd)}):\n{result.stdout}\n{result.stderr}"
        )
    return result.stdout.strip()


def _env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise SystemExit(f"Missing required env var: {name}")
    return value


def _changed_files(base: str, head: str) -> List[str]:
    output = _run(["bash", "-lc", f"git diff --name-only {base} {head}"], check=True)
    return [line.strip() for line in output.splitlines() if line.strip()]


def _read_text(rel_path: str) -> str:
    path = ROOT / rel_path
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


def _is_guardian_branch(branch: str) -> bool:
    return branch.startswith("guardian/")

def _enforce_branch_format(branch: str) -> None:
    if not BRANCH_RE.match(branch):
        raise SystemExit(
            f"Guardian PR branch must match 'guardian/<case_uuid>'. Got: {branch}"
        )


def _enforce_only_patch_files(files: List[str]) -> None:
    bad = [file_path for file_path in files if not file_path.startswith("guardian/patches/")]
    if bad:
        raise SystemExit(
            "Guardian PR must only modify files under guardian/patches/. Offenders: "
            + ", ".join(bad)
        )


def _validate_patch_markdown(path: str, case_id: str) -> List[str]:
    errors: List[str] = []
    content = _read_text(path)
    if not content:
        errors.append(f"{path}: file missing or unreadable")
        return errors

    required_sections = [
        "# Guardian Patch Proposal",
        "## Root cause hypothesis",
        "## Suggested patch steps",
        "## Verification checklist",
    ]
    for needle in required_sections:
        if needle not in content:
            errors.append(f"{path}: missing section marker: {needle}")

    if case_id.lower() not in content.lower():
        errors.append(f"{path}: does not mention case id {case_id}")

    if "- [ ]" not in content:
        errors.append(f"{path}: verification checklist has no checkboxes ('- [ ] ...')")

    return errors


def main() -> None:
    base = _env("BASE_SHA")
    head = _env("HEAD_SHA")
    branch = _env("PR_HEAD_REF")

    if not _is_guardian_branch(branch):
        print(f"Not a guardian PR branch ({branch}); skipping guardian validation.")
        return

    _enforce_branch_format(branch)

    files = _changed_files(base, head)
    _enforce_only_patch_files(files)
    patch_files: List[Tuple[str, str]] = []

    for file_path in files:
        match = PATCH_RE.match(file_path)
        if match:
            patch_files.append((file_path, match.group(1)))

    if not patch_files:
        raise SystemExit(
            "Guardian PR must include at least one patch file under guardian/patches/<case_id>.md"
        )

    errors: List[str] = []
    for path, case_id in patch_files:
        errors.extend(_validate_patch_markdown(path, case_id))

    if errors:
        print("Guardian validation failed:")
        for error in errors:
            print(f"- {error}")
        sys.exit(1)

    patch_list = ", ".join([path for path, _ in patch_files])
    print(f"Guardian validation OK. Patch files: {patch_list}")


if __name__ == "__main__":
    main()
