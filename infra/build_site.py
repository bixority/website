#!/usr/bin/env python3
"""Build one version of the site for Terraform's external data source (site.tf).

Reads the query {"site": "<version folder>"} from stdin, runs <version>/build.py
--strict with `uv run --script` (uv installs the build's one dependency, so uv must be
on the PATH) and prints {"dist": "<absolute path>"} on stdout, as the external data
source expects. The build's own output goes to stderr, which Terraform shows only
when the build fails.
"""

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def main() -> int:
    query = json.load(sys.stdin)
    site = query.get("site", "") if isinstance(query, dict) else ""
    root = REPO / site
    if not re.fullmatch(r"v[0-9]+", site) or not (root / "build.py").is_file():
        print(f"build_site.py: no site version folder {site!r} with a build.py in {REPO}", file=sys.stderr)
        return 1
    uv = shutil.which("uv")
    if uv is None:
        print("build_site.py: uv is not installed; the build needs it (https://docs.astral.sh/uv/)", file=sys.stderr)
        return 1
    result = subprocess.run(
        [uv, "run", "--script", str(root / "build.py"), "--strict"],
        cwd=root,
        stdout=sys.stderr,
        check=False,
    )
    if result.returncode != 0:
        return result.returncode
    json.dump({"dist": str(root / "dist")}, sys.stdout)
    return 0


if __name__ == "__main__":
    sys.exit(main())
