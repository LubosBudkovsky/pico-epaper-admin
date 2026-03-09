"""E-paper drawing backend using MicroPython framebuf.

The driver file is loaded at runtime from config/system.json
(EPAPER_DRIVER key, e.g. 'Pico-ePaper-7.5-B.mod'). The value is the
bare filename (no extension, no path prefix) of a .py file inside
vendor/.  Because hyphens and dots are valid in filenames but not in
Python identifiers, the file is loaded via exec() rather than import.
The driver module is expected to export a class whose name starts with
'EPD' that has:

    .width / .height        — display resolution in pixels (landscape)
    .buffer_black           — raw bytearray backing the framebuf
    .imageblack             — framebuf.FrameBuffer (MONO_HLSB) at hardware dims
    .init()                 — power-on and configure the display
    .display_Partial(buf, x, y, w, h)  — flush buffer to the panel
    .init_part()            — partial update init
    .Clear()                — fill the panel with white
    .sleep()                — put the panel into low-power sleep

Colors follow MicroPython framebuf MONO_HLSB convention: 0 = black, 1 = white.

Rotation
--------
`_flip_rotation` inverts the rotation value so the canvas is created with
the correct swapped dimensions.  At display_image() time the draw buffer is
pixel-rotated into the EPD's native landscape buffer.

Custom fonts
------------
Pre-generate font modules with font_to_py.py and place them in
assets/fonts/.  See that package's __init__.py for instructions.
When a module is not found, the built-in framebuf 8×8 bitmap font is used
(scaled by size // 8).
"""

import framebuf
import gc
from lib.log import log


# ── font configuration ────────────────────────────────────────────────────────

# Logical font name → font module base name (must match generated file names).
_FONT_MAP = {
    "SANS_REGULAR": "roboto_regular",
    "SANS_BOLD": "roboto_bold",
    "SERIF_REGULAR": "merriweather_regular",
    "SERIF_BOLD": "merriweather_bold",
}

_font_module_cache = {}  # (base_name, size) -> module or None


def clear_font_cache():
    """Evict all cached font modules from memory.

    Each font_to_py module keeps 15-30 KB of glyph bitmaps in RAM.  On a
    Pico 2 W the total set of fonts can consume 100-150 KB.  Calling this
    before every refresh ensures only the fonts the current template actually
    uses are resident, preventing gradual memory exhaustion when templates
    with different font sets are used across sessions.
    """
    import sys

    for (base, size), mod in list(_font_module_cache.items()):
        if mod is not None:
            mod_name = "assets.fonts.{}_{}".format(base, size)
            sys.modules.pop(mod_name, None)
            # Also remove the intermediate package entries so re-import works
            sys.modules.pop("assets.fonts", None)
            sys.modules.pop("assets", None)
    _font_module_cache.clear()
    gc.collect()
    log("EPD: font cache cleared")


def clear_icon_cache():
    """Evict all cached icon font modules from memory."""
    import sys

    global _icons_map_module
    for size, mod in list(_icon_font_module_cache.items()):
        if mod is not None:
            mod_name = "assets.icons.bootstrap_icons_{}".format(size)
            sys.modules.pop(mod_name, None)
            sys.modules.pop("assets.icons", None)
    _icon_font_module_cache.clear()
    if _icons_map_module not in (None, False):
        sys.modules.pop("assets.icons.icons_map", None)
    _icons_map_module = None
    gc.collect()
    log("EPD: icon cache cleared")


def _load_font_module(name, size):
    """Try to import a pre-generated font_to_py module for (name, size).

    Module path: assets.fonts.<base>_<size>
    Returns the module on success, None when not available.
    """
    base = _FONT_MAP.get(name)
    if not base:
        return None
    key = (base, size)
    if key in _font_module_cache:
        return _font_module_cache[key]
    mod_name = "assets.fonts.{}_{}".format(base, size)
    try:
        mod = __import__(mod_name, None, None, ("",))
        _font_module_cache[key] = mod
        log("Font loaded: {}".format(mod_name))
        return mod
    except ImportError:
        _font_module_cache[key] = None  # cache miss so we don't retry
        return None


# ── icon font configuration ─────────────────────────────────────────────────

_icon_font_module_cache = {}  # size -> module or None
_icons_map_module = None  # lazy-loaded assets.icons.icons_map


