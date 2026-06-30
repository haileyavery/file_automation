#!/usr/bin/env python3
"""
sort_downloads.py
------------------
Automatically organizes a Downloads folder by moving files into
subfolders based on file type (PDFs, Images, Installers, Documents,
Archives, Audio, Video, Spreadsheets, Code, Others).

USAGE
-----
One-time sort:
    python sort_downloads.py

Specify a different folder:
    python sort_downloads.py --path "C:/Users/me/Downloads"

Preview without moving anything:
    python sort_downloads.py --dry-run

"""

import argparse
import shutil
import sys
import time
from pathlib import Path

# map file folder names
CATEGORIES = {
    "PDFs": {".pdf"},
    "Images": {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".webp",
               ".tiff", ".heic", ".ico"},
    "Installers": {".exe", ".msi", ".dmg", ".pkg", ".deb", ".rpm", ".appimage"},
    "Archives": {".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz"},
    "Documents": {".doc", ".docx", ".txt", ".rtf", ".odt", ".pages", ".md"},
    "Spreadsheets": {".xls", ".xlsx", ".csv", ".ods", ".numbers"},
    "Presentations": {".ppt", ".pptx", ".key", ".odp"},
    "Audio": {".mp3", ".wav", ".aac", ".flac", ".m4a", ".ogg"},
    "Video": {".mp4", ".mov", ".avi", ".mkv", ".wmv", ".flv", ".webm"},
    "Code": {".py", ".js", ".ts", ".html", ".css", ".json", ".java", ".cpp",
             ".c", ".sh", ".ipynb", ".sql"},
}

# Files placed in a catch-all folder if their extension isn't recognized
CATCH_ALL = "Others"

# Files/folders to always ignore
IGNORE_NAMES = {".DS_Store", "desktop.ini", ".gitkeep"}


def get_category(file_path: Path) -> str:
    """Return the target folder name for a given file based on its extension."""
    ext = file_path.suffix.lower()
    for category, extensions in CATEGORIES.items():
        if ext in extensions:
            return category
    return CATCH_ALL


def unique_destination(dest_folder: Path, filename: str) -> Path:
    """
    Avoid overwriting existing files: if 'report.pdf' exists,
    use 'report (1).pdf', 'report (2).pdf', etc.
    """
    dest = dest_folder / filename
    if not dest.exists():
        return dest

    stem = dest.stem
    suffix = dest.suffix
    counter = 1
    while True:
        candidate = dest_folder / f"{stem} ({counter}){suffix}"
        if not candidate.exists():
            return candidate
        counter += 1


def sort_folder(folder: Path, dry_run: bool = False, verbose: bool = True) -> int:
    """
    Sort all top-level files in `folder` into category subfolders.
    Returns the number of files moved (or that would be moved, if dry_run).
    """
    if not folder.exists():
        print(f"Error: folder does not exist: {folder}")
        sys.exit(1)

    moved_count = 0
    category_folder_names = set(CATEGORIES.keys()) | {CATCH_ALL}

    for item in sorted(folder.iterdir()):
        # Skip directories (including the category folders we create)
        if item.is_dir():
            continue
        # Skip hidden/system files
        if item.name in IGNORE_NAMES or item.name.startswith("."):
            continue
        # Skip files that are still downloading (common partial-download extensions)
        if item.suffix.lower() in {".crdownload", ".part", ".download", ".tmp"}:
            continue

        category = get_category(item)
        dest_folder = folder / category
        dest_path = unique_destination(dest_folder, item.name)

        if verbose:
            action = "[DRY RUN] Would move" if dry_run else "Moving"
            print(f"{action}: {item.name}  ->  {category}/{dest_path.name}")

        if not dry_run:
            dest_folder.mkdir(exist_ok=True)
            shutil.move(str(item), str(dest_path))

        moved_count += 1

    return moved_count


def watch_folder(folder: Path, interval: int, dry_run: bool = False):
    """Continuously poll the folder and sort new files every `interval` seconds."""
    print(f"Watching {folder} every {interval}s. Press Ctrl+C to stop.")
    try:
        while True:
            moved = sort_folder(folder, dry_run=dry_run, verbose=True)
            if moved == 0:
                print("No new files to sort.")
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\nStopped watching.")


def main():
    parser = argparse.ArgumentParser(
        description="Auto-sort a Downloads folder by file type."
    )
    parser.add_argument(
        "--path",
        type=str,
        default=str(Path.home() / "Downloads"),
        help="Path to the folder to sort (default: ~/Downloads)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be moved without actually moving anything",
    )
    parser.add_argument(
        "--watch",
        action="store_true",
        help="Run continuously, sorting new files as they appear",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=10,
        help="Seconds between checks when using --watch (default: 10)",
    )
    args = parser.parse_args()

    folder = Path(args.path).expanduser().resolve()

    if args.watch:
        watch_folder(folder, interval=args.interval, dry_run=args.dry_run)
    else:
        moved = sort_folder(folder, dry_run=args.dry_run)
        word = "would be" if args.dry_run else "were"
        print(f"\nDone. {moved} file(s) {word} sorted in {folder}")


if __name__ == "__main__":
    main()