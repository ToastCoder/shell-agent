#!/bin/bash

# shell-agent
# install.sh

# Exit immediately if a command exits with a non-zero status.
set -e

# Configuration
REPO_URL="https://github.com/ToastCoder/shell-agent"
INSTALL_DIR="$HOME/.local/share/shell-agent"
PYTHON_APP_SCRIPT="main.py"
RUN_SCRIPT_NAME="shell-agent"
RUN_SCRIPT_PATH="${INSTALL_DIR}/${RUN_SCRIPT_NAME}"

# Directory where we will temporarily clone the repo content
TEMP_CLONE_DIR=$(mktemp -d)

echo "=================================================================================================="
echo "Shell-Agent Installer Initiated (System Deployment)"
echo "======================================================================================================"

# Check for Dependencies and Clone Repository
echo "Checking for dependencies and cloning repository from ${REPO_URL}..."
# Use git for cloning, which is the most reliable method.
git clone "${REPO_URL}" "${TEMP_CLONE_DIR}/shell-agent"

if [ $? -ne 0 ]; then
    echo "Error: Failed to clone the repository. Ensure you have 'git' installed and network access."
    exit 1
fi

# Set the working directory for all subsequent operations
cd "${TEMP_CLONE_DIR}/shell-agent"

# Clean up existing installation if present
if [ -d "${INSTALL_DIR}" ]; then
    echo "Found existing installation directory. Backing up and clearing: ${INSTALL_DIR}..."

    # Backup the old installation first
    mkdir -p "$HOME/.local/share/shell-agent.bak_$(date +%Y%m%d%H%M%d%H%M%S)"
    cp -r "${INSTALL_DIR}" "$HOME/.local/share/shell-agent.bak_*"
    rm -rf "${INSTALL_DIR}"
fi

# Setup the Directory Structure and Copy Files
echo "Creating isolated installation directory: ${INSTALL_DIR}"
mkdir -p "${INSTALL_DIR}"

echo "Copying all core project files to ${INSTALL_DIR}..."
# Use rsync to copy the entire working project state into the isolated location
rsync -av --delete "$PWD/" "${INSTALL_DIR}/"

# 4. Virtual Environment Setup and Dependency Installation
echo "------------------------------------------------------------------------"
echo "Initializing Virtual Environment and Installing Dependencies..."
echo "------------------------------------------------------------------------"

# Create the virtual environment inside the installed directory
echo "Step 4a: Creating virtual environment in ${INSTALL_DIR}/.venv..."
python3 -m venv "${INSTALL_DIR}/.venv"

if [ $? -ne 0 ]; then
    echo "Error: Failed to create virtual environment. Check python3 availability."
    exit 1
fi

# Activate the environment (must be done before pip can work correctly)
echo "Step 4b: Activating environment and installing dependencies..."
source "${INSTALL_DIR}/.venv/bin/activate"

# Install dependencies using the local requirements.txt
pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "Error: Dependency installation failed. Check requirements.txt and network connectivity."
    deactivate
    exit 1
fi

# Deactivate the environment after successful installation
deactivate

# Create and Configure run.sh Wrapper Script (The new global entry point)
echo "Creating wrapper script: ${RUN_SCRIPT_NAME}..."
cat > "${RUN_SCRIPT_PATH}" << EOF
#!/bin/bash
# This script is the main global entry point for Shell-Agent.
# It ensures the environment is sourced from the local installation path.

# Determine the absolute path of the directory containing this script.
SCRIPT_DIR=\$(dirname "\$BASH_SOURCE")
INSTALL_DIR=\$(dirname "\$SCRIPT_DIR")

# Activate the virtual environment using the full path to ensure sourcing works.
source "\${INSTALL_DIR}/.venv/bin/activate" 2>/dev/null

# Execute the main application logic.
python "\${INSTALL_DIR}/shell-agent/main.py"
EOF

# Make the entry point executable
chmod +x "${RUN_SCRIPT_PATH}"

# Add to PATH (Platform-Agnostic Shell Detection)
echo "Determining default shell and updating profile..."
USER_SHELL_PROFILE=""
SHELL_BIN="$SHELL"

if [ -z "$SHELL_BIN" ]; then
    echo "Warning: Cannot determine your default shell (\$SHELL). Manual action required."
    exit 0
fi

# Determine the config file based on the shell binary path
case "$SHELL_BIN" in
    */zsh)
        USER_SHELL_PROFILE="$HOME/.zshrc"
        ;;
    */bash)
        USER_SHELL_PROFILE="$HOME/.bashrc"
        ;;
    *)
        echo "Warning: Detected shell '$SHELL_BIN'. Cannot automatically determine profile. Manual action required."
        USER_SHELL_PROFILE=""
        ;;
esac

if [ -n "$USER_SHELL_PROFILE" ]; then
    echo "Detected shell (${SHELL_BIN}). Writing changes to ${USER_SHELL_PROFILE}."

    # Check if the directory is already in PATH to prevent duplicates
    if ! grep -q "${INSTALL_DIR}" "${USER_SHELL_PROFILE}"; then
        echo "" >> "${USER_SHELL_PROFILE}"
        echo "# Shell-Agent Deployment (Installed by installer)" >> "${USER_SHELL_PROFILE}"
        echo "export PATH=\"${INSTALL_DIR}:${PATH}\"" >> "${USER_SHELL_PROFILE}"
        echo ""
        echo "Success! Added ${INSTALL_DIR} to your PATH in ${USER_SHELL_PROFILE}."
        echo "Please run 'source ${USER_SHELL_PROFILE}' to apply changes."
    else
        echo "The agent directory is already configured in your shell profile."
    fi
else
    echo "Manual Step Required: Due to non-standard shell detection, please manually add the following line to your profile (~/.zshrc or ~/.bashrc):"
    echo "export PATH=\"${INSTALL_DIR}:${PATH}\""
fi

echo "====================================================================================================="
echo "Installation Complete! Shell-Agent is now installed for user."
echo "====================================================================================================="
echo "ACTION REQUIRED: Please source your shell profile to apply path changes."
echo "Then, you can run the agent by typing: shell-agent"
