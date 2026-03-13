"""Layout renderer for e-paper displays.

Translates a JSON-style layout dict into backend drawing calls.

This module owns all layout intelligence:
    - text sanitization (Unicode → ASCII fallbacks)
    - text measurement (single-line and wrapped)
    - word-wrap algorithm
    - element positioning (top/bottom/left/right anchors)

The backend is a thin hardware abstraction and must implement:
    .width, .height             — canvas dimensions (int)
    .init_canvas(w, h, r)       — reset/prepare the canvas
    .draw_line(x1,y1,x2,y2, stroke_width, fill)
    .draw_rect(x1,y1,x2,y2, stroke_width, fill)
    .draw_text(x, y, text, font, size, fill)   — single line, no wrapping
    .draw_icon(x, y, icon, size, fill)
    .get_font_module(name, size) — returns font_to_py module or None
    .get_icon_module(size)       — returns icon font module or None
    .get_icon_glyph(name)        — returns unicode glyph char
    .display_image()             — push canvas to hardware
"""

from lib.epaper.render_utils import (
    get_device_config,
    parse_el,
    pos_from_el,
)
from lib.log import log


# ── text sanitization ──────────────────────────────────────────────────────────────

# Fonts are generated with -l 176 (U+0000–U+00B0).  Characters outside that
# range render as '?'.  APIs commonly return typographic punctuation that falls
# far outside this range.  Map to the nearest ASCII equivalent.
_UNICODE_REPLACEMENTS = (
    ("\u2019", "'"),  # RIGHT SINGLE QUOTATION MARK  (most common)
    ("\u2018", "'"),  # LEFT SINGLE QUOTATION MARK
    ("\u201a", ","),  # SINGLE LOW-9 QUOTATION MARK
    ("\u201b", "'"),  # SINGLE HIGH-REVERSED-9
    ("\u201c", '"'),  # LEFT DOUBLE QUOTATION MARK
    ("\u201d", '"'),  # RIGHT DOUBLE QUOTATION MARK
    ("\u201e", '"'),  # DOUBLE LOW-9 QUOTATION MARK
    ("\u2014", "-"),  # EM DASH
    ("\u2013", "-"),  # EN DASH
    ("\u2015", "-"),  # HORIZONTAL BAR
    ("\u2026", "..."),  # HORIZONTAL ELLIPSIS
    ("\u00b4", "'"),  # ACUTE ACCENT
    ("\u0060", "'"),  # GRAVE ACCENT
    ("\u00ab", '"'),  # LEFT-POINTING DOUBLE ANGLE QUOTATION MARK
    ("\u00bb", '"'),  # RIGHT-POINTING DOUBLE ANGLE QUOTATION MARK
)


def _sanitize_text(text):
    """Replace out-of-range Unicode punctuation with ASCII equivalents."""
    for src, dst in _UNICODE_REPLACEMENTS:
        if src in text:
            text = text.replace(src, dst)
    return text


