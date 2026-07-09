#!/usr/bin/env bash
set -e

# Visual colors for terminal output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Takakia CLI Installer ===${NC}"

# 1. Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Error: Python 3 is not installed on this system.${NC}"
    exit 1
fi

# 2. Verify Python Version (>= 3.9)
PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
MAJOR=$(echo "$PYTHON_VERSION" | cut -d. -f1)
MINOR=$(echo "$PYTHON_VERSION" | cut -d. -f2)

if [ "$MAJOR" -lt 3 ] || { [ "$MAJOR" -eq 3 ] && [ "$MINOR" -lt 9 ]; }; then
    echo -e "${RED}❌ Error: Takakia requires Python 3.9 or higher. Found Python $PYTHON_VERSION${NC}"
    exit 1
fi

# 3. Detect and handle PEP 668 missing venv structures (Crucial for antiX/Debian Minimal)
if ! python3 -c "import venv" &> /dev/null; then
    echo -e "${RED}❌ Error: The Python 'venv' standard library module is missing.${NC}"
    echo -e "${YELLOW}Minimalist Linux distributions (like Debian, Ubuntu, and antiX) decouple this module.${NC}"
    echo -e "Please install the missing system packages via your package manager first:"
    echo -e "    ${GREEN}sudo apt update && sudo apt install python3-venv python3-pip${NC}"
    exit 1
fi

# 4. Establish Application Paths
INSTALL_DIR="$HOME/.local/share/takakia"
BIN_DIR="$HOME/.local/bin"

echo -e "${YELLOW}Creating isolated virtual environment layer...${NC}"
mkdir -p "$INSTALL_DIR"
python3 -m venv "$INSTALL_DIR/venv"

echo -e "${YELLOW}Installing core dependencies and application tracking vectors...${NC}"
"$INSTALL_DIR/venv/bin/pip" install --upgrade pip --quiet
"$INSTALL_DIR/venv/bin/pip" install . --quiet

# 5. Create the Execution Wrapper
echo -e "${YELLOW}Generating execution wrapper path...${NC}"
mkdir -p "$BIN_DIR"
cat << 'EOF' > "$BIN_DIR/takakia"
#!/bin/sh
# Transparent execution wrapper context for Takakia CLI
exec "$HOME/.local/share/takakia/venv/bin/takakia" "$@"
EOF

chmod +x "$BIN_DIR/takakia"

echo -e "${GREEN}========== SUCCESS ==========${NC}"
echo -e "${GREEN}✅ Takakia installed successfully inside isolated boundaries!${NC}"

# 6. Check if Binary Destination is indexed by user PATH variables
if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
    echo -e ""
    echo -e "${YELLOW}⚠️  Notice: '$BIN_DIR' is not yet present in your system PATH.${NC}"
    echo -e "To execute 'takakia' instantly from anywhere, add this to your shell config (~/.bashrc or ~/.zshrc):"
    echo -e "    ${GREEN}export PATH=\"\$HOME/.local/bin:\$PATH\"${NC}"
    echo -e "Then run: ${GREEN}source ~/.bashrc${NC} (or restart your terminal instance)"
else
    echo -e "Launch the tool instantly from any directory using: ${GREEN}takakia${NC}"
fi
