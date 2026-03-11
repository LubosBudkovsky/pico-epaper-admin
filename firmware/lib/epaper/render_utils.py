"""Geometry helpers for the e-paper renderer.

No typing / dataclasses — uses plain classes and pure functions.
"""

import re


def inject_layout_context_data(layout, context):
    """Inject values from context into layout by replacing {{KEY}} tokens in-place.

    Walks the layout dict recursively and replaces string values that contain
    {{KEY}} tokens with the corresponding context value.  Operates in-place to
    avoid the serialize→regex→deserialize round-trip that previously held
    2-3× the layout size in RAM simultaneously (json.dumps + substituted string
    + json.loads output, all live at the same time).
    """
    if not context:
        return layout

    def _sub(s):
        """Replace all {{KEY}} tokens in string s."""
        if "{{" not in s:
            return s
        for key, val in context.items():
            token = "{{" + key + "}}"
            if token in s:
                s = s.replace(token, str(val))
        return s

    def _walk(obj):
        if isinstance(obj, dict):
            for k in obj:
                v = obj[k]
                if isinstance(v, str):
                    obj[k] = _sub(v)
                elif isinstance(v, (dict, list)):
                    _walk(v)
        elif isinstance(obj, list):
            for i in range(len(obj)):
                item = obj[i]
                if isinstance(item, str):
                    obj[i] = _sub(item)
                elif isinstance(item, (dict, list)):
                    _walk(item)

    _walk(layout)
    return layout


class Box:
    """Absolute-pixel bounding box produced by parse_el()."""

    def __init__(self, x1, y1, x2, y2, stroke_width, fill, radius):
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2
        self.stroke_width = stroke_width
        self.fill = fill
        self.radius = radius


def get_device_config(device_config):
    """Extract padding, rotation and invert flag from device_config dict.

    Returns (padding_top, padding_right, padding_bottom, padding_left, rotation, invert_colors).
    """

    def _int(d, key, default=0):
        try:
            return int(d.get(key, default))
        except Exception:
            return default

    return (
        _int(device_config, "padding_top"),
        _int(device_config, "padding_right"),
        _int(device_config, "padding_bottom"),
        _int(device_config, "padding_left"),
        _int(device_config, "rotation"),
        bool(device_config.get("invert_colors", False)),
    )


def _to_px(value, axis_size):
    """Convert a layout coordinate value into pixels.

    Supports int/float, percentage strings ('70%') and numeric strings.
    """
    if isinstance(value, (int, float)):
        return int(round(value))
    if isinstance(value, str):
        s = value.strip()
        if s.endswith("%"):
            try:
                return int(round(axis_size * float(s[:-1]) / 100.0))
            except Exception:
                return 0
        try:
            return int(round(float(s)))
        except Exception:
            return 0
    try:
        return int(value)
    except Exception:
        return 0


def parse_el(el, inner_w, inner_h, pad_left=0, pad_top=0):
    """Parse a rectangle-like element dict into an absolute-pixel Box.

    Supports x1/x2/y1/y2, left/right/top/bottom, and width/height combos.
    """
    elem_w = el.get("width", None)
    elem_h = el.get("height", None)

    left_px = _to_px(el["left"], inner_w) if "left" in el else None
    right_px = _to_px(el["right"], inner_w) if "right" in el else None
    w_px = _to_px(elem_w, inner_w) if elem_w is not None else None

    if "x1" in el:
        x1_rel = _to_px(el["x1"], inner_w)
    elif left_px is not None:
        x1_rel = left_px
    elif right_px is not None and w_px is not None:
        x1_rel = max(0, inner_w - right_px - w_px)
    elif right_px is not None:
        x1_rel = max(0, inner_w - right_px)
    else:
        x1_rel = 0

    if "x2" in el:
        x2_rel = _to_px(el["x2"], inner_w)
    elif right_px is not None:
        x2_rel = max(0, inner_w - right_px)
    elif left_px is not None and w_px is not None:
        x2_rel = left_px + w_px
    elif left_px is not None:
        x2_rel = left_px
    else:
        x2_rel = inner_w

    top_px = _to_px(el["top"], inner_h) if "top" in el else None
    bottom_px = _to_px(el["bottom"], inner_h) if "bottom" in el else None
    h_px = _to_px(elem_h, inner_h) if elem_h is not None else None

    if "y1" in el:
        y1_rel = _to_px(el["y1"], inner_h)
    elif top_px is not None:
        y1_rel = top_px
    elif bottom_px is not None and h_px is not None:
        y1_rel = max(0, inner_h - bottom_px - h_px)
    elif bottom_px is not None:
        y1_rel = max(0, inner_h - bottom_px)
    else:
        y1_rel = 0

    if "y2" in el:
        y2_rel = _to_px(el["y2"], inner_h)
    elif bottom_px is not None:
        y2_rel = max(0, inner_h - bottom_px)
    elif top_px is not None and h_px is not None:
        y2_rel = top_px + h_px
    elif top_px is not None:
        y2_rel = top_px
    else:
        y2_rel = inner_h

    x1 = int(pad_left) + x1_rel
    y1 = int(pad_top) + y1_rel
    x2 = int(pad_left) + x2_rel
    y2 = int(pad_top) + y2_rel

    try:
        stroke_width = int(el.get("stroke_width", 1))
    except Exception:
        stroke_width = 1

    try:
        radius = int(el.get("radius", 0))
    except Exception:
        radius = 0

    fill_val = el.get("fill", None)
    if fill_val is None or fill_val is False:
        fill = None
    else:
        try:
            fill = int(fill_val)
        except Exception:
            fill = None

    return Box(
        x1=x1, y1=y1, x2=x2, y2=y2, stroke_width=stroke_width, fill=fill, radius=radius
    )


def pos_from_el(
    el, inner_w, inner_h, pad_left=0, pad_top=0, measured_w=None, measured_h=None
):
    """Compute (x, y) for a simply-positioned element.

    Supports x/left/right and y/top/bottom keys.
    """
    if "x" in el:
        x_rel = _to_px(el["x"], inner_w)
    elif "left" in el:
        x_rel = _to_px(el["left"], inner_w)
    elif "right" in el:
        right_px = _to_px(el["right"], inner_w)
        if measured_w is not None and "width" not in el:
            x_rel = max(0, inner_w - right_px - measured_w)
        else:
            x_rel = max(0, inner_w - right_px)
    else:
        x_rel = 0

    if "y" in el:
        y_rel = _to_px(el["y"], inner_h)
    elif "top" in el:
        y_rel = _to_px(el["top"], inner_h)
    elif "bottom" in el:
        bottom_px = _to_px(el["bottom"], inner_h)
        if measured_h is not None and "height" not in el:
            y_rel = max(0, inner_h - bottom_px - measured_h)
        else:
            y_rel = max(0, inner_h - bottom_px)
    else:
        y_rel = 0

    return int(pad_left) + x_rel, int(pad_top) + y_rel