class Renderer:
    """Translate a layout dict into backend drawing calls.

    layout dict schema:
        {
            "elements": [ ... ],       # required
            "device_config": { ... },  # optional padding / rotation
        }
    """

    def __init__(self, backend):
        self.backend = backend
        self.width = backend.width
        self.height = backend.height

    def render(self, body):
        """Render layout onto the backend canvas and push to display.

        `body` must be a dict with `layout` and optional `device_config` keys.
        The layout must already have all context variables resolved
        ({{KEY}} tokens replaced) before calling this method.

        After iterating elements, display_image() is called to push to hardware.
        """
        if not isinstance(body, dict):
            log("Renderer: invalid body (not a dict)")
            return

        layout = body.get("layout", {})
        device_config = body.get("device_config", {})
        if not isinstance(layout, dict):
            log("Renderer: invalid layout in body")
            return
        if not isinstance(device_config, dict):
            device_config = {}

        (
            self.padding_top,
            self.padding_right,
            self.padding_bottom,
            self.padding_left,
            self.rotation,
            self.invert_colors,
        ) = get_device_config(device_config)

        self.backend.init_canvas(
            self.width, self.height, self.rotation, self.invert_colors
        )

        # Read back actual dimensions the backend chose
        self.width = self.backend.width
        self.height = self.backend.height

        self.inner_width = self.width - self.padding_right - self.padding_left
        self.inner_height = self.height - self.padding_top - self.padding_bottom

        for el in layout.get("elements", []):
            self._render_element(el)

        self.backend.display_image()

    def _measure_text(self, font_mod, text, size):
        """Return (width, height) for a single line.

        height = font_mod.baseline() so a 'bottom' anchor lands at the ink
        bottom of capital letters/digits.
        """
        if font_mod is not None:
            try:
                h = font_mod.baseline()
                w = 0
                for c in text:
                    try:
                        _, _h, cw = font_mod.get_ch(c)
                        w += cw
                    except Exception:
                        w += size
                return w, h
            except Exception:
                pass
        scale = max(1, size // 8)
        return len(text) * 8 * scale, int(round(size * 0.77))

    def _wrap_text(self, font_mod, text, size, max_width):
        """Return list of line strings fitting within max_width pixels.

        Uses character-accurate word measurement when a font module is
        available; falls back to character-count estimation otherwise.
        """
        if not max_width or max_width <= 0:
            return [text]

        if font_mod is not None:

            def _word_px(word):
                w = 0
                for c in word:
                    try:
                        _, _, cw = font_mod.get_ch(c)
                        w += cw
                    except Exception:
                        w += size
                return w

            space_px = _word_px(" ")
            words = text.split(" ")
            lines = []
            cur_words = []
            cur_w = 0
            for word in words:
                ww = _word_px(word)
                needed = (space_px + ww) if cur_words else ww
                if cur_words and cur_w + needed > max_width:
                    lines.append(" ".join(cur_words))
                    cur_words = [word]
                    cur_w = ww
                else:
                    cur_words.append(word)
                    cur_w += needed
            if cur_words:
                lines.append(" ".join(cur_words))
            return lines

        # Fallback: estimate by character count
        scale = max(1, size // 8)
        chars_per_line = max(1, max_width // (8 * scale))
        words = text.split(" ")
        lines = []
        line = ""
        for word in words:
            candidate = (line + " " + word).strip() if line else word
            if len(candidate) > chars_per_line and line:
                lines.append(line)
                line = word
            else:
                line = candidate
        if line:
            lines.append(line)
        return lines

    def _measure_wrapped_height(self, font_mod, n_lines, size):
        """Return total pixel height for n_lines of wrapped text."""
        if font_mod is not None:
            try:
                # All lines except the last use full cell height (with
                # descenders); the final line contributes only baseline height.
                return (n_lines - 1) * font_mod.height() + font_mod.baseline()
            except Exception:
                pass
        scale = max(1, size // 8)
        return n_lines * (8 * scale + 2)

    def _line_height(self, font_mod, size):
        """Return the per-line vertical advance (full cell height with descenders)."""
        if font_mod is not None:
            try:
                return font_mod.height()
            except Exception:
                pass
        return 8 * max(1, size // 8) + 2

    def _render_element(self, el):
        t = el.get("type", "")

        if t == "line":
            box = parse_el(
                el,
                self.inner_width,
                self.inner_height,
                self.padding_left,
                self.padding_top,
            )
            self.backend.draw_line(
                box.x1, box.y1, box.x2, box.y2, box.stroke_width, box.fill
            )

        elif t == "rect":
            box = parse_el(
                el,
                self.inner_width,
                self.inner_height,
                self.padding_left,
                self.padding_top,
            )
            self.backend.draw_rect(
                box.x1, box.y1, box.x2, box.y2, box.stroke_width, box.fill
            )

        elif t == "text":
            text = _sanitize_text(str(el.get("text", "")))
            font = str(el.get("font", "SANS_REGULAR"))
            try:
                size = int(el.get("size", 24))
            except (ValueError, TypeError):
                size = 24

            fill_val = el.get("fill", None)
            fill = None if (fill_val is None or fill_val is False) else int(fill_val)

            wrap = bool(el.get("wrap", False))
            font_mod = self.backend.get_font_module(font, size)
            measured_w, measured_h = self._measure_text(font_mod, text, size)

            # For bottom-anchored wrapped text, total block height determines y.
            # x is independent of height so we resolve it first.
            if wrap and "bottom" in el and "top" not in el:
                x_only, _ = pos_from_el(
                    el,
                    self.inner_width,
                    self.inner_height,
                    self.padding_left,
                    self.padding_top,
                    measured_w=measured_w,
                    measured_h=0,
                )
                max_width = self.inner_width + self.padding_left - x_only
                if max_width > 0:
                    lines = self._wrap_text(font_mod, text, size, max_width)
                    measured_h = self._measure_wrapped_height(
                        font_mod, len(lines), size
                    )

            x, y = pos_from_el(
                el,
                self.inner_width,
                self.inner_height,
                self.padding_left,
                self.padding_top,
                measured_w=measured_w,
                measured_h=measured_h,
            )

            if wrap:
                max_width = self.inner_width + self.padding_left - x
                lines = self._wrap_text(font_mod, text, size, max_width)
                line_h = self._line_height(font_mod, size)
                cy = y
                for line in lines:
                    self.backend.draw_text(x, cy, line, font, size, fill)
                    cy += line_h
            else:
                self.backend.draw_text(x, y, text, font, size, fill)

        elif t == "icon":
            icon = str(el.get("icon", ""))
            try:
                size = int(el.get("size", 24))
            except (ValueError, TypeError):
                size = 24

            fill_val = el.get("fill", None)
            fill = None if (fill_val is None or fill_val is False) else int(fill_val)

            font_mod = self.backend.get_icon_module(size)
            glyph = self.backend.get_icon_glyph(icon)

            measured_w = measured_h = 0
            if font_mod is not None:
                try:
                    measured_h = font_mod.height()
                    try:
                        _, _, measured_w = font_mod.get_ch(glyph)
                    except Exception:
                        measured_w = measured_h  # assume square
                except Exception:
                    pass
            if not measured_w:
                scale = max(1, size // 8)
                measured_w = measured_h = 8 * scale

            x, y = pos_from_el(
                el,
                self.inner_width,
                self.inner_height,
                self.padding_left,
                self.padding_top,
                measured_w=measured_w,
                measured_h=measured_h,
            )

            self.backend.draw_icon(x, y, icon, size, fill)

        else:
            log(f"Renderer: unknown element type '{t}', skipping")
