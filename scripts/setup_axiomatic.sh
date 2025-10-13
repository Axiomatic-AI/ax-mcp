#!/usr/bin/env bash
set -e

echo "🚀 Starting environment setup for Axiomatic MCP Servers..."

# Detect OS package manager
if command -v brew >/dev/null 2>&1; then
  PKG_MANAGER="brew"
elif command -v apt-get >/dev/null 2>&1; then
  PKG_MANAGER="apt-get"
elif command -v yum >/dev/null 2>&1; then
  PKG_MANAGER="yum"
else
  echo "❌ No supported package manager found (brew/apt-get/yum). Please install Python manually."
  exit 1
fi

# --- Detect Python executable ---
if command -v python3 >/dev/null 2>&1; then
  PYTHON_BIN="python3"
elif command -v python >/dev/null 2>&1; then
  PYTHON_BIN="python"
else
  echo "📦 Installing Python..."
  if [ "$PKG_MANAGER" = "brew" ]; then
    brew install python
    PYTHON_BIN="python3"
  else
    sudo $PKG_MANAGER update -y
    sudo $PKG_MANAGER install -y python3 python3-pip
    PYTHON_BIN="python3"
  fi
fi

# --- Validate Python version ---
PY_VERSION=$($PYTHON_BIN -c "import sys; print(sys.version_info.major*10+sys.version_info.minor)")
if [ "$PY_VERSION" -lt 38 ]; then
  echo "❌ Python version must be >= 3.8. Found: $($PYTHON_BIN --version)"
  exit 1
fi
echo "✅ Using $($PYTHON_BIN --version)"

if [ "$PKG_MANAGER" = "brew" ]; then
  # Install pipx with brew if missing
  if ! command -v pipx >/dev/null 2>&1; then
    echo "📦 Installing pipx with brew..."
    brew install pipx
    pipx ensurepath
  fi

  # Install uv with brew if missing
  if ! command -v uv >/dev/null 2>&1; then
    echo "📦 Installing uv with brew..."
    brew install uv
  fi
else
  # Linux path: install pipx via pip, uv via curl
  if ! command -v pipx >/dev/null 2>&1; then
    echo "📦 Installing pipx with pip..."
    $PYTHON_BIN -m pip install --user pipx
    $PYTHON_BIN -m pipx ensurepath
  fi

  if ! command -v uv >/dev/null 2>&1; then
    echo "📦 Installing uv via curl..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
  fi
fi


# --- Ensure local bin in PATH ---
export PATH="$HOME/.local/bin:$PATH"

echo ""
echo "🎉 Setup complete!"
echo ""

# --- Prompt user to start MCP server now ---
read -p "✅ Installation successful. Do you want to start the Axiomatic MCP server now? (y/N): " RUN_NOW
RUN_NOW=$(echo "$RUN_NOW" | tr '[:upper:]' '[:lower:]')

if [[ "$RUN_NOW" == "y" || "$RUN_NOW" == "yes" ]]; then
  echo "🚀 Starting Axiomatic MCP server..."
  uvx --from axiomatic-mcp all
else
  echo "ℹ️ To start the Axiomatic MCP server later, run:"
  echo ""
  echo "    uvx --from axiomatic-mcp all"
  echo ""
fi
