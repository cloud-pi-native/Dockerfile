#!/usr/bin/env python3
"""Increment only the actions-runner-pw revision and print the resulting tag."""

import json
from pathlib import Path
import re
import sys


def increment(path):
    images = json.loads(path.read_text())
    runners = [image for image in images if image["name"] == "actions-runner-pw"]
    if len(runners) != 1:
        raise ValueError("Expected exactly one actions-runner-pw entry")
    build = runners[0]["build"]
    match = re.fullmatch(r"([0-9]+-[0-9]+\.[0-9]+\.[0-9]+)-(0|[1-9][0-9]*)", build["tag"])
    if not match:
        raise ValueError("Expected runner tag <Node>-<Playwright>-<revision>")
    build["tag"] = f"{match[1]}-{int(match[2]) + 1}"
    path.write_text(json.dumps(images, indent=2) + "\n")
    return build["tag"]


if __name__ == "__main__":
    print(increment(Path(sys.argv[1] if len(sys.argv) > 1 else "ci/matrix.json")))
