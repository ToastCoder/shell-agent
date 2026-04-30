# Required Libs
import subprocess
import re
import ollama


# Runs the command in the shell and returns the output
def run_bash(command: str):
    """Executes a bash command and returns the output."""
    print(f"  [Executing]: {command}")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=5)
        return f"Output: {result.stdout}\nError: {result.stderr}"
    except Exception as e:
        return str(e)


SYSTEM_PROMPT = """
You are Shell-Agent, a POSIX system expert.
You have access to a tool called 'run_bash'.
When you need to find information or take action, follow this format:

Thought: [Your reasoning about what to do next]
Action: run_bash("[the command]")
Observation: [The result of the command - this will be provided to you]

Once you have the final answer, respond with:
Final Answer: [Your summary]
"""

def start_agent(user_input):
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_input}
    ]

    for _ in range(5):  # Limit to 5 steps to prevent infinite loops
        response = ollama.chat(model='gemma4', messages=messages)
        content = response['message']['content']
        print(f"\n{content}")

        if "Final Answer:" in content:
            break

        # Simple string parsing for the Action
        if "Action: run_bash(" in content:
            # Finds the text between the first set of quotes
            match = re.search(r'run_bash\(["\'](.+?)["\']\)', content)
            if match:
                cmd = match.group(1)
                observation = run_bash(cmd)
                
                messages.append({"role": "assistant", "content": content})
                messages.append({"role": "user", "content": f"Observation: {observation}"})
            else:
                print("  [System]: Found Action tag but couldn't parse the command.")

print ("Press Ctrl+C to exit")

while True:
    user_input = input("You: ")
    start_agent(user_input)
