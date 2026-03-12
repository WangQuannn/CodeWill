import os
import sys
from pathlib import Path


def _env(name: str, default: str = "") -> str:
    raw = os.getenv(name)
    return default if raw is None else raw


def _env_int(name: str, default: int) -> int:
    raw = _env(name, "")
    try:
        return int(raw)
    except ValueError:
        return default


def _env_float(name: str, default: float) -> float:
    raw = _env(name, "")
    try:
        return float(raw)
    except ValueError:
        return default


def main() -> int:
    stage = _env("CODEWILL_STAGE", "").strip().lower()
    if stage not in {"warning", "final"}:
        print("CODEWILL_STAGE must be 'warning' or 'final'", file=sys.stderr)
        return 2

    inactive_days = _env_int("INACTIVE_DAYS", 0)
    warn_days = _env_int("WARN_DAYS", 60)
    kill_days = _env_int("KILL_DAYS", 90)
    fraction = _env_float("EUTHANASIA_FRACTION", 0.25)
    fraction_pct = int(round(max(0.0, min(1.0, fraction)) * 100.0))

    repo = _env("GITHUB_REPOSITORY", "").strip()
    server_url = _env("GITHUB_SERVER_URL", "https://github.com").strip()
    repo_url = f"{server_url}/{repo}" if server_url and repo else (server_url or "https://github.com")

    if stage == "warning":
        title = "⚠️ CodeWill warning"
        message = (
            f"No commits for {inactive_days} days. "
            f"If there are still no commits by {kill_days} days of inactivity, "
            f"CodeWill will delete about {fraction_pct}% of tracked files and push a commit."
        )
        button_text = "Open repository →"
    else:
        title = "🪦 CodeWill has executed the testament"
        message = (
            f"No commits for {inactive_days} days (>= {kill_days}). "
            f"CodeWill has deleted about {fraction_pct}% of tracked files and pushed a commit."
        )
        button_text = "Open repository →"

    template_path = Path(__file__).with_name("email_template.html")
    template = template_path.read_text(encoding="utf-8")

    rendered = (
        template.replace("{{TITLE}}", title)
        .replace("{{REPO}}", repo or "(unknown)")
        .replace("{{REPO_URL}}", repo_url)
        .replace("{{INACTIVE_DAYS}}", str(inactive_days))
        .replace("{{WARN_DAYS}}", str(warn_days))
        .replace("{{KILL_DAYS}}", str(kill_days))
        .replace("{{FRACTION_PCT}}", str(fraction_pct))
        .replace("{{MESSAGE}}", message)
        .replace("{{BUTTON_TEXT}}", button_text)
    )

    output_path = Path(_env("OUTPUT_PATH", "codewill_email.html"))
    output_path.write_text(rendered, encoding="utf-8")
    print(f"Wrote {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

