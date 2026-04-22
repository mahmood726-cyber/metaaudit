"""Assemble dashboard HTML by embedding dashboard_data.json into the template."""
import json, os, sys

from metaaudit.config import DASHBOARD_DATA, DASHBOARD_TEMPLATE, DASHBOARD_INDEX

data_path = DASHBOARD_DATA
template_path = DASHBOARD_TEMPLATE
out_path = DASHBOARD_INDEX

data_json = open(data_path, encoding="utf-8").read()
template = open(template_path, encoding="utf-8").read()

# Replace placeholder
html = template.replace("/*DATA_PLACEHOLDER*/", data_json, 1)

with open(out_path, "w", encoding="utf-8") as f:
    f.write(html)

size = os.path.getsize(out_path)
print(f"Dashboard written: {out_path}")
print(f"Size: {size/1024:.0f} KB ({size:,} bytes)")
