import io
import json
import os
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _resolve_conf_path(conf_file_path: str) -> Path:
    path = Path(conf_file_path)
    if path.is_absolute():
        return path
    for base in (Path.cwd(), PROJECT_ROOT):
        candidate = (base / path).resolve()
        if candidate.exists():
            return candidate
    return (PROJECT_ROOT / path).resolve()


def load_openimis_conf(conf_file_param="openimis.json"):
    conf_json_env = os.environ.get("OPENIMIS_CONF_JSON", "")
    conf_file_path = os.environ.get("OPENIMIS_CONF", conf_file_param)

    if conf_json_env:
        return json.load(io.StringIO(conf_json_env))

    resolved_path = _resolve_conf_path(conf_file_path)
    with resolved_path.open() as conf_file:
        return json.load(conf_file)

