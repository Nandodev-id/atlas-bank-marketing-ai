"""Manual-environment-gated CI deployment; requires configured host and verified SSH keys.
Host prerequisite: /opt/atlas/release.sh <image-tag>, implementing health check and rollback.
"""

import os
import re
import subprocess
from pathlib import Path

host = os.environ["DEPLOY_HOST"]
user = os.environ["DEPLOY_USER"]
assert re.fullmatch(r"[A-Za-z0-9.-]+", host) and re.fullmatch(r"[A-Za-z0-9_-]+", user)
key = Path("/tmp/atlas_deploy_key")
key.write_text(os.environ["SSH_KEY"])
key.chmod(0o600)
known = Path("/tmp/atlas_known_hosts")
known.write_text(os.environ["KNOWN_HOSTS"])
tag = os.environ["GITHUB_SHA"]
assert re.fullmatch("[a-f0-9]{40}", tag)
options = ["-i", str(key), "-o", "StrictHostKeyChecking=yes", "-o", f"UserKnownHostsFile={known}"]
try:
    subprocess.run(
        ["scp", *options, "image.tar", f"{user}@{host}:/opt/atlas/image.tar"], check=True
    )
    subprocess.run(["ssh", *options, f"{user}@{host}", f"/opt/atlas/release.sh {tag}"], check=True)
finally:
    key.unlink(missing_ok=True)
