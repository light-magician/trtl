#!/usr/bin/env python3
from pathlib import Path

from setuptools import find_packages, setup

# read requirements.txt, skipping blank lines and comments
req_file = Path(__file__).parent / "requirements.txt"
install_requires = []
if req_file.exists():
    with req_file.open() as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                install_requires.append(line)

setup(
    name="trtl",
    version="0.1.0",
    packages=find_packages(),
    install_requires=install_requires,
    entry_points={
        "console_scripts": [
            "trtl=trtl.main:main",
        ],
    },
)
