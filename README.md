# sandbox-policy-lab
# Harden a local sandbox policy

Draft README. Rewrite it in your own words before the repository is shared.

A sample course on Docker Sandboxes network policy, with a workflow that keeps it current when Docker's documentation changes. This is an independent sample and isn't affiliated with or endorsed by Docker.

## What's here

| Path | What it is |
|---|---|
| `docs/` | The published course: an index page, two lessons, and the check script. GitHub Pages serves this folder |
| `source-map.json` | Every claim the lessons make, traced to a docs heading or a tested result |
| `sources/SNAPSHOT.md` | The commit of Docker's docs the course was written against |
| `captures/` | Raw command output from the machine the course was tested on |
| `review/` | The change-triage rubric, the SME review checklist, and the writing rules |
| `prompts/` | The two prompts the workflow sends to Claude |
| `scripts/refresh.py` | The script that triages a docs change and redrafts the affected sections |
| `.github/workflows/refresh.yml` | The workflow that runs the script and opens a pull request |
| `refresh-log/` | One entry for each workflow run |
| `benchmark/` | The human-directed version of Lesson 1, kept for comparison with the workflow's draft |

## How the course was made

The first drafts were written with Claude in conversation, directed and tested by a subject-matter expert. Testing on a real machine caught an error in the first draft, which is the reason every claim now cites a source.

## How the course stays current

1. Someone runs the workflow and gives it one or more commits from `docker/docs`.
2. For each commit, Claude reads the diff, applies `review/triage-rubric.md` against `source-map.json`, and decides whether the change is material.
3. For a material change, Claude redrafts only the affected lesson sections.
4. The workflow opens a pull request with the reasoning and the draft.
5. A subject-matter expert reviews it against `review/sme-checklist.md`. Nothing is published without that approval.
6. When the pull request is merged, GitHub Pages republishes the course.

The workflow processes public documentation only. No learner data is sent to the model.
