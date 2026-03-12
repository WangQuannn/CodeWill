# CodeWill — The Code Testament

Your code misses you.

- After `warn_days` with no commits: send a warning email.
- After `kill_days` with no commits: delete a fraction of tracked files, push a commit, and send a final email.

## Setup

1) Create `.github/workflows/codewill.yml` in your repo:

```yaml
name: CodeWill

on:
  schedule:
    - cron: "0 0 * * *"
  workflow_dispatch:

jobs:
  codewill:
    uses: WangQuannn/CodeWill/.github/workflows/codewill.yml@main
    secrets: inherit
    with:
      warn_days: "60"
      kill_days: "90"
      euthanasia_fraction: "0.1"
```

2) Add secrets (repo → `Settings → Secrets and variables → Actions → Secrets`):

- `SMTP_HOST` (required)
- `SMTP_USER` (required)
- `SMTP_PASS` (required)

## Safety
- This workflow can delete files and push a commit. Use only in a controlled repo.
- Warning/final emails are sent to contributor emails collected from git history (excluding `noreply`).
- `euthanasia_fraction` can be set to `"1"` to delete everything except excluded paths.
