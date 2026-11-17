#!/usr/bin/env python3
"""Create a minimal, checksummed ZIP for the optional professor handoff."""

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


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from rebuild_project import required_inputs  # noqa: E402


PACKAGE_ROOT_NAME = "NE-NY-Generation-Analysis-professor-handoff"
ROOT_FILES = (
    "README.md",
    "requirements.txt",
)
HANDOFF_FILES = {
    "tools/professor_handoff/README.md": "PROFESSOR_HANDOFF.md",
    "tools/professor_handoff/build.py": "tools/professor_handoff/build.py",
    "tools/professor_handoff/verify.py": "tools/professor_handoff/verify.py",
}
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


def collect_files() -> list[tuple[Path, Path]]:
    """Collect the explicit handoff allowlist and reject unsafe entries."""
    files = {
        PROJECT_ROOT / relative: Path(relative)
        for relative in ROOT_FILES
    }
    files.update(
        {
            PROJECT_ROOT / source: Path(archive_path)
            for source, archive_path in HANDOFF_FILES.items()
        }
    )
    for directory, suffixes in ALLOWED_SUFFIXES.items():
        base = PROJECT_ROOT / directory
        files.update(
            {
                path: path.relative_to(PROJECT_ROOT)
                for path in base.rglob("*")
                if path.is_file() and path.suffix.lower() in suffixes
            }
        )

    raw_readme = PROJECT_ROOT / "data" / "raw" / "README.md"
    files[raw_readme] = raw_readme.relative_to(PROJECT_ROOT)

    for path in required_inputs():
        if path.is_relative_to(PROJECT_ROOT / "data" / "raw"):
            files[path] = path.relative_to(PROJECT_ROOT)

    missing = [path for path in sorted(files) if not path.is_file()]
    if missing:
        raise SystemExit(
            "Cannot build handoff; required files are missing:\n- "
            + "\n- ".join(str(path.relative_to(PROJECT_ROOT)) for path in missing)
        )

    selected: list[tuple[Path, Path]] = []
    archive_paths: set[Path] = set()
    for path, archive_path in sorted(
        files.items(), key=lambda item: item[1].as_posix()
    ):
        source_relative = path.relative_to(PROJECT_ROOT)
        if path.is_symlink():
            raise SystemExit(f"Refusing symlink in handoff: {source_relative}")
        if any(part in FORBIDDEN_PARTS for part in source_relative.parts):
            raise SystemExit(
                f"Refusing forbidden source path in handoff: {source_relative}"
            )
        if archive_path.is_absolute() or ".." in archive_path.parts:
            raise SystemExit(f"Refusing unsafe archive path: {archive_path}")
        if any(part in FORBIDDEN_PARTS for part in archive_path.parts):
            raise SystemExit(f"Refusing forbidden archive path: {archive_path}")
        if archive_path in archive_paths:
            raise SystemExit(f"Duplicate archive path: {archive_path}")
        archive_paths.add(archive_path)
        selected.append((path, archive_path))
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
        archive_path.as_posix() for _, archive_path in selected
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
        for source, relative in selected:
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
        path
        for path, _ in selected
        if path.is_relative_to(PROJECT_ROOT / "data" / "raw")
    ]
    print(f"Created {zip_path}")
    print(f"Created {external_hash_path}")
    print(f"Included {len(selected)} project files plus SHA256SUMS.txt")
    print(f"Included {len(raw_files)} required files from data/raw")
    print(f"ZIP size: {zip_path.stat().st_size / (1024 * 1024):.1f} MiB")
    print(f"ZIP SHA-256: {external_hash}")


if __name__ == "__main__":
    main()
