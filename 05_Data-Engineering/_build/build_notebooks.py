"""Convert the notebooks/*.py sources (# %% cell markers) into Fabric .Notebook folders.

Usage: python build_notebooks.py <workspace_id> <lakehouse_id> <lakehouse_name>
Output: _build/out/<name>.Notebook/{.platform, notebook-content.ipynb}
"""
import json
import re
import sys
import uuid
from pathlib import Path

ws_id, lh_id, lh_name = sys.argv[1:4]
root = Path(__file__).resolve().parent.parent
out = root / "_build" / "out"

LANG = {"language": "python", "language_group": "synapse_pyspark"}


def to_cells(text: str):
    cells = []
    for block in re.split(r"^# %%", text, flags=re.M)[1:]:
        header, _, body = block.partition("\n")
        body = body.strip("\n")
        if "[markdown]" in header:
            src = "\n".join(re.sub(r"^# ?", "", line) for line in body.split("\n"))
            cells.append({"cell_type": "markdown", "source": src.splitlines(keepends=True),
                          "metadata": {"microsoft": LANG}})
        else:
            meta = {"microsoft": LANG}
            if "parameters" in header:
                meta["tags"] = ["parameters"]
            cells.append({"cell_type": "code", "source": body.splitlines(keepends=True),
                          "outputs": [], "execution_count": None, "metadata": meta})
    return cells


for src in sorted((root / "notebooks").glob("nb_*.py")):
    name = src.stem
    nb = {
        "nbformat": 4, "nbformat_minor": 5,
        "cells": to_cells(src.read_text(encoding="utf-8")),
        "metadata": {
            "kernel_info": {"name": "synapse_pyspark"},
            "kernelspec": {"name": "synapse_pyspark", "display_name": "Synapse PySpark"},
            "language_info": {"name": "python"},
            "microsoft": LANG,
            "dependencies": {"lakehouse": {
                "default_lakehouse": lh_id, "default_lakehouse_name": lh_name,
                "default_lakehouse_workspace_id": ws_id, "known_lakehouses": [{"id": lh_id}]}},
        },
    }
    folder = out / f"{name}.Notebook"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "notebook-content.ipynb").write_text(json.dumps(nb, indent=1), encoding="utf-8")
    (folder / ".platform").write_text(json.dumps({
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/gitIntegration/platformProperties/2.0.0/schema.json",
        "metadata": {"type": "Notebook", "displayName": name},
        "config": {"version": "2.0", "logicalId": str(uuid.uuid5(uuid.NAMESPACE_URL, name))},
    }, indent=2), encoding="utf-8")
    print(f"built {folder.name} ({len(nb['cells'])} cells)")
