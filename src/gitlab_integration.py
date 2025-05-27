#!/usr/bin/env python3
"""
GitLab integration module for commit reader.
"""
import os
from typing import Dict, Optional, Any, Tuple

# Try to import gitlab module, but make it optional
try:
    import gitlab
    GITLAB_AVAILABLE = True
except ImportError:
    GITLAB_AVAILABLE = False
    print("Warning: python-gitlab module not installed. GitLab integration will be disabled.")
    print("To enable GitLab integration, install it with: pip install python-gitlab")

# Import the Agent class for AI processing
from agent import Agent

def get_gitlab_client(project_id: Optional[str] = None) -> Optional[Tuple[Any, Any]]:
    """
    Initialize the GitLab client and get the project.

    Args:
        project_id: GitLab project ID, if None uses GITLAB_PROJECT_ID from environment

    Returns:
        Tuple containing GitLab client and project, or None if not configured
    """
    if not GITLAB_AVAILABLE:
        return None

    # Use environment variable if project_id not provided
    if project_id is None:
        project_id = os.getenv("GITLAB_PROJECT_ID")

    try:
        # Initialize GitLab client from config file
        gl = gitlab.Gitlab.from_config()

        # Get the project using provided project_id or from environment
        if project_id:
            project = gl.projects.get(project_id)
            return gl, project
        else:
            print("GitLab project ID not configured. Set GITLAB_PROJECT_ID in your .env file or pass it as an argument.")
            return None
    except Exception as e:
        print(f"Error initializing GitLab client: {e}")
        return None

