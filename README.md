# Takakia ⸙

A command-line AI chat interface optimized for older or low-spec hardware.

By eliminating heavy external framework SDKs and utilizing direct, stateless HTTP streaming adapters, it delivers a responsive, jitter-free terminal chat experience while keeping its memory and CPU footprint exceptionally low.

## Features

* **Low-Spec Optimization:** Uses a sliding-window truncation algorithm to keep conversation memory tightly constrained, preserving cycles on older machines.
* **SDK-Free Streaming:** Direct integration with Google Gemini and OpenAI-compatible REST endpoints via lean streaming protocols.
* **Interactive Setup Wizard:** Step-by-step onboarding sequence that automatically verifies credentials and dynamically pulls/caches available models from your provider.
* **System Prompt Profiles:** Hot-swap conversational behaviors instantly mid-session using embedded markdown profiles.
* **Robust Terminal REPL:** Features smooth user interaction with a 500-line input history buffer, markdown response rendering, and intuitive slash-commands.
* **Native Localization:** Zero-overhead translation engine with full English and Brazilian Portuguese support.
* **Secure Storage & Stability:** Implements atomic configuration file writing with strict file permissions (`0o600` on POSIX systems) and silent global diagnostic logging.

## Core Slash Commands

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
* HTTPX (stateless network streaming)
* Rich (beautiful terminal layouts and error grids)
* Platformdirs (cross-platform directory compliance)

## How to Run and Test

Follow these steps to set up and run `takakia` on your machine:

### Prerequisites
* **Python 3.9 or higher** installed.
* An AI provider API key (OpenRouter, OpenAI, or Google Gemini).

### Step 1: Clone the Project
Open your terminal or Command Prompt and run:
```bash
git clone https://github.com/j46-txt/takakia.git
cd takakia
```

### Step 2: Install
Install the application locally:
```bash
pip install .
```

### Step 3: Launch
Run the global system command from anywhere in your terminal:
```bash
takakia
```
*Note: On your first run, an interactive wizard will guide you through setting up your language, API key, and preferred model automatically.*
