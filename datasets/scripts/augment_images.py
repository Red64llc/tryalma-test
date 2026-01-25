#!/usr/bin/env python3
"""
Script to generate quality-degraded versions of passport images.
Simulates real-world capture conditions for robustness testing.
"""
import os
import cv2
import numpy as np
from pathlib import Path
from typing import Optional
import json

try:
    import albumentations as A
    HAS_ALBUMENTATIONS = True
except ImportError:
    HAS_ALBUMENTATIONS = False
    print("Warning: albumentations not installed. Run: uv add albumentations")

DATASET_ROOT = Path(__file__).parent.parent


# Quality degradation pipelines
def get_blur_pipeline():
    """Motion and focus blur effects."""
    return A.Compose([
        A.OneOf([
            A.MotionBlur(blur_limit=(5, 15), p=1.0),
            A.GaussianBlur(blur_limit=(5, 11), p=1.0),
            A.Defocus(radius=(3, 8), alias_blur=(0.1, 0.5), p=1.0),
        ], p=1.0),
    ])


def get_noise_pipeline():
    """Sensor noise and grain effects."""
    return A.Compose([
        A.OneOf([
            A.GaussNoise(var_limit=(20.0, 80.0), p=1.0),
            A.ISONoise(color_shift=(0.01, 0.05), intensity=(0.1, 0.5), p=1.0),
            A.MultiplicativeNoise(multiplier=(0.9, 1.1), p=1.0),
        ], p=1.0),
    ])


def get_lighting_pipeline():
    """Uneven lighting and shadow effects."""
    return A.Compose([
        A.OneOf([
            A.RandomBrightnessContrast(
                brightness_limit=(-0.3, 0.3),
                contrast_limit=(-0.3, 0.3),
                p=1.0
            ),
            A.RandomShadow(
                shadow_roi=(0, 0, 1, 1),
                num_shadows_lower=1,
                num_shadows_upper=3,
                shadow_dimension=5,
                p=1.0
            ),
            A.RandomToneCurve(scale=0.3, p=1.0),
        ], p=1.0),
    ])


def get_perspective_pipeline():
    """Geometric distortions from angled capture."""
    return A.Compose([
        A.OneOf([
            A.Perspective(scale=(0.05, 0.15), p=1.0),
            A.Affine(
                rotate=(-10, 10),
                shear=(-5, 5),
                scale=(0.9, 1.1),
                p=1.0
            ),
        ], p=1.0),
    ])


def get_compression_pipeline():
    """JPEG compression artifacts."""
    return A.Compose([
        A.ImageCompression(quality_lower=30, quality_upper=70, p=1.0),
    ])


def get_combined_mild_pipeline():
    """Mild combined degradations (realistic good capture)."""
    return A.Compose([
        A.OneOf([
            A.GaussianBlur(blur_limit=(3, 5), p=0.5),
            A.MotionBlur(blur_limit=(3, 5), p=0.5),
        ], p=0.3),
        A.GaussNoise(var_limit=(5.0, 20.0), p=0.3),
        A.RandomBrightnessContrast(
            brightness_limit=0.1,
            contrast_limit=0.1,
            p=0.3
        ),
        A.Perspective(scale=(0.01, 0.03), p=0.2),
        A.ImageCompression(quality_lower=70, quality_upper=95, p=0.3),
    ])


def get_combined_severe_pipeline():
    """Severe combined degradations (stress testing)."""
    return A.Compose([
        A.OneOf([
            A.GaussianBlur(blur_limit=(7, 15), p=0.7),
            A.MotionBlur(blur_limit=(7, 15), p=0.7),
            A.Defocus(radius=(5, 10), p=0.5),
        ], p=0.7),
        A.OneOf([
            A.GaussNoise(var_limit=(30.0, 100.0), p=0.7),
            A.ISONoise(intensity=(0.3, 0.7), p=0.7),
        ], p=0.5),
        A.OneOf([
            A.RandomBrightnessContrast(
                brightness_limit=0.4,
                contrast_limit=0.4,
                p=0.7
            ),
            A.RandomShadow(
                num_shadows_lower=2,
                num_shadows_upper=4,
                p=0.5
            ),
        ], p=0.5),
        A.Perspective(scale=(0.05, 0.15), p=0.4),
        A.ImageCompression(quality_lower=20, quality_upper=50, p=0.5),
    ])


