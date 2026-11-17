# Change-triage rubric

Use this rubric to decide whether a change to Docker's documentation requires a change to the course. Apply it to one upstream commit at a time.

## A change is material when it does any of these

1. It changes a command, a flag, or an argument that a lesson uses.
2. It changes output that a lesson shows or asks the learner to read.
3. It changes a default, such as what a preset contains or what happens when no rule matches.
4. It changes a prerequisite, such as a required version or setup step.
5. It changes, limits, or contradicts a behavior that a claim in `source-map.json` relies on. A new section counts when it qualifies an existing claim, even if no existing heading changed.

## A change is non-material when it is only any of these

1. A typo, a rewording, or a formatting change that leaves the meaning the same.
2. A changed link or cross-reference.
3. An edit to a section that no claim in `source-map.json` cites, and that qualifies no claim.
4. Content about a feature the course doesn't cover, such as UDP rules, HTTP method and path rules, or organization policy.

## How to decide

1. Read the diff.
2. For each changed passage, look for claims in `source-map.json` whose source is that file and heading, or whose text the passage qualifies.
3. If at least one claim is affected, the change is material. Name each affected lesson section and say what must change.
4. If no claim is affected, the change is non-material. Say which rule above applies.

When in doubt, call the change material. A reviewer can close a pull request faster than a learner can recover from a wrong lesson.
