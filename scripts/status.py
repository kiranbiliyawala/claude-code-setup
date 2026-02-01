#!/usr/bin/env python3
"""
Custom statusline for Claude Code showing cost and context utilization
"""
import json
import sys
import os

# ANSI color codes
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"

# Colors
CYAN = "\033[36m"
BLUE = "\033[34m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
RED = "\033[31m"
MAGENTA = "\033[35m"
GRAY = "\033[90m"


def get_color_for_percentage(percent):
    """Return color based on usage percentage"""
    if percent is None:
        return GRAY
    if percent < 50:
        return GREEN
    elif percent < 75:
        return YELLOW
    else:
        return RED


def format_cost(cost_usd):
    """Format cost in USD"""
    if cost_usd is None or cost_usd == 0:
        return "$0.00"
    if cost_usd < 0.01:
        return f"<$0.01"
    elif cost_usd < 1.0:
        return f"${cost_usd:.3f}"
    else:
        return f"${cost_usd:.2f}"


def format_tokens(tokens):
    """Format token count with K/M suffix"""
    if tokens is None:
        tokens = 0
    if tokens < 1000:
        return str(tokens)
    elif tokens < 1000000:
        return f"{tokens/1000:.1f}K"
    else:
        return f"{tokens/1000000:.1f}M"


def get_context_bar(percent, width=10):
    """Generate a visual progress bar for context usage"""
    if percent is None:
        percent = 0
    filled = int(width * percent / 100)
    empty = width - filled
    color = get_color_for_percentage(percent)
    return f"{color}{'█' * filled}{'░' * empty}{RESET}"


def main():
    try:
        # Read JSON from stdin
        data = json.load(sys.stdin)

        # Extract model info
        model = data.get('model', {})
        model_name = model.get('display_name', 'Unknown')

        # Extract workspace info
        workspace = data.get('workspace', {})
        current_dir = workspace.get('current_dir', '/')
        dir_name = os.path.basename(current_dir) or '/'

        # Extract cost info
        cost_data = data.get('cost', {})
        total_cost = cost_data.get('total_cost_usd', 0) or 0
        lines_added = cost_data.get('total_lines_added', 0) or 0
        lines_removed = cost_data.get('total_lines_removed', 0) or 0

        # Extract context window info
        context = data.get('context_window', {})
        used_percent = context.get('used_percentage', 0) or 0
        total_input = context.get('total_input_tokens', 0) or 0
        total_output = context.get('total_output_tokens', 0) or 0
        context_size = context.get('context_window_size', 200000) or 200000

        # Check for git branch
        git_info = ""
        if os.path.exists('.git'):
            try:
                with open('.git/HEAD', 'r') as f:
                    ref = f.read().strip()
                    if ref.startswith('ref: refs/heads/'):
                        branch = ref.replace('ref: refs/heads/', '')
                        git_info = f"{GRAY}│{RESET} {MAGENTA}{branch}{RESET}"
            except:
                pass

        # Build status line components
        components = []

        # Model name
        components.append(f"{BOLD}{BLUE}[{model_name}]{RESET}")

        # Directory
        components.append(f"{CYAN}📁 {dir_name}{RESET}")

        # Git branch
        if git_info:
            components.append(git_info)

        # Cost
        cost_str = format_cost(total_cost)
        components.append(f"{GRAY}│{RESET} {GREEN}💰 {cost_str}{RESET}")

        # Context usage with bar
        context_color = get_color_for_percentage(used_percent)
        context_bar = get_context_bar(used_percent, width=10)
        components.append(
            f"{GRAY}│{RESET} {context_color}📊 {used_percent:.1f}%{RESET} {context_bar}"
        )

        # Token counts
        input_str = format_tokens(total_input)
        output_str = format_tokens(total_output)
        components.append(
            f"{GRAY}({input_str}↑ {output_str}↓){RESET}"
        )

        # Lines changed (if any)
        if lines_added > 0 or lines_removed > 0:
            components.append(
                f"{GRAY}│{RESET} {GREEN}+{lines_added}{RESET} {RED}-{lines_removed}{RESET}"
            )

        # Combine all components
        status_line = " ".join(components)
        print(status_line)

    except Exception as e:
        # Fallback status line if something goes wrong
        print(f"{RED}Status error: {str(e)}{RESET}")


if __name__ == "__main__":
    main()
