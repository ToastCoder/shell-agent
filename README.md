# Shell-Agent: The Autonomous CLI Agent

Shell-Agent is a sophisticated, autonomous AI assistant that lives directly in your terminal. Built with **Python, LangGraph, and Ollama**, it moves beyond standard chat UIs by actively executing bash commands to build, modify, and debug files on your local machine.

---

## Key Features
*   **Human-in-the-Loop (HITL):** Strict `y/n` approval gates ensure the agent never executes a command without explicit user permission, maintaining safety and control.
*   **Directory Sandboxing:** The agent is restricted to a secure workspace, preventing navigation into root or sensitive system directories.
*   **Context Awareness:** The agent always tracks the current working directory (`cwd`), ensuring all executed commands operate in the correct scope.
*   **Self-Contained Deployment:** All files are installed in a dedicated, isolated location (`~/.local/share/shell-agent`), ensuring portability and stability.

---

## Installation (One Command Deployment)
This single command handles the entire process: cloning the repository, copying all files, and configuring the system path.

### Prerequisites
Before running the installer, ensure the following are installed on your machine:
1.  **Python 3:** A modern Python 3 installation (3.9+ recommended).
2.  **Ollama:** The Ollama service must be running, and the specified model must be pulled locally.
3.  **Shell Access:** You must have permissions to modify your shell profile (`~/.zshrc` or `~/.bashrc`).

### The Single-Command Setup
You must execute the following command. It uses `curl` to fetch and execute the `install.sh` script from the raw GitHub URL.

```bash
curl -sL https://raw.githubusercontent.com/ToastCoder/shell-agent/refs/heads/master/install.sh | bash
```

### Running the Agent
After the installation script completes, it will prompt you to source your shell profile (e.g., `source ~/.zshrc`). Once done, you can run the agent from *any* terminal directory simply by typing:
```bash
shell-agent
```

---

## Configuration and Customization
All agent behavior is managed via the `config/settings.json` file.

### Default Configuration
The agent defaults to using the `gemma4` model via Ollama.

**Current Settings (Live in `config/settings.json`):**
```json
{
  "model": {
    "name": "gemma4",
    "temperature": 0
  },
  "prompt": [
    "You are Shell-Agent. Your BASE_DIR is {BASE_DIR}.",
    "To run a shell command, you MUST use this exact XML format:",
    "<run_shell>",
    "your command here",
    "</run_shell>",
    "",
    "RULES:",
    "1. After writing the <run_shell> block, STOP and wait for the Observation.",
    "2. Once you have the information you need, or if you have completed the task, you MUST exit by writing: Final Answer: [your response to the user]"
  ]
}
```

### How to Change Models or Parameters
To modify settings, you must edit the `config/settings.json` file located within the installed directory (`~/.local/share/shell-agent/config/settings.json`).

*   **Example: Switching to Llama 3.2:**
  ```json
    {
  "model": {
    "name": "llama3.2",
    "temperature": 0
  },
  "prompt": [
    "You are Shell-Agent. Your BASE_DIR is {BASE_DIR}.",
    "To run a shell command, you MUST use this exact XML format:",
    "<run_shell>",
    "your command here",
    "</run_shell>",
    "",
    "RULES:",
    "1. After writing the <run_shell> block, STOP and wait for the Observation.",
    "2. Once you have the information you need, or if you have completed the task, you MUST exit by writing: Final Answer: [your response to the user]"
  ]
}
```
