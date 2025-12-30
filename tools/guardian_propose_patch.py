#!/usr/bin/env python3
import json
import subprocess
from pathlib import Path
from typing import Any, Dict, Iterable, List

ROOT = Path(__file__).resolve().parents[1]
GENERATED_DIR = ROOT / "generated"
PATCH_DIR = ROOT / "guardian" / "patches"


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


def _load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _list_cases() -> Iterable[Path]:
    if not GENERATED_DIR.exists():
        return []
    return sorted(GENERATED_DIR.glob("*.json"))


def _is_reversible_proposal(case: Dict[str, Any]) -> bool:
    if case.get("policy_gate") != "green":
        return False
    if case.get("recommended_action") != "propose_patch":
        return False
    transition = case.get("proposed_transition") or {}
    return transition.get("reversibility") == "reversible"


def _existing_pr(branch: str) -> bool:
    output = _run(
        [
            "gh",
            "pr",
            "list",
            "--head",
            branch,
            "--state",
            "all",
            "--json",
            "number",
        ],
        check=True,
    )
    return output.strip() not in ("", "[]")


def _remote_branch_exists(branch: str) -> bool:
    output = _run(["git", "ls-remote", "--heads", "origin", branch], check=False)
    return bool(output)


def _configure_git_identity() -> None:
    _run(["git", "config", "user.name", "guardian-bot"], check=True)
    _run(
        ["git", "config", "user.email", "guardian-bot@users.noreply.github.com"],
        check=True,
    )


def _log_repo_context() -> None:
    output = _run(
        [
            "gh",
            "repo",
            "view",
            "--json",
            "nameWithOwner",
            "--jq",
            ".nameWithOwner",
        ],
        check=False,
    )
    if output:
        print(f"gh repo context: {output}")
    else:
        print("gh repo context: unavailable")

    actor = _run(["gh", "api", "user", "--jq", ".login"], check=False)
    if actor:
        print(f"gh actor: {actor}")
    else:
        print("gh actor: unknown")


