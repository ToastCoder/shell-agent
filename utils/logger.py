# shell-agent
# utils/logger.py

# Importing libaries
import logging
import os

# Ensure the logs directory exists
os.makedirs("logs", exist_ok=True)

# Rename the default INFO level to display as SUCCESS
logging.addLevelName(logging.INFO, "SUCCESS")

# Basic configuration
logging.basicConfig(
    filename='logs/agent_execution.log',
    filemode='a',
    format='[%(levelname)s] %(message)s',
    level=logging.INFO,
    force=True
)

# Getting the logger instance
log = logging.getLogger("ShellAgent")