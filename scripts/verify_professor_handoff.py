#!/usr/bin/env python3
"""Verify a professor handoff ZIP, optionally with a clean-room rebuild."""

from __future__ import annotations

import argparse
import hashlib
import os
import platform
import re
import subprocess
import sys
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path, PurePosixPath


PACKAGE_ROOT_NAME = "NE-NY-Generation-Analysis-professor-handoff"
IGNORED_RUNTIME_PARTS = {".DS_Store", ".pytest_cache", ".venv", "__pycache__"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_extract(zip_path: Path, destination: Path) -> Path:
    with zipfile.ZipFile(zip_path) as archive:
        bad = archive.testzip()
        if bad:
            raise RuntimeError(f"ZIP CRC validation failed at {bad}")
        for info in archive.infolist():
            path = PurePosixPath(info.filename)
            mode = info.external_attr >> 16
            if path.is_absolute() or ".." in path.parts:
                raise RuntimeError(f"Unsafe archive path: {info.filename}")
            if not path.parts or path.parts[0] != PACKAGE_ROOT_NAME:
                raise RuntimeError(f"Unexpected archive root: {info.filename}")
            if mode & 0o170000 == 0o120000:
                raise RuntimeError(f"Symlink is not allowed in archive: {info.filename}")
        archive.extractall(destination)
    root = destination / PACKAGE_ROOT_NAME
    if not root.is_dir():
        raise RuntimeError(f"Missing package root: {PACKAGE_ROOT_NAME}")
    return root


def verify_manifest(root: Path) -> int:
    manifest = root / "SHA256SUMS.txt"
    if not manifest.is_file():
        raise RuntimeError("Missing SHA256SUMS.txt")

    expected: dict[str, str] = {}
    for line_number, line in enumerate(
        manifest.read_text(encoding="utf-8").splitlines(), start=1
    ):
        match = re.fullmatch(r"([0-9a-f]{64})  (.+)", line)
        if not match:
            raise RuntimeError(f"Malformed SHA256SUMS.txt line {line_number}")
        digest, relative = match.groups()
        if relative in expected:
            raise RuntimeError(f"Duplicate manifest path: {relative}")
        posix = PurePosixPath(relative)
        if posix.is_absolute() or ".." in posix.parts:
            raise RuntimeError(f"Unsafe manifest path: {relative}")
        expected[relative] = digest

    actual = set()
    for path in root.rglob("*"):
        if not path.is_file() or path == manifest:
            continue
        relative_path = path.relative_to(root)
        if any(part in IGNORED_RUNTIME_PARTS for part in relative_path.parts):
            continue
        actual.add(relative_path.as_posix())
    listed = set(expected)
    if actual != listed:
        raise RuntimeError(
            "Manifest file list differs from package contents. "
            f"Missing from disk: {sorted(listed - actual)}; "
            f"unlisted files: {sorted(actual - listed)}"
        )

    mismatches = []
    for relative, expected_digest in expected.items():
        actual_digest = sha256(root / relative)
        if actual_digest != expected_digest:
            mismatches.append(relative)
    if mismatches:
        raise RuntimeError("SHA-256 mismatch: " + ", ".join(sorted(mismatches)))
    return len(expected)


def run_command(command: list[str], cwd: Path) -> str:
    environment = os.environ.copy()
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    environment["PYTHONHASHSEED"] = "0"
    print(f"\n$ {' '.join(command)}", flush=True)
    process = subprocess.Popen(
        command,
        cwd=cwd,
        env=environment,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    output: list[str] = []
    assert process.stdout is not None
    for line in process.stdout:
        print(line, end="", flush=True)
        output.append(line)
    return_code = process.wait()
    text = "".join(output)
    if return_code:
        raise RuntimeError(
            f"Command failed with exit code {return_code}: {' '.join(command)}"
        )
    return text


def verify_root(root: Path, rebuild: bool) -> dict[str, object]:
    before_count = verify_manifest(root)
    result: dict[str, object] = {
        "manifest_file_count": before_count,
        "preflight": "not requested",
        "rebuild": "not requested",
        "unit_tests": "not requested",
        "dictionary": "not requested",
        "post_rebuild_hashes": "not requested",
    }
    if not rebuild:
        return result

    run_command(
        [sys.executable, "scripts/rebuild_project.py", "--check-only"], root
    )
    result["preflight"] = "passed"

    build_output = run_command(
        [sys.executable, "scripts/rebuild_project.py"], root
    )
    stages = re.search(r"Completed (\d+) stages successfully", build_output)
    tests = re.search(r"Ran (\d+) tests", build_output)
    if not stages or not tests or "OK" not in build_output:
        raise RuntimeError("Could not confirm the stage and unit-test totals")
    result["rebuild"] = f"passed ({stages.group(1)} stages)"
    result["unit_tests"] = f"passed ({tests.group(1)} tests)"

    run_command(
        [sys.executable, "scripts/build_data_dictionary.py", "--check"], root
    )
    result["dictionary"] = "passed"

    after_count = verify_manifest(root)
    if after_count != before_count:
        raise RuntimeError("Manifest file count changed after rebuild")
    result["post_rebuild_hashes"] = "passed"
    return result


def format_report(
    *, zip_path: Path | None, zip_digest: str | None, result: dict[str, object]
) -> str:
    source = zip_path.name if zip_path else "already-extracted package"
    lines = [
        "Professor handoff verification",
        f"Verified at: {datetime.now().astimezone().isoformat(timespec='seconds')}",
        f"Source: {source}",
        f"ZIP SHA-256: {zip_digest or 'not applicable'}",
        f"Python: {platform.python_version()}",
        f"Platform: {platform.platform()}",
        "Archive structure and CRC: passed" if zip_path else "Archive extraction: not requested",
        f"Internal SHA-256 manifest before rebuild: passed ({result['manifest_file_count']} files)",
        f"Environment preflight: {result['preflight']}",
        f"Offline rebuild: {result['rebuild']}",
        f"Unit tests: {result['unit_tests']}",
        f"Data dictionary check: {result['dictionary']}",
        f"Internal SHA-256 manifest after rebuild: {result['post_rebuild_hashes']}",
        "Overall result: PASS",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "zip_path",
        nargs="?",
        type=Path,
        help="handoff ZIP to extract and verify; omit when running inside the extracted package",
    )
    parser.add_argument(
        "--rebuild",
        action="store_true",
        help="run the exact environment preflight, full offline rebuild, tests, and post-build hash check",
    )
    parser.add_argument(
        "--report",
        type=Path,
        help="optional path for a plain-text verification report",
    )
    args = parser.parse_args()

    zip_path = args.zip_path.resolve() if args.zip_path else None
    zip_digest = None
    try:
        if zip_path:
            if not zip_path.is_file():
                raise RuntimeError(f"ZIP not found: {zip_path}")
            zip_digest = sha256(zip_path)
            with tempfile.TemporaryDirectory(prefix="professor-handoff-verify-") as temp_name:
                root = safe_extract(zip_path, Path(temp_name))
                result = verify_root(root, args.rebuild)
        else:
            root = Path.cwd().resolve()
            result = verify_root(root, args.rebuild)
        report = format_report(
            zip_path=zip_path, zip_digest=zip_digest, result=result
        )
    except Exception as error:
        failure = (
            "Professor handoff verification\n"
            f"Verified at: {datetime.now().astimezone().isoformat(timespec='seconds')}\n"
            f"Overall result: FAIL\nReason: {error}\n"
        )
        if args.report:
            report_path = args.report.resolve()
            report_path.parent.mkdir(parents=True, exist_ok=True)
            report_path.write_text(failure, encoding="utf-8")
        raise SystemExit(failure) from error

    print("\n" + report)
    if args.report:
        report_path = args.report.resolve()
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(report, encoding="utf-8")
        print(f"Wrote verification report: {report_path}")


if __name__ == "__main__":
    main()