def _has_staged_changes() -> bool:
    result = subprocess.run(
        ["git", "diff", "--cached", "--quiet"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    return result.returncode != 0


def _checkout_branch(branch: str, base_branch: str) -> None:
    _run(["git", "fetch", "origin", base_branch], check=True)
    _run(["git", "checkout", "-B", branch, f"origin/{base_branch}"], check=True)


def _default_branch() -> str:
    output = _run(
        [
            "gh",
            "repo",
            "view",
            "--json",
            "defaultBranchRef",
            "--jq",
            ".defaultBranchRef.name",
        ],
        check=False,
    )
    return output.strip() or "main"


def _write_patch_stub(case: Dict[str, Any]) -> Path:
    PATCH_DIR.mkdir(parents=True, exist_ok=True)
    case_id = case["id"]
    path = PATCH_DIR / f"{case_id}.md"
    transition = case.get("proposed_transition") or {}
    verification = transition.get("verification") or []
    signals = case.get("signals") or []

    checklist = "\n".join([f"- [ ] {item}" for item in verification])
    signal_lines = "\n".join([f"- {sig.get('signal_id', 'unknown')}" for sig in signals])

    content = (
        f"# Guardian Patch Proposal ({case_id})\n\n"
        f"## Root cause hypothesis\n"
        f"{case.get('root_cause_hypothesis', 'TBD')}\n\n"
        "## Suggested patch steps (generic web perf)\n"
        "1. Audit critical rendering path (hero images, fonts, blocking scripts).\n"
        "2. Defer or async non-critical scripts; ensure bundles are split appropriately.\n"
        "3. Optimize images (proper sizing, modern formats, preload hero assets).\n"
        "4. Reduce server response time (cache headers, CDN, origin optimization).\n\n"
        "## Signals\n"
        f"{signal_lines or '- (none)'}\n\n"
        "## Verification checklist\n"
        f"{checklist or '- [ ] Add verification steps'}\n"
    )

    path.write_text(content, encoding="utf-8")
    return path


def _build_pr_body(case: Dict[str, Any]) -> str:
    transition = case.get("proposed_transition") or {}
    verification = transition.get("verification") or []
    signals = case.get("signals") or []

    checklist = "\n".join([f"- [ ] {item}" for item in verification])
    signal_lines = "\n".join([f"- {sig.get('signal_id', 'unknown')}" for sig in signals])

    return (
        "## Guardian Proposed Patch (green)\n\n"
        f"**Care-Case:** `{case.get('id', 'unknown')}`\n"
        f"**Gate:** `{case.get('policy_gate', 'unknown')}`\n"
        f"**Action:** `{case.get('recommended_action', 'unknown')}`\n"
        f"**Tension:** `{case.get('tension', 'unknown')}`\n\n"
        "### Signals\n"
        f"{signal_lines or '- (none)'}\n\n"
        "### Proposed transition\n"
        f"- intent: {transition.get('intent', 'TBD')}\n"
        f"- scope: {transition.get('scope', 'TBD')}\n"
        f"- reversibility: {transition.get('reversibility', 'TBD')}\n\n"
        "### Verification checklist\n"
        f"{checklist or '- [ ] Add verification steps'}\n"
    )


def _post_pr_metadata(pr_url: str) -> None:
    _run(
        ["gh", "pr", "edit", pr_url, "--add-label", "guardian"],
        check=False,
    )
    _run(["gh", "pr", "edit", pr_url, "--add-label", "bot"], check=False)

    comment = (
        "👮 Guardian PR checklist for reviewer:\n"
        "- Confirm patch file path: guardian/patches/<case_uuid>.md\n"
        "- Confirm sections exist (Root cause / Steps / Verification)\n"
        "- Confirm verification has checkboxes (- [ ])\n"
        "- Confirm proposal stays reversible & scope-limited\n"
    )
    _run(["gh", "pr", "comment", pr_url, "--body", comment], check=False)


def _get_pr_url_by_head(branch: str) -> str:
    url = _run(
        [
            "gh",
            "pr",
            "view",
            "--head",
            branch,
            "--json",
            "url",
            "--jq",
            ".url",
        ],
        check=False,
    ).strip()
    if not url:
        url = _run(
            ["gh", "pr", "view", "--head", branch, "--json", "url", "--jq", ".url"],
            check=False,
        ).strip()
    return url


def main() -> None:
    cases = [p for p in _list_cases()]
    if not cases:
        print("No generated care-cases found.")
        return

    _configure_git_identity()
    _log_repo_context()
    base_branch = _default_branch()

    created_any = False
    for path in cases:
        case = _load_json(path)
        if not _is_reversible_proposal(case):
            continue

        case_id = case["id"]
        branch = f"guardian/{case_id}"

        if _existing_pr(branch):
            print(f"PR already exists for {case_id}, skipping.")
            continue

        if _remote_branch_exists(branch):
            print(f"Remote branch {branch} exists, skipping.")
            continue

        _checkout_branch(branch, base_branch)

        patch_path = _write_patch_stub(case)
        _run(["git", "add", patch_path.as_posix()], check=True)
        if not _has_staged_changes():
            print(f"No changes for {case_id}, skipping commit/PR.")
            _run(
                ["git", "checkout", "-B", base_branch, f"origin/{base_branch}"],
                check=False,
            )
            continue
        _run(
            ["git", "commit", "-m", f"Guardian propose patch for {case_id}"],
            check=True,
        )
        _run(["git", "push", "-u", "origin", branch], check=True)

        pr_title = f"Guardian proposed patch: {case_id}"
        pr_body = _build_pr_body(case)
        _run(
            [
                "gh",
                "pr",
                "create",
                "--title",
                pr_title,
                "--body",
                pr_body,
                "--base",
                base_branch,
                "--head",
                branch,
                "--template",
                "guardian.md",
            ],
            check=True,
        )
        pr_url = _get_pr_url_by_head(branch)
        if pr_url:
            _post_pr_metadata(pr_url)
        else:
            print(
                "Warning: could not resolve PR URL for head branch "
                f"{branch}; skipping labels/comment."
            )

        created_any = True
        _run(
            ["git", "checkout", "-B", base_branch, f"origin/{base_branch}"],
            check=False,
        )

    if not created_any:
        print("No eligible care-cases for patch proposals.")


if __name__ == "__main__":
    main()
