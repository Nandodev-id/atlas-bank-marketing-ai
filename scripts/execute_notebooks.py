"""Execute notebooks with the project's kernel, then export standalone HTML."""

import os
import sys
from pathlib import Path
import nbformat
from nbclient import NotebookClient
from nbconvert import HTMLExporter

root = Path(__file__).resolve().parents[1]
os.environ["JUPYTER_PATH"] = (
    str(root / ".venv/share/jupyter") + os.pathsep + str(Path(sys.base_prefix) / "share/jupyter")
)
os.environ["JUPYTER_RUNTIME_DIR"] = str(root / "runtime/jupyter")
os.environ["IPYTHONDIR"] = str(root / "runtime/ipython")
os.environ["MPLCONFIGDIR"] = str(root / ".cache/matplotlib")
for name in ["certification", "exploration"]:
    path = root / f"notebooks/{name}.ipynb"
    nb = nbformat.read(path, as_version=4)
    NotebookClient(
        nb,
        timeout=180,
        kernel_name="atlas",
        resources={"metadata": {"path": str(root / "notebooks")}},
    ).execute()
    nbformat.write(nb, path)
    if name == "certification":
        html, _ = HTMLExporter().from_notebook_node(nb)
        (root / "reports/certification.html").write_text(html)
    print(f'{name}: executed {sum(c.cell_type=="code" for c in nb.cells)} code cells', flush=True)
