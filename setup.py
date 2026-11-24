#!/usr/bin/env python3
"""
ProxyManX Windows Setup Script
"""

import re
from setuptools import setup, find_packages
from pathlib import Path

this_directory = Path(__file__).parent

# Read the contents of README file
long_description = (this_directory / "README.md").read_text(encoding='utf-8')


def get_version():
    """Read __version__ from the package without importing it.

    Importing would pull in colorama, which may not be installed at build time.
    """
    init_py = (this_directory / "proxymanx" / "__init__.py").read_text(encoding='utf-8')
    match = re.search(r'^__version__\s*=\s*["\']([^"\']+)["\']', init_py, re.MULTILINE)
    if not match:
        raise RuntimeError("Unable to find __version__ in proxymanx/__init__.py")
    return match.group(1)


setup(
    name="proxymanx",
    version=get_version(),
    author="Pubudu Wijesundara",
    author_email="",  # Add your email if desired
    description="Comprehensive Windows proxy configuration tool",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/thewijay/ProxyManX",
    packages=find_packages(include=["proxymanx", "proxymanx.*"]),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Microsoft :: Windows",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Internet :: Proxy Servers",
        "Topic :: System :: Networking",
        "Topic :: System :: Systems Administration",
        "Topic :: Utilities",
    ],
    python_requires=">=3.7",
    install_requires=[
        "colorama>=0.4.4",
    ],
    extras_require={
        "dev": ["pytest>=7.0"],
    },
    entry_points={
        "console_scripts": [
            "proxymanx=proxymanx.cli:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
    keywords="proxy windows configuration network system administration",
    project_urls={
        "Bug Reports": "https://github.com/thewijay/ProxyManX/issues",
        "Source": "https://github.com/thewijay/ProxyManX",
        "Documentation": "https://github.com/thewijay/ProxyManX/blob/main/README.md",
    },
)
