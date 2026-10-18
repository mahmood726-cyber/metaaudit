"""Dashboard build regressions use explicit software fixtures."""
import importlib
import json
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_import_does_not_read_or_write_dashboard_files():
    code = "import build_dashboard; print('imported')"
    result = subprocess.run([sys.executable, '-c', code], cwd=ROOT,
                            capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout.strip() == 'imported'


def builder():
    return importlib.import_module('build_dashboard').build_dashboard


def inputs(tmp_path, data='{"label": "test fixture"}', marker='/*DATA_PLACEHOLDER*/'):
    source = tmp_path / 'data.json'
    source.write_text(data, encoding='utf-8')
    template = tmp_path / 'template.html'
    template.write_text('<script>const DATA = ' + marker + ';</script>', encoding='utf-8')
    return source, template, tmp_path / 'out' / 'index.html'


def test_explicit_paths_build_and_preserve_unicode(tmp_path):
    args = inputs(tmp_path, json.dumps({'label': 'Café test fixture'}, ensure_ascii=False))
    result = builder()(*args)
    assert result == args[2]
    assert 'Café test fixture' in result.read_text(encoding='utf-8')
    assert '/*DATA_PLACEHOLDER*/' not in result.read_text(encoding='utf-8')
    assert not result.read_bytes().startswith(b'\xef\xbb\xbf')


@pytest.mark.parametrize('data', ['{broken', '{"value": NaN}'])
def test_invalid_json_leaves_existing_output_untouched(tmp_path, data):
    args = inputs(tmp_path, data)
    args[2].parent.mkdir()
    args[2].write_text('previous output', encoding='utf-8')
    with pytest.raises(ValueError):
        builder()(*args)
    assert args[2].read_text(encoding='utf-8') == 'previous output'


@pytest.mark.parametrize('marker', ['', '/*DATA_PLACEHOLDER*//*DATA_PLACEHOLDER*/'])
def test_missing_or_duplicate_marker_cannot_write(tmp_path, marker):
    args = inputs(tmp_path, marker=marker)
    with pytest.raises(ValueError, match='exactly one'):
        builder()(*args)
    assert not args[2].exists()


def test_missing_input_cannot_create_output(tmp_path):
    args = inputs(tmp_path)
    args[0].unlink()
    with pytest.raises(FileNotFoundError):
        builder()(*args)
    assert not args[2].exists()


def test_json_cannot_terminate_script_element(tmp_path):
    value = '</ScRiPt><script>alert(1)</script>'
    args = inputs(tmp_path, json.dumps({'label': value}))
    html = builder()(*args).read_text(encoding='utf-8')
    assert html.lower().count('</script>') == 1
    embedded = html.split('const DATA = ', 1)[1].split(';</script>', 1)[0]
    assert json.loads(embedded)['label'] == value


def test_failed_replace_preserves_output_and_cleans_temporary_file(tmp_path, monkeypatch):
    module = importlib.import_module('build_dashboard')
    args = inputs(tmp_path)
    args[2].parent.mkdir()
    args[2].write_text('previous output', encoding='utf-8')
    def fail_replace(*args):
        raise OSError('fixture replacement failure')
    monkeypatch.setattr(module.os, 'replace', fail_replace)
    with pytest.raises(OSError, match='fixture replacement failure'):
        module.build_dashboard(*args)
    assert args[2].read_text(encoding='utf-8') == 'previous output'
    assert list(args[2].parent.iterdir()) == [args[2]]
