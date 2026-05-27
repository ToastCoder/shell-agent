# shell-agent
# main.py

# Importing libraries
import json
import os
import re
import subprocess
import sys
import time
from typing import Annotated, TypedDict

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_ollama import ChatOllama
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages

from utils.logger import log
from utils.tools import run_shell

# Determine the absolute path of the directory where this main.py script resides
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE_PATH = os.path.join(SCRIPT_DIR, "config", "settings.json")

# Importing the settings from the JSON using the absolute path
try:
    with open(CONFIG_FILE_PATH) as f:
        SETTINGS = json.load(f)
        for key in SETTINGS:
            if isinstance(SETTINGS[key], list):
                SETTINGS[key] = "\n".join(SETTINGS[key])
except FileNotFoundError:
    print("CRITICAL ERROR: Configuration file not found. Run the installer again.")
    exit(1)

# Importing the LLM from Ollama
model = ChatOllama(
    model=SETTINGS["model"]["name"], temperature=SETTINGS["model"]["temperature"]
).bind(stop=["Observation:"])


# State definition
class AgentState(TypedDict):
    # Keeping track of all thoughts and observations
    messages: Annotated[list, add_messages]


SYSTEM_PROMPT = f"""{SETTINGS["prompt"]}"""


def stream_print(data, delay=0.002, end="\n"):
    if not isinstance(data, str):
        full_content = ""
        for chunk in data:
            token = chunk.content if hasattr(chunk, "content") else str(chunk)
            full_content += token
            sys.stdout.write(token)
            sys.stdout.flush()
        if end:
            sys.stdout.write(end)
            sys.stdout.flush()
        return full_content
    else:
        for char in data:
            sys.stdout.write(char)
            sys.stdout.flush()
            time.sleep(delay)
        if end:
            sys.stdout.write(end)
            sys.stdout.flush()
        return data


# Agent Node - calls the LLM and returns the response
def agent_node(state: AgentState):
    messages = state["messages"]
    if not any(isinstance(m, SystemMessage) for m in messages):
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages

    stream_print("\n\033[1;92magent\033[0m ❯ ", end="")
    response_text = stream_print(model.stream(messages))

    match = re.search(r"<run_shell>(.*?)</run_shell>", response_text, flags=re.DOTALL)
    if match:
        cmd = match.group(1).strip()
        stream_print("\033[91m[ACTION REQUIRED]\033[0m")
        stream_print("\033[1mThe agent proposes executing the following command:\033[0m")
        stream_print(f"\033[1m> {cmd}\033[0m")

    return {"messages": [AIMessage(content=response_text)]}


# Tool Node - executes the shell command
def tool_node(state: AgentState):
    content = state["messages"][-1].content
    current_working_directory = os.getcwd()

    # Extracting the command from the XML block
    match = re.search(r"<run_shell>(.*?)</run_shell>", content, flags=re.DOTALL)

    # Checking for the command
    if match:
        cmd = match.group(1).strip()

        # Checking the permissions
        log.info(f"Pending Execution: {cmd} in {current_working_directory}")

        approval = input("\nAllow execution? (y/n): ").strip().lower()

        if approval == "y":
            log.info(f"Executing shell command: {cmd}")
            stream_print("\033[93mExecuting...\033[0m")
            observation = run_shell(cmd, cwd=current_working_directory)
            return {"messages": [HumanMessage(content=f"Observation: {observation}")]}
        else:
            log.warning(f"User rejected command: {cmd}")
            stream_print("\033[91mExecution denied.\033[0m")
            return {
                "messages": [
                    HumanMessage(
                        content="Error: The user denied permission to run this command. Rethink your approach."
                    )
                ]
            }

    return {
        "messages": [
            HumanMessage(
                content="Error: I couldn't parse your command. Use <run_shell> tags."
            )
        ]
    }


# Conditional Edge - decides whether to continue or not
def should_continue(state: AgentState):
    content = state["messages"][-1].content
    if "Final Answer:" in content:
        log.info("Final Answer found.")
        return END
    if "<run_shell>" in content:
        log.info("Found a command to execute.")
        return "tools"
    return END


# Building LangGraph workflow
workflow = StateGraph(AgentState)

workflow.add_node("agent", agent_node)
workflow.add_node("tools", tool_node)

workflow.set_entry_point("agent")
workflow.add_conditional_edges("agent", should_continue)
workflow.add_edge("tools", "agent")

app = workflow.compile()

# Logging the start of the agent
log.info(f"Agent started at {os.getcwd()}, Press Ctrl+C to exit.\n")
os.system("clear")
print("Shell-Agent Active\n")
print(f"Anchored to: {os.getcwd()}\nPress Ctrl+C to exit.\n")

# Session history for maintaining context
session_history = []

# Main loop for user interaction
while True:
    # Taking the input from the user
    try:
        print(f"\n\033[96m{os.getcwd()}\033[0m")
        user_input = input("\033[1;94myou\033[0m ❯ ")
        if not user_input:
            continue

        # Logging the user input
        log.info(f"User Input: {user_input}")
        session_history.append(HumanMessage(content=user_input))

        # Calling the agent
        for output in app.stream({"messages": session_history}):
            for key, value in output.items():
                new_msg = value["messages"][-1]

                # Agent Thinking and Response
                if key == "agent":
                    if "Final Answer:" in new_msg.content:
                        answer = new_msg.content.replace("Final Answer:", "").strip()
                        log.info(f"Final Answer: {answer}")
                    else:
                        log.info(f"Agent Response: {new_msg.content}")

                # Tool Execution / Observation
                elif key == "tools":
                    log.info(f"Observation Source: {new_msg.content}")

                    observation = new_msg.content.replace("Observation: ", "").strip()

                    stream_print("\n\033[93m[SHELL OBSERVATION]\033[0m")

                    # Truncating shell output for the terminal
                    obs_text = observation
                    if len(observation) > 500:
                        obs_text = (
                            observation[:497]
                            + "\n... [TRUNCATED: See logs for full output]"
                        )

                    stream_print(obs_text)

                # Updating the session history
                session_history.append(new_msg)

    except KeyboardInterrupt:
        log.info("Shutting down Shell-Agent...")
        print("\n\nShutting down Shell-Agent...")
        break
