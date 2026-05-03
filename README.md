# Shell-Agent

Shell-Agent is an autonomous AI assistant that lives directly in your terminal. Built with **Python, LangGraph, and Ollama**, it moves beyond standard chat UIs by actively executing bash commands to build, modify, and debug files on your local machine.

### Key Features
* **Human-in-the-Loop (HITL):** Strict `y/n` approval gates ensure the agent never executes a command without your permission.
* **Directory Sandboxing:** Custom regex security prevents the agent from navigating into root or sensitive system directories.
* **XML Tool Calling:** Bypasses the brittle nature of JSON/bash escaping, allowing the LLM to write flawless multi-line Python and bash scripts.
* **Silent Logging:** Keeps the terminal UI clean while recording the agent's full thought process and execution trace in the background.
