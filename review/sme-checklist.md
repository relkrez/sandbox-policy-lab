# SME review checklist

A subject-matter expert uses this checklist to review every pull request the refresh workflow opens. Nothing is published without this review.

## The triage decision

- [ ] I read the upstream diff myself, not only the summary.
- [ ] I agree with the material or non-material decision for each commit.
- [ ] For a non-material decision, I checked that no lesson claim depends on the changed passage.

## Technical accuracy

- [ ] Every new or changed claim cites a docs heading or a tested result in `source-map.json`.
- [ ] I ran every new or changed command on the pinned `sbx` version, and the output shown matches what I saw.
- [ ] No statement goes beyond what the source says. If the docs describe one case, the lesson doesn't generalize it.

## Instructional design

- [ ] Each changed section's heading still states its takeaway as a sentence, and the body is evidence for it.
- [ ] The exercise at the end of each changed section still tests that section's heading.
- [ ] Only the affected sections changed. The scenario, the story, and unaffected sections are untouched.
- [ ] Lesson 1 still uses plain language and no commands. Lesson 2 still shows real output under every command.

## Writing

- [ ] The text follows `review/writing-rules.md`.
- [ ] Nothing blames the learner or a character for a mistake.

## Before merging

- [ ] I opened the changed lesson in a browser and tried each changed exercise.
- [ ] The refresh log entry in this pull request describes what changed and why.
