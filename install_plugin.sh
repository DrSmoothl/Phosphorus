#!/bin/bash

# Installation script for Hydro OJ Phosphorus Plugin
# Usage: ./install.sh [hydro_addons_directory]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"
PLUGIN_NAME="CAUCOJ-Phosphorus"

# Default Hydro addons directory
HYDRO_ADDONS_DIR="${1:-/opt/hydro/addons}"

echo "=== Hydro OJ Phosphorus Plugin Installer ==="
echo "Plugin directory: $SCRIPT_DIR/FrontendHydroPlugin"
echo "Target directory: $HYDRO_ADDONS_DIR/$PLUGIN_NAME"
echo

# Check if plugin directory exists
if [ ! -d "$SCRIPT_DIR/FrontendHydroPlugin" ]; then
    echo "❌ Error: FrontendHydroPlugin directory not found in $SCRIPT_DIR"
    exit 1
fi

# Check if target directory exists
if [ ! -d "$HYDRO_ADDONS_DIR" ]; then
    echo "❌ Error: Hydro addons directory not found: $HYDRO_ADDONS_DIR"
    echo "Please specify the correct path: $0 /path/to/hydro/addons"
    exit 1
fi

# Check if plugin is already installed
if [ -d "$HYDRO_ADDONS_DIR/$PLUGIN_NAME" ]; then
    echo "⚠️  Plugin is already installed at $HYDRO_ADDONS_DIR/$PLUGIN_NAME"
    read -p "Do you want to overwrite it? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Installation cancelled."
        exit 0
    fi
    echo "Removing existing installation..."
    rm -rf "$HYDRO_ADDONS_DIR/$PLUGIN_NAME"
fi

# Copy plugin files
echo "Copying plugin files..."
cp -r "$SCRIPT_DIR/FrontendHydroPlugin" "$HYDRO_ADDONS_DIR/$PLUGIN_NAME"

# Install Node.js dependencies
echo "Installing dependencies..."
cd "$HYDRO_ADDONS_DIR/$PLUGIN_NAME"

if command -v npm &> /dev/null; then
    npm install
    echo "✅ Dependencies installed with npm"
elif command -v yarn &> /dev/null; then
    yarn install
    echo "✅ Dependencies installed with yarn"
else
    echo "⚠️  Neither npm nor yarn found. Please install dependencies manually:"
    echo "   cd $HYDRO_ADDONS_DIR/$PLUGIN_NAME && npm install"
fi

# Set up environment configuration
if [ ! -f ".env" ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit $HYDRO_ADDONS_DIR/$PLUGIN_NAME/.env to configure your Phosphorus backend URL"
fi

echo
echo "=== Installation Complete ==="
echo "✅ Plugin installed successfully!"
echo
echo "Next steps:"
echo "1. Configure Phosphorus backend URL:"
echo "   Edit: $HYDRO_ADDONS_DIR/$PLUGIN_NAME/.env"
echo "   Set: PHOSPHORUS_URL=http://your-phosphorus-server:8000"
echo
echo "2. Enable the plugin in your Hydro configuration:"
echo "   Add '$PLUGIN_NAME' to your addons list"
echo
echo "3. Restart Hydro OJ:"
echo "   pm2 restart hydro  # or your preferred method"
echo
echo "4. Test the plugin:"
echo "   - Navigate to any contest admin page"
echo "   - Look for 'Plagiarism Detection' in the admin menu"
echo
echo "For detailed usage instructions, see:"
echo "$HYDRO_ADDONS_DIR/$PLUGIN_NAME/README.md"
echo
echo "If you encounter issues, check the logs and ensure:"
echo "- Phosphorus backend is running and accessible"
echo "- MongoDB contains contest and submission data"
echo "- User has appropriate permissions"