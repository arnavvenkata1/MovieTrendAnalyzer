#!/bin/bash
# MongoDB Local Setup Script
# Run this script to update Command Line Tools and install MongoDB

echo "============================================================"
echo "MONGODB LOCAL SETUP"
echo "============================================================"
echo ""

# Step 1: Update Command Line Tools
echo "[1] Updating Command Line Tools..."
echo "    This will remove old tools and install new ones."
echo "    You may see a GUI installer - please follow its instructions."
echo ""
read -p "Press Enter to continue or Ctrl+C to cancel..."

sudo rm -rf /Library/Developer/CommandLineTools
sudo xcode-select --install

echo ""
echo "[2] Waiting for Command Line Tools installation to complete..."
echo "    Please wait for the installer to finish, then press Enter here to continue..."
read -p "Press Enter after Command Line Tools installation is complete..."

# Step 2: Install MongoDB
echo ""
echo "[3] Installing MongoDB Community Edition 7.0..."
brew install mongodb-community@7.0

# Step 3: Link MongoDB
echo ""
echo "[4] Linking MongoDB..."
brew link mongodb-community@7.0

# Step 4: Start MongoDB service
echo ""
echo "[5] Starting MongoDB service..."
brew services start mongodb-community@7.0

# Step 5: Verify installation
echo ""
echo "[6] Verifying MongoDB installation..."
sleep 2
mongosh --version

echo ""
echo "============================================================"
echo "MongoDB setup complete!"
echo "============================================================"
echo ""
echo "You can now run the data loader:"
echo "  python3 src/data_loader.py"
echo ""

