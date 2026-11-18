"""Refresh the course when Docker's documentation changes.

For each upstream commit it is given, this script:
  1. reads the commit's diff, limited to the pages the course draws on
  2. asks Claude to triage the change against the rubric and the source map
  3. for a material change, asks Claude to redraft each affected lesson section
  4. writes a refresh log entry and a pull request description

It never publishes anything. The workflow opens a pull request, and a
subject-matter expert reviews it before it can be merged.

Environment variables:
  COMMITS            upstream commit IDs, oldest first, separated by spaces
  ANTHROPIC_API_KEY  Claude API key
  CLAUDE_MODEL       model ID (optional)
  UPSTREAM_DIR       path to a clone of docker/docs (default: _upstream)
  REFRESH_MOCK       set to 1 to skip the API and use stand-in answers,
                     for testing the plumbing only
  GITHUB_REPOSITORY  owner/repo, set by GitHub Actions (optional, for preview links)
  BRANCH             the pull request's branch (optional, for preview links)
"""

import datetime
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPSTREAM = os.environ.get("UPSTREAM_DIR", os.path.join(ROOT, "_upstream"))
MODEL = os.environ.get("CLAUDE_MODEL") or "claude-opus-5-5"
MOCK = os.environ.get("REFRESH_MOCK") == "1"
MAX_DIFF_CHARS = 60000
TRIAGE_MAX_TOKENS = 4000

LESSON_NOTES = {
    "docs/lesson-1.html": (
        "Lesson 1 is the reasoning lesson. It uses plain language and no commands. "
        "Call the proxy 'the checkpoint'. Say 'blocked', not 'denied', in running text."
    ),
    "docs/lesson-2.html": (
        "Lesson 2 is the hands-on lab. Every command is followed by its real output. "
        "Never invent output. Flag anything that needs a new capture with a draft note."
    ),
}


def read(path):
    with open(os.path.join(ROOT, path), encoding="utf-8") as f:
        return f.read()


