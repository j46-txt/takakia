#!/usr/bin/env bash
set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}=== Takakia CLI Installer ===${NC}"

# 1. Verify Python availability
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

# 3. Verify Python venv module
if ! python3 -c "import venv, ensurepip" &> /dev/null; then
    echo -e "${RED}❌ Error: Python 'venv' or 'ensurepip' modules are missing.${NC}"
    echo -e "Please install missing packages via: ${GREEN}sudo apt update && sudo apt install python3-venv${NC}"
    exit 1
fi

# 4. Establish Application Paths
INSTALL_DIR="$HOME/.local/share/takakia"
BIN_DIR="$HOME/.local/bin"

echo -e "${YELLOW}Creating isolated virtual environment...${NC}"
mkdir -p "$INSTALL_DIR"
python3 -m venv "$INSTALL_DIR/venv"

echo -e "${YELLOW}Installing core dependencies and application...${NC}"
"$INSTALL_DIR/venv/bin/pip" install --upgrade pip --quiet
"$INSTALL_DIR/venv/bin/pip" install . --quiet

# 5. Create Execution Wrapper
echo -e "${YELLOW}Generating execution wrapper...${NC}"
mkdir -p "$BIN_DIR"
cat << 'EOF' > "$BIN_DIR/takakia"
#!/bin/sh
exec "$HOME/.local/share/takakia/venv/bin/takakia" "$@"
EOF

chmod +x "$BIN_DIR/takakia"

# 6. Ensure BIN_DIR is in user PATH automatically
if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
    echo -e "${YELLOW}Adding $BIN_DIR to shell configuration...${NC}"
    
    ADDED=0
    for RC_FILE in "$HOME/.bashrc" "$HOME/.zshrc" "$HOME/.profile" "$HOME/.bash_profile"; do
        if [ -f "$RC_FILE" ]; then
            if ! grep -q 'export PATH="$HOME/.local/bin:$PATH"' "$RC_FILE"; then
                echo '' >> "$RC_FILE"
                echo '# Takakia CLI binary path' >> "$RC_FILE"
                echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$RC_FILE"
                echo -e "${GREEN}✓ Added PATH entry to $RC_FILE${NC}"
                ADDED=1
            fi
        fi
    done

    if [ "$ADDED" -eq 0 ]; then
        echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.profile"
        echo -e "${GREEN}✓ Created and updated ~/.profile${NC}"
    fi
    
    echo -e "${GREEN}========== SUCCESS ==========${NC}"
    echo -e "${GREEN}✅ Installation complete!${NC}"
    echo -e "${YELLOW}⚠️  Please restart your terminal window, or run: ${GREEN}source ~/.bashrc${NC}"
else
    echo -e "${GREEN}========== SUCCESS ==========${NC}"
    echo -e "${GREEN}✅ Takakia installed successfully! Launch using: takakia${NC}"
fi
