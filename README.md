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
- **AI Learning Sheets**: Generate comprehensive learning documents from merge requests for knowledge sharing
- **Seamless Integration**: Works alongside your existing coding workflow

## 🛠️ Getting Started

1. Clone the repository
2. Copy `.env.example` to `.env` and configure your environment variables:
   ```
   API_KEY=your_api_key_here
   BASE_URL=https://api.openai.com/v1  # Optional, defaults to OpenAI
   MODEL=gpt-4-0125-preview  # Optional, defaults to this model
   PROJECT_PATH=/path/to/your/project/repository
   DIRECTORY=path/to/specific/directory/to/analyze
   GITLAB_PROJECT_ID=123  # Your GitLab project ID
   ```
3. Install the required dependencies
4. Run the provided scripts to analyze your commit history

## 📝 License

See the [LICENSE](LICENSE) file for details.

# Git Commit History Reader & AI Learning Sheet Generator

This script analyzes Git commit history for a specific directory, identifies merge requests, and can generate AI-powered learning sheets from merge request data.

## Features

- Parses Git commit history including merge commits
- Identifies GitLab merge requests
- Groups commits by merge request
- Retrieves comprehensive details from GitLab API (title, description, author, discussions, changes, etc.)
- **NEW**: AI-powered learning sheet generation from merge request data
- Modular design with separate GitLab integration and AI agent modules

## Requirements

- Python 3.6+
- Required Python packages:
  - `python-dotenv`
  - `sh`
  - `openai` (for AI learning sheet generation)
  - `python-gitlab` (optional, for GitLab integration)

## Installation

1. Clone this repository
2. Install required packages:
   ```
   pip install python-dotenv sh openai
   pip install python-gitlab  # Optional, for GitLab integration
   ```

## Configuration

### Environment Variables

Create a `.env` file in the project root with the following variables:

```
PROJECT_PATH=/path/to/git/repository
DIRECTORY=path/within/repo/to/analyze
GITLAB_PROJECT_ID=123  # Your GitLab project ID

# AI Configuration (for learning sheet generation)
API_KEY=your_openai_api_key_here
BASE_URL=https://api.openai.com/v1  # Optional, defaults to OpenAI
MODEL=gpt-4-0125-preview  # Optional, defaults to this model
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

### Commit History Analysis

Run the main commit reader script:

```bash
python src/commit_reader.py
```

#### Command Line Arguments

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

### GitLab Merge Request Analysis & AI Learning Sheets

**NEW**: Generate detailed merge request analysis and AI-powered learning sheets:

```bash
# Fetch and display MR details in markdown format
python src/gitlab_integration.py PROJECT_ID MR_NUMBER

# Generate AI learning sheet and display it
python src/gitlab_integration.py PROJECT_ID MR_NUMBER --learning-sheet

# Generate learning sheet and save to file
python src/gitlab_integration.py PROJECT_ID MR_NUMBER --learning-sheet --output-file learning_sheet.md
```

#### Examples:

```bash
# View MR details for project 123, MR !456
python src/gitlab_integration.py 123 456

# Generate learning sheet for the same MR
python src/gitlab_integration.py 123 456 --learning-sheet

# Save learning sheet to a file
python src/gitlab_integration.py 123 456 --learning-sheet --output-file mr_456_learning_sheet.md
```

## AI Learning Sheets

The AI learning sheet feature analyzes merge request data and generates comprehensive learning documents with the following sections:

### **Story/Issue**
- Problem context and business requirements
- Key challenges and constraints identified

### **Solution**
- Technical approach and architectural decisions
- Implementation strategy and design patterns used

### **Discussion**
- Code review insights and important decisions
- Alternative approaches considered
- Best practices and lessons learned

### **References**
- Modified files and components
- External resources and documentation
- Related issues and links

These learning sheets serve as valuable knowledge artifacts for future engineers and AI agents to understand solution patterns and coding practices.

## Output

### Commit Reader Output:
- List of all commits in the specified directory
- References to external tools (GitHub, GitLab, Jira) found in commit messages
- Merge requests with their related commits
- When GitLab integration is enabled:
  - MR title and description
  - URL to the merge request
  - State and author information
  - Creation date

### GitLab Integration Output:
- Comprehensive merge request details in markdown format
- All discussions and code review comments
- Complete diff information for all changed files
- Commit history and approval information
- **NEW**: AI-generated learning sheets with structured insights

## Project Structure

- `src/commit_reader.py`: Main script for analyzing git commit history
- `src/gitlab_integration.py`: Module for GitLab API integration and AI learning sheet generation
- `src/agent.py`: AI agent class for interacting with language models

## Example Output

### Commit Reader:
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

### AI Learning Sheet Generation:
```bash
$ python src/gitlab_integration.py 123 456 --learning-sheet

Generating learning sheet...

==================================================
LEARNING SHEET
==================================================

# Learning Sheet: Feature Implementation

## Story/Issue
The merge request addressed the need to implement multiple mDNS service instances...

## Solution
The technical approach involved modifying the core mDNS service handler...

## Discussion
Key insights from code review discussions included...

## References
- Modified files: `src/mdns/service.c`, `include/mdns.h`
- Related documentation: mDNS RFC 6763
- External resources: ESP-IDF mDNS component documentation
```
