# Vibe My Way

An intelligent coding assistant enhancement that learns from your unique coding style and project history.

![Vibe My Way Demo](myway2.gif)

## 🌟 Overview

Vibe My Way analyzes your commit history using large language models to extract important insights and patterns from your coding style, decisions, and project evolution. This personalized knowledge is then used to enhance your coding assistant's recommendations and suggestions.

## 🚀 How It Works

1. **Commit Analysis**: We use LLMs to process your git commit history, extracting meaningful patterns, coding decisions, and project context.

2. **Knowledge Embedding**: This extracted information is stored in a vector database as embeddings, creating a searchable knowledge base of your unique coding style.

3. **Assistant Integration**: When using supported coding assistants (like Cursor), Vibe My Way serves as an MCP (Model Control Protocol) server that enhances suggestions by comparing your current task with your historical patterns.

## 🔧 Features

- **Personalized Code Suggestions**: Get recommendations that align with your coding style and previous decisions
- **Context-Aware Assistance**: The assistant understands the broader context of your project from your commit history
- **Seamless Integration**: Works alongside your existing coding workflow

## 🛠️ Getting Started

1. Clone the repository
2. Copy `.env.example` to `.env` and configure your environment variables:
   ```
   API_KEY=your_api_key_here
   PROJECT_PATH=/path/to/your/project/repository
   DIRECTORY=path/to/specific/directory/to/analyze
   ```
3. Install the required dependencies
4. Run the provided scripts to analyze your commit history

## 📝 License

See the [LICENSE](LICENSE) file for details.

# Git Commit History Reader

This script analyzes Git commit history for a specific directory, identifies merge requests, and groups related commits.

## Features

- Parses Git commit history including merge commits
- Identifies GitLab merge requests
- Groups commits by merge request
- Retrieves additional details from GitLab API (title, description, author, etc.)
- Modular design with separate GitLab integration module

## Requirements

- Python 3.6+
- Required Python packages:
  - `python-dotenv`
  - `sh`
  - `python-gitlab` (optional, for GitLab integration)

## Installation

1. Clone this repository
2. Install required packages:
   ```
   pip install python-dotenv sh
   pip install python-gitlab  # Optional, for GitLab integration
   ```

## Configuration

### Environment Variables

Create a `.env` file in the project root with the following variables:

```
PROJECT_PATH=/path/to/git/repository
DIRECTORY=path/within/repo/to/analyze
GITLAB_PROJECT_ID=123  # Your GitLab project ID
```

### GitLab Configuration

This script uses the GitLab Python API with configuration from `~/.python-gitlab.cfg`. To set up GitLab integration:

1. Create a configuration file at `~/.python-gitlab.cfg` with the following content:

```ini
[global]
default = your-gitlab-instance

[your-gitlab-instance]
url = https://gitlab.example.com
private_token = your-private-token
api_version = 4
```

2. Add your GitLab project ID to the `.env` file as shown above.

You can also use other configuration methods supported by python-gitlab, such as environment variables. See [python-gitlab documentation](https://python-gitlab.readthedocs.io/en/stable/cli.html#configuration) for more details.

## Usage

Run the script:

```
python src/commit_reader.py
```

### Command Line Arguments

The script supports the following command line arguments:

- `--project-path PATH`: Path to the git repository (overrides environment variable)
- `--directory DIR`: Directory within the repository to analyze (overrides environment variable)
- `--gitlab-project-id ID`: GitLab project ID (overrides environment variable)
- `--first-mr-only`: Process only the first merge request (for faster testing)

Example:

```bash
# Analyze a specific directory and process only the first MR
python src/commit_reader.py --project-path /path/to/repo --directory src/components --first-mr-only
```

## Output

The script outputs:
- List of all commits in the specified directory
- References to external tools (GitHub, GitLab, Jira) found in commit messages
- Merge requests with their related commits
- When GitLab integration is enabled:
  - MR title and description
  - URL to the merge request
  - State and author information
  - Creation date

## Project Structure

- `src/commit_reader.py`: Main script for analyzing git commit history
- `src/gitlab_integration.py`: Module for GitLab API integration

## Example

```
$ python src/commit_reader.py --first-mr-only

Found 184 commits in components/mdns/
...

Found 19 merge requests in components/mdns/:

MR !15180:
  Merge commit: 1e67cf1ec5b02ba77d822e6c59d4c20906e1d98a
  Message: Merge branch 'feature/mdns-multiple-instance' into 'master'
  Title: mDNS: Allow multiple instances with same service type
  URL: https://gitlab.example.com/your-project/merge_requests/15180
  State: merged
  Author: John Doe
  Created: 2023-05-12T09:32:18.721Z
  Description:
    This MR adds support for multiple instances with the same service type.
  Related commits (1):
    b7a99f46587a69a2cd07e7616c3bb30b7b1a6edf: mdns: allow multiple instances with same service type

Stopping after first merge request due to --first-mr-only flag
```
