# Super Calculator v1.0

First public release.

## Features

- **🧮 Calculator** — Scientific arithmetic (sympy-backed), DEG/RAD toggle, history, named variables, programmer mode with hex/oct/bin and bitwise ops.
- **ƒ(x) Symbolic / CAS** — Simplify, expand, factor, differentiate, integrate (definite + indefinite), limits, series, solve, substitute. LaTeX rendering of results, export as LaTeX or Python.
- **📈 Graph 2D** — Explicit, parametric, polar, implicit, vector fields, slope fields. Curated example library per kind. Range presets, resolution slider.
- **🧊 Graph 3D** — Surfaces, wireframes, filled contours, 3D parametric curves, complex domain coloring.
- **📊 Data** — Drag-and-drop CSV. Auto column profiling, summary stats, histograms, scatter (with regression: linear / poly-2/3 / exponential / logarithmic / power), correlation heatmap, scatter matrix.
- **✨ 17 Interactive Demos**:
  - Fractals: Mandelbrot (click-to-zoom), Julia (sliders), Newton's (8 polynomials), Sierpinski (3–8 vertices), L-system tree, Koch snowflake
  - Probability: Buffon's needle, Monte Carlo π
  - Dynamical systems: Lorenz attractor, double pendulum, 3-body gravity, 2D wave PDE, logistic-map bifurcation
  - Discrete: Conway's Game of Life, Collatz orbits
  - Waves: Fourier series builder, Lissajous curves
- **📂 Templates** — 18 click-to-load examples spanning algebra, calculus, ODEs, physics, statistics, finance, number theory.
- **📏 Units** — 7 categories of unit conversion, 17 physical constants.
- **⚙️ Settings** — 4 themes (Dark, Light, Synthwave, Solarized), angle mode, precision.

## Download

Grab **`SuperCalc.exe`** below. ~80 MB single-file Windows binary. No installer, no Python required.

Windows SmartScreen may warn on first launch (the exe is unsigned). Click **More info → Run anyway**.

## What's bundled inside the exe

- Python 3.13
- NumPy 2.4
- SciPy 1.17
- SymPy 1.14
- Matplotlib 3.10
- Pillow 12
- tkinterdnd2 (drag-and-drop support)

All packed via PyInstaller `--onefile`.

## Requirements

- Windows 10 or 11
- ~200 MB free disk for the runtime unpack

## Known quirks

- First launch takes ~3–5 seconds (PyInstaller unpacks to `%TEMP%`). Subsequent launches are instant.
- The .exe is unsigned — SmartScreen will warn once.
- 3D plots may need a click in the matplotlib toolbar's "home" icon to reset the view.
