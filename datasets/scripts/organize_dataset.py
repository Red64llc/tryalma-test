#!/usr/bin/env python3
"""
Organize passport images into a unified structure with metadata.
"""
import json
import shutil
from pathlib import Path
from typing import Optional
import hashlib

DATASET_ROOT = Path(__file__).parent.parent


def get_file_hash(filepath: Path) -> str:
    """Get MD5 hash of file for deduplication."""
    return hashlib.md5(filepath.read_bytes()).hexdigest()[:8]


def organize_maskrcnn(source_dir: Path, output_dir: Path) -> list:
    """Organize MASK-RCNN dataset images."""
    metadata = []

    # Mapping of folder names to country codes and document types
    folder_mapping = {
        "IndCard": ("IND", "id_card"),
        "IndPass": ("IND", "passport"),
        "PakCNIC": ("PAK", "id_card"),
        "PakPass": ("PAK", "passport"),
    }

    for folder_name, (country_code, doc_type) in folder_mapping.items():
        folder_path = source_dir / folder_name
        if not folder_path.exists():
            continue

        country_dir = output_dir / country_code
        country_dir.mkdir(parents=True, exist_ok=True)

        # Search recursively for images
        for img_file in folder_path.rglob("*"):
            if img_file.suffix.lower() not in [".jpg", ".jpeg", ".png"]:
                continue

            # Create unique filename
            file_hash = get_file_hash(img_file)
            new_name = f"{country_code}_{doc_type}_{file_hash}{img_file.suffix.lower()}"
            dest_path = country_dir / new_name

            if not dest_path.exists():
                # Use symlink instead of copy to save space
                dest_path.symlink_to(img_file.resolve())

            metadata.append({
                "id": f"{country_code}_{file_hash}",
                "filename": str(dest_path.relative_to(output_dir)),
                "country_code": country_code,
                "document_type": doc_type,
                "source": "maskrcnn_dataset",
                "quality": "good",
                "original_path": str(img_file),
            })

    return metadata


def organize_midv500(source_dir: Path, output_dir: Path) -> list:
    """Organize MIDV-500 dataset images."""
    metadata = []

    # MIDV-500 has folders per document type
    # Example structure: midv500/images/01_alb_id/...
    country_codes = {
        "alb": "ALB", "aze": "AZE", "esp": "ESP", "est": "EST",
        "fin": "FIN", "grc": "GRC", "lva": "LVA", "rus": "RUS",
        "srb": "SRB", "svk": "SVK", "deu": "DEU", "usa": "USA",
        "tur": "TUR", "cze": "CZE", "arg": "ARG", "aus": "AUS",
        "bra": "BRA", "chn": "CHN", "gbr": "GBR", "fra": "FRA",
        "aut": "AUT", "chl": "CHL", "ita": "ITA", "pol": "POL",
        "rou": "ROU", "ukr": "UKR", "mex": "MEX", "ind": "IND",
    }

    for tif_file in source_dir.rglob("*.tif"):
        # Extract country from path (e.g., 06_bra_passport)
        for parent in tif_file.parents:
            parts = parent.name.split("_")
            if len(parts) >= 2:
                country_hint = parts[1].lower()
                country_code = country_codes.get(country_hint, "UNK")
                if country_code != "UNK":
                    break
        else:
            country_code = "UNK"

        # Determine document type from path
        doc_type = "passport" if "passport" in str(tif_file).lower() else "id_card"

        country_dir = output_dir / country_code
        country_dir.mkdir(parents=True, exist_ok=True)

        file_hash = get_file_hash(tif_file)
        new_name = f"{country_code}_{doc_type}_{file_hash}.tif"
        dest_path = country_dir / new_name

        if not dest_path.exists():
            # Use symlink instead of copy to save space
            dest_path.symlink_to(tif_file.resolve())

        metadata.append({
            "id": f"{country_code}_{file_hash}",
            "filename": str(dest_path.relative_to(output_dir)),
            "country_code": country_code,
            "document_type": doc_type,
            "source": "midv500",
            "quality": "good",
            "original_path": str(tif_file),
        })

    return metadata


def organize_uae_passports(source_dir: Path, output_dir: Path) -> list:
    """Organize existing UAE passport images."""
    metadata = []
    country_code = "ARE"

    country_dir = output_dir / country_code
    country_dir.mkdir(parents=True, exist_ok=True)

    for img_file in source_dir.glob("*"):
        if img_file.suffix.lower() not in [".jpg", ".jpeg", ".png"]:
            continue

        file_hash = get_file_hash(img_file)
        new_name = f"{country_code}_passport_{file_hash}{img_file.suffix.lower()}"
        dest_path = country_dir / new_name

        if not dest_path.exists():
            # Use symlink instead of copy to save space
            dest_path.symlink_to(img_file.resolve())

        metadata.append({
            "id": f"{country_code}_{file_hash}",
            "filename": str(dest_path.relative_to(output_dir)),
            "country_code": country_code,
            "document_type": "passport",
            "source": "original",
            "quality": "excellent",
            "original_path": str(img_file),
        })

    return metadata


def organize_all():
    """Organize all datasets into unified structure."""
    output_dir = DATASET_ROOT / "organized"
    output_dir.mkdir(exist_ok=True)

    all_metadata = []

    print("Organizing datasets...")
    print()

    # 1. Original UAE passports
    uae_source = DATASET_ROOT / "files"
    if uae_source.exists():
        print("[1/3] Organizing UAE passports...")
        meta = organize_uae_passports(uae_source, output_dir)
        all_metadata.extend(meta)
        print(f"      {len(meta)} images")

    # 2. MASK-RCNN dataset
    maskrcnn_source = DATASET_ROOT / "raw" / "by_source" / "maskrcnn_passports"
    if maskrcnn_source.exists():
        print("[2/3] Organizing MASK-RCNN dataset...")
        meta = organize_maskrcnn(maskrcnn_source, output_dir)
        all_metadata.extend(meta)
        print(f"      {len(meta)} images")

    # 3. MIDV-500 dataset
    midv500_source = DATASET_ROOT / "raw" / "by_source" / "midv500"
    if midv500_source.exists():
        print("[3/3] Organizing MIDV-500 dataset...")
        meta = organize_midv500(midv500_source, output_dir)
        all_metadata.extend(meta)
        print(f"      {len(meta)} images")

    # Save metadata
    metadata_file = DATASET_ROOT / "metadata.json"
    with open(metadata_file, "w") as f:
        json.dump({
            "total_images": len(all_metadata),
            "images": all_metadata
        }, f, indent=2)

    print()
    print(f"Total: {len(all_metadata)} images organized")
    print(f"Metadata saved to: {metadata_file}")

    # Print summary by country
    print()
    print("By country:")
    countries = {}
    for img in all_metadata:
        cc = img["country_code"]
        countries[cc] = countries.get(cc, 0) + 1

    for cc, count in sorted(countries.items(), key=lambda x: -x[1]):
        print(f"  {cc}: {count}")


if __name__ == "__main__":
    organize_all()
