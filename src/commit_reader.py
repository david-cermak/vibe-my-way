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
        Dictionary with commit IDs as keys and merge requests as a separate dictionary
    """
    print(f"Using git repository at {project_path}")

    # Configure git command with the project path
    git = sh.git.bake(_cwd=project_path)

    try:
        # First, get a list of all commits
        print(f"Getting commit list for {directory}...")
        git_log = git("log", "--format=%H", "--", directory, _tty_out=False)
        commit_list = git_log.strip().split("\n")

        # Process each commit to get details and identify merge commits
        print(f"Found {len(commit_list)} commits, processing details...")
        commits = {}
        merge_commits = []

        for commit_id in commit_list:
            if not commit_id:
                continue

            # Get commit details
            commit_info = git("show", "--format=%P%n%s%n%B", "--no-patch", commit_id, _tty_out=False)
            commit_parts = commit_info.strip().split("\n", 2)

            if len(commit_parts) < 3:
                continue

            # Parse parent hashes, subject and full message
            parents = commit_parts[0].split()
            subject = commit_parts[1]
            full_message = commit_parts[2]

            # A merge commit has more than one parent
            is_merge = len(parents) > 1
            if is_merge:
                merge_commits.append(commit_id)

            # Extract references
            references = extract_references(full_message)

            # Store commit in dictionary
            commits[commit_id] = {
                "message": subject,
                "full_message": full_message,
                "references": references,
                "is_merge": is_merge,
                "parents": parents
            }

        print(f"Found {len(merge_commits)} merge commits")

        # Process merge requests
        merge_requests = {}

        # First pass: find all merge commits that have GitLab MR references
        for commit_id in merge_commits:
            commit_data = commits[commit_id]
            gitlab_refs = commit_data["references"]["gitlab"]

            # If this merge commit references a GitLab MR, create an entry
            if gitlab_refs:
                for mr_id in gitlab_refs:
                    merge_requests[mr_id] = {
                        "merge_commit": commit_id,
                        "message": commit_data["message"],
                        "full_message": commit_data["full_message"],
                        "related_commits": []
                    }

        # Second pass: associate commits with merge requests
        for mr_id, mr_data in merge_requests.items():
            merge_commit = mr_data["merge_commit"]
            merge_commit_data = commits[merge_commit]

            # For merge commits with 2 parents, first parent is target branch, second is source branch
            if len(merge_commit_data["parents"]) >= 2:
                first_parent = merge_commit_data["parents"][0]
                second_parent = merge_commit_data["parents"][1]

                try:
                    # Get all commits that are in the second parent but not in the first parent
                    # This gives us the commits that were added by the merge request
                    mr_commits = git("log", "--format=%H", f"{first_parent}..{second_parent}", "--", directory, _tty_out=False)

                    for commit in mr_commits.strip().split("\n"):
                        if commit and commit in commits and commit != merge_commit:
                            mr_data["related_commits"].append(commit)
                except Exception as e:
                    print(f"Error getting commits for MR !{mr_id}: {e}")

        return {"commits": commits, "merge_requests": merge_requests}
    except Exception as e:
        print(f"Error retrieving git log: {e}")
        return {"commits": {}, "merge_requests": {}}

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

    # GitLab: !123 or "See merge request" pattern
    gitlab_refs = re.findall(r"(?:^|\s)!(\d+)(?=\s|$)", commit_msg)
    mr_pattern = re.search(r"See merge request\s+[^!]+!(\d+)", commit_msg)
    if mr_pattern and mr_pattern.group(1) not in gitlab_refs:
        gitlab_refs.append(mr_pattern.group(1))
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

    result = get_commit_history(PROJECT_PATH, DIRECTORY)
    commits = result["commits"]
    merge_requests = result["merge_requests"]

    print(f"\nFound {len(commits)} commits in {DIRECTORY}:")
    for commit_id, commit_data in commits.items():
        commit_type = "Merge commit" if commit_data["is_merge"] else "Commit"
        print(f"{commit_type} {commit_id}: {commit_data['message']}")

        # Print references if any
        refs = commit_data["references"]
        if any(refs.values()):
            print("  References:")
            for ref_type, ref_ids in refs.items():
                if ref_ids:
                    print(f"    {ref_type.capitalize()}: {', '.join(ref_ids)}")

    print(f"\nFound {len(merge_requests)} merge requests in {DIRECTORY}:")
    for mr_id, mr_data in merge_requests.items():
        print(f"\nMR !{mr_id}:")
        print(f"  Merge commit: {mr_data['merge_commit']}")
        print(f"  Message: {mr_data['message']}")

        if mr_data['related_commits']:
            print(f"  Related commits ({len(mr_data['related_commits'])}):")
            for commit in mr_data['related_commits']:
                if commit in commits:
                    print(f"    {commit}: {commits[commit]['message']}")
                else:
                    print(f"    {commit}")
        else:
            print("  No related commits found")

if __name__ == "__main__":
    main()