PIPELINES = {
    "blur": get_blur_pipeline,
    "noise": get_noise_pipeline,
    "lighting": get_lighting_pipeline,
    "perspective": get_perspective_pipeline,
    "compression": get_compression_pipeline,
    "combined_mild": get_combined_mild_pipeline,
    "combined_severe": get_combined_severe_pipeline,
}


def augment_image(
    image_path: Path,
    output_dir: Path,
    pipeline_name: str,
    num_variants: int = 3
) -> list:
    """
    Apply augmentation pipeline to an image and save variants.

    Args:
        image_path: Path to source image
        output_dir: Directory to save augmented images
        pipeline_name: Name of the pipeline to use
        num_variants: Number of variants to generate

    Returns:
        List of output file paths
    """
    if not HAS_ALBUMENTATIONS:
        print("Error: albumentations required. Run: uv add albumentations")
        return []

    # Load image
    image = cv2.imread(str(image_path))
    if image is None:
        print(f"Error: Could not load {image_path}")
        return []

    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    # Get pipeline
    pipeline_fn = PIPELINES.get(pipeline_name)
    if pipeline_fn is None:
        print(f"Error: Unknown pipeline '{pipeline_name}'")
        return []

    pipeline = pipeline_fn()

    # Generate variants
    output_dir.mkdir(parents=True, exist_ok=True)
    outputs = []

    for i in range(num_variants):
        # Apply augmentation
        augmented = pipeline(image=image)["image"]

        # Convert back to BGR for saving
        augmented_bgr = cv2.cvtColor(augmented, cv2.COLOR_RGB2BGR)

        # Save with descriptive name
        stem = image_path.stem
        suffix = image_path.suffix
        output_name = f"{stem}_{pipeline_name}_{i+1}{suffix}"
        output_path = output_dir / output_name

        cv2.imwrite(str(output_path), augmented_bgr)
        outputs.append(output_path)

    return outputs


def augment_dataset(
    input_dir: Path,
    output_base: Path,
    pipelines: Optional[list] = None,
    num_variants: int = 3
):
    """
    Augment all images in a directory.

    Args:
        input_dir: Directory containing source images
        output_base: Base directory for augmented outputs
        pipelines: List of pipeline names to apply (default: all)
        num_variants: Number of variants per pipeline
    """
    if pipelines is None:
        pipelines = list(PIPELINES.keys())

    # Find all images
    image_extensions = {".jpg", ".jpeg", ".png", ".bmp", ".tiff"}
    images = [
        f for f in input_dir.rglob("*")
        if f.suffix.lower() in image_extensions
    ]

    print(f"Found {len(images)} images in {input_dir}")
    print(f"Applying pipelines: {pipelines}")
    print(f"Generating {num_variants} variants per pipeline")
    print()

    results = {
        "source_dir": str(input_dir),
        "output_dir": str(output_base),
        "pipelines": pipelines,
        "num_variants": num_variants,
        "images": []
    }

    for img_path in images:
        print(f"Processing: {img_path.name}")
        img_results = {"source": str(img_path), "augmentations": {}}

        for pipeline_name in pipelines:
            output_dir = output_base / pipeline_name
            outputs = augment_image(img_path, output_dir, pipeline_name, num_variants)
            img_results["augmentations"][pipeline_name] = [str(p) for p in outputs]
            print(f"  {pipeline_name}: {len(outputs)} variants")

        results["images"].append(img_results)

    # Save results manifest
    manifest_path = output_base / "augmentation_manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\nAugmentation complete! Manifest saved to {manifest_path}")


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate quality-degraded passport images for testing"
    )
    parser.add_argument(
        "input_dir",
        type=Path,
        help="Directory containing source images"
    )
    parser.add_argument(
        "-o", "--output",
        type=Path,
        default=DATASET_ROOT / "augmented",
        help="Output directory for augmented images"
    )
    parser.add_argument(
        "-p", "--pipelines",
        nargs="+",
        choices=list(PIPELINES.keys()),
        help="Pipelines to apply (default: all)"
    )
    parser.add_argument(
        "-n", "--num-variants",
        type=int,
        default=3,
        help="Number of variants per pipeline (default: 3)"
    )

    args = parser.parse_args()

    if not args.input_dir.exists():
        print(f"Error: Input directory does not exist: {args.input_dir}")
        return

    augment_dataset(
        args.input_dir,
        args.output,
        args.pipelines,
        args.num_variants
    )


if __name__ == "__main__":
    main()
