#!/usr/bin/env python3
"""
Script to download and organize passport datasets for testing.
"""
import json
import os
import subprocess
import sys
import urllib.request
from pathlib import Path

DATASET_ROOT = Path(__file__).parent.parent

# Dataset sources with actual download URLs
DATASETS = {
    "midv500": {
        "name": "MIDV-500",
        "url": "https://github.com/fcakyon/midv500",
        "type": "midv500_pip",
        "description": "500 video clips, 50 document types (via pip package)"
    },
    "maskrcnn_passports": {
        "name": "MASK-RCNN Passport Dataset",
        "url": "https://github.com/iAmmarTahir/MASK-RCNN-Dataset",
        "type": "git",
        "description": "500+ passport/ID images with COCO annotations"
    },
    "mrz_dataset": {
        "name": "Dynamsoft MRZ Dataset",
        "url": "https://github.com/tony-xlh/MRZ-dataset",
        "type": "git_with_images",
        "description": "Synthetic MRZ images for OCR testing"
    },
    "huggingface_synthetic": {
        "name": "UniDataPro Synthetic Passports (Preview)",
        "dataset_id": "UniDataPro/synthetic-passports",
        "type": "huggingface",
        "description": "15 sample synthetic passport images"
    },
    "huggingface_usa": {
        "name": "Generated USA Passports",
        "dataset_id": "TrainingDataPro/generated-usa-passeports-dataset",
        "type": "huggingface",
        "description": "Synthetic USA passport images"
    },
    "huggingface_mrz": {
        "name": "MRZ Text Detection",
        "dataset_id": "UniqueData/ocr-generated-machine-readable-zone-mrz-text-detection",
        "type": "huggingface",
        "description": "MRZ-focused dataset with OCR ground truth"
    }
}


def setup_directories():
    """Create the dataset directory structure."""
    dirs = [
        "raw/by_country",
        "raw/by_source/midv2020",
        "raw/by_source/midv500",
        "raw/by_source/synthetic",
        "raw/by_source/huggingface",
        "augmented/blur",
        "augmented/noise",
        "augmented/shadow",
        "augmented/perspective",
        "augmented/combined",
        "annotations/mrz",
        "annotations/fields",
        "annotations/bounding_boxes",
        "splits",
        "scripts",
    ]

    for d in dirs:
        path = DATASET_ROOT / d
        path.mkdir(parents=True, exist_ok=True)
        print(f"Created: {path}")


def download_file(url: str, dest: Path, desc: str = ""):
    """Download a file with progress indicator."""
    print(f"  Downloading {desc or url}...")
    try:
        urllib.request.urlretrieve(url, dest)
        print(f"  Saved to {dest}")
        return True
    except Exception as e:
        print(f"  Failed: {e}")
        return False


def download_ftp_dataset(name: str, base_url: str, files: list, dest: Path):
    """Download files from FTP server."""
    dest.mkdir(parents=True, exist_ok=True)

    print(f"  Downloading from {base_url}")
    for filename in files:
        file_url = f"{base_url}{filename}"
        file_dest = dest / filename

        if file_dest.exists():
            print(f"  {filename} already exists, skipping...")
            continue

        # Use wget or curl for FTP downloads
        try:
            print(f"  Downloading {filename}...")
            result = subprocess.run(
                ["wget", "-q", "--show-progress", "-O", str(file_dest), file_url],
                check=False,
                capture_output=False
            )
            if result.returncode != 0:
                # Try curl as fallback
                subprocess.run(
                    ["curl", "-#", "-o", str(file_dest), file_url],
                    check=True
                )
            print(f"  Downloaded {filename}")
        except Exception as e:
            print(f"  Failed to download {filename}: {e}")
            print(f"  Try manually: wget {file_url}")


def download_huggingface(name: str, dataset_id: str, dest: Path):
    """Download a dataset from Hugging Face."""
    dest.mkdir(parents=True, exist_ok=True)

    # Check if already downloaded
    if (dest / "dataset_info.json").exists():
        print(f"  {name} already downloaded, skipping...")
        return

    print(f"  Downloading {dataset_id} from Hugging Face...")
    try:
        # Import here to avoid dependency if not downloading HF datasets
        from datasets import load_dataset

        ds = load_dataset(dataset_id)
        ds.save_to_disk(str(dest))
        print(f"  Successfully saved to {dest}")
    except ImportError:
        print("  Error: 'datasets' library required. Run: uv add datasets")
    except Exception as e:
        print(f"  Failed to download {dataset_id}: {e}")


