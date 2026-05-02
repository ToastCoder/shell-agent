# Required Libraries
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
    
    # 1. Block obvious escapes
    forbidden_strings = ["..", "~", "$HOME"]
    if any(p in command for p in forbidden_strings):
        return "Error: Access denied. You cannot use .., ~, or $HOME."

    # 2. Block absolute paths using Regex
    # This matches a space, followed by a forward slash, followed by a letter or number (e.g., " /etc", " /var", " /Users")
    # It ignores math or comments like " / Row" because "Row" starts with an uppercase letter, or you can just block specific root folders.
    # To keep it simple and robust, let's just block the exact root directories we care about on macOS/Linux:
    forbidden_roots = [" /bin", " /etc", " /var", " /usr", " /System", " /Volumes", " /private"]
    if any(p in command for p in forbidden_roots):
        return "Error: Access denied. You cannot access root system directories."

    print(f"  [Executing]:\n{command}")

    # Running the command
    try:
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True, timeout=5, cwd=BASE_DIR
        )
        return f"Output: {result.stdout}\nError: {result.stderr}"
    except Exception as e:
        return str(e)

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

    # Match everything between the XML tags, regardless of quotes or newlines
    match = re.search(r'<run_shell>(.*?)</run_shell>', content, flags=re.DOTALL)
    
    if match:
        cmd = match.group(1).strip() # .strip() removes leading/trailing whitespace
        observation = run_shell(cmd)
        return {"messages": [HumanMessage(content=f"Observation: {observation}")]}
    else:
        error_msg = "Error: I couldn't parse your command. Use the format: <run_shell> command </run_shell>"
        return {"messages": [HumanMessage(content=error_msg)]}

# Determine the next node to execute
def should_continue(state: AgentState):
    content = state['messages'][-1].content

    if "Final Answer:" in content:
        return END

    # Watch for the opening XML tag
    if "<run_shell>" in content:
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

SYSTEM_PROMPT = f"""
You are Shell-Agent. Your BASE_DIR is {BASE_DIR}.

To run a shell command, you MUST use this exact XML format:
<run_shell>
your command here
</run_shell>

RULES:
1. After writing the <run_shell> block, STOP and wait for the Observation.
2. Once you have the information you need, or if you have completed the task, you MUST exit by writing: Final Answer: [your response to the user]
"""

# Main Loop
print("Shell-Agent (LangGraph) is active. Press Ctrl+C to exit.")
print(f"DEBUG: Agent is anchored to: {os.path.abspath(BASE_DIR)}")

session_history = []

while True:
    user_input = input("\nYou: ")
    if not user_input: continue
    
    session_history.append(HumanMessage(content=user_input))
    
    for output in app.stream({"messages": session_history}):
        for key, value in output.items():
            new_msg = value["messages"][-1]
            
            # Now you will actually see what the terminal is doing!
            if key == "agent":
                print(f"\nAgent:\n{new_msg.content}")
            elif key == "tools":
                print(f"\n Shell Output:\n{new_msg.content}")
            
            session_history.append(new_msg)
