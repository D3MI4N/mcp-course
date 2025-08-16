#!/usr/bin/env python3
"""
Module 1: Basic MCP Server - Starter Code
TODO: Implement tools for analyzing git changes and suggesting PR templates
"""

import json
import os
import subprocess
from typing import Optional
from pathlib import Path
# Import pdb library for debugging
import pdb
import asyncio

from mcp.server.fastmcp import FastMCP

# Initialize the FastMCP server
mcp = FastMCP("pr-agent")

# PR template directory (shared across all modules)
TEMPLATES_DIR = Path(__file__).parent.parent.parent / "templates"

# Ensure the templates directory exists
if not TEMPLATES_DIR.exists():
    raise FileNotFoundError(f"Templates directory not found: {TEMPLATES_DIR}")

# # list available PR templates
# def list_pr_templates() -> dict:
#     """List available PR templates with their content."""
#     templates = {}
#     for template_file in TEMPLATES_DIR.glob("*.md"):
#         with open(template_file, "r") as f:
#             templates[template_file.stem] = f.read()
#     return templates

# # print list of available templates
# print("Available PR templates:")
# for name, content in list_pr_templates().items():
#     print(f"- {name}: {len(content)} characters")

# Set trace to test until this point
# pdb.set_trace()



# TODO: Implement tool functions here
# Example structure for a tool:
@mcp.tool()
async def analyze_file_changes(base_branch: str = "main", 
                              include_diff: bool = True,
                              max_diff_lines: int = 500) -> str:
    """Analyze file changes with smart output limiting.
    
    Args:
        base_branch: Branch to compare against
        include_diff: Whether to include the actual diff
        max_diff_lines: Maximum diff lines to include (default 500)
    """
    try:
        # Get the diff
        result = subprocess.run(
            ["git", "diff", f"{base_branch}...HEAD"],
            capture_output=True, 
            text=True
        )
        
        diff_output = result.stdout
        diff_lines = diff_output.split('\n')
        
        # Smart truncation if needed
        if len(diff_lines) > max_diff_lines:
            truncated_diff = '\n'.join(diff_lines[:max_diff_lines])
            truncated_diff += f"\n\n... Output truncated. Showing {max_diff_lines} of {len(diff_lines)} lines ..."
            diff_output = truncated_diff
        
        # Get summary statistics
        stats_result = subprocess.run(
            ["git", "diff", "--stat", f"{base_branch}...HEAD"],
            capture_output=True,
            text=True
        )

        # Get changed files
        files_result = subprocess.run(
            ["git", "diff", "--name-only", f"{base_branch}...HEAD"],
            capture_output=True,
            text=True
        )
        files_changed = files_result.stdout.strip().split('\n') if files_result.stdout else []

        return json.dumps({
            "stats": stats_result.stdout,
            "total_lines": len(diff_lines),
            "diff": diff_output if include_diff else "Use include_diff=true to see diff",
            "files_changed": files_changed
        })
        
    except Exception as e:
        return json.dumps({"error": str(e)})

# Minimal stub implementations so the server runs
# TODO: Replace these with your actual implementations


@mcp.tool()
async def get_pr_templates() -> str:
    """List available PR templates with their content."""
    try:
        templates = []
        for template_file in TEMPLATES_DIR.glob("*.md"):
            # Safely read template content
            with open(template_file, "r", encoding="utf-8") as f:
                content = f.read()
            templates.append({
                "name": template_file.stem,
                "content": content
            })
        return json.dumps(templates, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})

# print("PR templates loaded successfully.") 
# print(asyncio.run(get_pr_templates()))  # Print the templates to verify

# pdb.set_trace()  # Set trace to test until this point


@mcp.tool()
async def suggest_template(changes_summary: str, change_type: str) -> str:
    """Suggest the most appropriate PR template based on change_type and available templates."""
    try:
        # Dynamically map change_type to available templates in the templates folder
        available_templates = {f.stem: f for f in TEMPLATES_DIR.glob("*.md")}
        normalized_type = change_type.strip().lower()

        # Try to match change_type to a template name
        matched_template = None
        for name in available_templates:
            if normalized_type in name.lower():
                matched_template = available_templates[name]
                break

        # Fallback: exact match
        if not matched_template and normalized_type in available_templates:
            matched_template = available_templates[normalized_type]

        if not matched_template:
            return json.dumps({
                "error": f"No template found for change_type '{change_type}'",
                "available_templates": list(available_templates.keys())
            })

        with open(matched_template, "r", encoding="utf-8") as f:
            content = f.read()

        return json.dumps({
            "template": matched_template.stem,
            "content": content,
            "summary": changes_summary
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})

if __name__ == "__main__":
    # print(asyncio.run(suggest_template("Fixed a bug in login flow", "bug")))
    mcp.run()