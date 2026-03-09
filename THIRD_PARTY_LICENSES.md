# Third-Party Licenses

This repository bundles or distributes the following third-party components.

---

## microdot

**Files:** `firmware/vendor/microdot.py`  
**Source:** https://github.com/miguelgrinberg/microdot  
**License:** MIT

```
MIT License
Copyright (c) 2019 Miguel Grinberg

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## micropython-font-to-py (writer)

**Files:** `firmware/vendor/writer.py`  
**Source:** https://github.com/peterhinch/micropython-font-to-py  
**License:** MIT

```
MIT License
Copyright (c) 2019-2021 Peter Hinch

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## Waveshare Pico ePaper 7.5" B driver

**Files:** `firmware/vendor/Pico-ePaper-7.5-B.mod.py`  
**Source:** https://github.com/waveshareteam/Pico_ePaper_Code  
**Note:** Modified from original — `buffer_red`/`imagered` removed (black-only mode). See modification notice at the top of the file.  
**License:** MIT (as stated in the file header by the Waveshare team)

The original license text is reproduced verbatim at the top of the file.

---

## Roboto

**Files:** `assets/fonts/Roboto-*.ttf`, `firmware/assets/fonts/roboto_*.py`  
**Source:** https://github.com/googlefonts/roboto-classic  
**License:** SIL Open Font License, Version 1.1

```
Copyright 2011 The Roboto Project Authors (https://github.com/googlefonts/roboto-classic)
```

The generated `firmware/assets/fonts/roboto_*.py` files are derived Font Software produced
by `font_to_py.py` and are distributed under the same OFL 1.1 terms as the source `.ttf` files.

Full license text: https://openfontlicense.org/open-font-license-official-text/

---

## Merriweather

**Files:** `assets/fonts/Merriweather_*.ttf`, `firmware/assets/fonts/merriweather_*.py`  
**Source:** https://github.com/SorkinType/Merriweather  
**Reserved Font Name:** "Merriweather"  
**License:** SIL Open Font License, Version 1.1

```
Copyright 2020 The Merriweather Project Authors (https://github.com/EbenSorkin/Merriweather4)
```

The generated `firmware/assets/fonts/merriweather_*.py` files are derived Font Software produced
by `font_to_py.py` and are distributed under the same OFL 1.1 terms as the source `.ttf` files.

Full license text: https://openfontlicense.org/open-font-license-official-text/

---

## Bootstrap Icons

**Files:** `assets/icons/bootstrap-icons.ttf`, `assets/icons/bootstrap-icons-map.json`,
`firmware/assets/icons/bootstrap_icons_*.py`, `firmware/assets/icons/icons_map.py`  
**Source:** https://github.com/twbs/icons  
**License:** MIT

```
The MIT License (MIT)
Copyright (c) 2019-2024 The Bootstrap Authors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

The generated `firmware/assets/icons/bootstrap_icons_*.py` files are bitmap extracts
from `bootstrap-icons.ttf` produced by `font_to_py.py`, distributed under the same
MIT terms.
