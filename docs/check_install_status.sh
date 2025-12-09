#!/bin/bash
# Quick script to check if Command Line Tools installation is complete

echo "Checking Command Line Tools installation status..."
echo ""

# Check if installer is running
if ps aux | grep -i "Install Command Line Developer Tools" | grep -v grep > /dev/null; then
    echo "⏳ Installer is still running... Please wait."
    echo "   This typically takes 10-15 minutes."
    exit 1
fi

# Check if directory exists
if [ -d "/Library/Developer/CommandLineTools" ]; then
    echo "✅ Command Line Tools directory found!"
    echo ""
    xcode-select -p 2>&1
    echo ""
    pkgutil --pkg-info=com.apple.pkg.CLTools_Executables 2>&1 | grep version
    echo ""
    echo "✅ Installation appears complete! Ready to install MongoDB."
    exit 0
else
    echo "⏳ Installation not complete yet..."
    echo "   The installer may have finished but directory not created yet."
    echo "   Try running: sudo xcode-select --reset"
    exit 1
fi

