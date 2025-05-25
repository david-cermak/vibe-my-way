#!/usr/bin/env python3
"""
Script to read git commit history for a specific directory.
"""
import os
import re
import sys
import argparse
from typing import Dict, List, Optional, Tuple, Any
from dotenv import load_dotenv
import sh

# Import GitLab integration module if available
try:
    from gitlab_integration import get_gitlab_client, get_merge_request_details
    GITLAB_MODULE_AVAILABLE = True
except ImportError:
    # Try importing from the current directory
    try:
        from src.gitlab_integration import get_gitlab_client, get_merge_request_details
        GITLAB_MODULE_AVAILABLE = True
    except ImportError:
        GITLAB_MODULE_AVAILABLE = False
        print("Warning: GitLab integration module not found. GitLab functionality will be disabled.")

# Load environment variables
load_dotenv()

API_KEY = os.getenv("API_KEY")
PROJECT_PATH = os.getenv("PROJECT_PATH")
DIRECTORY = os.getenv("DIRECTORY")
GITLAB_PROJECT_ID = os.getenv("GITLAB_PROJECT_ID")

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
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Analyze git commit history and merge requests')
    parser.add_argument('--first-mr-only', action='store_true', help='Process only the first merge request (for testing)')
    parser.add_argument('--project-path', help='Path to the git repository')
    parser.add_argument('--directory', help='Directory within the repository to analyze')
    parser.add_argument('--gitlab-project-id', help='GitLab project ID')
    args = parser.parse_args()

    # Override environment variables with command line arguments if provided
    project_path = args.project_path or PROJECT_PATH
    directory = args.directory or DIRECTORY
    gitlab_project_id = args.gitlab_project_id or GITLAB_PROJECT_ID

    if not all([project_path, directory]):
        print("Error: PROJECT_PATH and DIRECTORY are required.")
        print("Please set them in a .env file or pass them as command line arguments.")
        print("Example .env file:")
        print("PROJECT_PATH=/path/to/project/repo")
        print("DIRECTORY=path/to/specific/directory")
        print("GITLAB_PROJECT_ID=123")
        print("\nOr use command line arguments:")
        print("python src/commit_reader.py --project-path /path/to/project/repo --directory path/to/specific/directory")
        return

    result = get_commit_history(project_path, directory)
    commits = result["commits"]
    merge_requests = result["merge_requests"]

    print(f"\nFound {len(commits)} commits in {directory}:")
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

    print(f"\nFound {len(merge_requests)} merge requests in {directory}:")

    # Get GitLab integration if configured and available
    gitlab_info = None
    if GITLAB_MODULE_AVAILABLE:
        gitlab_info = get_gitlab_client(gitlab_project_id)

    # Keep track of whether we've processed an MR yet (for first-mr-only option)
    processed_mr = False

    for mr_id, mr_data in merge_requests.items():
        # If we're only processing the first MR and we've already processed one, break
        if args.first_mr_only and processed_mr:
            print("\nStopping after first merge request due to --first-mr-only flag")
            break

        print(f"\nMR !{mr_id}:")
        print(f"  Merge commit: {mr_data['merge_commit']}")
        print(f"  Message: {mr_data['message']}")

        # If GitLab integration is configured, fetch and display MR details
        if gitlab_info:
            gl, project = gitlab_info
            mr_details = get_merge_request_details(project, mr_id)

            if mr_details:
                print(f"  Title: {mr_details['title']}")
                print(f"  URL: {mr_details['web_url']}")
                print(f"  State: {mr_details['state']}")
                print(f"  Author: {mr_details['author']}")
                print(f"  Created: {mr_details['created_at']}")
                print(f"  Updated: {mr_details['updated_at']}")

                if mr_details['description']:
                    print("  Description:")
                    print(f"    {mr_details['description']}")

                print("\n  Debug Information:")
                print(f"    Discussions: {mr_details['debug_info']['discussions_count']}")
                print(f"    Changes: {mr_details['debug_info']['changes_count']}")
                print(f"    Commits: {mr_details['debug_info']['commits_count']}")
                print(f"    Description Length: {mr_details['debug_info']['description_length']} chars")

                print("\n  Full Details (Markdown):")
                for line in mr_details['markdown'].split('\n'):
                    print(f"    {line}")
        if mr_data['related_commits']:
            print(f"  Related commits ({len(mr_data['related_commits'])}):")
            for commit in mr_data['related_commits']:
                if commit in commits:
                    print(f"    {commit}: {commits[commit]['message']}")
                else:
                    print(f"    {commit}")
        else:
            print("  No related commits found")

        # Mark that we've processed an MR
        processed_mr = True

if __name__ == "__main__":
    main()
