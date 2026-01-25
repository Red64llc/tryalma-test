# Passport Dataset

Dataset of passport and ID card images for testing document extraction systems.

## Quick Start

```bash
# 1. Download datasets (run from project root)
uv run python datasets/scripts/download_datasets.py download

# 2. Organize into unified structure
uv run python datasets/scripts/organize_dataset.py

# 3. (Optional) Generate quality variations
uv add albumentations opencv-python
uv run python datasets/scripts/augment_images.py datasets/organized/IND/ -o datasets/augmented/ -n 3
```

## Dataset Structure

```
datasets/
├── README.md              # This file
├── metadata.json          # Full index with all image metadata
├── countries.json         # List of country codes
├── files/                 # Original sample images (UAE)
├── raw/                   # Downloaded source datasets
│   └── by_source/
│       ├── maskrcnn_passports/   # India, Pakistan IDs
│       └── midv500/              # MIDV-500 benchmark
├── organized/             # Unified structure (symlinks)
│   ├── ARE/              # UAE - 15 images
│   ├── AUT/              # Austria - 903 images
│   ├── AZE/              # Azerbaijan - 301 images
│   ├── BRA/              # Brazil - 301 images
│   ├── ALB/              # Albania - 301 images
│   ├── PAK/              # Pakistan - 250 images
│   └── IND/              # India - 230 images
├── augmented/            # Quality-degraded versions
│   ├── blur/
│   ├── noise/
│   ├── lighting/
│   └── combined/
└── scripts/
    ├── download_datasets.py    # Download source datasets
    ├── organize_dataset.py     # Organize into unified structure
    └── augment_images.py       # Generate quality variations
```

## Available Datasets

| Dataset | Command | Description |
|---------|---------|-------------|
| MIDV-500 | `download midv500` | 50 document types, 500 videos |
| MASK-RCNN | `download maskrcnn_passports` | India/Pakistan IDs with annotations |
| MRZ Dataset | `download mrz_dataset` | MRZ-focused images |

List all available datasets:
```bash
uv run python datasets/scripts/download_datasets.py list
```

## Metadata Format

Each image in `metadata.json` has:

```json
{
  "id": "IND_a1b2c3d4",
  "filename": "IND/IND_passport_a1b2c3d4.jpg",
  "country_code": "IND",
  "document_type": "passport",
  "source": "maskrcnn_dataset",
  "quality": "good",
  "original_path": "/path/to/original/file.jpg"
}
```

## Quality Augmentation

Generate degraded versions to test extraction robustness:

```bash
# All augmentation types
uv run python datasets/scripts/augment_images.py datasets/organized/ARE/ -o datasets/augmented/

# Specific augmentations only
uv run python datasets/scripts/augment_images.py datasets/organized/ARE/ -p blur noise -n 5
```

Available pipelines:
- `blur` - Motion and focus blur
- `noise` - Sensor noise and grain
- `lighting` - Shadows and brightness variations
- `perspective` - Angled capture distortion
- `compression` - JPEG artifacts
- `combined_mild` - Realistic good capture
- `combined_severe` - Stress testing

## Usage in Code

```python
import json
from pathlib import Path

# Load metadata
with open("datasets/metadata.json") as f:
    data = json.load(f)

# Filter by country
india_images = [
    img for img in data["images"]
    if img["country_code"] == "IND"
]

# Get file paths
for img in india_images[:5]:
    path = Path("datasets/organized") / img["filename"]
    print(f"{img['id']}: {path}")
```

## Git Configuration

Only sample images (ARE, IND) are tracked in git. To download the full dataset:

```bash
uv run python datasets/scripts/download_datasets.py download
uv run python datasets/scripts/organize_dataset.py
```

## Sources

- [MIDV-500](https://github.com/fcakyon/midv500) - Academic benchmark dataset
- [MASK-RCNN Dataset](https://github.com/iAmmarTahir/MASK-RCNN-Dataset) - Passport/ID segmentation dataset
- [MRZ Dataset](https://github.com/tony-xlh/MRZ-dataset) - MRZ-focused images

## Country Codes (ISO 3166-1 alpha-3)

| Code | Country |
|------|---------|
| ARE | United Arab Emirates |
| AUT | Austria |
| AZE | Azerbaijan |
| BRA | Brazil |
| ALB | Albania |
| PAK | Pakistan |
| IND | India |
