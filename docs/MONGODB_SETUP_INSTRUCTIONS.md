# MongoDB Local Setup - Manual Steps

Since MongoDB installation requires updating Command Line Tools (which needs sudo access), please run these commands **one at a time** in your terminal:

## Step 1: Update Command Line Tools

Open Terminal and run:

```bash
# Remove old Command Line Tools
sudo rm -rf /Library/Developer/CommandLineTools

# Install new Command Line Tools (this will open a GUI installer)
sudo xcode-select --install
```

**Note:** The `xcode-select --install` command will open a GUI installer window. Please:
1. Click "Install" in the popup window
2. Wait for the download and installation to complete (this may take 10-15 minutes)
3. Once complete, come back here and continue

## Step 2: Verify Command Line Tools Installation

After the installer completes, verify it worked:

```bash
xcode-select -p
```

You should see: `/Library/Developer/CommandLineTools`

## Step 3: Install MongoDB

Now install MongoDB:

```bash
# Install MongoDB 7.0
brew install mongodb-community@7.0

# Link it so it's available in PATH
brew link mongodb-community@7.0

# Start MongoDB service
brew services start mongodb-community@7.0
```

## Step 4: Verify MongoDB is Running

```bash
# Check if MongoDB service is running
brew services list | grep mongodb

# Test MongoDB connection
mongosh --version
```

You should see MongoDB shell version information.

## Step 5: Test Connection with Python

Once MongoDB is running, test the connection:

```bash
cd /Users/anish/MovieTrendAnalyzer-1
python3 tests/test_database.py
```

Both PostgreSQL and MongoDB should now show ✅ PASS.

## Step 6: Load Data into MongoDB

```bash
python3 src/data_loader.py
```

This will load the movie data into both PostgreSQL and MongoDB.

---

**Troubleshooting:**

If you get "Command Line Tools are too outdated" even after updating:
1. Make sure the installer completed fully
2. Try restarting Terminal
3. Check version: `pkgutil --pkg-info=com.apple.pkg.CLTools_Executables`

If MongoDB won't start:
```bash
brew services restart mongodb-community@7.0
brew services list
```

