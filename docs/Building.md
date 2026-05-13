# Building from source

The whole app is a single Python file: **`super_calc.py`** (~2700 lines). The `build.ps1` script wraps it into a one-file Windows executable using PyInstaller.

## Prerequisites

- **Python 3.10+** (tested with 3.13)
- **pip**

Install dependencies once:

```powershell
pip install numpy scipy sympy matplotlib pillow pyinstaller tkinterdnd2
```

## Run from source (no build)

For development, just run the script directly:

```powershell
python super_calc.py
```

Edits to `super_calc.py` take effect on next launch — no PyInstaller round-trip needed.

## Build the .exe

```powershell
.\build.ps1
```

Behind the scenes this runs:

```
pyinstaller --noconfirm --onefile --windowed \
    --name SuperCalc \
    --collect-data tkinterdnd2 \
    --collect-data matplotlib \
    --hidden-import="matplotlib.backends.backend_tkagg" \
    --hidden-import="PIL._tkinter_finder" \
    --exclude-module=PyQt5 ... [other excludes] \
    super_calc.py
```

Build time: ~5 minutes (first run; subsequent rebuilds are faster). Output: `dist\SuperCalc.exe` (~80 MB).

### What the flags do

- `--onefile` — one self-extracting exe (vs `--onedir`'s folder of files).
- `--windowed` — no console window opens alongside the GUI.
- `--collect-data tkinterdnd2` and `--collect-data matplotlib` — bundle their data files (font caches, Tcl scripts).
- `--hidden-import` lines — modules that PyInstaller's static analysis misses (matplotlib's Tk backend, PIL's Tk-image bridge).
- `--exclude-module=…` — keep the exe small by excluding heavy packages we don't use (PyQt, IPython, pandas, torch, tensorflow, etc.). Without these excludes, the exe balloons to 300+ MB.

## Project layout

```
super_calculator/
├── super_calc.py          # all source — one file
├── build.ps1              # PyInstaller wrapper
├── README.md
├── LICENSE
├── .gitignore
├── docs/                  # this wiki
│   ├── *.md
│   └── images/*.png
└── dist/
    └── SuperCalc.exe      # build output (gitignored)
```

## Code structure inside `super_calc.py`

Roughly in this order:

1. **Themes** (`THEMES`, `CURRENT_THEME`, `T()`)
2. **Constants** and **unit ratios** (`CONSTANTS`, `UNIT_CATEGORIES`, `EXPRESSION_LIBRARY`, `RANGE_PRESETS_2D`/`_3D`)
3. **Engine** — sympy-backed expression evaluator, namespace builder, preprocessor (factorial syntax, unicode shortcuts)
4. **UI helpers** — `styled_button`, `render_latex_to_image`, `parse_num`, `make_scroll_frame`, `style_axes`, `get_cmap`
5. **Tabs** — one class per tab: `CalcTab`, `CASTab`, `Graph2DTab`, `Graph3DTab`, `DataTab`, `DemosTab`, `TemplatesTab`, `UnitsTab`, `SettingsTab`
6. **`App`** — top-level Tk root, notebook, theme application, keyboard shortcuts, template loader
7. **`_build_icon`** — generates the application icon programmatically via Pillow (avoids bundling an external file)

## Releasing

To cut a GitHub Release with the .exe:

```powershell
gh release create v1.0 dist\SuperCalc.exe --title "Super Calculator v1.0" --notes-file RELEASE_NOTES.md
```

After release, users can grab the binary via `https://github.com/USER/REPO/releases/latest/download/SuperCalc.exe` — this is the URL referenced in the README's download badge.
