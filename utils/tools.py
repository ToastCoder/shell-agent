# shell-agent
# utils/tools.py

# Importing libraries
import subprocess
import os
from utils.logger import log

# Setting base directory
BASE_DIR = os.getcwd()

# Defining the function to execute shell commands
def run_shell(command: str):
    """Executes a shell command within BASE_DIR and returns output."""
    
    # Sandbox to prevent accessing root directories
    forbidden_roots = [" /bin", " /etc", " /var", " /usr", " /System", " /Volumes", " /private"]
    
    # Checking if the command is in the forbidden roots
    if any(p in command for p in forbidden_roots):
        log.warning(f"Sandbox blocked command: {command}")
        return "Error: Access denied. You cannot access root system directories."

    log.info(f"Executing shell command: {command}")
    
    # Executing the command
    try:
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True, timeout=10, cwd=BASE_DIR
        )
        if result.stderr:
            log.error(f"Execution Error: {result.stderr}")
        
        full_output = f"Output: {result.stdout}\nError: {result.stderr}"
        log.info(f"Command Result: {full_output}")
        return full_output
    
    # Handling exceptions
    except Exception as e:
        log.error(f"System Exception: {str(e)}")
        return str(e)