from __future__ import annotations

import math
import re
import xml.etree.ElementTree as ET
from collections import Counter
from typing import Any


GRAPHIC_TAGS = {"path", "circle", "ellipse", "rect", "polygon", "polyline", "line"}
FORBIDDEN_RE = re.compile(
    r"<\s*(script|foreignObject|iframe|image|video|audio|canvas)\b|"
    r"\bon\w+\s*=|javascript:|data:|"
    r"(?:href|xlink:href|src)\s*=\s*['\"]\s*https?://",
    re.I,
)
HEX_RE = re.compile(r"#[0-9a-fA-F]{3}(?:[0-9a-fA-F]{3})?\b")
NUM_RE = re.compile(r"[-+]?(?:\d*\.\d+|\d+)(?:[eE][-+]?\d+)?")

COLOR_WORDS = {
    "red": ("red", "coral", "crimson"),
    "orange": ("orange", "amber"),
    "yellow": ("yellow", "gold", "golden", "mustard"),
    "green": ("green", "teal", "mint", "leaf"),
    "blue": ("blue", "navy", "cyan", "turquoise"),
    "purple": ("purple", "violet"),
    "brown": ("brown", "walnut", "tan"),
    "white": ("white", "cream"),
    "black": ("black",),
    "gray": ("gray", "grey", "silver"),
}

SHAPE_WORDS = {
    "circle": ("circle", "circular", "badge", "coin", "dot"),
    "rect": ("square", "rectangle", "rounded-square", "badge"),
    "path": ("leaf", "swirl", "curve", "hand", "roof", "note", "brush", "ribbon"),
    "line": ("line", "ray", "stem", "stroke"),
    "polygon": ("triangle", "star", "sparkle", "roof"),
}


def _tag(tag: str) -> str:
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def _clamp(x: float) -> float:
    return max(0.0, min(1.0, x))


def _band(v: int, good_lo: int, good_hi: int, hard_lo: int, hard_hi: int) -> float:
    if good_lo <= v <= good_hi:
        return 1.0
    if v < hard_lo or v > hard_hi:
        return 0.0
    if v < good_lo:
        return (v - hard_lo) / max(1, good_lo - hard_lo)
    return (hard_hi - v) / max(1, hard_hi - good_hi)


def _extract_svg(text: str) -> str:
    m = re.search(r"<svg\b.*?</svg>", text.strip(), re.I | re.S)
    return m.group(0) if m else text.strip()


def _parse(text: str):
    if not text or FORBIDDEN_RE.search(text):
        return None
    try:
        root = ET.fromstring(_extract_svg(text))
    except ET.ParseError:
        return None
    return root if _tag(root.tag) == "svg" else None


def _numbers(root: ET.Element) -> list[float]:
    vals = []
    for e in root.iter():
        for val in e.attrib.values():
            for token in NUM_RE.findall(val):
                try:
                    x = float(token)
                except ValueError:
                    continue
                if math.isfinite(x):
                    vals.append(x)
    return vals


def score_svg(svg_text: str, prompt: str = "") -> dict[str, Any]:
    root = _parse(svg_text)
    if root is None:
        return {
            "score": 0.0,
            "validity": 0.0,
            "structure": 0.0,
            "geometry": 0.0,
            "palette": 0.0,
            "prompt_fidelity": 0.0,
            "penalty": 1.0,
        }

    text = svg_text.strip()
    attrs = root.attrib
    viewbox = attrs.get("viewBox") or attrs.get("viewbox", "")
    view_nums = [float(x) for x in NUM_RE.findall(viewbox)]
    view_ok = len(view_nums) == 4 and view_nums == [0.0, 0.0, 256.0, 256.0]
    xmlns_ok = "xmlns" in attrs or root.tag.startswith("{http://www.w3.org/2000/svg}")
    svg_only = text.lower().startswith("<svg") and text.lower().endswith("</svg>")
    validity = 0.35 + (0.25 if view_ok else 0) + (0.20 if xmlns_ok else 0) + (0.20 if svg_only else 0)

    tags = [_tag(e.tag) for e in root.iter()]
    counts = Counter(tags)
    elem_count = len(tags) - 1
    graphic_count = sum(counts[t] for t in GRAPHIC_TAGS)
    structure = 0.45 * _band(graphic_count, 3, 35, 1, 80) + 0.35 * _band(elem_count, 4, 45, 1, 90) + 0.20

    vals = _numbers(root)
    bad = [v for v in vals if v < -64 or v > 320]
    geometry = 0.2 if not vals else _clamp(1.0 - min(0.7, 2 * len(bad) / len(vals)))

    colors = [c.lower() for c in HEX_RE.findall(text)]
    unique_colors = len(set(colors))
    palette = 0.75 * _band(unique_colors, 2, 7, 1, 12) + 0.25 * (
        1.0 if any("fill" in e.attrib or "stroke" in e.attrib for e in root.iter()) else 0.35
    )

    prompt_l = prompt.lower()
    text_l = text.lower()
    requested_colors = [k for k, words in COLOR_WORDS.items() if any(w in prompt_l for w in words)]
    matched_colors = [k for k in requested_colors if HEX_RE.search(text) or k in text_l]
    requested_shapes = [t for t, words in SHAPE_WORDS.items() if any(w in prompt_l for w in words)]
    matched_shapes = [t for t in requested_shapes if t in counts]
    color_score = len(matched_colors) / len(requested_colors) if requested_colors else 0.6
    shape_score = len(matched_shapes) / len(requested_shapes) if requested_shapes else 0.6
    fidelity = _clamp(0.55 * color_score + 0.45 * shape_score)

    penalty = 0.0
    if len(text) < 120:
        penalty += 0.25
    if len(text) > 12000:
        penalty += 0.20
    if "```" in text:
        penalty += 0.25

    score = _clamp(0.30 * validity + 0.25 * structure + 0.15 * geometry + 0.15 * palette + 0.15 * fidelity - penalty)
    return {
        "score": round(score, 6),
        "validity": round(_clamp(validity), 6),
        "structure": round(_clamp(structure), 6),
        "geometry": round(_clamp(geometry), 6),
        "palette": round(_clamp(palette), 6),
        "prompt_fidelity": round(_clamp(fidelity), 6),
        "penalty": round(_clamp(penalty), 6),
    }


def reward(svg_text: str, prompt: str = "") -> float:
    return float(score_svg(svg_text, prompt)["score"])


def compute_reward(example_or_svg: Any, prompt: str = "") -> float:
    if isinstance(example_or_svg, dict):
        svg = example_or_svg.get("svg") or example_or_svg.get("prediction") or example_or_svg.get("generated") or ""
        return reward(str(svg), str(example_or_svg.get("prompt", prompt)))
    return reward(str(example_or_svg), prompt)

