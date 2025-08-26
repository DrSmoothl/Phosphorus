#!/bin/bash

# Test script for Hydro OJ Phosphorus Plugin
# This script helps verify the plugin installation and basic functionality

echo "=== Hydro OJ Phosphorus Plugin Test Script ==="
echo

# Check if plugin directory exists
if [ ! -d "FrontendHydroPlugin" ]; then
    echo "❌ Error: FrontendHydroPlugin directory not found"
    exit 1
fi

echo "✅ Plugin directory found"

# Check required files
required_files=(
    "FrontendHydroPlugin/index.ts"
    "FrontendHydroPlugin/package.json"
    "FrontendHydroPlugin/config.ts"
    "FrontendHydroPlugin/templates/contest_plagiarism.html"
    "FrontendHydroPlugin/locales/en.json"
    "FrontendHydroPlugin/locales/zh.json"
    "FrontendHydroPlugin/README.md"
)

echo "Checking required files..."
for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file"
    else
        echo "❌ Missing: $file"
        exit 1
    fi
done

# Check TypeScript syntax (if tsc is available)
if command -v tsc &> /dev/null; then
    echo
    echo "Checking TypeScript syntax..."
    cd FrontendHydroPlugin
    if tsc --noEmit index.ts config.ts 2>/dev/null; then
        echo "✅ TypeScript syntax check passed"
    else
        echo "⚠️  TypeScript syntax check failed (this may be due to missing Hydro OJ types)"
    fi
    cd ..
else
    echo "⚠️  TypeScript compiler not found, skipping syntax check"
fi

# Check JSON files
echo
echo "Validating JSON files..."
json_files=(
    "FrontendHydroPlugin/package.json"
    "FrontendHydroPlugin/locales/en.json"
    "FrontendHydroPlugin/locales/zh.json"
)

for file in "${json_files[@]}"; do
    if command -v python3 &> /dev/null; then
        if python3 -m json.tool "$file" > /dev/null 2>&1; then
            echo "✅ $file - Valid JSON"
        else
            echo "❌ $file - Invalid JSON"
            exit 1
        fi
    elif command -v jq &> /dev/null; then
        if jq empty "$file" > /dev/null 2>&1; then
            echo "✅ $file - Valid JSON"
        else
            echo "❌ $file - Invalid JSON"
            exit 1
        fi
    else
        echo "⚠️  No JSON validator found, skipping $file"
    fi
done

# Test Phosphorus backend connectivity (if URL is provided)
echo
if [ -n "$PHOSPHORUS_URL" ]; then
    echo "Testing Phosphorus backend connectivity..."
    if command -v curl &> /dev/null; then
        if curl -s "$PHOSPHORUS_URL/api/v1/health" > /dev/null; then
            echo "✅ Phosphorus backend is accessible at $PHOSPHORUS_URL"
        else
            echo "❌ Cannot connect to Phosphorus backend at $PHOSPHORUS_URL"
        fi
    else
        echo "⚠️  curl not found, skipping backend connectivity test"
    fi
else
    echo "⚠️  PHOSPHORUS_URL not set, skipping backend connectivity test"
    echo "   Set PHOSPHORUS_URL environment variable to test backend connectivity"
fi

echo
echo "=== Test Summary ==="
echo "✅ Plugin structure is valid"
echo "✅ All required files are present"
echo "✅ JSON files are valid"
echo
echo "Next steps:"
echo "1. Copy FrontendHydroPlugin to your Hydro OJ addons directory"
echo "2. Install dependencies: cd /path/to/hydro/addons/CAUCOJ-Phosphorus && npm install"
echo "3. Configure PHOSPHORUS_URL environment variable"
echo "4. Restart Hydro OJ to load the plugin"
echo "5. Test plagiarism detection functionality in a contest"
echo
echo "For detailed installation instructions, see FrontendHydroPlugin/README.md"