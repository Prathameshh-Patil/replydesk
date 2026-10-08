"""Load each agent's instructions from agents/<name>.md (the file is the agent)."""

import re

from app.core.settings import settings

# The first ``` code block after the "## Instructions" heading.
INSTRUCTIONS_BLOCK = re.compile(r"^## Instructions\s*\n+```[a-z]*\n(.*?)\n```", re.M | re.S)


def load_instructions(agent_name: str) -> str:
    """Read on every call, so editing the .md file changes the agent without a restart."""
    path = settings.agents_dir / f"{agent_name}.md"
    match = INSTRUCTIONS_BLOCK.search(path.read_text(encoding="utf-8"))
    if match is None:
        raise ValueError(f"{path} has no code block under '## Instructions'")
    return match.group(1).strip()
