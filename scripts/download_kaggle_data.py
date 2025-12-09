"""
Download Kaggle Dataset and Copy to data/raw/
Script to automate Kaggle dataset download
"""

import kagglehub
import shutil
from pathlib import Path
import sys

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config.settings import DATA_RAW_PATH


def download_kaggle_dataset():
    """Download TMDB movie metadata dataset from Kaggle"""
    print("=" * 60)
    print("DOWNLOADING KAGGLE DATASET")
    print("=" * 60)
    
    # Download latest version
    print("\n[1] Downloading dataset from Kaggle...")
    try:
        path = kagglehub.dataset_download("tmdb/tmdb-movie-metadata")
        print(f"  ✓ Dataset downloaded to: {path}")
    except Exception as e:
        print(f"  ✗ Error downloading dataset: {e}")
        print("\n  Make sure you have kagglehub installed:")
        print("    pip install kagglehub")
        return False
    
    # Find CSV files in downloaded directory
    print("\n[2] Locating CSV files...")
    csv_files = list(Path(path).glob("*.csv"))
    
    if not csv_files:
        print(f"  ✗ No CSV files found in {path}")
        return False
    
    print(f"  ✓ Found {len(csv_files)} CSV file(s):")
    for csv_file in csv_files:
        print(f"    - {csv_file.name}")
    
    # Copy files to data/raw/
    print("\n[3] Copying files to data/raw/...")
    DATA_RAW_PATH.mkdir(parents=True, exist_ok=True)
    
    copied_count = 0
    for csv_file in csv_files:
        dest_path = DATA_RAW_PATH / csv_file.name
        try:
            shutil.copy2(csv_file, dest_path)
            print(f"  ✓ Copied {csv_file.name} -> {dest_path}")
            copied_count += 1
        except Exception as e:
            print(f"  ✗ Error copying {csv_file.name}: {e}")
    
    # Verify expected files exist
    print("\n[4] Verifying files...")
    expected_files = ["tmdb_5000_movies.csv", "tmdb_5000_credits.csv"]
    all_present = True
    
    for expected_file in expected_files:
        file_path = DATA_RAW_PATH / expected_file
        if file_path.exists():
            file_size = file_path.stat().st_size / (1024 * 1024)  # Size in MB
            print(f"  ✓ {expected_file} exists ({file_size:.2f} MB)")
        else:
            print(f"  ⚠ {expected_file} not found (may be optional)")
    
    print("\n" + "=" * 60)
    print("DOWNLOAD COMPLETE")
    print(f"Files copied to: {DATA_RAW_PATH}")
    print("=" * 60)
    
    return copied_count > 0


if __name__ == "__main__":
    success = download_kaggle_dataset()
    sys.exit(0 if success else 1)

