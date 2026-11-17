# Source snapshot

The course was written against Docker's documentation as it stood at one commit. The pages aren't copied here. They're pinned by commit, so anyone can read the exact text the course relied on.

- Repository: https://github.com/docker/docs
- Snapshot commit: `01932368c8957d8b033a32026da484880a3a1489`, Nov. 4, 2026
- Browse the repository at that commit: https://github.com/docker/docs/tree/01932368c8957d8b033a32026da484880a3a1489/content/manuals/ai/governance

## Pages the course draws on

| Page | At the snapshot commit |
|---|---|
| Local policy overview | https://github.com/docker/docs/blob/01932368c8957d8b033a32026da484880a3a1489/content/manuals/ai/governance/local/_index.md |
| Inspect local policy | https://github.com/docker/docs/blob/01932368c8957d8b033a32026da484880a3a1489/content/manuals/ai/governance/local/inspect.md |
| Manage local network rules | https://github.com/docker/docs/blob/01932368c8957d8b033a32026da484880a3a1489/content/manuals/ai/governance/local/network-rules.md |
| Test and monitor local policy | https://github.com/docker/docs/blob/01932368c8957d8b033a32026da484880a3a1489/content/manuals/ai/governance/local/test-monitor.md |
| Network rule reference | https://github.com/docker/docs/blob/01932368c8957d8b033a32026da484880a3a1489/content/manuals/ai/governance/reference/network-rules.md |

`source-map.json` lists which heading on which page each lesson claim depends on.

## Tested behavior

Where the docs are silent, the course relies on results from a real machine: `sbx` v0.54.0, Windows 11, Command Prompt, Nov. 16, 2026. The raw output is in `captures/`.