def _load_icon_module(size):
    """Try to import assets.icons.bootstrap_icons_{size}.

    Returns the module on success, None when not available.
    """
    if size in _icon_font_module_cache:
        return _icon_font_module_cache[size]
    mod_name = "assets.icons.bootstrap_icons_{}".format(size)
    try:
        mod = __import__(mod_name, None, None, ("",))
        _icon_font_module_cache[size] = mod
        log("Icon font loaded: {}".format(mod_name))
        return mod
    except ImportError:
        _icon_font_module_cache[size] = None
        return None


def _get_icon_glyph(name):
    """Return the unicode glyph char for icon name, or '?' if not found.

    Lazily imports assets.icons.icons_map on first call.
    """
    global _icons_map_module
    if _icons_map_module is None:
        try:
            _icons_map_module = __import__("assets.icons.icons_map", None, None, ("",))
        except ImportError:
            _icons_map_module = False
            log("icons_map not found — run tools/gen_icons.py to generate it")
    if _icons_map_module is False:
        return "?"
    return _icons_map_module.get(name)


# ── rotation helpers ──────────────────────────────────────────────────────────


def _flip_rotation(rotation):
    """Return the corrected rotation value for the hardware coordinate system.

    The hardware and framebuf rotate in opposite directions; flipping
    90↔270 corrects for that so the rendered content appears with the expected
    orientation on screen.
    """
    return {0: 0, 90: 270, 180: 180, 270: 90}.get(rotation, 0)


def _rotate_framebuf(src_fb, src_w, src_h, dst_fb, rotation):
    """Pixel-by-pixel rotation from src_fb into dst_fb.

    Supports 90° and 270° CW rotation only (the cases where canvas dimensions
    are swapped).  dst_fb must already be sized for the rotated dimensions
    (src_h × src_w).
    """
    if rotation == 90:
        # 90° CW: src(x, y) → dst(src_h-1-y, x)
        for y in range(src_h):
            for x in range(src_w):
                dst_fb.pixel(src_h - 1 - y, x, src_fb.pixel(x, y))
    elif rotation == 270:
        # 270° CW (= 90° CCW): src(x, y) → dst(y, src_w-1-x)
        for y in range(src_h):
            for x in range(src_w):
                dst_fb.pixel(y, src_w - 1 - x, src_fb.pixel(x, y))


# ── FrameBuffer wrapper ──────────────────────────────────────────────────────


class _FB(framebuf.FrameBuffer):
    """FrameBuffer subclass that exposes .width and .height attributes.

    vendor/writer.py (and other consumers) read device.width / device.height
    but MicroPython's built-in FrameBuffer C type does not store them.
    This subclass adds them without any other behavioural change.
    """

    def __init__(self, buf, width, height):
        super().__init__(buf, width, height, framebuf.MONO_HLSB)
        self.width = width
        self.height = height


# ── driver loader ─────────────────────────────────────────────────────────────


def _load_epd_class(driver_name):
    """Load driver .py from vendor/ by bare filename; return the first EPD* class.

    Using exec() instead of __import__ so that filenames with hyphens/dots
    (e.g. 'Pico-ePaper-7.5-B') are handled without any import-system tricks.
    The globs dict is freed after class extraction so driver-level constants and
    helper functions don't linger on the heap.
    """
    path = "vendor/" + driver_name + ".py"
    globs = {}
    with open(path) as f:
        exec(f.read(), globs)  # noqa: S102
    epd_class = None
    for name, obj in globs.items():
        if name.startswith("EPD") and isinstance(obj, type):
            epd_class = obj
            break
    del globs
    gc.collect()
    if epd_class is None:
        raise RuntimeError("No EPD class found in " + path)
    return epd_class


# ── backend ───────────────────────────────────────────────────────────────────


