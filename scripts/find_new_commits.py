"""List new docker/docs commits that touch the pages this course draws on.

Reads the last commit already checked from refresh-state.json, then lists
every later commit on docker/docs that changes a watched path, oldest first.
Writes the list to the GitHub Actions output `commits` (empty when there is
nothing new) and the newest upstream commit to `newest`.

Environment variables:
  UPSTREAM_DIR    path to a clone of docker/docs (default: _upstream)
  GITHUB_OUTPUT   set by GitHub Actions
"""

import json
import os
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPSTREAM = os.environ.get("UPSTREAM_DIR", os.path.join(ROOT, "_upstream"))


def git(*args):
    return subprocess.run(["git", "-C", UPSTREAM, *args], check=True, capture_output=True, text=True).stdout


def main():
    with open(os.path.join(ROOT, "source-map.json"), encoding="utf-8") as f:
        watched = json.load(f)["upstream"]["watched_paths"]
    with open(os.path.join(ROOT, "refresh-state.json"), encoding="utf-8") as f:
        last = json.load(f)["last_checked"]

    head = git("rev-parse", "origin/HEAD").strip()
    commits = git("log", "--reverse", "--format=%H", f"{last}..{head}", "--", *watched).split()

    print(f"Last checked: {last[:10]}. Upstream now at: {head[:10]}.")
    if commits:
        print(f"{len(commits)} new commit(s) touch the course's pages: " + " ".join(c[:10] for c in commits))
    else:
        print("No new commits touch the course's pages. Nothing to review tonight.")

    out = os.environ.get("GITHUB_OUTPUT")
    if out:
        with open(out, "a", encoding="utf-8") as f:
            f.write(f"commits={' '.join(commits)}\n")
            f.write(f"newest={commits[-1] if commits else ''}\n")


if __name__ == "__main__":
    main()
