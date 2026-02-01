#!/bin/bash

# Read JSON input from stdin
input=$(cat)

# Extract data from JSON
session_id=$(echo "$input" | jq -r '.session_id')
transcript_path=$(echo "$input" | jq -r '.transcript_path')
current_dir=$(echo "$input" | jq -r '.workspace.current_dir')
model_name=$(echo "$input" | jq -r '.model.display_name')

# Try to extract cost from the input JSON first - check multiple possible locations
session_cost=$(echo "$input" | jq -r '.cost // .session_cost // .usage.cost // .session.cost // .pricing.total_cost // empty' 2>/dev/null)
session_input_tokens=$(echo "$input" | jq -r '.usage.input_tokens // .input_tokens // .session.input_tokens // .tokens.input // empty' 2>/dev/null)
session_output_tokens=$(echo "$input" | jq -r '.usage.output_tokens // .output_tokens // .session.output_tokens // .tokens.output // empty' 2>/dev/null)

# Debug: Save input JSON to file for inspection (uncomment for debugging)
echo "$input" > /tmp/statusline-debug.json
echo "Cost extracted: $session_cost" >> /tmp/statusline-debug.log
echo "Input tokens: $session_input_tokens" >> /tmp/statusline-debug.log
echo "Output tokens: $session_output_tokens" >> /tmp/statusline-debug.log

# Get folder name
folder_name=$(basename "$current_dir")

# Get git branch (if in a git repo)
git_branch=""
if [ -d "$current_dir/.git" ] || git -C "$current_dir" rev-parse --git-dir > /dev/null 2>&1; then
    git_branch=$(git -C "$current_dir" branch --show-current 2>/dev/null)
    if [ -z "$git_branch" ]; then
        git_branch=$(git -C "$current_dir" rev-parse --short HEAD 2>/dev/null)
    fi
fi

# Initialize variables
session_duration=""
input_tokens=0
output_tokens=0
total_cost=0.0

# Use session cost from input JSON if available
if [ -n "$session_cost" ] && [ "$session_cost" != "null" ] && [ "$session_cost" != "empty" ]; then
    total_cost="$session_cost"
fi

# Use session tokens from input JSON if available
if [ -n "$session_input_tokens" ] && [ "$session_input_tokens" != "null" ] && [ "$session_input_tokens" != "empty" ]; then
    input_tokens="$session_input_tokens"
fi

if [ -n "$session_output_tokens" ] && [ "$session_output_tokens" != "null" ] && [ "$session_output_tokens" != "empty" ]; then
    output_tokens="$session_output_tokens"
fi