def write(path, text):
    full = os.path.join(ROOT, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def git(*args):
    result = subprocess.run(
        ["git", "-C", UPSTREAM, *args], capture_output=True, text=True, check=True
    )
    return result.stdout


def fill(template, values):
    for key, value in values.items():
        template = template.replace("{{" + key + "}}", value)
    return template


def ask_claude(prompt, max_tokens):
    """Send one prompt to the Claude Messages API.

    Returns the reply text and the stop reason. A stop reason of "max_tokens"
    means the reply was cut off before it finished.
    """
    body = json.dumps(
        {
            "model": MODEL,
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}],
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=body,
        headers={
            "x-api-key": os.environ["ANTHROPIC_API_KEY"],
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=600) as response:
            reply = json.load(response)
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", "replace")
        sys.exit(f"The Claude API returned {error.code}: {detail}")
    stop_reason = reply.get("stop_reason", "")
    if stop_reason == "max_tokens":
        print("Warning: the reply was cut off at the token limit.")
    text = "".join(part.get("text", "") for part in reply.get("content", []))
    return text, stop_reason


# --- Stand-in answers, used only when REFRESH_MOCK=1 -------------------------

def mock_triage(diff):
    if "Hostname blocking limitations" in diff:
        return json.dumps(
            {
                "material": True,
                "rule": "material 5 (stand-in answer)",
                "reasoning": "STAND-IN ANSWER FOR TESTING. The diff adds a section that qualifies claim L1-S3-3.",
                "affected": [
                    {
                        "lesson": "docs/lesson-1.html",
                        "section": "s4",
                        "claims": ["L1-S3-3"],
                        "change_needed": "Stand-in: add the limitation.",
                    }
                ],
            }
        )
    return json.dumps(
        {
            "material": False,
            "rule": "non-material 3 (stand-in answer)",
            "reasoning": "STAND-IN ANSWER FOR TESTING. No claim cites the changed passage.",
            "affected": [],
        }
    )


def mock_redraft(section_html):
    revised = section_html.replace(
        "</section>",
        '<p class="note">Draft note: stand-in redraft for testing.</p>\n</section>',
    )
    return (
        f"<replacement>\n{revised}\n</replacement>\n"
        "<summary>Stand-in summary.</summary>\n<new_claims>[]</new_claims>"
    )


# --- Lesson sections ---------------------------------------------------------

def section_pattern(section_id):
    return re.compile(
        r"(<!-- BEGIN section:%s -->\n)(.*?)(\n<!-- END section:%s -->)"
        % (re.escape(section_id), re.escape(section_id)),
        re.S,
    )


def get_section(lesson_path, section_id):
    match = section_pattern(section_id).search(read(lesson_path))
    return match.group(2) if match else None


def put_section(lesson_path, section_id, new_html):
    text = read(lesson_path)
    pattern = section_pattern(section_id)
    write(lesson_path, pattern.sub(lambda m: m.group(1) + new_html + m.group(3), text, count=1))


def check_replacement(section_id, old_html, new_html):
    """Return a reason to reject the draft, or None if it's safe to apply."""
    if not new_html.startswith(f'<section id="{section_id}">'):
        return "it doesn't start with the section's opening tag"
    if not new_html.endswith("</section>"):
        return "it doesn't end with </section>"
    if new_html.count("<section") != 1:
        return "it contains more than one section"
    if "<script" in new_html.lower():
        return "it contains a script"
    if not 0.5 * len(old_html) <= len(new_html) <= 3 * len(old_html):
        return "its length changed by more than the allowed range"
    return None


def parse_json_reply(reply):
    """Read a JSON object from a model reply, or return None.

    Accepts a reply wrapped in a code fence, surrounded by other text, or with
    line breaks inside text values, which strict JSON forbids.
    """
    text = reply.strip()
    fenced = re.search(r"```(?:json)?\s*(.*?)```", text, re.S)
    if fenced:
        text = fenced.group(1)
    start = text.find("{")
    if start == -1:
        return None
    try:
        value, _ = json.JSONDecoder(strict=False).raw_decode(text[start:])
    except ValueError:
        return None
    return value if isinstance(value, dict) else None


def tagged(reply, tag):
    match = re.search(r"<%s>\s*(.*?)\s*</%s>" % (tag, tag), reply, re.S)
    return match.group(1) if match else ""


# --- Main --------------------------------------------------------------------

def triage(commit_meta, diff, rubric, source_map_text):
    prompt = fill(
        read("prompts/triage.md"),
        {
            "RUBRIC": rubric,
            "SOURCE_MAP": source_map_text,
            "COMMIT_META": commit_meta,
            "DIFF": diff,
        },
    )
    if MOCK:
        reply, stop_reason = mock_triage(diff), "end_turn"
    else:
        reply, stop_reason = ask_claude(prompt, TRIAGE_MAX_TOKENS)
    result = parse_json_reply(reply)
    if result is not None:
        return result
    cause = (
        "The reply was cut off at the token limit before it finished."
        if stop_reason == "max_tokens"
        else "The reply wasn't readable as JSON."
    )
    return {
        "material": True,
        "rule": "unreadable reply",
        "reasoning": cause + " This change needs a manual review. The full reply follows.",
        "raw_reply": reply,
        "affected": [],
    }


def redraft(item, commit_meta, diff, rules):
    lesson, section_id = item["lesson"], item["section"]
    old_html = get_section(lesson, section_id)
    if old_html is None:
        return {"status": "skipped", "detail": f"No section {section_id} in {lesson}."}
    prompt = fill(
        read("prompts/redraft.md"),
        {
            "CHANGE_NEEDED": item.get("change_needed", ""),
            "RULES": rules,
            "LESSON_NOTES": LESSON_NOTES.get(lesson, ""),
            "COMMIT_META": commit_meta,
            "DIFF": diff,
            "SECTION_HTML": old_html,
        },
    )
    if MOCK:
        reply = mock_redraft(old_html)
    else:
        reply, stop_reason = ask_claude(prompt, 12000)
        if stop_reason == "max_tokens":
            return {
                "status": "rejected",
                "detail": "The draft was cut off at the token limit, so it wasn't applied. The section is unchanged.",
            }
    new_html = tagged(reply, "replacement")
    problem = check_replacement(section_id, old_html, new_html)
    if problem:
        return {
            "status": "rejected",
            "detail": f"The draft was not applied because {problem}. The section is unchanged.",
        }
    put_section(lesson, section_id, new_html)
    try:
        new_claims = json.loads(tagged(reply, "new_claims") or "[]", strict=False)
    except ValueError:
        new_claims = []
    return {"status": "applied", "detail": tagged(reply, "summary"), "new_claims": new_claims}


def main():
    commits = os.environ.get("COMMITS", "").split()
    if not commits:
        sys.exit("Set COMMITS to one or more docker/docs commit IDs.")
    for commit in commits:
        if not re.fullmatch(r"[0-9a-fA-F]{7,40}", commit):
            sys.exit(f"'{commit}' isn't a commit ID.")
    if not MOCK and not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit("ANTHROPIC_API_KEY isn't set.")

    source_map = json.loads(read("source-map.json"))
    source_map_text = json.dumps(source_map["sections"], indent=1)
    watched = source_map["upstream"]["watched_paths"]
    known = {(s["lesson"], s["section"]) for s in source_map["sections"]}
    repo, branch = os.environ.get("GITHUB_REPOSITORY"), os.environ.get("BRANCH")
    changed_lessons = []
    rubric = read("review/triage-rubric.md")
    rules = read("review/writing-rules.md")

    today = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
    log = [f"# Refresh run, {today}", "", f"Model: `{MODEL}`" + (" (stand-in answers, no API call)" if MOCK else ""), ""]
    material_count = 0

    for commit in commits:
        sha, date, subject = git("show", "-s", "--format=%H%n%ad%n%s", "--date=short", commit).strip().split("\n", 2)
        link = f"https://github.com/{source_map['upstream']['repo']}/commit/{sha}"
        commit_meta = f"Commit {sha}\nDate: {date}\nSubject: {subject}"
        diff = git("show", "--format=", "--unified=3", sha, "--", *watched)
        log += [f"## [`{sha[:10]}`]({link}), {date}", "", f"Upstream subject: {subject}", ""]
        print(f"Reviewing {sha[:10]}: {subject}")

        if not diff.strip():
            log += ["**Decision: non-material.** The commit doesn't touch any page the course draws on. No model call was made.", ""]
            continue
        if len(diff) > MAX_DIFF_CHARS:
            diff = diff[:MAX_DIFF_CHARS] + "\n[diff shortened]"

        result = triage(commit_meta, diff, rubric, source_map_text)
        material = bool(result.get("material"))
        log += [
            f"**Decision: {'material' if material else 'non-material'}.** Rule applied: {result.get('rule', 'not stated')}.",
            "",
            str(result.get("reasoning", "")),
            "",
        ]
        if result.get("raw_reply"):
            log += ["<details><summary>Full reply from Claude</summary>", "", "```", result["raw_reply"], "```", "", "</details>", ""]
        if not material:
            continue
        material_count += 1

        affected = [a for a in result.get("affected", []) if (a.get("lesson"), a.get("section")) in known]
        if not affected:
            log += ["No section could be redrafted automatically. Review this change by hand.", ""]
        for item in affected:
            outcome = redraft(item, commit_meta, diff, rules)
            log += [
                f"### {item['lesson']}, section `{item['section']}`",
                "",
                f"Change needed: {item.get('change_needed', '')}",
                "",
                f"Claims affected: {', '.join(item.get('claims', [])) or 'none listed'}",
                "",
                f"Draft {outcome['status']}. {outcome['detail']}",
                "",
            ]
            if outcome["status"] == "applied":
                if item["lesson"] not in changed_lessons:
                    changed_lessons.append(item["lesson"])
                for section in source_map["sections"]:
                    if (section["lesson"], section["section"]) == (item["lesson"], item["section"]):
                        section.setdefault("revised_for", []).append(sha)
                        for number, claim in enumerate(outcome.get("new_claims", []), 1):
                            section["claims"].append(
                                {
                                    "id": f"{section['claims'][0]['id'].rsplit('-', 1)[0]}-R{sha[:7]}-{number}",
                                    "text": str(claim.get("text", "")),
                                    "source": {
                                        "kind": "docs",
                                        "path": "see upstream commit " + sha,
                                        "heading": str(claim.get("heading", "")),
                                        "added_by": "refresh workflow, pending SME review",
                                    },
                                }
                            )

    write("source-map.json", json.dumps(source_map, indent=2) + "\n")
    short = "-".join(c[:7] for c in commits)
    log_path = f"refresh-log/{today}-{short}.md"
    if changed_lessons:
        log += ["## Preview the changed lessons", ""]
        if repo and branch:
            log += [
                "These links render the lessons from this pull request's branch, using htmlpreview.github.io, a third-party viewer. Compare each with the published version.",
                "",
            ]
            for lesson in changed_lessons:
                url = f"https://github.com/{repo}/blob/{branch}/{lesson}"
                log.append(f"- [{lesson}, as redrafted](https://htmlpreview.github.io/?{url})")
            log.append("")
        else:
            log += ["Download the changed files from the **Files changed** tab and open them in a browser.", ""]
    log += ["---", "", "Review this pull request against `review/sme-checklist.md` before merging."]
    write(log_path, "\n".join(log) + "\n")

    title = (
        f"Refresh: {material_count} material change{'s' if material_count != 1 else ''} in {len(commits)} upstream commit{'s' if len(commits) != 1 else ''}"
    )
    write("_pr-title.txt", title + "\n")
    write("_pr-body.md", "\n".join(review_guide(repo, branch, changed_lessons) + log) + "\n")
    print(title)
    print(f"Log written to {log_path}")

    # Tell the workflow whether a pull request is needed.
    out = os.environ.get("GITHUB_OUTPUT")
    if out:
        with open(out, "a", encoding="utf-8") as f:
            f.write(f"material={material_count}\n")


def review_guide(repo, branch, changed_lessons):
    """The opening of the pull request: everything the SME needs, in order."""
    checklist = f"https://github.com/{repo}/blob/{branch}/review/sme-checklist.md" if repo and branch else "review/sme-checklist.md"
    lines = [
        "## Your review",
        "",
        "Docker changed a documentation page this course draws on. The workflow judged the change material and drafted an update. Nothing is published until you merge this pull request.",
        "",
        "1. **Read why.** The refresh log below explains each decision and links to Docker's original change.",
        "2. **See the changes.** Open the **Files changed** tab to compare the draft with the published lesson, line by line.",
    ]
    if changed_lessons and repo and branch:
        links = ", ".join(
            f"[{lesson.split('/')[-1]}](https://htmlpreview.github.io/?https://github.com/{repo}/blob/{branch}/{lesson})"
            for lesson in changed_lessons
        )
        lines.append(f"3. **Try the lesson.** Open the redrafted version in a browser: {links}.")
    else:
        lines.append("3. **Try the lesson.** Download the changed file from **Files changed** and open it in a browser.")
    lines += [
        f"4. **Check it.** Work through the [SME checklist]({checklist}). Run any new command on your own machine.",
        "5. **Decide.**",
        "   - **Accept:** select **Merge pull request**. GitHub Pages republishes the course within a few minutes.",
        f"   - **Accept with edits:** open the file from **Files changed**, choose **Edit file**, and commit to this branch (`{branch or 'the pull request branch'}`). Then merge.",
        "   - **Reject:** add a comment that says why, then select **Close pull request**. The workflow won't draft this change again.",
        "",
        "---",
        "",
    ]
    return lines


if __name__ == "__main__":
    main()