def get_merge_request_details(project: Any, mr_id: str) -> Dict:
    """
    Get comprehensive details for a specific merge request in Markdown format.

    Args:
        project: GitLab project object
        mr_id: The ID of the merge request

    Returns:
        Dictionary with merge request details or empty dict if not found,
        including a formatted markdown string with all MR information
    """
    if not GITLAB_AVAILABLE:
        return {}

    try:
        # Fetch the merge request with lazy=False to get all attributes
        mr = project.mergerequests.get(mr_id, lazy=False)

        # Fetch all discussions (comments and reviews) - include resolved ones
        discussions = mr.discussions.list(all=True)

        # Fetch all changes with full diff context
        changes = mr.changes()

        # Fetch commits
        commits = mr.commits()

        # Fetch approvals
        approvals = None
        try:
            approvals = mr.approvals.get()
        except:
            pass  # Approvals might not be enabled

        # Build markdown representation
        markdown = f"# {mr.title}\n\n"

        # Basic information
        markdown += "## Basic Information\n\n"
        markdown += f"- **ID**: !{mr_id}\n"
        markdown += f"- **URL**: {mr.web_url}\n"
        markdown += f"- **State**: {mr.state}\n"
        markdown += f"- **Created**: {mr.created_at}\n"
        markdown += f"- **Updated**: {mr.updated_at}\n"
        markdown += f"- **Author**: {mr.author['name'] if 'name' in mr.author else mr.author['username']}\n"

        if hasattr(mr, 'assignee') and mr.assignee:
            markdown += f"- **Assignee**: {mr.assignee['name'] if 'name' in mr.assignee else mr.assignee['username']}\n"

        if hasattr(mr, 'labels') and mr.labels:
            markdown += f"- **Labels**: {', '.join(mr.labels)}\n"

        # Source and target branches
        markdown += f"- **Source Branch**: {mr.source_branch}\n"
        markdown += f"- **Target Branch**: {mr.target_branch}\n"

        # Add merge status information
        if hasattr(mr, 'merge_status'):
            markdown += f"- **Merge Status**: {mr.merge_status}\n"
        if hasattr(mr, 'merged_at') and mr.merged_at:
            markdown += f"- **Merged At**: {mr.merged_at}\n"
        if hasattr(mr, 'merged_by') and mr.merged_by:
            merged_by_name = mr.merged_by.get('name', mr.merged_by.get('username', 'Unknown'))
            markdown += f"- **Merged By**: {merged_by_name}\n"

        markdown += "\n"

        # Description - get the full description without truncation
        markdown += "## Description\n\n"
        full_description = getattr(mr, 'description', '') or ''
        if full_description:
            # Ensure we get the complete description
            markdown += f"{full_description}\n\n"
        else:
            markdown += "No description provided.\n\n"

        # Approvals
        if approvals:
            markdown += "## Approvals\n\n"
            markdown += f"- **Required approvals**: {getattr(approvals, 'approvals_required', 'N/A')}\n"
            markdown += f"- **Approvals left**: {getattr(approvals, 'approvals_left', 'N/A')}\n"

            if hasattr(approvals, 'approved_by') and approvals.approved_by:
                markdown += "- **Approved by**:\n"
                for approval in approvals.approved_by:
                    user = approval.get('user', {})
                    markdown += f"  - {user.get('name', user.get('username', 'Unknown'))}\n"
            markdown += "\n"

        # Commits
        markdown += "## Commits\n\n"
        if commits:
            for commit in commits:
                markdown += f"- **{commit.short_id}**: {commit.title}\n"
                markdown += f"  - Author: {commit.author_name} <{commit.author_email}>\n"
                markdown += f"  - Date: {commit.created_at}\n"
                # Add commit message if different from title
                if hasattr(commit, 'message') and commit.message and commit.message.strip() != commit.title.strip():
                    # Show full commit message
                    commit_lines = commit.message.strip().split('\n')
                    if len(commit_lines) > 1:
                        markdown += f"  - Full message:\n"
                        for line in commit_lines[1:]:  # Skip the title line
                            if line.strip():
                                markdown += f"    {line}\n"
                markdown += "\n"
        else:
            markdown += "No commits found.\n\n"

        # Discussions (comments and reviews) - include resolved discussions
        markdown += "## Comments and Reviews\n\n"
        discussion_count = 0
        if discussions:
            for discussion in discussions:
                # Get discussion attributes
                discussion_attrs = getattr(discussion, 'attributes', {})
                notes = discussion_attrs.get('notes', [])

                if not notes:
                    continue

                discussion_count += len(notes)

                # Check if discussion is resolved
                resolved = discussion_attrs.get('individual_note', False) == False and discussion_attrs.get('resolvable', False) and discussion_attrs.get('resolved', False)

                for note in notes:
                    author = note.get('author', {})
                    author_name = author.get('name', author.get('username', 'Unknown'))
                    created_at = note.get('created_at', 'unknown date')

                    markdown += f"### Comment by {author_name} on {created_at}"
                    if resolved:
                        markdown += " (RESOLVED)"
                    markdown += "\n\n"

                    # Check if this is a system note
                    if note.get('system', False):
                        markdown += f"*System note*: {note.get('body', '')}\n\n"
                        continue

                    if note.get('type') == 'DiffNote':
                        # This is a comment on a specific line in the code
                        position = note.get('position', {})
                        old_path = position.get('old_path', '')
                        new_path = position.get('new_path', '')
                        old_line = position.get('old_line', '')
                        new_line = position.get('new_line', '')

                        if old_path and new_path and old_path != new_path:
                            markdown += f"**On file change from** `{old_path}` **to** `{new_path}`\n\n"
                        else:
                            path = new_path or old_path
                            if path:
                                markdown += f"**On file** `{path}`\n\n"

                        if old_line and new_line and old_line != new_line:
                            markdown += f"**Line change from** `{old_line}` **to** `{new_line}`\n\n"
                        else:
                            line = new_line or old_line
                            if line:
                                markdown += f"**Line** `{line}`\n\n"

                    # Add the comment body
                    body = note.get('body', '')
                    if body:
                        markdown += f"{body}\n\n"
                    else:
                        markdown += "*No comment text*\n\n"

        if discussion_count == 0:
            markdown += "No comments or reviews found.\n\n"
        else:
            markdown += f"*Total comments/notes: {discussion_count}*\n\n"

        # Changes/Diffs
        markdown += "## Changes\n\n"
        if changes and 'changes' in changes:
            change_count = len(changes['changes'])
            markdown += f"*Total files changed: {change_count}*\n\n"

            for change in changes['changes']:
                old_path = change.get('old_path', '')
                new_path = change.get('new_path', '')

                if change.get('new_file', False):
                    markdown += f"### New file: `{new_path}`\n\n"
                elif change.get('deleted_file', False):
                    markdown += f"### Deleted file: `{old_path}`\n\n"
                elif old_path != new_path:
                    markdown += f"### Renamed file: `{old_path}` → `{new_path}`\n\n"
                else:
                    markdown += f"### Modified file: `{new_path}`\n\n"

                # Add file statistics if available
                if 'a_mode' in change or 'b_mode' in change:
                    markdown += f"**File mode**: {change.get('a_mode', 'N/A')} → {change.get('b_mode', 'N/A')}\n\n"

                if change.get('diff', ''):
                    markdown += "```diff\n"
                    markdown += change['diff']
                    markdown += "\n```\n\n"
                else:
                    markdown += "*No diff available (binary file or no changes)*\n\n"
        else:
            markdown += "No changes found.\n\n"

        # Add debug information
        markdown += "## Debug Information\n\n"
        markdown += f"- **Discussions fetched**: {len(discussions) if discussions else 0}\n"
        markdown += f"- **Changes fetched**: {len(changes.get('changes', [])) if changes else 0}\n"
        markdown += f"- **Commits fetched**: {len(commits) if commits else 0}\n"
        markdown += f"- **Description length**: {len(full_description)} characters\n\n"

        # Return both the original details and the markdown
        return {
            "title": mr.title,
            "description": full_description,
            "web_url": mr.web_url,
            "state": mr.state,
            "created_at": mr.created_at,
            "updated_at": mr.updated_at,
            "author": mr.author['name'] if 'name' in mr.author else mr.author['username'],
            "markdown": markdown,
            # Include raw data for further processing if needed
            "raw_discussions": discussions,
            "raw_changes": changes,
            "raw_commits": commits,
            # Add debug info
            "debug_info": {
                "discussions_count": len(discussions) if discussions else 0,
                "changes_count": len(changes.get('changes', [])) if changes else 0,
                "commits_count": len(commits) if commits else 0,
                "description_length": len(full_description)
            }
        }
    except Exception as e:
        print(f"Error fetching details for MR !{mr_id}: {e}")
        import traceback
        traceback.print_exc()
        return {}

