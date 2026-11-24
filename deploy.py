#!/usr/bin/env python3
"""
ProxyManX Windows - Deployment Script
Creates a deployable package for distribution
"""

import os
import shutil
import zipfile
from pathlib import Path

# Files and directories that make up a distributable ProxyManX
PACKAGE_CONTENTS = [
    "proxymanx/",
    "proxymanx.bat",
    "refresh_path.bat",
    "requirements.txt",
    "setup.py",
    "install.py",
    "install.ps1",
    "uninstall.py",
    "uninstall.ps1",
    "README.md",
    "QUICKSTART.md",
    "CHANGELOG.md",
    "LICENSE",
]

# Never ship build artefacts or caches
EXCLUDE_PATTERNS = shutil.ignore_patterns('__pycache__', '*.pyc', '*.pyo')


def create_package():
    """Create a deployable package."""
    print("Creating ProxyManX Windows deployment package...")

    source_dir = Path(".")
    dist_dir = Path("dist")
    package_dir = dist_dir / "ProxyManX-Windows"

    # Clean previous builds
    if dist_dir.exists():
        shutil.rmtree(dist_dir)

    package_dir.mkdir(parents=True, exist_ok=True)

    missing = []
    for item in PACKAGE_CONTENTS:
        source = source_dir / item
        dest = package_dir / item

        if source.is_file():
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, dest)
            print(f"Copied: {item}")
        elif source.is_dir():
            shutil.copytree(source, dest, ignore=EXCLUDE_PATTERNS)
            print(f"Copied directory: {item}")
        else:
            missing.append(item)

    if missing:
        print("\nWARNING: the following expected files were not found:")
        for item in missing:
            print(f"  - {item}")

    # Create ZIP package
    zip_path = dist_dir / "ProxyManX-Windows.zip"
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(package_dir):
            for file in files:
                file_path = Path(root) / file
                arcname = file_path.relative_to(dist_dir)
                zipf.write(file_path, arcname)

    print("\nPackage created successfully:")
    print(f"  Directory: {package_dir}")
    print(f"  Archive: {zip_path}")
    print(f"  Size: {zip_path.stat().st_size / 1024:.1f} KB")

    return not missing


if __name__ == "__main__":
    create_package()
