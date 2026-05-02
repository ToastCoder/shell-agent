# shell-agent
# main.py

# Importing libraries
import subprocess
import os
import re
from typing import Annotated, TypedDict
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage

from utils.tools import run_shell, BASE_DIR
from utils.logger import log

# Importing the LLM from Ollama
model = ChatOllama(model="gemma4", temperature=0).bind(stop=["Observation:"])

# State definition
class AgentState(TypedDict):

    # Keeping track of all thoughts and observations
    messages: Annotated[list, add_messages]

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

# Agent Node - calls the LLM and returns the response
def agent_node(state: AgentState):

    # Updating the messages with the system prompt if not already added
    messages = state['messages']
    if not any(isinstance(m, SystemMessage) for m in messages):
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages
    
    # Invoking the LLM
    response = model.invoke(messages)
    
    # Returning the response
    return {"messages": [response]}

# Tool Node - executes the shell command
def tool_node(state: AgentState):
    content = state['messages'][-1].content

    # Extracting the command from the XML block
    match = re.search(r'<run_shell>(.*?)</run_shell>', content, flags=re.DOTALL)
    
    # Checking for the command
    if match:
        cmd = match.group(1).strip()
        
        # Checking the permissions
        log.info(f"Pending Execution: {cmd}")
        approval = input("Allow execution? (y/n): ").strip().lower()
        
        if approval == 'y':
            log.info(f"Executing shell command: {cmd}")
            observation = run_shell(cmd)
            return {"messages": [HumanMessage(content=f"Observation: {observation}")]}
        else:
            log.warning(f"User rejected command: {cmd}")
            return {"messages": [HumanMessage(content="Error: The user denied permission to run this command. Rethink your approach.")]}
            
    return {"messages": [HumanMessage(content="Error: I couldn't parse your command. Use <run_shell> tags.")]}

# Conditional Edge - decides whether to continue or not
def should_continue(state: AgentState):
    content = state['messages'][-1].content
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
log.info(f"Agent started at {BASE_DIR}, Press Ctrl+C to exit.\n")

# Session history for maintaining context
session_history = []

# Main loop for user interaction
while True:
    # Taking the input from the user
    try:
        user_input = input("\nYou: ")
        if not user_input: continue
        
        # Logging the user input
        log.info(f"User Input: {user_input}")
        session_history.append(HumanMessage(content=user_input))
        
        # Calling the agent
        for output in app.stream({"messages": session_history}):
            for key, value in output.items():
                new_msg = value["messages"][-1]
                
                # Checking the key
                if key == "agent":
                    if "<run_shell>" in new_msg.content:
                        thinking = new_msg.content.split("<run_shell>")[0].strip()

                        # Logging the agent's thinking process
                        if thinking:
                            log.info(f"Agent Thinking: {thinking}")

                    # Checking for the final answer
                    elif "Final Answer:" in new_msg.content:
                        answer = new_msg.content.replace("Final Answer:", "").strip()
                        log.info(f"Final Answer: {answer}")
                    
                    # Logging the agent's response
                    else:
                        log.info(f"Agent: {new_msg.content}")

                # Checking the key
                elif key == "tools":
                    log.info(f"Shell Output: {new_msg.content}")
                
                # Updating the session history
                session_history.append(new_msg)

    except KeyboardInterrupt:
        log.info("Shutting down Shell-Agent...")
        break