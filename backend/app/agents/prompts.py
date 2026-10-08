"""Load each agent's instructions from agents/<name>.md (the file is the agent)."""

import re

from app.core.settings import settings

# The first ``` code block after the "## Instructions" heading.
INSTRUCTIONS_BLOCK = re.compile(r"^## Instructions\s*\n+```[a-z]*\n(.*?)\n```", re.M | re.S)
# Everything after the "## Examples" heading (it is the last section of each file).
EXAMPLES_SECTION = re.compile(r"^## Examples\s*\n(.*)\Z", re.M | re.S)


def load_instructions(agent_name: str) -> str:
    """Read on every call, so editing the .md file changes the agent without a restart.

    The system prompt is the Instructions block plus the Examples section ("few-shot" examples).
    A {{GUIDELINES}} marker is replaced with agents/guidelines.md, so the Drafter and the Checker
    always work from the same rules.
    """
    path = settings.agents_dir / f"{agent_name}.md"
    match = INSTRUCTIONS_BLOCK.search(path.read_text(encoding="utf-8"))
    if match is None:
        raise ValueError(f"{path} has no code block under '## Instructions'")
    instructions = match.group(1).strip()
    examples = EXAMPLES_SECTION.search(path.read_text(encoding="utf-8"))
    if examples:
        instructions += "\n\nEXAMPLES (input, then the exact output to return):\n\n"
        instructions += examples.group(1).strip()
    if "{{GUIDELINES}}" in instructions:
        guidelines = (settings.agents_dir / "guidelines.md").read_text(encoding="utf-8").strip()
        instructions = instructions.replace("{{GUIDELINES}}", guidelines)
    return instructions
