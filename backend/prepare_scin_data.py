"""
Build train/val (and optional test) image folders from the SCIN dataset layout
used in scin_demo.ipynb: merged scin_cases + scin_labels CSVs and images under
dataset/images/.

Same layout as the public bucket (see notebook Globals):
  <scin_root>/dataset/scin_cases.csv
  <scin_root>/dataset/scin_labels.csv
  <scin_root>/dataset/images/...

From the repo root (creates scin_data/dataset/):
  mkdir -p scin_data && gsutil -m cp -r gs://dx-scin-public-data/dataset scin_data/

Splits by case_id (not by image) so views of the same case stay in one split.
"""

from __future__ import annotations

import argparse
import ast
import shutil
from pathlib import Path
from collections import Counter

import pandas as pd
from sklearn.model_selection import train_test_split
from tqdm import tqdm

IMAGE_PATH_COLUMNS = ["image_1_path", "image_2_path", "image_3_path"]
WEIGHTED_LABEL_COL = "weighted_skin_condition_label"
CASES_CSV = "dataset/scin_cases.csv"
LABELS_CSV = "dataset/scin_labels.csv"


def _sanitize_class(name: str) -> str:
    """Sanitizes class folder names by removing invalid path characters.

    Args:
        name (str): Original string (e.g., class label).

    Returns:
        str: Sanitized file-system safe string.
    """
    for c in r'\/:*?"<>|':
        name = name.replace(c, "_")
    s = name.strip()
    return s if s else "unknown"


def _primary_label_from_weighted(cell) -> str | None:
    """Extracts the primary (highest probability) label from a dictionary-like string.

    Args:
        cell (str | list): The CSV cell contents representing weighted labels.

    Returns:
        str | None: The max-weighted label, or None if invalid.
    """
    if pd.isna(cell):
        return None
    try:
        d = ast.literal_eval(str(cell))
    except (ValueError, SyntaxError):
        return None
    if not isinstance(d, dict) or not d:
        return None
    return max(d.items(), key=lambda x: x[1])[0]


def load_scin_merged(scin_root: Path) -> pd.DataFrame:
    """Loads and merges the SCIN case and label CSV files into one DataFrame.

    Args:
        scin_root (Path): Directory where SCIN CSV files exist.

    Returns:
        pd.DataFrame: Merged DataFrame grouping metadata and image paths.

    Raises:
        FileNotFoundError: If cases or labels CSV do not exist.
    """
    scin_root = Path(scin_root)
    cases_path = scin_root / CASES_CSV
    labels_path = scin_root / LABELS_CSV
    if not cases_path.is_file():
        raise FileNotFoundError(f"Missing {cases_path}")
    if not labels_path.is_file():
        raise FileNotFoundError(f"Missing {labels_path}")

    cases_df = pd.read_csv(cases_path, dtype={"case_id": str})
    labels_df = pd.read_csv(labels_path, dtype={"case_id": str})
    merged = pd.merge(cases_df, labels_df, on="case_id")
    return merged


def build_case_records(
    df: pd.DataFrame,
    min_cases_per_class: int,
    max_classes: int | None,
) -> tuple[list[dict], list[str]]:
    """Generates case-level structures containing valid primary labels and relative image paths.

    Ensures that classes meet minimum count requirements and cuts off lower-count classes if
    `max_classes` is enforced.

    Args:
        df (pd.DataFrame): Merged SCIN dataframe.
        min_cases_per_class (int): Threshold representing minimum required classes to keep.
        max_classes (int | None): Limit on number of classes to export.

    Returns:
        tuple[list[dict], list[str]]: List of valid records and a sorted list of class names.
    """
    rows: list[dict] = []
    for _, row in df.iterrows():
        label = _primary_label_from_weighted(row.get(WEIGHTED_LABEL_COL))
        if label is None:
            continue
        paths = []
        for col in IMAGE_PATH_COLUMNS:
            if col not in row.index:
                continue
            p = row[col]
            if pd.isna(p) or not str(p).strip():
                continue
            paths.append(str(p).strip())
        if not paths:
            continue
        rows.append(
            {
                "case_id": str(row["case_id"]),
                "label": label,
                "paths": paths,
            }
        )

    label_counts = Counter(r["label"] for r in rows)
    if max_classes is not None and max_classes > 0:
        top = {lab for lab, _ in label_counts.most_common(max_classes)}
        rows = [r for r in rows if r["label"] in top]

    label_counts = Counter(r["label"] for r in rows)
    keep_labels = {lab for lab, c in label_counts.items() if c >= min_cases_per_class}
    rows = [r for r in rows if r["label"] in keep_labels]

    classes_sorted = sorted({r["label"] for r in rows})
    return rows, classes_sorted


