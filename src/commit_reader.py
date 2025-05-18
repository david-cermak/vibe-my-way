#!/usr/bin/env python3
"""
Script to read git commit history for a specific directory.
"""
import os
import re
from typing import Dict, List
from dotenv import load_dotenv
import sh

# Load environment variables
load_dotenv()

API_KEY = os.getenv("API_KEY")
PROJECT_PATH = os.getenv("PROJECT_PATH")
DIRECTORY = os.getenv("DIRECTORY")

def get_commit_history(project_path: str, directory: str) -> Dict[str, Dict]:
    """
    Get commit history for a specific directory within a git repository.

    Args:
        project_path: Path to the git repository
        directory: Directory within the repository to filter commits

    Returns:
        Dictionary with commit IDs as keys
    """
    print(f"Using git repository at {project_path}")

    # Configure git command with the project path
    git = sh.git.bake(_cwd=project_path)

    # Use sh to run git command
    try:
        print(f"Running git log --oneline --no-merges -- {directory}")
        # Get git log for the specified directory, excluding merge commits
        git_log = git("log", "--oneline", "--no-merges", "--", directory, _tty_out=False)
        print(f"Git log received, processing...")

        # Process the output
        commits = {}
        for line in git_log.strip().split("\n"):
            if not line:
                continue

            # Parse commit ID and message
            match = re.match(r"^([a-f0-9]+)\s+(.*)$", line)
            if match:
                commit_id = match.group(1)
                commit_msg = match.group(2)

                # Store commit in dictionary
                commits[commit_id] = {
                    "message": commit_msg,
                    "references": extract_references(commit_msg)
                }

        return commits
    except Exception as e:
        print(f"Error retrieving git log: {e}")
        return {}

def extract_references(commit_msg: str) -> Dict[str, List[str]]:
    """
    Extract references to external tools from commit messages.

    Args:
        commit_msg: The commit message to analyze

    Returns:
        Dictionary with reference types as keys and lists of references as values
    """
    references = {
        "github": [],
        "gitlab": [],
        "jira": []
    }

    # GitHub: #123 or GH-123
    github_refs = re.findall(r"(?:^|\s)(?:#|GH-)(\d+)(?=\s|$)", commit_msg)
    references["github"] = github_refs

    # GitLab: !123
    gitlab_refs = re.findall(r"(?:^|\s)!(\d+)(?=\s|$)", commit_msg)
    references["gitlab"] = gitlab_refs

    # Jira: PROJECT-123
    jira_refs = re.findall(r"([A-Z]+-\d+)", commit_msg)
    references["jira"] = jira_refs

    return references

def main():
    """Main function to run the script."""
    if not all([PROJECT_PATH, DIRECTORY]):
        print("Error: PROJECT_PATH and DIRECTORY environment variables are required.")
        print("Please set them in a .env file or environment.")
        print("Example .env file:")
        print("API_KEY=sk***")
        print("PROJECT_PATH=/path/to/project/repo")
        print("DIRECTORY=path/to/specific/directory")
        return

    commits = get_commit_history(PROJECT_PATH, DIRECTORY)

    print(f"Found {len(commits)} non-merge commits in {DIRECTORY}:")
    for commit_id, commit_data in commits.items():
        print(f"{commit_id}: {commit_data['message']}")

        # Print references if any
        refs = commit_data["references"]
        if any(refs.values()):
            print("  References:")
            for ref_type, ref_ids in refs.items():
                if ref_ids:
                    print(f"    {ref_type.capitalize()}: {', '.join(ref_ids)}")

if __name__ == "__main__":
    main()
