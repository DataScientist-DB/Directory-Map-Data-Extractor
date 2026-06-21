# src/taxonomy_static.py
from __future__ import annotations

import html
import re
from typing import Dict, List

# -------------------------
# RPC categories (canonical)
# -------------------------
RPC_CATEGORY_MAP: Dict[str, str] = {
    "rpc1": "Beef",
    "rpc2": "Poultry",
    "rpc3": "Pork",
    "rpc4": "Lamb",
    "rpc5": "Vegetables",
    "rpc6": "Dairy",
    "rpc7": "Fruit",
    "rpc8": "Grains",
    "rpc9": "Nuts",
    "rpc10": "Seeds",
    "rpc11": "Honey & bee products",
    "rpc12": "Value-added products",
    "rpc13": "Mixed farming",
    "rpc14": "Herbs & medicinal plants",
    "rpc15": "Other / multiple categories",
    "rpc100": "Other / multiple categories",
}

# -------------------------
# Services (UI legend)
# -------------------------
RSS_SERVICE_MAP: Dict[str, str] = {
    "rss1": "Workshops & trainings",
    "rss2": "Activities for kids",
    "rss3": "Soil testing",
    "rss4": "Farm equipment sharing",
    "rss5": "Pick-your-own",
    "rss6": "Farm tour (for other farmers)",
    "rss7": "Farm tour (for general public)",
    "rss8": "Volunteer program",
    "rss9": "Internship program",
    "rss10": "Wwoofing",
    "rss11": "Farm dinners and events",
    "rss12": "Employment opportunities",
}

# ------------------------------------------------
# Product category (UI) → RPC semantic alignment
# ------------------------------------------------
PRODUCT_LABEL_TO_RPC: Dict[str, List[str]] = {
    "meat & poultry": ["rpc1", "rpc2", "rpc3", "rpc4"],
    "eggs": ["rpc2"],
    "grains": ["rpc8"],
    "pulses": ["rpc8"],
    "vegetables": ["rpc5"],
    "dairy": ["rpc6"],
    "fruits": ["rpc7"],
    "berries": ["rpc7"],
    "nuts": ["rpc9"],
    "wine, cider and liquor": ["rpc12", "rpc7"],
    "flowers": ["rpc10"],
    "nursery": ["rpc10"],
    "honey & syrups": ["rpc11", "rpc12"],
    "fibres": ["rpc4", "rpc15"],
    "compost": ["rpc12"],
    "other": ["rpc15"],
}

# -------------------------
# Helpers
# -------------------------
_SPLIT_RE = re.compile(r"[\t;|\n]+")  # do NOT split commas (Wine, cider and liquor)


_WS_RE = re.compile(r"\s+")

def _norm(s: str) -> str:
    s = html.unescape(str(s or ""))
    s = s.strip().lower()
    return _WS_RE.sub(" ", s)

def map_product_labels_to_rpc(products) -> List[str]:
    """
    Map UI product labels to canonical rpc codes.
    """
    if not products:
        return []

    if isinstance(products, list):
        parts = [str(x) for x in products]
    else:
        parts = _SPLIT_RE.split(str(products))

    out: List[str] = []
    seen = set()

    for p in parts:
        key = _norm(p)
        if not key or key in ("all", "any"):
            continue
        for c in PRODUCT_LABEL_TO_RPC.get(key, []):
            if c not in seen:
                seen.add(c)
                out.append(c)

    return out
