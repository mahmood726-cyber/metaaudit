"""Assemble dashboard HTML by embedding dashboard_data.json into the template."""
import json, os, sys

data_path = r"C:\MetaAudit\results\dashboard_data.json"
template_path = r"C:\MetaAudit\dashboard\index.template.html"
out_path = r"C:\MetaAudit\dashboard\index.html"

data_json = open(data_path, encoding="utf-8").read()
template = open(template_path, encoding="utf-8").read()

# Replace placeholder
html = template.replace("/*DATA_PLACEHOLDER*/", data_json, 1)

with open(out_path, "w", encoding="utf-8") as f:
    f.write(html)

size = os.path.getsize(out_path)
print(f"Dashboard written: {out_path}")
print(f"Size: {size/1024:.0f} KB ({size:,} bytes)")