def prepare_scin_layout(
    scin_root: Path,
    target_dir: Path,
    train_ratio: float,
    val_ratio: float,
    test_ratio: float,
    seed: int,
    min_cases_per_class: int,
    max_classes: int | None,
    symlink: bool,
) -> None:
    """Prepares stratified Train/Val/Test directories by copying/symlinking SCIN files.

    Args:
        scin_root (Path): Directory of the raw SCIN dataset.
        target_dir (Path): Output destination directory.
        train_ratio (float): Ratio of dataset allocated to training.
        val_ratio (float): Ratio allocated for validation.
        test_ratio (float): Ratio allocated for testing.
        seed (int): Random seed for reproducible stratified splitting.
        min_cases_per_class (int): Minimum cases required to retain a class label.
        max_classes (int | None): Max number of distinct class folders to output.
        symlink (bool): Whether to create symlinks instead of physically copying files.

    Raises:
        ValueError: If ratio sums are not equivalent to 1.0.
        RuntimeError: If data filters result in zero cases.
    """
    if abs(train_ratio + val_ratio + test_ratio - 1.0) > 1e-6:
        raise ValueError("train_ratio + val_ratio + test_ratio must sum to 1")

    scin_root = Path(scin_root).resolve()
    target_dir = Path(target_dir).resolve()

    df = load_scin_merged(scin_root)
    records, classes = build_case_records(df, min_cases_per_class, max_classes)
    if not records:
        raise RuntimeError("No cases left after filtering; relax --min_cases_per_class or --max_classes")

    labels = [r["label"] for r in records]

    # Stratify if every class has at least 2 cases (sklearn requirement)
    stratify = labels if min(Counter(labels).values()) >= 2 else None

    temp_ratio = val_ratio + test_ratio
    if temp_ratio <= 0:
        train_rec, rest_rec = records, []
    else:
        train_rec, rest_rec = train_test_split(
            records,
            test_size=temp_ratio,
            random_state=seed,
            stratify=stratify,
        )

    if test_ratio <= 0 or not rest_rec:
        val_rec, test_rec = rest_rec, []
    elif val_ratio <= 0:
        val_rec, test_rec = [], rest_rec
    else:
        frac_val_of_rest = val_ratio / temp_ratio
        labels_rest = [r["label"] for r in rest_rec]
        st2 = labels_rest if min(Counter(labels_rest).values()) >= 2 else None
        val_rec, test_rec = train_test_split(
            rest_rec,
            test_size=1.0 - frac_val_of_rest,
            random_state=seed,
            stratify=st2,
        )

    class_to_dir = {_sanitize_class(c): c for c in classes}

    def copy_case_images(split_name: str, split_records: list[dict]) -> None:
        """Copies or symlinks images for a given split into the target directory structure.

        Args:
            split_name (str): The name of the dataset split (e.g., 'train', 'val').
            split_records (list[dict]): List of case records to copy/symlink.
        """
        for rec in tqdm(split_records, desc=f"{split_name}"):
            lab_dir = _sanitize_class(rec["label"])
            out_class = target_dir / split_name / lab_dir
            out_class.mkdir(parents=True, exist_ok=True)
            for i, rel in enumerate(rec["paths"]):
                src = scin_root / rel
                if not src.is_file():
                    continue
                ext = src.suffix.lower() or ".jpg"
                dst = out_class / f"{rec['case_id']}_{i}{ext}"
                if dst.exists():
                    continue
                if symlink:
                    try:
                        dst.symlink_to(src)
                    except OSError:
                        shutil.copy2(src, dst)
                else:
                    shutil.copy2(src, dst)

    for split_name, split_records in [
        ("train", train_rec),
        ("val", val_rec),
        ("test", test_rec),
    ]:
        if not split_records:
            continue
        (target_dir / split_name).mkdir(parents=True, exist_ok=True)
        copy_case_images(split_name, split_records)

    # Save class list (sanitized folder names, one per line)
    names_path = target_dir / "scin_class_names.txt"
    with open(names_path, "w") as f:
        for c in sorted(class_to_dir.keys()):
            f.write(f"{c}\n")

    print("\nSCIN layout prepared.")
    print(f"  Classes (folder names): {len(class_to_dir)}")
    print(f"  Train cases: {len(train_rec)}  Val: {len(val_rec)}  Test: {len(test_rec)}")
    print(f"  Output: {target_dir}")
    print(f"  Class list: {names_path}")
    print(f"\nTrain with e.g.:\n  python train.py --data_dir {target_dir} --num_classes {len(class_to_dir)}")


def main():
    """CLI entry-point for parsing arguments and launching SCIN layout preparation."""
    p = argparse.ArgumentParser(description="Prepare SCIN dataset for train.py (folder layout)")
    p.add_argument(
        "--scin_root",
        type=str,
        required=True,
        help="Directory containing dataset/scin_cases.csv, dataset/scin_labels.csv, dataset/images/",
    )
    p.add_argument(
        "--target_dir",
        type=str,
        default="data_scin",
        help="Output directory with train/val[/test] class subfolders",
    )
    p.add_argument("--train_ratio", type=float, default=0.7)
    p.add_argument("--val_ratio", type=float, default=0.15)
    p.add_argument("--test_ratio", type=float, default=0.15)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument(
        "--min_cases_per_class",
        type=int,
        default=2,
        help="Drop classes with fewer cases (needed for stratified split)",
    )
    p.add_argument(
        "--max_classes",
        type=int,
        default=None,
        help="If set, keep only the N most frequent condition labels",
    )
    p.add_argument(
        "--symlink",
        action="store_true",
        help="Symlink images instead of copying (saves disk; same filesystem required)",
    )
    args = p.parse_args()

    prepare_scin_layout(
        scin_root=Path(args.scin_root),
        target_dir=Path(args.target_dir),
        train_ratio=args.train_ratio,
        val_ratio=args.val_ratio,
        test_ratio=args.test_ratio,
        seed=args.seed,
        min_cases_per_class=args.min_cases_per_class,
        max_classes=args.max_classes,
        symlink=args.symlink,
    )


if __name__ == "__main__":
    main()
