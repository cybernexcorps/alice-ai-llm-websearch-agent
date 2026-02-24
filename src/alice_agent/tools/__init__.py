"""Local tools for Alice Agent.

Note: Web search is handled server-side by the Yandex AI Studio Agent Atelier.
The `fetch_webpage` tool here is available as a standalone CLI utility.
"""

from alice_agent.tools.web_fetch import fetch_webpage

__all__ = ["fetch_webpage"]
