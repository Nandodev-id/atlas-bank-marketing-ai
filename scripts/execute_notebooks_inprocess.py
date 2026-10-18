"""Socket-free execution fallback for restricted environments.
All code cells really execute, in order, in a fresh IPython namespace. This is not
an external Jupyter-kernel test; the normal executor remains available separately.
"""

import os
import sys
from pathlib import Path
import nbformat
from nbconvert import HTMLExporter
from IPython.core.interactiveshell import InteractiveShell
from IPython.utils.capture import capture_output

root = Path(__file__).resolve().parents[1]
os.environ["JUPYTER_PATH"] = str(Path(sys.base_prefix) / "share/jupyter")
os.environ["MPLCONFIGDIR"] = str(root / ".cache/matplotlib")
os.environ["IPYTHONDIR"] = str(root / "runtime/ipython")
os.chdir(root / "notebooks")
for name in ["certification", "exploration"]:
    nb = nbformat.read(root / f"notebooks/{name}.ipynb", as_version=4)
    shell = InteractiveShell.instance()
    shell.reset(new_session=True)
    count = 0
    for cell in nb.cells:
        if cell.cell_type != "code":
            continue
        count += 1
        with capture_output(stdout=True, stderr=True, display=True) as capture:
            result = shell.run_cell(cell.source, store_history=True)
        if result.error_before_exec or result.error_in_exec:
            raise RuntimeError(
                f"{name} cell {count}: {result.error_before_exec or result.error_in_exec}\n{capture.stdout}"
            )
        outputs = []
        if capture.stdout:
            outputs.append(nbformat.v4.new_output("stream", name="stdout", text=capture.stdout))
        if capture.stderr:
            outputs.append(nbformat.v4.new_output("stream", name="stderr", text=capture.stderr))
        for rich in capture.outputs:
            outputs.append(
                nbformat.v4.new_output("display_data", data=rich.data, metadata=rich.metadata)
            )
        cell.outputs = outputs
        cell.execution_count = count
    nb.metadata["atlas_execution"] = {
        "method": "IPython in-process, sequential, fresh namespace",
        "reason": "Sandbox blocks socket binding required for an external Jupyter kernel",
        "code_cells_executed": count,
        "errors": 0,
    }
    nbformat.validate(nb)
    nbformat.write(nb, root / f"notebooks/{name}.ipynb")
    if name == "certification":
        html, _ = HTMLExporter().from_notebook_node(nb)
        (root / "reports/certification.html").write_text(html)
    print(f"{name}: {count} code cells executed without errors", flush=True)
