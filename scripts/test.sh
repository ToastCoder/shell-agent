#!/bin/zsh

# shell-agent
# scripts/test.sh

cd ..

# check for the file and give execution perms, then run
if [ -f "install.sh" ]; then
    echo "Running target_script.sh in $(pwd)..."
    chmod +x install.sh
    ./install.sh

    # post installation, wait for user go to test before removing the installed files
    read -p "Press Enter to continue..."

    # remove the installed one from the user dir
    rm rm -rf ~/.local/share/shell-agent

else
    echo "Error: target_script.sh not found in $(pwd)"
fi