# Calculate session duration and extract token usage from transcript JSONL format
if [ -f "$transcript_path" ]; then
    # Get session start time from first entry in transcript (JSONL format - each line is a JSON object)
    start_time=$(head -1 "$transcript_path" | jq -r '.timestamp // empty' 2>/dev/null)
    
    if [ -n "$start_time" ] && [ "$start_time" != "null" ]; then
        start_epoch=$(date -j -f "%Y-%m-%dT%H:%M:%S" "${start_time%.*}" "+%s" 2>/dev/null || date -d "$start_time" +%s 2>/dev/null)
        current_epoch=$(date +%s)
        duration_seconds=$((current_epoch - start_epoch))
        
        if [ $duration_seconds -ge 3600 ]; then
            hours=$((duration_seconds / 3600))
            minutes=$(((duration_seconds % 3600) / 60))
            session_duration="${hours}h${minutes}m"
        elif [ $duration_seconds -ge 60 ]; then
            minutes=$((duration_seconds / 60))
            session_duration="${minutes}m"
        else
            session_duration="${duration_seconds}s"
        fi
    fi
    
    # Extract token usage from transcript JSONL format and calculate cost
    if command -v jq >/dev/null 2>&1; then
        # Parse JSONL file (each line is a JSON object) and extract usage from assistant messages
        # Claude Sonnet 4 pricing per million tokens:
        # Input: $3.00, Cache creation: $3.75, Cache read: $0.30, Output: $15.00
        
        total_input_tokens=0
        total_cache_creation_tokens=0
        total_cache_read_tokens=0
        total_output_tokens=0
        
        # Process each line of the JSONL file
        while IFS= read -r line; do
            # Check if this line contains an assistant message with usage data
            message_type=$(echo "$line" | jq -r '.type // empty' 2>/dev/null)
            if [ "$message_type" = "assistant" ]; then
                # Extract token usage from assistant messages
                line_input_tokens=$(echo "$line" | jq -r '.message.usage.input_tokens // 0' 2>/dev/null)
                line_cache_creation_tokens=$(echo "$line" | jq -r '.message.usage.cache_creation_input_tokens // 0' 2>/dev/null)
                line_cache_read_tokens=$(echo "$line" | jq -r '.message.usage.cache_read_input_tokens // 0' 2>/dev/null)
                line_output_tokens=$(echo "$line" | jq -r '.message.usage.output_tokens // 0' 2>/dev/null)
                
                # Add to totals
                total_input_tokens=$((total_input_tokens + line_input_tokens))
                total_cache_creation_tokens=$((total_cache_creation_tokens + line_cache_creation_tokens))
                total_cache_read_tokens=$((total_cache_read_tokens + line_cache_read_tokens))
                total_output_tokens=$((total_output_tokens + line_output_tokens))
            fi
        done < "$transcript_path"
        
        # Calculate cost based on Claude Sonnet 4 pricing (per million tokens)
        # Using bc for floating point arithmetic
        if command -v bc >/dev/null 2>&1; then
            input_cost=$(echo "scale=6; $total_input_tokens * 3.00 / 1000000" | bc 2>/dev/null || echo 0)
            cache_creation_cost=$(echo "scale=6; $total_cache_creation_tokens * 3.75 / 1000000" | bc 2>/dev/null || echo 0)
            cache_read_cost=$(echo "scale=6; $total_cache_read_tokens * 0.30 / 1000000" | bc 2>/dev/null || echo 0)
            output_cost=$(echo "scale=6; $total_output_tokens * 15.00 / 1000000" | bc 2>/dev/null || echo 0)
            calculated_cost=$(echo "scale=6; $input_cost + $cache_creation_cost + $cache_read_cost + $output_cost" | bc 2>/dev/null || echo 0)
        else
            # Fallback calculation using awk if bc is not available
            calculated_cost=$(awk "BEGIN { 
                input_cost = $total_input_tokens * 3.00 / 1000000;
                cache_creation_cost = $total_cache_creation_tokens * 3.75 / 1000000;
                cache_read_cost = $total_cache_read_tokens * 0.30 / 1000000;
                output_cost = $total_output_tokens * 15.00 / 1000000;
                printf \"%.6f\", input_cost + cache_creation_cost + cache_read_cost + output_cost
            }")
        fi
        
        # Use calculated values if not provided by input JSON
        if [ "$total_cost" = "0.0" ] || [ "$total_cost" = "0" ]; then
            total_cost="$calculated_cost"
        fi
        
        if [ "$input_tokens" = "0" ]; then
            # For display purposes, show total input tokens (regular + cache creation + cache read)
            input_tokens=$((total_input_tokens + total_cache_creation_tokens + total_cache_read_tokens))
        fi
        
        if [ "$output_tokens" = "0" ]; then
            output_tokens="$total_output_tokens"
        fi
        
        # Debug logging
        echo "Transcript tokens - Input: $total_input_tokens, Cache creation: $total_cache_creation_tokens, Cache read: $total_cache_read_tokens, Output: $total_output_tokens" >> /tmp/statusline-debug.log
        echo "Calculated cost: $calculated_cost" >> /tmp/statusline-debug.log
    fi
fi

# Format cost to 2 decimal places
if [ "$total_cost" != "0" ]; then
    cost_display=$(printf "%.2f" "$total_cost")
else
    cost_display="0.00"
fi

# Build status line with colors
printf '\033[2m\033[36m%s\033[0m' "$folder_name"

if [ -n "$git_branch" ]; then
    printf '\033[2m:\033[35m%s\033[0m' "$git_branch"
fi

if [ -n "$session_duration" ]; then
    printf '\033[2m | \033[33m%s\033[0m' "$session_duration"
fi

printf '\033[2m | $\033[32m%s\033[0m' "$cost_display"

if [ "$input_tokens" -gt 0 ] || [ "$output_tokens" -gt 0 ]; then
    printf '\033[2m | \033[34m%dk\033[0m/\033[31m%dk\033[0m' "$((input_tokens / 1000))" "$((output_tokens / 1000))"
fi

printf '\033[2m\033[0m'