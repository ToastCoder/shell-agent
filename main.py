# Required Libs
import subprocess
import os
import re
from typing import Annotated, TypedDict
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage

# Config & State
BASE_DIR = os.getcwd()
# Set temperature to 0 for deterministic (predictable) behavior
model = ChatOllama(model="gemma4", temperature=0).bind(stop=["Observation:"])

# State definition
class AgentState(TypedDict):

    # Keeps track of all thoughts and observations
    messages: Annotated[list, add_messages]

# Running the shell with sandboxing from outer directories
def run_shell(command: str):
    """Executes a shell command within BASE_DIR and returns output."""
    
    # Sandbox check: Block directory climbing or absolute paths
    forbidden = ["..", " /", "~", "$HOME"]

    # Checking if any forbidden string is present in the command
    if any(p in command for p in forbidden):
        return "Error: Access denied. You cannot leave the current project directory."

    print(f"  [Executing]: {command}")

    # Running the command
    try:
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True, timeout=5, cwd=BASE_DIR
        )
        return f"Output: {result.stdout}\nError: {result.stderr}"
    except Exception as e:
        return str(e)

# Define the Node
def agent_node(state: AgentState):
    """The LLM decides what to do."""

    # Updating the messages with new system prompt if not already added
    messages = state['messages']
    
    # 
    if not any(isinstance(m, SystemMessage) for m in messages):
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages
    
    response = model.invoke(messages)
    return {"messages": [response]}

# Define the tool
def tool_node(state: AgentState):
    content = state['messages'][-1].content

    # Flexible regex for run_shell("cmd") or run_shell('cmd')
    match = re.search(r'run_shell\s*\(\s*["\'](.+?)["\']\s*\)', content)
    
    if match:
        result = run_shell(match.group(1))
        return {"messages": [HumanMessage(content=f"Observation: {result}")]}
    return {"messages": [HumanMessage(content="Error: Could not parse command.")]}
    
    if match:
        cmd = match.group(1)
        observation = run_shell(cmd)
        return {"messages": [HumanMessage(content=f"Observation: {observation}")]}
    else:
        # If parsing fails, we MUST tell the agent so it can try again
        return {"messages": [HumanMessage(content="Error: I couldn't parse your command. Use the format: Action: run_shell(\"command\")")]}

# Determine the next node to execute
def should_continue(state: AgentState):
    content = state['messages'][-1].content

    # Only route to tools if 'run_shell' is called AND the agent hasn't hallucinated an observation
    if "run_shell(" in content and "Observation:" not in content:
        return "tools"
    return END

# Building the Graph
workflow = StateGraph(AgentState)

workflow.add_node("agent", agent_node)
workflow.add_node("tools", tool_node)

workflow.set_entry_point("agent")
workflow.add_conditional_edges("agent", should_continue)
workflow.add_edge("tools", "agent")

app = workflow.compile()

# Main Loop
SYSTEM_PROMPT = f"""
You are Shell-Agent. Your BASE_DIR is {BASE_DIR}.
To run a command, you MUST write: Action: run_shell("command")
After writing the Action, STOP and wait for the Observation.
"""

print("Shell-Agent (LangGraph) is active. Press Ctrl+C to exit.")
print(f"DEBUG: Agent is anchored to: {os.path.abspath(BASE_DIR)}")

session_history = []

while True:
    user_input = input("\nYou: ")
    if not user_input: continue
    
    # 1. Add user input to history
    session_history.append(HumanMessage(content=user_input))
    
    # 2. Pass the FULL history to the graph
    for output in app.stream({"messages": session_history}):
        for key, value in output.items():
            # 3. Get the new message created by the agent or the tool
            new_msg = value["messages"][-1]
            
            if key == "agent":
                print(new_msg.content)
            
            # 4. CRITICAL: Add the agent's thought AND the tool's result to history
            session_history.append(new_msg)