def generate_learning_sheet(mr_details: Dict) -> str:
    """
    Generate a learning sheet from MR details using AI.

    Args:
        mr_details: Dictionary containing MR details with markdown

    Returns:
        String containing the AI-generated learning sheet
    """
    if not mr_details or "markdown" not in mr_details:
        return "Error: No MR details provided or markdown not available."

    # Create the system prompt for learning sheet generation
    system_prompt = """You are an expert software engineering mentor tasked with creating learning sheets from merge request data.

Your goal is to analyze the provided merge request information and create a comprehensive learning sheet that future engineers and AI agents can use to understand the solution approach, coding patterns, and best practices demonstrated in this merge request.

Please create a learning sheet in markdown format with the following sections:

## Story/Issue
- Summarize the problem or feature that was being addressed
- Extract the business context and requirements
- Identify the key challenges or constraints

## Solution
- Describe the technical approach taken
- Highlight key architectural decisions
- Explain the implementation strategy
- Note any design patterns or methodologies used

## Discussion
- Summarize important conversations and decisions from code reviews
- Extract key insights from reviewer feedback
- Note any alternative approaches that were considered
- Highlight lessons learned or best practices discussed

## References
- List relevant files, functions, or components modified
- Note any external resources, documentation, or standards referenced
- Include links to related issues, documentation, or external resources mentioned

Focus on extracting actionable insights and patterns that would be valuable for future similar work. Be concise but comprehensive, and ensure the learning sheet serves as a practical reference for engineering best practices."""

    # Initialize the agent with the learning sheet system prompt
    agent = Agent(system_prompt=system_prompt)

    # Use the markdown content as the user prompt
    user_prompt = f"Please analyze this merge request and create a learning sheet:\n\n{mr_details['markdown']}"

    # Generate the learning sheet
    try:
        learning_sheet = agent.generate_response(user_prompt)
        return learning_sheet
    except Exception as e:
        return f"Error generating learning sheet: {str(e)}"

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Fetch GitLab Merge Request details and generate learning sheet.")
    parser.add_argument("project_id", help="GitLab project ID (numeric or path)")
    parser.add_argument("mr_number", help="Merge Request number (IID)")
    parser.add_argument("--learning-sheet", action="store_true",
                       help="Generate AI learning sheet from MR details")
    parser.add_argument("--output-file", help="Output file to save the learning sheet")
    args = parser.parse_args()

    client_project = get_gitlab_client(args.project_id)
    if not client_project:
        print("Failed to initialize GitLab client or project. Check your configuration.")
        exit(1)

    gl, project = client_project
    details = get_merge_request_details(project, args.mr_number)
    if not details or "markdown" not in details:
        print(f"Failed to fetch details for MR !{args.mr_number} in project {args.project_id}.")
        exit(1)

    if args.learning_sheet:
        print("Generating learning sheet...")
        learning_sheet = generate_learning_sheet(details)

        if args.output_file:
            try:
                with open(args.output_file, 'w', encoding='utf-8') as f:
                    f.write(learning_sheet)
                print(f"Learning sheet saved to: {args.output_file}")
            except Exception as e:
                print(f"Error saving learning sheet to file: {e}")
                print("\n" + "="*50)
                print("LEARNING SHEET")
                print("="*50)
                print(learning_sheet)
        else:
            print("\n" + "="*50)
            print("LEARNING SHEET")
            print("="*50)
            print(learning_sheet)
    else:
        print(details["markdown"])