class EPDBackend:
    """Drawing backend that renders into a framebuf then pushes to hardware.

    The canvas may have different dimensions than the hardware when rotation
    is 90 or 270 (portrait canvas for a landscape display).  At display_image()
    time the canvas is pixel-rotated into the driver's native buffer.
    """

    def __init__(self, driver_name):
        log("EPD backend: loading driver vendor/" + driver_name + ".py")
        EPDClass = _load_epd_class(driver_name)  # globs freed inside
        gc.collect()  # free exec() residue BEFORE driver allocates its buffers
        self._epd = EPDClass()
        # Expose hardware dimensions; init_canvas may swap them for the canvas.
        self.width = self._epd.width
        self.height = self._epd.height
        self.rotation = 0
        # _draw_buf is NOT pre-allocated here.  It is allocated in init_canvas()
        # and freed at the end of display_image() so that 48 KB is returned to
        # the heap between refreshes — while the HTTP server handles requests.
        # The server and a display cycle never run concurrently, so this is safe.
        self._draw_buf = None
        self._fb = None
        log(f"EPD backend ready: {self.width}x{self.height}")

    # ── canvas control ───────────────────────────────────────────────────────

    def init_canvas(self, width=None, height=None, rotation=0):
        """Prepare the drawing canvas with the given rotation.

        When rotation is 90 or 270 the canvas dimensions are swapped
        (portrait canvas for a landscape display).  The rotation is stored
        and applied in display_image().
        """
        self._user_rotation = rotation  # preserved for logging
        self.rotation = _flip_rotation(rotation)
        epd = self._epd

        gc.collect()  # free any previous render state before allocating

        if self.rotation in (90, 270):
            # Portrait canvas: swap hardware dims.
            canvas_w = epd.height
            canvas_h = epd.width
        else:
            canvas_w = epd.width
            canvas_h = epd.height

        log(f"EPD: canvas {canvas_w}×{canvas_h}, rotation {rotation}°")

        # Allocate the draw buffer now.  It will be freed in display_image()
        # after epd.sleep(), so the 48 KB is only on the heap for the duration
        # of one render+display cycle.
        _buf_size = (epd.width * epd.height + 7) // 8
        self._draw_buf = bytearray(_buf_size)
        self._fb = _FB(self._draw_buf, canvas_w, canvas_h)
        self.width = canvas_w
        self.height = canvas_h
        self._fb.fill(1)  # white

    # ── drawing primitives ───────────────────────────────────────────────────

    def draw_line(self, x1, y1, x2, y2, stroke_width=1, fill=None):
        """Draw a line with optional stroke width.

        For horizontal and vertical lines, stroke_width draws that many parallel
        lines to produce a thick stroke.  For diagonal lines framebuf.line() is
        1px only, so stroke_width is ignored.
        """
        color = 0 if fill is None else fill
        sw = max(1, stroke_width)
        if sw == 1 or (x1 != x2 and y1 != y2):
            self._fb.line(x1, y1, x2, y2, color)
        elif y1 == y2:
            # Horizontal — stack rows downward
            for i in range(sw):
                self._fb.line(x1, y1 + i, x2, y2 + i, color)
        else:
            # Vertical — stack columns rightward
            for i in range(sw):
                self._fb.line(x1 + i, y1, x2 + i, y2, color)

    def draw_rect(self, x1, y1, x2, y2, stroke_width=1, fill=None):
        x, y = x1, y1
        w = max(0, x2 - x1)
        h = max(0, y2 - y1)
        if fill is not None:
            self._fb.fill_rect(x, y, w, h, fill)  # fill=0 black, fill=1 white
        else:
            # Outline: draw stroke_width nested rects inward
            sw = max(1, stroke_width)
            for i in range(sw):
                rw, rh = w - 2 * i, h - 2 * i
                if rw > 0 and rh > 0:
                    self._fb.rect(x + i, y + i, rw, rh, 0)

    def draw_text(self, x, y, text, font="SANS_REGULAR", size=24, fill=None):
        """Render a single line of text at (x, y).

        No word-wrapping — that is handled by the Renderer before calling here.
        Sanitization is also the Renderer's responsibility.

        fill=None/0  → black text on white background
        fill=1       → white text (inverted)
        """
        color = 0 if fill is None else fill
        font_mod = _load_font_module(font, size)
        if font_mod is not None:
            from vendor.writer import Writer

            Writer.set_textpos(self._fb, y, x)
            wri = Writer(self._fb, font_mod, verbose=False)
            wri.set_clip(row_clip=True, col_clip=True, wrap=False)
            wri.printstring(text, invert=(color == 0))
            return
        # fallback: built-in 8×8 font
        scale = max(1, int(size) // 8)
        self._draw_text_scaled(x, y, text, scale, color)

    def get_font_module(self, name, size):
        """Return the font_to_py module for (name, size), or None if unavailable.

        Exposed so the Renderer can access font metrics (baseline, height,
        get_ch) for measurement and word-wrap without re-importing.
        """
        return _load_font_module(name, size)

    def get_icon_module(self, size):
        """Return the icon font module for the given size, or None."""
        return _load_icon_module(size)

    def get_icon_glyph(self, name):
        """Return the unicode glyph char for the named icon."""
        return _get_icon_glyph(name)

    def draw_icon(self, x, y, icon, size=24, fill=None):
        """Render a Bootstrap icon glyph at (x, y).

        icon  — icon name as in bootstrap-icons (e.g. 'alarm', 'wifi')
        size  — pixel height; must match a pre-generated bootstrap_icons_{size}.py
        fill  — 0 = black (default), 1 = white

        Falls back to drawing '?' with the built-in font when the icon font
        module or icon name is not found.
        """
        color = 0 if fill is None else fill
        glyph = _get_icon_glyph(icon)
        font_mod = _load_icon_module(size)

        if font_mod is not None:
            from vendor.writer import Writer

            Writer.set_textpos(self._fb, y, x)
            wri = Writer(self._fb, font_mod, verbose=False)
            wri.set_clip(row_clip=True, col_clip=True, wrap=False)
            wri.printstring(glyph, invert=(color == 0))
            return

        # Fallback: draw the glyph char with scaled built-in font
        scale = max(1, size // 8)
        self._draw_text_scaled(x, y, glyph, scale, color)

    # ── display control ──────────────────────────────────────────────────────

    def display_image(self, full_refresh=False):
        """Push the draw buffer to the e-paper panel.

        Sends a white frame first to reduce ghosting between renders, then
        copies/rotates the draw buffer into the driver's native buffer and
        sends the actual content frame.

        For 90°/270° rotations the portrait draw buffer is pixel-rotated into
        the driver's native landscape buffer.  For 0°/180° a direct blit is
        used (same dimensions, no rotation needed).

        The draw buffer is allocated in init_canvas() and freed here after
        epd.sleep() so that 48 KB is returned to the heap before the next
        HTTP request arrives.

        Pass full_refresh=True to do a hardware Clear() first (removes deep ghosting).
        """
        epd = self._epd
        log("EPD: sending frame to display")

        epd.init()
        if full_refresh:
            epd.Clear()
        epd.init_part()
        epd.partFlag = 1

        # ── Step 1: soft clear — send a white frame to flush previous content ──
        # Safe because rendered content lives in self._draw_buf, not epd.buffer_black.
        epd.imageblack.fill(1)
        epd.display_Partial(epd.buffer_black, 0, 0, epd.width, epd.height)

        # ── Step 2: copy/rotate draw buffer into epd.imageblack ───────────────
        if self.rotation in (90, 270):
            log(f"EPD: rotating {self._user_rotation}°")
            _rotate_framebuf(
                self._fb, self.width, self.height, epd.imageblack, self.rotation
            )
            gc.collect()
        else:
            # 0° / 180°: same dimensions, blit directly
            epd.imageblack.blit(self._fb, 0, 0)

        # ── Step 3: send actual content ────────────────────────────────────────
        epd.display_Partial(epd.buffer_black, 0, 0, epd.width, epd.height)
        log("EPD: display done")
        epd.sleep()

        # Free the draw buffer so 48 KB is returned to the heap before the HTTP
        # server handles the next request.  init_canvas() will re-allocate it
        # at the start of the next render cycle.
        self._fb = None
        del self._draw_buf
        self._draw_buf = None
        gc.collect()
        log("EPD: draw buffer freed")

    def clear_screen(self):
        """Clear the panel to white and put it to sleep."""
        epd = self._epd
        log("EPD: clearing screen")
        epd.init()
        epd.Clear()
        epd.sleep()
        log("EPD: screen cleared")

    # ── internal helpers ─────────────────────────────────────────────────────

    def _draw_text_scaled(self, x, y, text, scale, color):
        """Draw text scaled by integer factor using a temporary framebuf blit."""
        if not text:
            return
        if scale == 1:
            self._fb.text(text, x, y, color)
            return
        text_w = len(text) * 8
        text_h = 8
        buf_bytes = (text_w * text_h + 7) // 8
        tmp = bytearray(buf_bytes)
        tmp_fb = framebuf.FrameBuffer(tmp, text_w, text_h, framebuf.MONO_HLSB)
        tmp_fb.fill(1)
        tmp_fb.text(text, 0, 0, 0)
        for row in range(text_h):
            for col in range(text_w):
                if tmp_fb.pixel(col, row) == 0:
                    self._fb.fill_rect(
                        x + col * scale, y + row * scale, scale, scale, color
                    )
        del tmp, tmp_fb
        gc.collect()
