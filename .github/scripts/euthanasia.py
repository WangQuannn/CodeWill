import os
import random
import subprocess
from typing import List, Optional


EXCLUDED_PREFIXES = (
    ".github",
)


def _truthy(value: Optional[str]) -> bool:
    if value is None:
        return False
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def _env_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def _git_output(args: List[str]) -> str:
    return subprocess.check_output(
        ["git", *args],
        text=True,
        encoding="utf-8",
        errors="replace",
    ).strip()


def _git_run(args: List[str], *, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], check=check)


def _ensure_git_identity() -> None:
    name = os.getenv("GIT_USER_NAME", "github-actions[bot]")
    email = os.getenv("GIT_USER_EMAIL", "github-actions[bot]@users.noreply.github.com")
    _git_run(["config", "user.name", name], check=True)
    _git_run(["config", "user.email", email], check=True)


def _ensure_on_branch(target_branch: str) -> None:
    current = _git_output(["rev-parse", "--abbrev-ref", "HEAD"])
    if current != "HEAD":
        return

    _git_run(["checkout", "-B", target_branch], check=True)


def _get_tracked_files() -> List[str]:
    raw = subprocess.check_output(["git", "ls-files", "-z"], text=True, encoding="utf-8", errors="replace")
    files = [f for f in raw.split("\0") if f]

    kept: List[str] = []
    for f in files:
        if f.startswith(EXCLUDED_PREFIXES):
            continue
        kept.append(f)
    return kept


def main() -> int:
    files = _get_tracked_files()
    if not files:
        print("✅ No files to euthanize.")
        return 0

    fraction = _env_float("EUTHANASIA_FRACTION", 0.25)
    fraction = min(max(fraction, 0.0), 1.0)

    seed = os.getenv("RANDOM_SEED")
    if seed:
        random.seed(seed)

    kill_count = max(1, int(len(files) * fraction))
    to_kill = sorted(random.sample(files, min(kill_count, len(files))))

    if _truthy(os.getenv("DRY_RUN")):
        print("DRY_RUN=1, would delete:")
        for f in to_kill:
            print(f"- {f}")
        return 0

    target_branch = os.getenv("TARGET_BRANCH") or os.getenv("GITHUB_REF_NAME") or "main"

    _ensure_git_identity()
    _ensure_on_branch(target_branch)

    for f in to_kill:
        _git_run(["rm", "-f", "--", f], check=True)

    staged = subprocess.run(["git", "diff", "--cached", "--quiet"]).returncode != 0
    if not staged:
        print("✅ Nothing staged after deletions; exiting.")
        return 0

    _git_run(["commit", "-m", "🪦 CodeWill: code dignity has expired — euthanasia executed"], check=True)
    _git_run(["push", "origin", f"HEAD:{target_branch}"], check=True)

    print(f"✅ Euthanasia complete: removed {len(to_kill)} files and pushed to {target_branch}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
