#!/usr/bin/env bash
set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}=== Uninstalling Takakia CLI ===${NC}"

# 1. Remove wrapper executable
if [ -f "$HOME/.local/bin/takakia" ]; then
    rm -f "$HOME/.local/bin/takakia"
    echo -e "${GREEN}✓ Removed executable wrapper (~/.local/bin/takakia)${NC}"
fi

# 2. Remove virtual environment
if [ -d "$HOME/.local/share/takakia" ]; then
    rm -rf "$HOME/.local/share/takakia"
    echo -e "${GREEN}✓ Removed application environment (~/.local/share/takakia)${NC}"
fi

# 3. Remove PATH export lines from shell configs
for RC_FILE in "$HOME/.bashrc" "$HOME/.zshrc" "$HOME/.profile" "$HOME/.bash_profile"; do
    if [ -f "$RC_FILE" ]; then
        if grep -q 'export PATH="$HOME/.local/bin:$PATH"' "$RC_FILE"; then
            sed -i '/# Takakia CLI binary path/d' "$RC_FILE" 2>/dev/null || true
            sed -i '/export PATH="\$HOME\/\.local\/bin:\$PATH"/d' "$RC_FILE" 2>/dev/null || \
            sed -i '' '/export PATH="\$HOME\/\.local\/bin:\$PATH"/d' "$RC_FILE" 2>/dev/null || true
            echo -e "${GREEN}✓ Cleaned PATH configuration from $RC_FILE${NC}"
        fi
    fi
done

# 4. Optional removal of user config and custom profiles
CONFIG_DIR="$HOME/.config/takakia"
if [ -d "$CONFIG_DIR" ]; then
    read -p "Do you also want to remove user configs and custom profiles ($CONFIG_DIR)? [y/N] " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf "$CONFIG_DIR"
        echo -e "${GREEN}✓ Removed user configuration directory.${NC}"
    else
        echo -e "${YELLOW}i Preserved configuration directory at $CONFIG_DIR${NC}"
    fi
fi

echo -e "${GREEN}✅ Takakia has been successfully uninstalled.${NC}"
