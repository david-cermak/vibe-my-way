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