def download_git_repo(name: str, url: str, dest: Path):
    """Clone a git repository."""
    if (dest / ".git").exists():
        print(f"  {name} already cloned, skipping...")
        return True

    dest.parent.mkdir(parents=True, exist_ok=True)
    print(f"  Cloning {url}...")
    try:
        subprocess.run(
            ["git", "clone", "--depth", "1", url, str(dest)],
            check=True,
            capture_output=True
        )
        print(f"  Successfully cloned {name}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"  Failed to clone: {e}")
        return False


def download_midv500_pip(dest: Path):
    """Download MIDV-500 using the midv500 pip package."""
    dest.mkdir(parents=True, exist_ok=True)

    # Check if already downloaded
    if list(dest.glob("*.tif")) or list(dest.glob("*/*.tif")):
        print("  MIDV-500 images already exist, skipping...")
        return

    print("  Installing midv500 package...")
    try:
        subprocess.run(
            ["uv", "add", "midv500"],
            check=True,
            capture_output=True
        )
    except subprocess.CalledProcessError:
        print("  Failed to install midv500 package")
        return

    print("  Downloading MIDV-500 dataset (this may take a while)...")
    try:
        # Use the midv500 package to download
        download_script = f'''
import midv500
midv500.download_dataset("{dest}")
'''
        subprocess.run(
            ["uv", "run", "python", "-c", download_script],
            check=True,
            timeout=600  # 10 minute timeout
        )
        print(f"  Successfully downloaded to {dest}")
    except subprocess.TimeoutExpired:
        print("  Download timed out - dataset is large, try running manually:")
        print(f"    uv run python -c \"import midv500; midv500.download_dataset('{dest}')\"")
    except Exception as e:
        print(f"  Failed to download: {e}")


def download_mrz_images(dest: Path):
    """Download images from the MRZ dataset using data.json."""
    data_json = dest / "data.json"
    if not data_json.exists():
        print("  data.json not found, cloning repo first...")
        subprocess.run(
            ["git", "clone", "--depth", "1",
             "https://github.com/tony-xlh/MRZ-dataset", str(dest)],
            check=True,
            capture_output=True
        )

    images_dir = dest / "images"
    images_dir.mkdir(exist_ok=True)

    with open(data_json) as f:
        data = json.load(f)

    print(f"  Downloading {len(data['images'])} images...")
    downloaded = 0
    for i, img in enumerate(data["images"]):
        url = img.get("url")
        filename = img.get("filename")
        if url and filename:
            img_path = images_dir / filename
            if img_path.exists():
                downloaded += 1
                continue
            try:
                urllib.request.urlretrieve(url, img_path)
                downloaded += 1
                print(f"  [{downloaded}/{len(data['images'])}] {filename}")
            except Exception as e:
                print(f"  Failed: {filename} - {e}")
    print(f"  Downloaded {downloaded} images")


def download_all(datasets_to_download: list = None):
    """Download all or specified datasets."""
    print("=" * 60)
    print("Passport Dataset Downloader")
    print("=" * 60)

    setup_directories()
    print()

    if datasets_to_download is None:
        datasets_to_download = list(DATASETS.keys())

    for key in datasets_to_download:
        if key not in DATASETS:
            print(f"Unknown dataset: {key}")
            continue

        info = DATASETS[key]
        print(f"\n[{info['name']}]")
        print(f"  Description: {info['description']}")

        dest = DATASET_ROOT / "raw" / "by_source" / key

        if info["type"] == "ftp":
            download_ftp_dataset(info["name"], info["url"], info.get("files", []), dest)
        elif info["type"] == "huggingface":
            download_huggingface(info["name"], info["dataset_id"], dest)
        elif info["type"] == "git_with_images":
            download_mrz_images(dest)
        elif info["type"] == "git":
            download_git_repo(info["name"], info["url"], dest)
        elif info["type"] == "midv500_pip":
            download_midv500_pip(dest)

    print("\n" + "=" * 60)
    print("Download complete!")
    print("=" * 60)


def download_single(dataset_key: str):
    """Download a single dataset."""
    if dataset_key not in DATASETS:
        print(f"Unknown dataset: {dataset_key}")
        print(f"Available: {', '.join(DATASETS.keys())}")
        return
    download_all([dataset_key])


def create_country_list():
    """Create a list of all countries with ISO codes."""
    countries = [
        # North America
        ("USA", "United States"),
        ("CAN", "Canada"),
        ("MEX", "Mexico"),
        # Europe - Western
        ("GBR", "United Kingdom"),
        ("DEU", "Germany"),
        ("FRA", "France"),
        ("ITA", "Italy"),
        ("ESP", "Spain"),
        ("NLD", "Netherlands"),
        ("BEL", "Belgium"),
        ("CHE", "Switzerland"),
        ("AUT", "Austria"),
        ("PRT", "Portugal"),
        ("IRL", "Ireland"),
        # Europe - Northern
        ("SWE", "Sweden"),
        ("NOR", "Norway"),
        ("DNK", "Denmark"),
        ("FIN", "Finland"),
        # Europe - Eastern
        ("POL", "Poland"),
        ("CZE", "Czech Republic"),
        ("ROU", "Romania"),
        ("HUN", "Hungary"),
        ("UKR", "Ukraine"),
        ("RUS", "Russia"),
        # Asia - East
        ("CHN", "China"),
        ("JPN", "Japan"),
        ("KOR", "South Korea"),
        ("TWN", "Taiwan"),
        ("HKG", "Hong Kong"),
        # Asia - South
        ("IND", "India"),
        ("PAK", "Pakistan"),
        ("BGD", "Bangladesh"),
        ("LKA", "Sri Lanka"),
        # Asia - Southeast
        ("PHL", "Philippines"),
        ("VNM", "Vietnam"),
        ("THA", "Thailand"),
        ("IDN", "Indonesia"),
        ("MYS", "Malaysia"),
        ("SGP", "Singapore"),
        # Middle East
        ("ARE", "United Arab Emirates"),
        ("SAU", "Saudi Arabia"),
        ("ISR", "Israel"),
        ("TUR", "Turkey"),
        ("IRN", "Iran"),
        ("IRQ", "Iraq"),
        # Africa
        ("NGA", "Nigeria"),
        ("ZAF", "South Africa"),
        ("EGY", "Egypt"),
        ("KEN", "Kenya"),
        ("MAR", "Morocco"),
        ("ETH", "Ethiopia"),
        ("GHA", "Ghana"),
        # South America
        ("BRA", "Brazil"),
        ("ARG", "Argentina"),
        ("COL", "Colombia"),
        ("CHL", "Chile"),
        ("PER", "Peru"),
        ("VEN", "Venezuela"),
        # Oceania
        ("AUS", "Australia"),
        ("NZL", "New Zealand"),
    ]

    for code, name in countries:
        country_dir = DATASET_ROOT / "raw" / "by_country" / code
        country_dir.mkdir(parents=True, exist_ok=True)

    country_file = DATASET_ROOT / "countries.json"
    with open(country_file, "w") as f:
        json.dump(
            [{"code": code, "name": name} for code, name in countries],
            f,
            indent=2
        )

    print(f"Created {len(countries)} country directories")
    print(f"Country list saved to {country_file}")


def list_datasets():
    """List available datasets."""
    print("Available datasets:")
    print()
    for key, info in DATASETS.items():
        print(f"  {key:25} - {info['description']}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  uv run python download_datasets.py setup      - Create directory structure")
        print("  uv run python download_datasets.py countries  - Create country directories")
        print("  uv run python download_datasets.py list       - List available datasets")
        print("  uv run python download_datasets.py download   - Download all datasets")
        print("  uv run python download_datasets.py download <name> - Download specific dataset")
        print()
        print("Examples:")
        print("  uv run python download_datasets.py download huggingface_synthetic")
        print("  uv run python download_datasets.py download mrz_dataset")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "setup":
        setup_directories()
    elif cmd == "countries":
        create_country_list()
    elif cmd == "list":
        list_datasets()
    elif cmd == "download":
        if len(sys.argv) > 2:
            download_single(sys.argv[2])
        else:
            download_all()
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)
