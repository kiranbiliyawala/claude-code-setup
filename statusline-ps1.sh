#!/bin/bash

# Read JSON input from stdin
input=$(cat)

# Extract current directory from JSON
current_dir=$(echo "$input" | jq -r '.workspace.current_dir')

# Get username
username=$(whoami)

# Get hostname (short form)
hostname=$(hostname -s)

# Build status line based on your PS1 configuration
# Original PS1: %{$fg[red]%}%n%{$reset_color%}@%{$fg[blue]%}%m %{$fg[yellow]%}%~ %{$reset_color%}%%
# Converting zsh color codes to ANSI and removing trailing %

printf '\033[2m\033[31m%s\033[0m\033[2m@\033[34m%s\033[0m \033[2m\033[33m%s\033[0m' "$username" "$hostname" "$current_dir"