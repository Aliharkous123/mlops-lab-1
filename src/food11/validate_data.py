import argparse
import hashlib
import sys
from collections import Counter
from pathlib import Path

from PIL import Image

from src.food11.data import CLASSES

SPLITS = ("training", "validation", "evaluation")


def validate(dataset: Path, min_per_class: int, tau: float) -> bool:
    results = {}
    counts = {}
    hashes = {}
    expected_classes = set(CLASSES)

    # Check 1: exactly 11 class folders
    folders_ok = True

    for split in SPLITS:
        split_dir = dataset / split
        actual_classes = (
            {p.name for p in split_dir.iterdir() if p.is_dir()}
            if split_dir.is_dir()
            else set()
        )

        if actual_classes != expected_classes:
            folders_ok = False
            print(f"  Invalid class folders in {split}")

    results["Class folders"] = folders_ok

    # Checks 2, 3, 4
    images_ok = True
    minimum_ok = True
    duplicates_ok = True

    for split in SPLITS:
        counts[split] = Counter()

        for category in CLASSES:
            folder = dataset / split / category

            if not folder.is_dir():
                minimum_ok = False
                continue

            for path in folder.iterdir():
                if not path.is_file():
                    continue

                counts[split][category] += 1

                try:
                    with Image.open(path) as img:
                        img.load()
                        if img.mode != "RGB" or img.size != (128, 128):
                            images_ok = False
                            print(f"  Invalid image: {path}")

                except (OSError, ValueError):
                    images_ok = False
                    print(f"  Cannot open image: {path}")

                digest = hashlib.md5(path.read_bytes()).hexdigest()

                if digest in hashes and hashes[digest] != split:
                    duplicates_ok = False
                    print(f"  Duplicate across splits: {path}")
                else:
                    hashes[digest] = split

            if counts[split][category] < min_per_class:
                minimum_ok = False
                print(f"  Too few images: {split}/{category}")

    results["Image format and size"] = images_ok
    results["Minimum images per class"] = minimum_ok
    results["No duplicates across splits"] = duplicates_ok

    # Check 5: class distribution
    proportions_ok = True

    train_total = sum(counts["training"].values())
    val_total = sum(counts["validation"].values())

    if train_total == 0 or val_total == 0:
        proportions_ok = False
    else:
        for category in CLASSES:
            train_share = counts["training"][category] / train_total
            val_share = counts["validation"][category] / val_total

            if abs(train_share - val_share) > tau:
                proportions_ok = False

    results["Class distribution"] = proportions_ok

    print("\nData validation report")
    print("----------------------")

    for name, passed in results.items():
        print(f"{'PASS' if passed else 'FAIL'} - {name}")

    return all(results.values())


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("dataset", type=Path)
    parser.add_argument("--min-per-class", type=int, default=50)
    parser.add_argument("--tau", type=float, default=0.05)

    args = parser.parse_args()

    if not validate(args.dataset, args.min_per_class, args.tau):
        sys.exit(1)


if __name__ == "__main__":
    main()