# Installing DailyReport for Codex

Codex currently discovers DailyReport through native skill discovery. Install the skill and use it through natural-language requests or explicit skill naming.

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/nedhuohuo/DailyReport.git ~/.codex/daily-report
   ```

2. Symlink the skill into the Codex skills directory:
   ```bash
   mkdir -p ~/.agents/skills
   ln -s ~/.codex/daily-report/skills/daily-report ~/.agents/skills/daily-report
   ```

3. Restart Codex.

## What to expect

- Codex should discover the `daily-report` skill from `~/.agents/skills`.
- You can trigger it by saying things like `generate today's daily report` or `initialize DailyReport`.
- This repository also includes plugin command manifests for plugin-based tools such as Claude Code. Codex support is currently skill-based; slash-command menu support is not guaranteed.

## Verify

```bash
ls -la ~/.agents/skills/daily-report
```

The symlink should point to:

```text
~/.codex/daily-report/skills/daily-report
```
