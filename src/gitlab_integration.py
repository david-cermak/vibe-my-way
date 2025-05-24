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
    Get details for a specific merge request.

    Args:
        project: GitLab project object
        mr_id: The ID of the merge request

    Returns:
        Dictionary with merge request details or empty dict if not found
    """
    if not GITLAB_AVAILABLE:
        return {}

    try:
        mr = project.mergerequests.get(mr_id)
        return {
            "title": mr.title,
            "description": mr.description,
            "web_url": mr.web_url,
            "state": mr.state,
            "created_at": mr.created_at,
            "updated_at": mr.updated_at,
            "author": mr.author['name'] if 'name' in mr.author else mr.author['username']
        }
    except Exception as e:
        print(f"Error fetching details for MR !{mr_id}: {e}")
        return {}
