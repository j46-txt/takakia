# Takakia

A lightweight, lightning-fast command-line AI chat interface optimized explicitly for older or low-spec hardware.
Modern web-based AI interfaces are heavy, cluttered, and introduce noticeable CPU/RAM lag on older laptops. This application strips away the overhead.

### Key Highlights
* **Minimalist Stack:** Avoids heavy multi-tier SDKs. Powered directly by generic `httpx` and `rich` rendering.
* **Universal Compatibility:** A single implementation structured around API compatibility. Works out of the box with OpenRouter (default), OpenAI, Groq, Together, DeepInfra, or local LLMs (Ollama) via any OpenAI-v1 compliant endpoint.
* **Local Model Caching:** Available models are fetched on demand and cached locally to keep day-to-day execution speeds independent of network handshakes.
* **Detached Prompt Profiles:** System behavior constraints are managed inside standard, modular Markdown files. No Python modification is required to customize AI personas.
* **Low Hardware Footprint:** Uses a custom character-based sliding window context algorithm to control request payload density rather than downloading massive C-compiled tokenization matrices. Fully performant on vintage Intel Core Duo architectures running minimalist Linux window managers.

---

## Installation

### 1. Prerequisites
Ensure you have **Python 3.9** or newer installed on your machine.

### 2. Clone and Setup
```bash
# Clone the repository
git clone [https://github.com/yourusername/takakia.git](https://github.com/yourusername/takakia.git)
cd takakia

# Create a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install the package in editable development mode
pip install -e .