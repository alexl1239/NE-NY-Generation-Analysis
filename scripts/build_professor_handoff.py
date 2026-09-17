#!/usr/bin/env python3
"""Create a minimal, checksummed ZIP for the professor handoff."""

from __future__ import annotations

import argparse
import hashlib
import shutil
import subprocess
import sys
import tempfile
import zipfile
from datetime import date
from pathlib import Path

from rebuild_project import PROJECT_ROOT, required_inputs


PACKAGE_ROOT_NAME = "NE-NY-Generation-Analysis-professor-handoff"
ROOT_FILES = (
    "PROFESSOR_HANDOFF.md",
    "README.md",
    "requirements.txt",
)
ALLOWED_SUFFIXES = {
    "data/manual": {".csv"},
    "data/processed": {".csv", ".json"},
    "docs": {".csv", ".md"},
    "scripts": {".mjs", ".py"},
    "site": {".css", ".csv", ".html", ".js", ".json"},
    "tests": {".py"},
}
FORBIDDEN_PARTS = {".DS_Store", "__pycache__", ".pytest_cache", ".venv"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def collect_files() -> list[Path]:
    """Collect the explicit handoff allowlist and reject unsafe entries."""
    files = {PROJECT_ROOT / relative for relative in ROOT_FILES}
    for directory, suffixes in ALLOWED_SUFFIXES.items():
        base = PROJECT_ROOT / directory
        files.update(
            path
            for path in base.rglob("*")
            if path.is_file() and path.suffix.lower() in suffixes
        )

    files.add(PROJECT_ROOT / "data" / "raw" / "README.md")
    files.update(
        path
        for path in required_inputs()
        if path.is_relative_to(PROJECT_ROOT / "data" / "raw")
    )

    missing = [path for path in sorted(files) if not path.is_file()]
    if missing:
        raise SystemExit(
            "Cannot build handoff; required files are missing:\n- "
            + "\n- ".join(str(path.relative_to(PROJECT_ROOT)) for path in missing)
        )

    selected: list[Path] = []
    for path in sorted(files):
        relative = path.relative_to(PROJECT_ROOT)
        if path.is_symlink():
            raise SystemExit(f"Refusing symlink in handoff: {relative}")
        if any(part in FORBIDDEN_PARTS for part in relative.parts):
            raise SystemExit(f"Refusing forbidden path in handoff: {relative}")
        selected.append(path)
    return selected


def write_zip_entry(
    archive: zipfile.ZipFile,
    source: Path,
    arcname: str,
    timestamp: tuple[int, int, int, int, int, int],
) -> None:
    info = zipfile.ZipInfo(arcname, date_time=timestamp)
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o100644 << 16
    with source.open("rb") as input_handle, archive.open(info, "w") as output_handle:
        shutil.copyfileobj(input_handle, output_handle, length=1024 * 1024)


def validate_archive(zip_path: Path, expected_relative: set[str]) -> None:
    with zipfile.ZipFile(zip_path) as archive:
        names = {name for name in archive.namelist() if not name.endswith("/")}
        expected = {
            f"{PACKAGE_ROOT_NAME}/{relative}" for relative in expected_relative
        }
        expected.add(f"{PACKAGE_ROOT_NAME}/SHA256SUMS.txt")
        if names != expected:
            missing = sorted(expected - names)
            extra = sorted(names - expected)
            raise SystemExit(
                "Archive content validation failed."
                f"\nMissing: {missing}\nUnexpected: {extra}"
            )
        bad = archive.testzip()
        if bad:
            raise SystemExit(f"Archive CRC validation failed at: {bad}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=PROJECT_ROOT / "outputs" / "professor-handoff",
        help="directory for the ZIP and its external SHA-256 file",
    )
    parser.add_argument(
        "--package-date",
        default=date.today().isoformat(),
        help="date in YYYY-MM-DD format used in the filename and deterministic ZIP metadata",
    )
    args = parser.parse_args()

    try:
        package_date = date.fromisoformat(args.package_date)
    except ValueError as error:
        raise SystemExit(f"Invalid --package-date: {args.package_date}") from error

    subprocess.run(
        [sys.executable, "scripts/build_data_dictionary.py", "--check"],
        cwd=PROJECT_ROOT,
        check=True,
    )
    selected = collect_files()
    relative_paths = {
        path.relative_to(PROJECT_ROOT).as_posix() for path in selected
    }
    timestamp = (
        package_date.year,
        package_date.month,
        package_date.day,
        0,
        0,
        0,
    )

    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    base_name = f"NE-NY-Generation-Analysis-professor-handoff-{package_date.isoformat()}"
    zip_path = output_dir / f"{base_name}.zip"
    external_hash_path = output_dir / f"{base_name}.zip.sha256"

    with tempfile.TemporaryDirectory(prefix="professor-handoff-build-") as temp_name:
        temp_root = Path(temp_name) / PACKAGE_ROOT_NAME
        for source in selected:
            relative = source.relative_to(PROJECT_ROOT)
            destination = temp_root / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, destination)

        manifest_lines = []
        for path in sorted(item for item in temp_root.rglob("*") if item.is_file()):
            relative = path.relative_to(temp_root).as_posix()
            manifest_lines.append(f"{sha256(path)}  {relative}")
        manifest = temp_root / "SHA256SUMS.txt"
        manifest.write_text("\n".join(manifest_lines) + "\n", encoding="utf-8")

        with zipfile.ZipFile(
            zip_path,
            mode="w",
            compression=zipfile.ZIP_DEFLATED,
            compresslevel=9,
            allowZip64=True,
        ) as archive:
            for source in sorted(item for item in temp_root.rglob("*") if item.is_file()):
                relative = source.relative_to(temp_root).as_posix()
                write_zip_entry(
                    archive,
                    source,
                    f"{PACKAGE_ROOT_NAME}/{relative}",
                    timestamp,
                )

    validate_archive(zip_path, relative_paths)
    external_hash = sha256(zip_path)
    external_hash_path.write_text(
        f"{external_hash}  {zip_path.name}\n", encoding="utf-8"
    )

    raw_files = [
        path for path in selected if path.is_relative_to(PROJECT_ROOT / "data" / "raw")
    ]
    print(f"Created {zip_path}")
    print(f"Created {external_hash_path}")
    print(f"Included {len(selected)} project files plus SHA256SUMS.txt")
    print(f"Included {len(raw_files)} required files from data/raw")
    print(f"ZIP size: {zip_path.stat().st_size / (1024 * 1024):.1f} MiB")
    print(f"ZIP SHA-256: {external_hash}")


if __name__ == "__main__":
    main()
