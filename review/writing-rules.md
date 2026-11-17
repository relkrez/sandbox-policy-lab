# Writing rules for the course

These rules apply to every lesson. They combine Docker's public documentation style guide with the course's own instructional design choices.

Docker's guide: https://github.com/docker/docs/blob/main/STYLE.md

## Voice

- Write as though a friend is frustrated at work and needs help. Fix the problem first, explain second.
- Address the learner as "you". Use contractions.
- Use US English and the present tense.
- Don't blame the learner or a character. People in examples make reasonable choices.

## Words and punctuation

- Don't use "simply", "just", "easily", "please", or "note that".
- Don't use exclamation marks, semicolons, or parentheses in lesson text.
- Spell out the numbers one through nine. Use numerals for 10 and above, and for versions, ports, and counts shown in output.
- Use the serial comma.
- Use bold only for UI elements. Put commands, flags, hosts, and rule IDs in code formatting.

## Structure

- Each section follows the assertion-evidence pattern. The heading is a full sentence that states the takeaway. The body is evidence for it. An exercise at the end tests it.
- Section headings are sentences on purpose. This is the one place the course departs from Docker's eight-word heading limit.
- Lesson 1 uses plain language and no commands. Say "the checkpoint" for the proxy.
- Lesson 2 shows the real command output under every command.
- State what always happens, then what the product doesn't control, then what to do.
