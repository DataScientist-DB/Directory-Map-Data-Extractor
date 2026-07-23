from __future__ import annotations

import html as html_lib
import json
import re
from typing import Any, Dict, Optional, Tuple


# "rpc5":"Vegetables"  OR  'rpc5':'Vegetables'
_RPC_KV = re.compile(r"""["'](rpc\d+)["']\s*:\s*["']([^"']+)["']""", re.I)

# "rss6":"Farm visits" etc.
_RSS_KV = re.compile(r"""["'](rss\d+)["']\s*:\s*["']([^"']+)["']""", re.I)

# Object style e.g. { id:"rpc5", name:"Vegetables" } (order can vary)
# We'll match: id/slug = rpcX and name/label/title = Something
_RPC_OBJ = re.compile(
    r"""\b(id|slug)\s*:\s*["'](rpc\d+)["'][^{}]{0,500}?\b(name|label|title)\s*:\s*["']([^"']+)["']""",
    re.I | re.S,
)
_RSS_OBJ = re.compile(
    r"""\b(id|slug)\s*:\s*["'](rss\d+)["'][^{}]{0,500}?\b(name|label|title)\s*:\s*["']([^"']+)["']""",
    re.I | re.S,
)


def extract_taxonomy_maps(html: str) -> Tuple[Dict[str, str], Dict[str, str]]:
    """
    Best-effort extraction of category/service mapping from HTML/JS.
    Returns (category_map, service_map).
    """
    cat: Dict[str, str] = {}
    srv: Dict[str, str] = {}

    def clean(label: str) -> str:
        label = html_lib.unescape(label).strip()
        low = label.lower()

        # ignore placeholders / junk
        if low in {"…", "...", "&hellip;"}:
            return ""
        if label.lower().startswith("http"):
            return ""
        return label

    for code, label in _RPC_KV.findall(html):
        label = clean(label)
        if label:
            cat.setdefault(code, label)

    for code, label in _RSS_KV.findall(html):
        label = clean(label)
        if label:
            srv.setdefault(code, label)

    for _, code, _, label in _RPC_OBJ.findall(html):
        label = clean(label)
        if label:
            cat.setdefault(code, label)

    for _, code, _, label in _RSS_OBJ.findall(html):
        label = clean(label)
        if label:
            srv.setdefault(code, label)

    return cat, srv


def merge_maps(auto_map: Dict[str, str], manual_map: Dict[str, str]) -> Dict[str, str]:
    """
    Manual overrides auto.
    """
    out = dict(auto_map or {})
    for k, v in (manual_map or {}).items():
        if k and v:
            out[str(k).strip()] = str(v).strip()
    return out



def extract_taxonomy_maps_from_json(obj: Any) -> tuple[dict[str, str], dict[str, str]]:
    """
    Walk any JSON structure and try to find rpc*/rss* labels.
    Looks for patterns like:
      {"id":"rpc5","name":"Vegetables"} OR {"rpc5":"Vegetables"}
    """
    cat: dict[str, str] = {}
    srv: dict[str, str] = {}

    def visit(x: Any) -> None:
        if isinstance(x, dict):
            # direct mapping {"rpc5":"Vegetables"}
            for k, v in x.items():
                if isinstance(k, str) and isinstance(v, str):
                    kk = k.strip()
                    vv = v.strip()
                    if re.fullmatch(r"rpc\d+", kk, re.I) and vv:
                        cat.setdefault(kk, vv)
                    if re.fullmatch(r"rss\d+", kk, re.I) and vv:
                        srv.setdefault(kk, vv)

            # object style {"id":"rpc5","name":"Vegetables"}
            _id = x.get("id") or x.get("slug")
            _name = x.get("name") or x.get("label") or x.get("title")
            if isinstance(_id, str) and isinstance(_name, str):
                _id = _id.strip()
                _name = _name.strip()
                if re.fullmatch(r"rpc\d+", _id, re.I) and _name:
                    cat.setdefault(_id, _name)
                if re.fullmatch(r"rss\d+", _id, re.I) and _name:
                    srv.setdefault(_id, _name)

            for v in x.values():
                visit(v)

        elif isinstance(x, list):
            for v in x:
                visit(v)

    visit(obj)
    return cat, srv


def try_parse_json(text: str) -> Optional[Any]:
    """
    Try parse JSON safely.
    """
    text = text.strip()
    if not text:
        return None
    # quick sanity check
    if not (text.startswith("{") or text.startswith("[")):
        return None
    try:
        return json.loads(text)
    except Exception:
        return None
