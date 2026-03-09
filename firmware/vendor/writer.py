# writer.py — Monochrome Writer for MicroPython framebuf displays.
# Based on Peter Hinch's micropython-font-to-py (MIT License).
# Copyright (c) 2019-2021 Peter Hinch
# https://github.com/peterhinch/micropython-font-to-py
# Stripped to monochrome-only (Writer) for use with font_to_py-generated modules.
#
# Usage:
#   Writer.set_textpos(fb, row, col)
#   wri = Writer(fb, font_module, verbose=False)
#   wri.printstring("Hello", invert=True)   # invert=True → black text on white bg

import framebuf


class _DisplayState:
    def __init__(self):
        self.text_row = 0
        self.text_col = 0


def _get_id(device):
    if not isinstance(device, framebuf.FrameBuffer):
        raise ValueError("Device must be a FrameBuffer instance.")
    return id(device)


class Writer:
    """Render proportional/fixed-width fonts to a monochrome FrameBuffer.

    Font modules are produced by font_to_py.py:
        font_to_py.py Roboto-Regular.ttf 36 roboto_regular_36.py

    Each size needs its own pre-generated module. Place them in
    lib/epaper/fonts/ on the device.
    """

    state = {}  # keyed by id(device)

    @staticmethod
    def set_textpos(device, row=None, col=None):
        """Set the text cursor position for a device."""
        devid = _get_id(device)
        if devid not in Writer.state:
            Writer.state[devid] = _DisplayState()
        s = Writer.state[devid]
        if row is not None:
            s.text_row = row
        if col is not None:
            s.text_col = col
        return s.text_row, s.text_col

    def __init__(self, device, font, verbose=False):
        self.devid = _get_id(device)
        self.device = device
        if self.devid not in Writer.state:
            Writer.state[self.devid] = _DisplayState()
        self.font = font
        if not font.hmap():
            raise ValueError("Font must be horizontally mapped (font_to_py default).")
        self.map = framebuf.MONO_HMSB if font.reverse() else framebuf.MONO_HLSB
        self.screenwidth = device.width
        self.screenheight = device.height
        self.bgcolor = 1  # white (1 = white in MONO_HLSB)
        self.fgcolor = 0  # black
        self.row_clip = False
        self.col_clip = False
        self.wrap = True
        self.cpos = 0
        self.tab = 4
        self.glyph = None
        self.char_height = 0
        self.char_width = 0
        if verbose:
            print(
                "Writer: w={} h={} font_h={}".format(
                    device.width, device.height, font.height()
                )
            )

    def _getstate(self):
        return Writer.state[self.devid]

    def _newline(self):
        s = self._getstate()
        height = self.font.height()
        s.text_row += height
        s.text_col = 0
        margin = self.screenheight - (s.text_row + height)
        if margin < 0:
            if not self.row_clip:
                self.device.scroll(0, margin)
                self.device.fill_rect(
                    0,
                    self.screenheight + margin,
                    self.screenwidth,
                    abs(margin),
                    self.bgcolor,
                )
                s.text_row += margin

    def set_clip(self, row_clip=None, col_clip=None, wrap=None):
        if row_clip is not None:
            self.row_clip = row_clip
        if col_clip is not None:
            self.col_clip = col_clip
        if wrap is not None:
            self.wrap = wrap
        return self.row_clip, self.col_clip, self.wrap

    @property
    def height(self):
        return self.font.height()

    def printstring(self, string, invert=False):
        """Print a string at the current cursor position.

        Pass invert=True to draw black text on white background
        (the common case for e-paper with 0=black, 1=white).
        """
        lines = string.split("\n")
        last = len(lines) - 1
        for n, line in enumerate(lines):
            if line:
                self._printline(line, invert)
            if n != last:
                self._printchar("\n")

    def _printline(self, string, invert):
        rstr = None
        if self.wrap and self.stringlen(string, True):
            pos = 0
            lstr = string[:]
            while self.stringlen(lstr, True):
                pos = lstr.rfind(" ")
                if pos <= 0:
                    break
                lstr = lstr[:pos].rstrip()
            if pos > 0:
                rstr = string[pos + 1 :]
                string = lstr
        for char in string:
            self._printchar(char, invert)
        if rstr is not None:
            self._printchar("\n")
            self._printline(rstr, invert)

    def stringlen(self, string, oh=False):
        """Return pixel width of string; if oh=True return bool (overhangs screen)."""
        if not string:
            return 0
        sc = self._getstate().text_col
        wd = self.screenwidth
        total = 0
        for char in string[:-1]:
            _, _, cw = self.font.get_ch(char)
            total += cw
            if oh and total + sc > wd:
                return True
        _, _, cw = self.font.get_ch(string[-1])
        total += cw
        return (total + sc > wd) if oh else total

    def _get_char(self, char, recurse):
        if not recurse:
            if char == "\n":
                self.cpos = 0
            elif char == "\t":
                nspaces = self.tab - (self.cpos % self.tab) or self.tab
                while nspaces:
                    nspaces -= 1
                    self._printchar(" ", recurse=True)
                self.glyph = None
                return
        self.glyph = None
        if char == "\n":
            self._newline()
            return
        glyph, char_height, char_width = self.font.get_ch(char)
        if glyph is None:
            return
        s = self._getstate()
        if s.text_row + char_height > self.screenheight:
            if self.row_clip:
                return
            self._newline()
        if s.text_col + char_width > self.screenwidth:
            if self.col_clip or self.wrap:
                return
            self._newline()
        self.glyph = glyph
        self.char_height = char_height
        self.char_width = char_width

    def _printchar(self, char, invert=False, recurse=False):
        s = self._getstate()
        self._get_char(char, recurse)
        if self.glyph is None:
            return
        buf = bytearray(self.glyph)
        if invert:
            for i, v in enumerate(buf):
                buf[i] = 0xFF & ~v
        fbc = framebuf.FrameBuffer(buf, self.char_width, self.char_height, self.map)
        self.device.blit(fbc, s.text_col, s.text_row)
        s.text_col += self.char_width
        self.cpos += 1

    def tabsize(self, value=None):
        if value is not None:
            self.tab = value
        return self.tab
