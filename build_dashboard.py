"""Build dashboard HTML explicitly; importing this module performs no file I/O."""
import argparse
import json
import os
from pathlib import Path
import tempfile

from metaaudit.config import DASHBOARD_DATA, DASHBOARD_TEMPLATE, DASHBOARD_INDEX

MARKER = "/*DATA_PLACEHOLDER*/"


def _reject_constant(value):
    raise ValueError(f"Non-finite JSON constant: {value}")


def build_dashboard(data_path=DASHBOARD_DATA, template_path=DASHBOARD_TEMPLATE,
                    out_path=DASHBOARD_INDEX):
    """Validate inputs before atomically replacing the output HTML.

    JSON is escaped for an inline script so a source string cannot close the
    script element. Explicit paths support builds from any working directory.
    """
    data_path, template_path, out_path = map(Path, (data_path, template_path, out_path))
    data = json.loads(data_path.read_text(encoding="utf-8"), parse_constant=_reject_constant)
    template = template_path.read_text(encoding="utf-8")
    if template.count(MARKER) != 1:
        raise ValueError("Dashboard template must contain exactly one data placeholder")
    data_json = json.dumps(data, ensure_ascii=False, allow_nan=False)
    data_json = data_json.replace("<", "\\u003c").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")
    html = template.replace(MARKER, data_json, 1)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="",
                                         dir=out_path.parent, suffix=".tmp", delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(html)
        os.replace(temporary, out_path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    return out_path


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=DASHBOARD_DATA)
    parser.add_argument("--template", type=Path, default=DASHBOARD_TEMPLATE)
    parser.add_argument("--output", type=Path, default=DASHBOARD_INDEX)
    args = parser.parse_args(argv)
    output = build_dashboard(args.data, args.template, args.output)
    print(f"Dashboard written: {output}")
    print(f"Size: {output.stat().st_size:,} bytes")


if __name__ == "__main__":
    main()
