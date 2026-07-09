# Takakia 𖧧

A command-line AI chat interface optimized for older or low-spec hardware that struggles with modern LLM web interfaces. Designed for an immediate, ready-to-use experience: open a terminal, type a prompt, and get an answer.

By minimizing external dependencies and using direct, stateless HTTP streaming adapters, it delivers a responsive terminal chat experience while keeping its memory and CPU footprint exceptionally low.

The project intentionally prioritizes simplicity and efficiency. As a result, it does not support file or image attachments, and conversation history is limited to a bounded sliding window (~40,000 characters) to keep resource usage predictable on modest systems.

## Features

* Sliding-window context truncation for low-spec hardware
* Direct Gemini and OpenAI-compatible API streaming
* Interactive configuration setup wizard
* Dynamic system prompt profile switching
* Terminal REPL with input history and slash-commands
* English and Brazilian Portuguese localization
* Secure configuration handling with strict file permissions (`0o600`) and background logging

## Commands

Inside the chat loop, type `/` followed by one of these commands to control your session:

* `/help` - Displays the command syntax mapping ledger.
* `/clear` - Wipes conversational history to start a brand new thread.
* `/model` - Views active AI endpoints or switches to another cached model.
* `/profile` - Lists or changes the current system prompt persona dynamically.
* `/refresh` - Forces a manual online discovery scan of vendor model listings.
* `/setup` - Reruns the interactive wizard to update API keys and endpoints safely.
* `/exit` / `/quit` - Closes the application cleanly.

## Technology

* Python 3.9+
* HTTPX
* Rich
* Platformdirs

## How to Run and Test

Follow these steps to set up and run `takakia` on your machine:

### Prerequisites
* **Python 3.9 or higher** installed.
* An AI provider API key (e.g., OpenRouter, OpenAI, or Google Gemini).

### Step 1: Clone the Project (or download it)
Open your terminal or PowerShell and run:
```bash
git clone https://github.com/j46-txt/takakia.git
cd takakia
```
*(If you downloaded and extracted the ZIP file from GitHub instead, just open your terminal and cd into the extracted folder).*

### Step 2: Install
Run the automated installation script for your platform. The installer automatically handles background virtual environment isolation to bypass PEP 668 restrictions.

#### Linux & macOS
Open your **Terminal**, ensure you are inside the cloned `takakia` folder, and execute the installation script:
```bash
chmod +x install.sh && ./install.sh
```
> [!NOTE]
> If you are running an ultra-minimalist Linux distribution (like antiX minimal or a barebones Debian server) that strips out Python's core environment utilities, the script will detect it and prompt you to add them:
> ```bash
> sudo apt update && sudo apt install python3-venv python3-pip
> ```

#### Windows
Open **PowerShell**, ensure you are inside the cloned `takakia` folder, and execute the installer bypassing the execution policy:
```powershell
powershell -ExecutionPolicy Bypass -File .\install.ps1
```
*(Or run `.\install.ps1` directly if your system's execution policy already permits it).*

### Step 3: Launch
Restart your terminal session to fully apply the path updates, then run the global command from anywhere:
```bash
takakia
```
*Note: On your first run, an interactive wizard will guide you through setting up your interface language, API key, and preferred model.*
