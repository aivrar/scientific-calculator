"""
Super Calculator — an all-in-one scientific calculator with visualizations.

Build with:  pyinstaller --onefile --noconsole --collect-data tkinterdnd2 \
                         --collect-data matplotlib --name SuperCalc super_calc.py
"""
from __future__ import annotations

import csv
import io
import math
import os
import random
import sys
import threading
import time
import tkinter as tk
from tkinter import filedialog, font as tkfont, messagebox, ttk

import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
import numpy as np
import sympy as sp
from matplotlib import animation, colors as mcolors, cm
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401 (registers 3d projection)

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    DND_AVAILABLE = True
except Exception:
    DND_AVAILABLE = False

APP_NAME = "Super Calculator"
APP_VERSION = "1.0"

# ---------------------------------------------------------------------------
# THEMES
# ---------------------------------------------------------------------------
THEMES = {
    "Dark": {  # Catppuccin Mocha
        "bg": "#1e1e2e", "panel": "#181825", "fg": "#cdd6f4",
        "muted": "#7f849c", "accent": "#89b4fa", "accent2": "#cba6f7",
        "btn": "#313244", "btn_hover": "#45475a",
        "btn_op": "#89b4fa", "btn_op_fg": "#1e1e2e",
        "btn_fn": "#45475a", "btn_fn_fg": "#94e2d5",
        "entry": "#11111b", "ok": "#a6e3a1", "err": "#f38ba8",
        "mpl": "dark_background", "mpl_face": "#1e1e2e",
    },
    "Light": {  # Catppuccin Latte
        "bg": "#eff1f5", "panel": "#e6e9ef", "fg": "#4c4f69",
        "muted": "#8c8fa1", "accent": "#1e66f5", "accent2": "#8839ef",
        "btn": "#ccd0da", "btn_hover": "#bcc0cc",
        "btn_op": "#1e66f5", "btn_op_fg": "#eff1f5",
        "btn_fn": "#dce0e8", "btn_fn_fg": "#179299",
        "entry": "#ffffff", "ok": "#40a02b", "err": "#d20f39",
        "mpl": "default", "mpl_face": "#ffffff",
    },
    "Synthwave": {  # refined retrowave
        "bg": "#1a1a2e", "panel": "#16213e", "fg": "#f4f4f8",
        "muted": "#8888aa", "accent": "#f72585", "accent2": "#4cc9f0",
        "btn": "#0f3460", "btn_hover": "#1a4076",
        "btn_op": "#f72585", "btn_op_fg": "#1a1a2e",
        "btn_fn": "#1a4076", "btn_fn_fg": "#4cc9f0",
        "entry": "#0f0f1e", "ok": "#06ffa5", "err": "#ff5555",
        "mpl": "dark_background", "mpl_face": "#1a1a2e",
    },
    "Solarized": {  # canonical Solarized Dark
        "bg": "#002b36", "panel": "#073642", "fg": "#eee8d5",
        "muted": "#586e75", "accent": "#268bd2", "accent2": "#b58900",
        "btn": "#073642", "btn_hover": "#0d4a59",
        "btn_op": "#268bd2", "btn_op_fg": "#fdf6e3",
        "btn_fn": "#0d4a59", "btn_fn_fg": "#b58900",
        "entry": "#001f27", "ok": "#859900", "err": "#dc322f",
        "mpl": "Solarize_Light2", "mpl_face": "#002b36",
    },
}
CURRENT_THEME = "Dark"


def T() -> dict:
    return THEMES[CURRENT_THEME]


# ---------------------------------------------------------------------------
# CONSTANTS & UNITS
# ---------------------------------------------------------------------------
CONSTANTS = {
    "pi": (math.pi, "π — ratio of circle's circumference to diameter"),
    "e": (math.e, "e — Euler's number, base of natural log"),
    "phi": ((1 + 5 ** 0.5) / 2, "φ — golden ratio"),
    "tau": (2 * math.pi, "τ — 2π"),
    "c": (299792458.0, "c — speed of light in vacuum (m/s)"),
    "G": (6.67430e-11, "G — gravitational constant"),
    "h": (6.62607015e-34, "h — Planck's constant"),
    "hbar": (1.054571817e-34, "ℏ — reduced Planck's constant"),
    "k_B": (1.380649e-23, "k_B — Boltzmann constant"),
    "N_A": (6.02214076e23, "N_A — Avogadro's number"),
    "R": (8.31446261815324, "R — universal gas constant"),
    "e_charge": (1.602176634e-19, "e — elementary charge (C)"),
    "m_e": (9.1093837015e-31, "m_e — electron mass (kg)"),
    "m_p": (1.67262192369e-27, "m_p — proton mass (kg)"),
    "g": (9.80665, "g — standard gravity (m/s²)"),
    "epsilon_0": (8.8541878128e-12, "ε₀ — vacuum permittivity"),
    "mu_0": (1.25663706212e-6, "μ₀ — vacuum permeability"),
    "atm": (101325.0, "atm — standard atmosphere (Pa)"),
}

# Pre-built expressions for one-click insertion. Per "kind" used in graph tabs.
EXPRESSION_LIBRARY = {
    "2d_explicit": [
        "sin(x)", "cos(x)", "tan(x)",
        "sin(x)/x", "x^2", "x^3 - 3*x", "x^4 - 4*x^2",
        "exp(x)", "exp(-x^2)  (Gaussian)", "ln(x)", "1/x", "sqrt(x)", "abs(x)",
        "sin(x)*cos(2*x)", "x*sin(1/x)", "sin(x^2)",
        "cos(x) + 0.3*sin(10*x)", "floor(x)", "x - floor(x)  (fractional)",
        "tanh(x)", "x*exp(-x^2)",
    ],
    "2d_parametric": [
        "cos(t) ; sin(t)  (circle)",
        "cos(3*t) ; sin(5*t)  (Lissajous)",
        "16*sin(t)^3 ; 13*cos(t)-5*cos(2*t)-2*cos(3*t)-cos(4*t)  (heart)",
        "t - sin(t) ; 1 - cos(t)  (cycloid)",
        "cos(t)+t*sin(t) ; sin(t)-t*cos(t)  (involute)",
        "(1+0.5*cos(7*t))*cos(t) ; (1+0.5*cos(7*t))*sin(t)  (rose-ish)",
        "exp(0.1*t)*cos(t) ; exp(0.1*t)*sin(t)  (log spiral)",
        "sin(t)*(exp(cos(t))-2*cos(4*t)-sin(t/12)^5) ; cos(t)*(exp(cos(t))-2*cos(4*t)-sin(t/12)^5)  (butterfly)",
    ],
    "2d_polar": [
        "cos(4*theta)  (4-petal rose)",
        "sin(5*theta)  (5-petal rose)",
        "1 + cos(theta)  (cardioid)",
        "1 + 2*cos(theta)  (limaçon)",
        "theta  (Archimedean spiral)",
        "exp(0.15*theta)  (logarithmic spiral)",
        "2*cos(2*theta)  (lemniscate)",
        "1 - sin(theta)  (cardioid down)",
    ],
    "2d_implicit": [
        "x^2 + y^2 - 1  (circle)",
        "x^2/9 + y^2/4 - 1  (ellipse)",
        "x^2 - y^2 - 1  (hyperbola)",
        "(x^2+y^2)^2 - 4*x^2*y^2  (4-leaf)",
        "x^3 + y^3 - 6*x*y  (folium of Descartes)",
        "(x^2+y^2-1)^3 - x^2*y^3  (heart)",
        "sin(x^2 + y^2) - 0.5",
        "x^4 + y^4 - 1",
    ],
    "2d_vfield": [
        "-y ; x  (rotation)",
        "x ; y  (source)",
        "-x ; -y  (sink)",
        "y ; -x  (clockwise)",
        "sin(y) ; sin(x)",
        "x*y ; y^2 - x^2",
        "y ; -sin(x) - 0.1*y  (pendulum phase)",
    ],
    "2d_slope": [
        "y - x", "x*y", "y / (x + 0.01)",
        "sin(x*y)", "x^2 - y", "-y  (decay)",
        "y*(1 - y)  (logistic)", "x + y",
    ],
    "3d_surface": [
        "sin(sqrt(x^2 + y^2))  (ripple)",
        "x^2 - y^2  (saddle)",
        "exp(-x^2 - y^2)  (Gaussian hill)",
        "sin(x)*cos(y)  (egg crate)",
        "(x^2 - 3*y^2)*exp(1 - x^2 - y^2)  (peaks)",
        "cos(x) + sin(y)",
        "1/(1 + x^2 + y^2)  (witch of Agnesi 3D)",
        "sin(x*y)",
    ],
    "3d_wire": [
        "sin(sqrt(x^2 + y^2))", "x^2 - y^2",
        "exp(-x^2 - y^2)", "sin(x)*cos(y)",
    ],
    "3d_contour": [
        "x^2 + y^2", "x^2 - y^2",
        "sin(x)*cos(y)", "exp(-(x^2+y^2))",
        "x*y", "sin(x*y)",
    ],
    "3d_param3": [
        "cos(t) ; sin(t) ; t  (helix)",
        "t*cos(t) ; t*sin(t) ; t  (conical spiral)",
        "sin(t) ; cos(2*t) ; sin(3*t)  (knot)",
        "(2+cos(7*t))*cos(t) ; (2+cos(7*t))*sin(t) ; sin(7*t)  (torus knot)",
        "cos(t)*(1+cos(7*t)/3) ; sin(t)*(1+cos(7*t)/3) ; sin(7*t)/3",
    ],
    "3d_complex": [
        "x^2", "1/x", "x^3 - 1", "sin(x)",
        "x + 1/x", "(x^2 - 1)/(x^2 + 1)", "tan(x)", "exp(x)",
    ],
    "cas": [
        "sin(x)^2 + cos(x)^2", "(x+1)*(x-1)*(x-2)", "x^3 - 6*x^2 + 11*x - 6",
        "sin(x)/x", "x*exp(-x)", "ln(1+x)", "1/(1+x^2)",
        "x*sin(x)", "exp(x)*cos(x)", "x^2 * exp(x)",
        "a*x^2 + b*x + c", "sin(x)*cos(x)", "(1+x)^n",
        "log(x)/x", "sqrt(1-x^2)", "tan(x)",
    ],
}

# (xmin, xmax, ymin, ymax) presets for the 2D graph tab.
RANGE_PRESETS_2D = {
    "Default  x:(-10,10)  y:(-5,5)":         (-10, 10, -5, 5),
    "Trigonometric  x:(-2π,2π)  y:(-2,2)":   (-2*math.pi, 2*math.pi, -2, 2),
    "Trig zoom  x:(-π,π)  y:(-1.5,1.5)":     (-math.pi, math.pi, -1.5, 1.5),
    "Q1 only  x:(0,10)  y:(0,10)":           (0, 10, 0, 10),
    "Unit  x:(-1,1)  y:(-1,1)":              (-1, 1, -1, 1),
    "Square  x:(-5,5)  y:(-5,5)":            (-5, 5, -5, 5),
    "Wide  x:(-50,50)  y:(-50,50)":          (-50, 50, -50, 50),
    "Tight  x:(-2,2)  y:(-2,2)":             (-2, 2, -2, 2),
}

RANGE_PRESETS_3D = {
    "Default  (-6, 6)":         (-6, 6),
    "Trigonometric  (-2π, 2π)": (-2*math.pi, 2*math.pi),
    "Half-trig  (-π, π)":       (-math.pi, math.pi),
    "Positive  (0, 2π)":        (0, 2*math.pi),
    "Unit  (-1, 1)":            (-1, 1),
    "Wide  (-10, 10)":          (-10, 10),
    "Small  (-3, 3)":           (-3, 3),
}

# Aux-value preset chips for the CAS tab.
CAS_AUX_PRESETS = [
    ("0", "0"), ("1", "1"), ("2", "2"), ("3", "3"),
    ("π/2", "pi/2"), ("π", "pi"), ("2π", "2*pi"),
    ("∞", "oo"), ("−∞", "-oo"),
    ("0,1", "0,1"), ("0,π", "0,pi"), ("-1,1", "-1,1"),
    ("0,2π", "0,2*pi"), ("0,5", "0,5"),
]

# Extra calculator functions accessible from a dropdown.
EXTRA_CALC_FUNCTIONS = [
    "floor(", "ceil(", "round(", "sign(", "mod(", "gcd(", "lcm(",
    "factorial(", "isprime(", "nCr(", "nPr(", "Abs(",
    "min(", "max(", "re(", "im(", "arg(", "conj(",
    "sinh(", "cosh(", "tanh(", "asinh(", "acosh(", "atanh(",
    "log2(", "log10(", "log(", "ln(", "exp(", "sqrt(", "cbrt(", "root(",
]


UNIT_CATEGORIES = {
    "Length (to meter)": {
        "m": 1.0, "km": 1000.0, "cm": 0.01, "mm": 0.001,
        "inch": 0.0254, "ft": 0.3048, "yd": 0.9144, "mile": 1609.344,
        "nm": 1e-9, "μm": 1e-6, "ly": 9.4607e15, "AU": 1.495979e11, "pc": 3.0857e16,
    },
    "Mass (to kg)": {
        "kg": 1.0, "g": 0.001, "mg": 1e-6, "ton": 1000.0,
        "lb": 0.45359237, "oz": 0.0283495, "stone": 6.35029,
    },
    "Time (to second)": {
        "s": 1.0, "ms": 0.001, "min": 60.0, "h": 3600.0,
        "day": 86400.0, "week": 604800.0, "year": 31557600.0,
    },
    "Energy (to joule)": {
        "J": 1.0, "kJ": 1000.0, "cal": 4.184, "kcal": 4184.0,
        "Wh": 3600.0, "kWh": 3.6e6, "eV": 1.602176634e-19, "BTU": 1055.06,
    },
    "Pressure (to Pa)": {
        "Pa": 1.0, "kPa": 1000.0, "atm": 101325.0,
        "bar": 1e5, "psi": 6894.76, "torr": 133.322, "mmHg": 133.322,
    },
    "Data (to byte)": {
        "B": 1.0, "KB": 1024.0, "MB": 1024**2, "GB": 1024**3,
        "TB": 1024**4, "bit": 0.125,
    },
    "Angle (to radian)": {
        "rad": 1.0, "deg": math.pi / 180.0, "grad": math.pi / 200.0,
        "turn": 2 * math.pi, "arcmin": math.pi / 10800.0, "arcsec": math.pi / 648000.0,
    },
}


# ---------------------------------------------------------------------------
# EXPRESSION EVALUATOR (sympy-based, safe — no arbitrary eval)
# ---------------------------------------------------------------------------
class Engine:
    """Evaluates math expressions safely using sympy with a math-friendly namespace."""

    def __init__(self):
        self.angle_mode = "rad"  # "rad" or "deg"
        self.memory = {}         # user-defined variables, e.g. A..Z and named vars
        self.ans = None
        self.history = []        # list of (expr, result)
        self.precision = 12

    def _ns(self):
        ns = {}
        for name, (val, _) in CONSTANTS.items():
            ns[name] = sp.Float(val)
        ns["π"] = sp.pi
        ns["pi"] = sp.pi
        ns["e"] = sp.E
        ns["i"] = sp.I
        ns["I"] = sp.I
        ns["inf"] = sp.oo
        ns["oo"] = sp.oo
        ns["nan"] = sp.nan
        # Functions: in deg mode, wrap trig to convert input degrees -> radians.
        if self.angle_mode == "deg":
            def deg_wrap(fn):
                return lambda x: fn(sp.pi * x / 180)
            def arc_wrap(fn):
                return lambda x: 180 * fn(x) / sp.pi
            ns["sin"] = deg_wrap(sp.sin); ns["cos"] = deg_wrap(sp.cos); ns["tan"] = deg_wrap(sp.tan)
            ns["asin"] = arc_wrap(sp.asin); ns["acos"] = arc_wrap(sp.acos); ns["atan"] = arc_wrap(sp.atan)
            ns["arcsin"] = ns["asin"]; ns["arccos"] = ns["acos"]; ns["arctan"] = ns["atan"]
        else:
            ns["sin"] = sp.sin; ns["cos"] = sp.cos; ns["tan"] = sp.tan
            ns["asin"] = sp.asin; ns["acos"] = sp.acos; ns["atan"] = sp.atan
            ns["arcsin"] = sp.asin; ns["arccos"] = sp.acos; ns["arctan"] = sp.atan
        # Hyperbolics — always radian
        for nm in ("sinh", "cosh", "tanh", "asinh", "acosh", "atanh"):
            ns[nm] = getattr(sp, nm)
        # Misc
        ns["ln"] = sp.log
        ns["log"] = lambda x, b=10: sp.log(x, b)
        ns["log10"] = lambda x: sp.log(x, 10)
        ns["log2"] = lambda x: sp.log(x, 2)
        ns["exp"] = sp.exp
        ns["sqrt"] = sp.sqrt
        ns["cbrt"] = lambda x: sp.root(x, 3)
        ns["root"] = lambda x, n: sp.root(x, n)
        ns["abs"] = sp.Abs
        ns["Abs"] = sp.Abs
        ns["floor"] = sp.floor
        ns["ceil"] = sp.ceiling
        ns["ceiling"] = sp.ceiling
        ns["round"] = lambda x, n=0: sp.Float(round(float(x), int(n)))
        ns["sign"] = sp.sign
        ns["min"] = sp.Min
        ns["max"] = sp.Max
        ns["gcd"] = sp.gcd
        ns["lcm"] = sp.lcm
        ns["factorial"] = sp.factorial
        ns["nCr"] = sp.binomial
        ns["nPr"] = lambda n, k: sp.factorial(n) / sp.factorial(n - k)
        ns["mod"] = sp.Mod
        ns["re"] = sp.re
        ns["im"] = sp.im
        ns["arg"] = sp.arg
        ns["conj"] = sp.conjugate
        ns["isprime"] = lambda n: sp.Integer(1 if sp.isprime(int(n)) else 0)
        # User memory
        for k, v in self.memory.items():
            ns[k] = v
        if self.ans is not None:
            ns["Ans"] = self.ans
            ns["ans"] = self.ans
        return ns

    @staticmethod
    def _preprocess(s: str) -> str:
        s = s.strip()
        if not s:
            return s
        # Replace caret with python power
        s = s.replace("^", "**")
        # Replace unicode π and √
        s = s.replace("π", "pi").replace("√", "sqrt").replace("²", "**2").replace("³", "**3")
        s = s.replace("×", "*").replace("÷", "/")
        # Trailing factorial: N! -> factorial(N). Handle simple identifiers and parens.
        out = []
        i = 0
        while i < len(s):
            ch = s[i]
            if ch == "!" and out and (out[-1].isdigit() or out[-1].isalpha() or out[-1] == ")"):
                # Walk back to find a balanced operand
                j = len(out) - 1
                if out[j] == ")":
                    depth = 1
                    j -= 1
                    while j >= 0 and depth > 0:
                        if out[j] == ")":
                            depth += 1
                        elif out[j] == "(":
                            depth -= 1
                        j -= 1
                    j += 1
                else:
                    while j >= 0 and (out[j].isalnum() or out[j] == "_" or out[j] == "."):
                        j -= 1
                    j += 1
                operand = "".join(out[j:])
                out = out[:j] + list(f"factorial({operand})")
                i += 1
                continue
            out.append(ch)
            i += 1
        return "".join(out)

    def evaluate(self, expr: str, numeric: bool = True):
        expr_pp = self._preprocess(expr)
        if not expr_pp:
            return ""
        # Handle assignment: name = value
        if "=" in expr_pp and "==" not in expr_pp:
            lhs, rhs = expr_pp.split("=", 1)
            name = lhs.strip()
            if name.isidentifier() and name not in ("pi", "e", "i"):
                val = sp.sympify(rhs, locals=self._ns())
                if numeric:
                    val = sp.nsimplify(val, rational=False)
                    try:
                        val = val.evalf(self.precision)
                    except Exception:
                        pass
                self.memory[name] = val
                self.ans = val
                self.history.append((expr, f"{name} = {val}"))
                return val
        result = sp.sympify(expr_pp, locals=self._ns())
        if numeric:
            try:
                result_num = result.evalf(self.precision)
                result = result_num
            except Exception:
                pass
        self.ans = result
        self.history.append((expr, result))
        return result


# ---------------------------------------------------------------------------
# UI HELPERS
# ---------------------------------------------------------------------------
def styled_button(parent, text, command, kind="default", **kw):
    t = T()
    if kind == "op":
        bg, fg = t["btn_op"], t["btn_op_fg"]
    elif kind == "fn":
        bg, fg = t["btn_fn"], t["btn_fn_fg"]
    else:
        bg, fg = t["btn"], t["fg"]
    btn = tk.Button(parent, text=text, command=command, bg=bg, fg=fg,
                    activebackground=t["btn_hover"], activeforeground=fg,
                    relief="flat", borderwidth=0, font=("Segoe UI", 11, "bold"),
                    cursor="hand2", **kw)
    return btn


def render_latex_to_image(latex: str, fontsize: int = 18) -> tk.PhotoImage | None:
    """Render a LaTeX-ish string to an embeddable PhotoImage using matplotlib."""
    try:
        fig = Figure(figsize=(0.01, 0.01), dpi=140)
        fig.patch.set_facecolor(T()["panel"])
        ax = fig.add_axes([0, 0, 1, 1])
        ax.set_axis_off()
        ax.set_facecolor(T()["panel"])
        text = ax.text(0.5, 0.5, f"${latex}$", color=T()["fg"],
                       ha="center", va="center", fontsize=fontsize)
        fig.canvas.draw()
        bbox = text.get_window_extent(renderer=fig.canvas.get_renderer())
        w_in = (bbox.width + 20) / fig.dpi
        h_in = (bbox.height + 20) / fig.dpi
        fig.set_size_inches(max(w_in, 0.5), max(h_in, 0.4))
        buf = io.BytesIO()
        fig.savefig(buf, format="png", facecolor=T()["panel"], bbox_inches="tight", pad_inches=0.1)
        plt.close(fig)
        buf.seek(0)
        from PIL import Image, ImageTk
        img = Image.open(buf)
        return ImageTk.PhotoImage(img)
    except Exception:
        return None


def parse_num(s, engine=None) -> float:
    """Accept plain floats and symbolic values ('pi', '-pi/2', '2*pi', '-oo')."""
    if isinstance(s, (int, float)):
        return float(s)
    s = str(s).strip()
    if not s:
        return 0.0
    try:
        return float(s)
    except ValueError:
        try:
            ns = engine._ns() if engine else {}
            return float(sp.sympify(s, locals=ns).evalf())
        except Exception:
            return 0.0


def themed_figure() -> Figure:
    fig = Figure(figsize=(6, 4.5), dpi=100, facecolor=T()["mpl_face"])
    return fig


def style_axes(ax):
    t = T()
    ax.set_facecolor(t["mpl_face"])
    for spine in ax.spines.values():
        spine.set_color(t["muted"])
    ax.tick_params(colors=t["fg"])
    if hasattr(ax, "xaxis"):
        ax.xaxis.label.set_color(t["fg"])
        ax.yaxis.label.set_color(t["fg"])
    if hasattr(ax, "title"):
        ax.title.set_color(t["fg"])


def get_cmap(name):
    """Compat shim — cm.get_cmap is deprecated in newer matplotlib."""
    try:
        return matplotlib.colormaps[name]
    except (KeyError, AttributeError):
        return cm.get_cmap(name)


def make_scroll_frame(parent, width: int, bg: str | None = None) -> tk.Frame:
    """Return an inner Frame inside a scrollable Canvas of the given fixed width.

    Pack the result's children normally — the panel scrolls vertically on overflow.
    """
    bg = bg or T()["panel"]
    outer = tk.Frame(parent, bg=bg, width=width)
    outer.pack(side="left", fill="y", padx=(10, 4), pady=10)
    outer.pack_propagate(False)
    canvas = tk.Canvas(outer, bg=bg, highlightthickness=0, width=width-18)
    canvas.pack(side="left", fill="both", expand=True)
    sb = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)
    sb.pack(side="right", fill="y")
    canvas.configure(yscrollcommand=sb.set)
    inner = tk.Frame(canvas, bg=bg)
    win = canvas.create_window((0, 0), window=inner, anchor="nw")
    def _config(_e=None):
        canvas.configure(scrollregion=canvas.bbox("all"))
        canvas.itemconfigure(win, width=canvas.winfo_width())
    inner.bind("<Configure>", _config)
    canvas.bind("<Configure>", _config)
    # Mouse wheel scroll
    def _wheel(event):
        canvas.yview_scroll(int(-event.delta / 120), "units")
    def _bind_wheel(_e):
        canvas.bind_all("<MouseWheel>", _wheel)
    def _unbind_wheel(_e):
        canvas.unbind_all("<MouseWheel>")
    inner.bind("<Enter>", _bind_wheel)
    inner.bind("<Leave>", _unbind_wheel)
    return inner


# ---------------------------------------------------------------------------
# CALCULATOR TAB (scientific + programmer + memory + history)
# ---------------------------------------------------------------------------
class CalcTab(tk.Frame):
    def __init__(self, parent, engine: Engine, app):
        super().__init__(parent, bg=T()["bg"])
        self.engine = engine
        self.app = app
        self.programmer_mode = False
        self._build()

    def _build(self):
        # Top: display
        top = tk.Frame(self, bg=T()["bg"])
        top.pack(fill="x", padx=10, pady=(10, 4))

        self.mode_var = tk.StringVar(value=self.engine.angle_mode.upper())
        mode_lbl = tk.Label(top, textvariable=self.mode_var, bg=T()["bg"], fg=T()["accent"],
                            font=("Segoe UI", 10, "bold"))
        mode_lbl.pack(side="left")
        tk.Button(top, text="DEG/RAD", command=self._toggle_angle, bg=T()["btn"], fg=T()["fg"],
                  relief="flat", font=("Segoe UI", 9)).pack(side="left", padx=8)
        tk.Button(top, text="Programmer mode", command=self._toggle_programmer, bg=T()["btn"], fg=T()["fg"],
                  relief="flat", font=("Segoe UI", 9)).pack(side="left", padx=2)

        # More functions dropdown — click any to insert at the cursor.
        tk.Label(top, text="  Functions:", bg=T()["bg"], fg=T()["muted"],
                 font=("Segoe UI", 9)).pack(side="left")
        self.fn_cb = ttk.Combobox(top, state="readonly", width=14, values=EXTRA_CALC_FUNCTIONS)
        self.fn_cb.pack(side="left", padx=4)
        self.fn_cb.bind("<<ComboboxSelected>>", self._insert_function)

        # Constants dropdown for one-click insertion.
        tk.Label(top, text="  Constants:", bg=T()["bg"], fg=T()["muted"],
                 font=("Segoe UI", 9)).pack(side="left")
        self.const_cb = ttk.Combobox(top, state="readonly", width=10, values=list(CONSTANTS.keys()))
        self.const_cb.pack(side="left", padx=4)
        self.const_cb.bind("<<ComboboxSelected>>", self._insert_constant)

        self.display = tk.Entry(self, font=("Cascadia Code", 16),
                                bg=T()["entry"], fg=T()["fg"], insertbackground=T()["fg"],
                                relief="flat", justify="right")
        self.display.pack(fill="x", padx=10, pady=(8, 2), ipady=6)
        self.display.bind("<Return>", lambda e: self._eval())
        self.display.focus_set()

        self.result_lbl = tk.Label(self, text="", bg=T()["bg"], fg=T()["accent2"],
                                   font=("Cascadia Code", 12), anchor="e", justify="right")
        self.result_lbl.pack(fill="x", padx=10, pady=(0, 4))

        # Main panes: button grid (left) + history/memory (right)
        body = tk.Frame(self, bg=T()["bg"])
        body.pack(fill="both", expand=True, padx=10, pady=6)

        self.grid_frame = tk.Frame(body, bg=T()["bg"])
        self.grid_frame.pack(side="left", fill="both", expand=True)

        side = tk.Frame(body, bg=T()["panel"], width=240)
        side.pack(side="right", fill="y", padx=(8, 0))
        side.pack_propagate(False)

        tk.Label(side, text="History", bg=T()["panel"], fg=T()["accent"],
                 font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=8, pady=(8, 2))
        self.history_box = tk.Listbox(side, bg=T()["entry"], fg=T()["fg"],
                                       selectbackground=T()["accent"], relief="flat",
                                       font=("Cascadia Code", 9), height=10)
        self.history_box.pack(fill="both", expand=True, padx=8, pady=2)
        self.history_box.bind("<Double-Button-1>", self._history_click)

        tk.Label(side, text="Variables", bg=T()["panel"], fg=T()["accent"],
                 font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=8, pady=(8, 2))
        self.mem_box = tk.Listbox(side, bg=T()["entry"], fg=T()["fg"],
                                   selectbackground=T()["accent"], relief="flat",
                                   font=("Cascadia Code", 9), height=6)
        self.mem_box.pack(fill="both", expand=True, padx=8, pady=2)
        self.mem_box.bind("<Double-Button-1>", self._mem_click)

        ctl = tk.Frame(side, bg=T()["panel"])
        ctl.pack(fill="x", padx=8, pady=4)
        tk.Button(ctl, text="Clear Hist", command=self._clear_history, bg=T()["btn"], fg=T()["fg"],
                  relief="flat", font=("Segoe UI", 9)).pack(side="left", padx=2)
        tk.Button(ctl, text="Clear Vars", command=self._clear_vars, bg=T()["btn"], fg=T()["fg"],
                  relief="flat", font=("Segoe UI", 9)).pack(side="left", padx=2)

        # Constants picker
        tk.Label(side, text="Constants", bg=T()["panel"], fg=T()["accent"],
                 font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=8, pady=(8, 2))
        const_frame = tk.Frame(side, bg=T()["panel"])
        const_frame.pack(fill="x", padx=8, pady=(0, 8))
        for i, name in enumerate(list(CONSTANTS)[:9]):
            b = tk.Button(const_frame, text=name, command=lambda n=name: self._insert(n),
                          bg=T()["btn"], fg=T()["fg"], relief="flat", font=("Segoe UI", 8),
                          width=6)
            b.grid(row=i // 3, column=i % 3, padx=1, pady=1, sticky="ew")
        for c in range(3):
            const_frame.grid_columnconfigure(c, weight=1)

        self._render_buttons()
        self._refresh_vars()

    def _render_buttons(self):
        for w in self.grid_frame.winfo_children():
            w.destroy()
        if self.programmer_mode:
            keys = [
                ["AND", "OR",  "XOR", "NOT", "<<",  ">>"],
                ["A",   "B",   "C",   "D",   "E",   "F"],
                ["7",   "8",   "9",   "/",   "BIN", "OCT"],
                ["4",   "5",   "6",   "*",   "DEC", "HEX"],
                ["1",   "2",   "3",   "-",   "(",   ")"],
                ["0",   ".",   "Ans", "+",   "AC",  "="],
            ]
        else:
            keys = [
                ["sin", "cos", "tan", "ln",  "log", "π"],
                ["asin","acos","atan","exp", "√",   "e"],
                ["x²",  "x³",  "x^y", "1/x", "n!",  "|x|"],
                ["7",   "8",   "9",   "/",   "(",   ")"],
                ["4",   "5",   "6",   "*",   "Ans", "C"],
                ["1",   "2",   "3",   "-",   ",",   "⌫"],
                ["0",   ".",   "E",   "+",   "=",   "="],
            ]
        for r, row in enumerate(keys):
            for c, k in enumerate(row):
                kind = "default"
                if k in {"+", "-", "*", "/", "=", "(", ")"}:
                    kind = "op"
                if k in {"sin", "cos", "tan", "asin", "acos", "atan", "ln", "log",
                         "exp", "√", "x²", "x³", "x^y", "1/x", "n!", "|x|",
                         "AND", "OR", "XOR", "NOT", "<<", ">>", "BIN", "OCT", "DEC", "HEX"}:
                    kind = "fn"
                btn = styled_button(self.grid_frame, k,
                                    lambda kk=k: self._press(kk), kind=kind)
                btn.grid(row=r, column=c, padx=2, pady=2, sticky="nsew",
                         ipady=8, ipadx=2)
            self.grid_frame.grid_rowconfigure(r, weight=1)
        for c in range(6):
            self.grid_frame.grid_columnconfigure(c, weight=1)

    def _press(self, k):
        d = self.display
        if k == "=":
            self._eval(); return
        if k in ("AC", "⌫"):
            if k == "AC":
                d.delete(0, tk.END); self.result_lbl.config(text=""); return
            text = d.get()
            if text: d.delete(len(text)-1, tk.END)
            return
        if self.programmer_mode:
            # In programmer mode, hex digits A-F and base prefixes insert literally.
            # "C" is a hex digit here (clear is "AC"); "E" is a hex digit (not *10^).
            if k == "BIN":
                d.insert(tk.END, "0b")
            elif k == "OCT":
                d.insert(tk.END, "0o")
            elif k == "HEX":
                d.insert(tk.END, "0x")
            elif k == "DEC":
                pass  # default; nothing to insert
            elif k in ("AND", "OR", "XOR", "NOT", "<<", ">>"):
                d.insert(tk.END, {"AND": " & ", "OR": " | ", "XOR": " ^ ",
                                  "NOT": "~", "<<": " << ", ">>": " >> "}[k])
            else:
                d.insert(tk.END, k)
            d.focus_set()
            return
        if k == "C":
            d.delete(0, tk.END); self.result_lbl.config(text=""); return
        ins = {
            "π": "pi", "√": "sqrt(", "x²": "**2", "x³": "**3", "x^y": "^",
            "1/x": "1/(", "|x|": "abs(", "n!": "!", "E": "*10^",
            "Ans": "Ans", "sin": "sin(", "cos": "cos(", "tan": "tan(",
            "asin": "asin(", "acos": "acos(", "atan": "atan(",
            "ln": "ln(", "log": "log(", "exp": "exp(",
        }
        d.insert(tk.END, ins.get(k, k))
        d.focus_set()

    def _eval(self):
        expr = self.display.get().strip()
        if not expr:
            return
        try:
            if self.programmer_mode:
                # interpret as integer expression
                py_expr = expr.replace("^", "**")
                # only allow digits + operators
                allowed = set("0123456789abcdefABCDEFxXoObB+-*/%&|^~<>() ")
                if not all(ch in allowed for ch in py_expr):
                    raise ValueError("Programmer mode: only int operators allowed")
                val = int(eval(py_expr, {"__builtins__": {}}, {}))
                disp = (f"DEC: {val}\n"
                        f"HEX: {hex(val)}\n"
                        f"OCT: {oct(val)}\n"
                        f"BIN: {bin(val)}")
                self.result_lbl.config(text=disp, fg=T()["ok"])
                self.engine.ans = sp.Integer(val)
                self.engine.history.append((expr, val))
            else:
                result = self.engine.evaluate(expr)
                self.result_lbl.config(text=f"= {result}", fg=T()["ok"])
            self._refresh_history()
            self._refresh_vars()
        except Exception as ex:
            self.result_lbl.config(text=f"⚠ {ex.__class__.__name__}: {ex}", fg=T()["err"])

    def _insert(self, s):
        self.display.insert(tk.END, s); self.display.focus_set()

    def _insert_function(self, _e=None):
        v = self.fn_cb.get()
        if v:
            self.display.insert(tk.INSERT, v)
            self.fn_cb.set("")
            self.display.focus_set()

    def _insert_constant(self, _e=None):
        v = self.const_cb.get()
        if v:
            self.display.insert(tk.INSERT, v)
            self.const_cb.set("")
            self.display.focus_set()

    def _toggle_angle(self):
        self.engine.angle_mode = "deg" if self.engine.angle_mode == "rad" else "rad"
        self.mode_var.set(self.engine.angle_mode.upper())

    def _toggle_programmer(self):
        self.programmer_mode = not self.programmer_mode
        self._render_buttons()

    def _refresh_history(self):
        self.history_box.delete(0, tk.END)
        for expr, res in self.engine.history[-50:][::-1]:
            line = f"{expr}  =  {res}"
            if len(line) > 60:
                line = line[:57] + "..."
            self.history_box.insert(tk.END, line)

    def _refresh_vars(self):
        self.mem_box.delete(0, tk.END)
        for name, val in list(self.engine.memory.items())[-20:]:
            line = f"{name} = {val}"
            if len(line) > 60:
                line = line[:57] + "..."
            self.mem_box.insert(tk.END, line)

    def _history_click(self, _e):
        sel = self.history_box.curselection()
        if not sel: return
        idx = sel[0]
        item = self.engine.history[-50:][::-1][idx]
        self.display.delete(0, tk.END)
        self.display.insert(0, str(item[0]))

    def _mem_click(self, _e):
        sel = self.mem_box.curselection()
        if not sel: return
        names = list(self.engine.memory.keys())[-20:]
        if sel[0] >= len(names): return
        self.display.insert(tk.END, names[sel[0]])

    def _clear_history(self):
        self.engine.history.clear(); self._refresh_history()

    def _clear_vars(self):
        self.engine.memory.clear(); self._refresh_vars()


# ---------------------------------------------------------------------------
# CAS / SYMBOLIC TAB
# ---------------------------------------------------------------------------
class CASTab(tk.Frame):
    def __init__(self, parent, engine: Engine, app):
        super().__init__(parent, bg=T()["bg"])
        self.engine = engine
        self.app = app
        self._build()

    def _build(self):
        top = tk.Frame(self, bg=T()["bg"]); top.pack(fill="x", padx=10, pady=8)
        tk.Label(top, text="Symbolic / CAS — pick or type an expression",
                 bg=T()["bg"], fg=T()["accent"], font=("Segoe UI", 11, "bold")).pack(anchor="w")

        # Expression preset dropdown → fills the entry on selection.
        preset_row = tk.Frame(self, bg=T()["bg"]); preset_row.pack(fill="x", padx=10, pady=(0,4))
        tk.Label(preset_row, text="Pick example:", bg=T()["bg"], fg=T()["fg"],
                 font=("Segoe UI", 10)).pack(side="left")
        self.preset_cb = ttk.Combobox(preset_row, state="readonly",
                                       values=EXPRESSION_LIBRARY["cas"], width=44)
        self.preset_cb.pack(side="left", padx=6)
        self.preset_cb.bind("<<ComboboxSelected>>", self._on_preset)

        row1 = tk.Frame(self, bg=T()["bg"]); row1.pack(fill="x", padx=10)
        tk.Label(row1, text="Expression:", bg=T()["bg"], fg=T()["fg"], font=("Segoe UI", 10)).pack(side="left")
        self.expr_entry = tk.Entry(row1, font=("Cascadia Code", 13), bg=T()["entry"], fg=T()["fg"],
                                    insertbackground=T()["fg"], relief="flat")
        self.expr_entry.pack(side="left", fill="x", expand=True, padx=8, ipady=6)
        self.expr_entry.insert(0, "sin(x)^2 + cos(x)^2")
        self.expr_entry.bind("<Return>", lambda e: self._do("simplify"))

        row2 = tk.Frame(self, bg=T()["bg"]); row2.pack(fill="x", padx=10, pady=4)
        tk.Label(row2, text="Variable:", bg=T()["bg"], fg=T()["fg"], font=("Segoe UI", 10)).pack(side="left")
        self.var_entry = ttk.Combobox(row2, state="readonly", width=6,
                                       values=["x", "y", "z", "t", "theta", "w", "n", "a", "b", "k"])
        self.var_entry.set("x"); self.var_entry.pack(side="left", padx=4)
        tk.Label(row2, text="Order/Point:", bg=T()["bg"], fg=T()["fg"], font=("Segoe UI", 10)).pack(side="left", padx=(10,0))
        self.aux_entry = ttk.Spinbox(row2, from_=-1000, to=1000, increment=1,
                                       width=10, font=("Cascadia Code", 11))
        self.aux_entry.set("0"); self.aux_entry.pack(side="left", padx=4)

        row3 = tk.Frame(self, bg=T()["bg"]); row3.pack(fill="x", padx=10, pady=(0, 4))
        tk.Label(row3, text="Quick aux:", bg=T()["bg"], fg=T()["muted"],
                 font=("Segoe UI", 9)).pack(side="left")
        for label, val in CAS_AUX_PRESETS:
            tk.Button(row3, text=label, width=4,
                      command=lambda v=val: self._set_aux(v),
                      bg=T()["btn"], fg=T()["fg"], activebackground=T()["btn_hover"],
                      relief="flat", font=("Segoe UI", 8)).pack(side="left", padx=1)

        ops = [("Simplify", "simplify"), ("Expand", "expand"), ("Factor", "factor"),
               ("Collect", "collect"), ("Apart", "apart"), ("Together", "together"),
               ("d/dx", "diff"), ("∫ dx", "integrate"), ("∫ definite", "defint"),
               ("Limit", "limit"), ("Series", "series"), ("Solve = 0", "solve"),
               ("Substitute", "subst"), ("Numeric ≈", "numeric"), ("LaTeX", "latex"),
               ("Python", "python")]
        op_grid = tk.Frame(self, bg=T()["bg"]); op_grid.pack(fill="x", padx=10, pady=8)
        for i, (label, key) in enumerate(ops):
            b = styled_button(op_grid, label, lambda k=key: self._do(k), kind="fn")
            b.grid(row=i // 8, column=i % 8, padx=3, pady=3, sticky="nsew", ipady=6)
        for c in range(8):
            op_grid.grid_columnconfigure(c, weight=1)

        # Output area: a Canvas for LaTeX images plus a Text fallback
        out_frame = tk.Frame(self, bg=T()["panel"])
        out_frame.pack(fill="both", expand=True, padx=10, pady=8)
        tk.Label(out_frame, text="Result", bg=T()["panel"], fg=T()["accent"],
                 font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=8, pady=4)
        self.out_text = tk.Text(out_frame, bg=T()["entry"], fg=T()["fg"], relief="flat",
                                font=("Cascadia Code", 11), height=8, insertbackground=T()["fg"])
        self.out_text.pack(fill="both", expand=True, padx=8, pady=(0,4))

        self.latex_canvas = tk.Canvas(out_frame, bg=T()["panel"], height=140, highlightthickness=0)
        self.latex_canvas.pack(fill="x", padx=8, pady=(0, 8))
        self._latex_image_ref = None

    def _on_preset(self, _e=None):
        v = self.preset_cb.get()
        # Strip trailing "  (description)" if present.
        if "  (" in v:
            v = v.split("  (")[0]
        self.expr_entry.delete(0, tk.END)
        self.expr_entry.insert(0, v)
        self.preset_cb.set("")

    def _set_aux(self, val):
        self.aux_entry.delete(0, tk.END)
        self.aux_entry.insert(0, val)

    def _parse(self):
        s = self.expr_entry.get()
        s = Engine._preprocess(s)
        var_s = self.var_entry.get().strip() or "x"
        x = sp.Symbol(var_s)
        ns = self.engine._ns()
        ns[var_s] = x
        # also accept y,z,t etc.
        for v in ("y", "z", "t", "a", "b", "c", "n"):
            ns.setdefault(v, sp.Symbol(v))
        expr = sp.sympify(s, locals=ns)
        return expr, x

    def _do(self, op):
        try:
            expr, x = self._parse()
            aux = self.aux_entry.get().strip() or "0"
            result = expr
            if op == "simplify":
                result = sp.simplify(expr)
            elif op == "expand":
                result = sp.expand(expr)
            elif op == "factor":
                result = sp.factor(expr)
            elif op == "collect":
                result = sp.collect(sp.expand(expr), x)
            elif op == "apart":
                result = sp.apart(expr, x)
            elif op == "together":
                result = sp.together(expr)
            elif op == "diff":
                n = int(float(aux)) if aux.lstrip("-+").isdigit() else 1
                result = sp.diff(expr, x, max(1, n))
            elif op == "integrate":
                result = sp.integrate(expr, x)
            elif op == "defint":
                # aux as "a,b"
                if "," in aux:
                    a, b = [sp.sympify(p.strip()) for p in aux.split(",", 1)]
                else:
                    a, b = sp.Integer(0), sp.sympify(aux)
                result = sp.integrate(expr, (x, a, b))
            elif op == "limit":
                point = sp.sympify(aux)
                result = sp.limit(expr, x, point)
            elif op == "series":
                point_s, _, order_s = aux.partition(",")
                point = sp.sympify(point_s.strip() or "0")
                order = int(order_s.strip() or "6") if order_s.strip() else 6
                result = sp.series(expr, x, point, order).removeO()
            elif op == "solve":
                result = sp.solve(expr, x)
            elif op == "subst":
                # aux as "x=2" or "x=pi/2"
                if "=" in aux:
                    lhs, rhs = aux.split("=", 1)
                    sym = sp.Symbol(lhs.strip())
                    result = expr.subs(sym, sp.sympify(rhs.strip()))
                else:
                    result = expr.subs(x, sp.sympify(aux))
            elif op == "numeric":
                result = expr.evalf(self.engine.precision)
            elif op == "latex":
                self.out_text.delete("1.0", tk.END)
                self.out_text.insert(tk.END, sp.latex(expr))
                self._render_latex(sp.latex(expr))
                return
            elif op == "python":
                self.out_text.delete("1.0", tk.END)
                self.out_text.insert(tk.END, sp.pycode(expr))
                return
            self.out_text.delete("1.0", tk.END)
            pretty = sp.pretty(result)
            self.out_text.insert(tk.END, str(pretty))
            try:
                latex = sp.latex(result)
                self._render_latex(latex)
            except Exception:
                self.latex_canvas.delete("all")
        except Exception as ex:
            self.out_text.delete("1.0", tk.END)
            self.out_text.insert(tk.END, f"⚠ {ex.__class__.__name__}: {ex}")
            self.latex_canvas.delete("all")

    def _render_latex(self, latex: str):
        self.latex_canvas.delete("all")
        img = render_latex_to_image(latex, fontsize=18)
        if img is None:
            return
        self._latex_image_ref = img
        self.latex_canvas.update_idletasks()
        w = self.latex_canvas.winfo_width()
        self.latex_canvas.create_image(max(w//2, 100), 70, image=img)


# ---------------------------------------------------------------------------
# 2D GRAPH TAB
# ---------------------------------------------------------------------------
class Graph2DTab(tk.Frame):
    PALETTE = ["#7aa2f7", "#f7768e", "#9ece6a", "#e0af68", "#bb9af7", "#7dcfff", "#ff9e64"]

    def __init__(self, parent, engine: Engine, app):
        super().__init__(parent, bg=T()["bg"])
        self.engine = engine
        self.app = app
        self._build()

    def _build(self):
        ctrl = make_scroll_frame(self, width=320)

        tk.Label(ctrl, text="2D Plot", bg=T()["panel"], fg=T()["accent"],
                 font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=8, pady=(8, 4))

        self.kind = tk.StringVar(value="explicit")
        for txt, val in [("y = f(x)", "explicit"),
                         ("Parametric (x(t), y(t))", "parametric"),
                         ("Polar r = f(θ)", "polar"),
                         ("Implicit F(x,y)=0", "implicit"),
                         ("Vector field (Fx, Fy)", "vfield"),
                         ("Slope field dy/dx=f(x,y)", "slope")]:
            tk.Radiobutton(ctrl, text=txt, variable=self.kind, value=val,
                           bg=T()["panel"], fg=T()["fg"], selectcolor=T()["entry"],
                           activebackground=T()["panel"], activeforeground=T()["accent"],
                           font=("Segoe UI", 9), command=self._kind_changed).pack(anchor="w", padx=8)

        self.expr_label = tk.Label(ctrl, text="Functions (one per line):",
                                   bg=T()["panel"], fg=T()["fg"], font=("Segoe UI", 10))
        self.expr_label.pack(anchor="w", padx=8, pady=(8, 2))

        # Expression preset dropdown — picking a value appends it as a new line.
        prow = tk.Frame(ctrl, bg=T()["panel"]); prow.pack(fill="x", padx=8, pady=(0, 4))
        tk.Label(prow, text="Pick:", bg=T()["panel"], fg=T()["muted"], font=("Segoe UI", 9)).pack(side="left")
        self.preset_cb = ttk.Combobox(prow, state="readonly", width=24)
        self.preset_cb.pack(side="left", fill="x", expand=True, padx=4)
        self.preset_cb.bind("<<ComboboxSelected>>", self._on_preset)

        self.expr_text = tk.Text(ctrl, height=6, bg=T()["entry"], fg=T()["fg"],
                                  insertbackground=T()["fg"], relief="flat",
                                  font=("Cascadia Code", 10))
        self.expr_text.pack(fill="x", padx=8)
        self.expr_text.insert("1.0", "sin(x)\ncos(x)\n0.5*x")

        # Range preset dropdown — sets all four spinboxes at once.
        tk.Label(ctrl, text="Range preset:", bg=T()["panel"], fg=T()["fg"],
                 font=("Segoe UI", 10)).pack(anchor="w", padx=8, pady=(8, 2))
        self.range_preset = ttk.Combobox(ctrl, state="readonly",
                                          values=list(RANGE_PRESETS_2D.keys()), width=28)
        self.range_preset.pack(fill="x", padx=8)
        self.range_preset.bind("<<ComboboxSelected>>", self._on_range_preset)

        rng = tk.Frame(ctrl, bg=T()["panel"]); rng.pack(fill="x", padx=8, pady=6)
        tk.Label(rng, text="x:", bg=T()["panel"], fg=T()["fg"]).grid(row=0, column=0, sticky="w")
        self.xmin = ttk.Spinbox(rng, from_=-10000, to=10000, increment=1, width=8)
        self.xmin.set(-10); self.xmin.grid(row=0, column=1, padx=2, pady=2)
        tk.Label(rng, text="→", bg=T()["panel"], fg=T()["fg"]).grid(row=0, column=2)
        self.xmax = ttk.Spinbox(rng, from_=-10000, to=10000, increment=1, width=8)
        self.xmax.set(10); self.xmax.grid(row=0, column=3, padx=2, pady=2)
        tk.Label(rng, text="y:", bg=T()["panel"], fg=T()["fg"]).grid(row=1, column=0, sticky="w")
        self.ymin = ttk.Spinbox(rng, from_=-10000, to=10000, increment=1, width=8)
        self.ymin.set(-5); self.ymin.grid(row=1, column=1, padx=2, pady=2)
        tk.Label(rng, text="→", bg=T()["panel"], fg=T()["fg"]).grid(row=1, column=2)
        self.ymax = ttk.Spinbox(rng, from_=-10000, to=10000, increment=1, width=8)
        self.ymax.set(5); self.ymax.grid(row=1, column=3, padx=2, pady=2)

        tk.Label(ctrl, text="Points (drag to set resolution):", bg=T()["panel"], fg=T()["fg"],
                 font=("Segoe UI", 10)).pack(anchor="w", padx=8, pady=(8, 0))
        srow = tk.Frame(ctrl, bg=T()["panel"]); srow.pack(fill="x", padx=8)
        self.npts_var = tk.IntVar(value=800)
        self.npts_label = tk.Label(srow, text="800", bg=T()["panel"], fg=T()["accent"],
                                    font=("Cascadia Code", 10, "bold"), width=5)
        self.npts_label.pack(side="right")
        self.npts = ttk.Scale(srow, from_=50, to=3000, orient="horizontal",
                               command=lambda v: self.npts_label.config(text=str(int(float(v)))))
        self.npts.set(800); self.npts.pack(side="left", fill="x", expand=True)

        styled_button(ctrl, "Plot", self._plot, kind="op").pack(fill="x", padx=8, pady=6, ipady=8)
        styled_button(ctrl, "Clear", self._clear).pack(fill="x", padx=8, pady=2, ipady=4)

        # Plot area
        right = tk.Frame(self, bg=T()["bg"])
        right.pack(side="right", fill="both", expand=True, padx=(4, 10), pady=10)
        self.fig = themed_figure()
        self.ax = self.fig.add_subplot(111)
        style_axes(self.ax)
        self.canvas = FigureCanvasTkAgg(self.fig, master=right)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)
        toolbar = NavigationToolbar2Tk(self.canvas, right)
        toolbar.update()
        toolbar.config(bg=T()["bg"])
        for child in toolbar.winfo_children():
            try: child.config(bg=T()["bg"])
            except Exception: pass
        self._kind_changed()
        self._plot()

    def _kind_changed(self):
        k = self.kind.get()
        labels = {
            "explicit": "Functions f(x) (one per line):",
            "parametric": "Pairs 'x_of_t ; y_of_t' per line, t in [0,2π]:",
            "polar": "r(θ) (one per line), θ in [0,2π]:",
            "implicit": "Expression F(x,y) (one per line, plotted at F=0):",
            "vfield": "Pair 'Fx ; Fy':",
            "slope": "f(x,y):",
        }
        self.expr_label.config(text=labels[k])
        try:
            self.preset_cb["values"] = EXPRESSION_LIBRARY["2d_" + k]
            self.preset_cb.set("")
        except Exception:
            pass

    def _on_preset(self, _e=None):
        v = self.preset_cb.get()
        if not v:
            return
        if "  (" in v:
            v = v.split("  (")[0]
        cur = self.expr_text.get("1.0", "end-1c")
        if cur and not cur.endswith("\n"):
            self.expr_text.insert("end", "\n")
        self.expr_text.insert("end", v)
        self.preset_cb.set("")

    def _on_range_preset(self, _e=None):
        key = self.range_preset.get()
        if key not in RANGE_PRESETS_2D:
            return
        xmin, xmax, ymin, ymax = RANGE_PRESETS_2D[key]
        for sb, val in [(self.xmin, xmin), (self.xmax, xmax),
                        (self.ymin, ymin), (self.ymax, ymax)]:
            sb.set(round(val, 4))
        self._plot()

    def _plot(self):
        self.ax.clear()
        style_axes(self.ax)
        ns = self.engine._ns()
        x = sp.Symbol("x"); y = sp.Symbol("y"); t = sp.Symbol("t"); theta = sp.Symbol("theta")
        for sym, name in ((x, "x"), (y, "y"), (t, "t"), (theta, "theta")):
            ns[name] = sym
        ns["θ"] = theta
        kind = self.kind.get()
        try:
            xmin = parse_num(self.xmin.get(), self.engine)
            xmax = parse_num(self.xmax.get(), self.engine)
            ymin = parse_num(self.ymin.get(), self.engine)
            ymax = parse_num(self.ymax.get(), self.engine)
            n = max(50, int(float(self.npts.get())))
        except Exception as ex:
            messagebox.showerror("Range error", str(ex)); return

        lines = [ln for ln in self.expr_text.get("1.0", tk.END).splitlines() if ln.strip()]
        try:
            if kind == "explicit":
                xs = np.linspace(xmin, xmax, n)
                for i, ln in enumerate(lines):
                    expr = sp.sympify(Engine._preprocess(ln), locals=ns)
                    fn = sp.lambdify(x, expr, modules=["numpy"])
                    ys = self._safe_eval(fn, xs)
                    self.ax.plot(xs, ys, color=self.PALETTE[i % len(self.PALETTE)], lw=1.6, label=ln)
                self.ax.legend(facecolor=T()["panel"], edgecolor=T()["muted"],
                               labelcolor=T()["fg"], fontsize=8)
            elif kind == "parametric":
                ts = np.linspace(0, 2 * math.pi, n)
                for i, ln in enumerate(lines):
                    if ";" not in ln: continue
                    a, b = ln.split(";", 1)
                    fx = sp.lambdify(t, sp.sympify(Engine._preprocess(a), locals=ns), "numpy")
                    fy = sp.lambdify(t, sp.sympify(Engine._preprocess(b), locals=ns), "numpy")
                    self.ax.plot(self._safe_eval(fx, ts), self._safe_eval(fy, ts),
                                 color=self.PALETTE[i % len(self.PALETTE)], lw=1.6, label=ln)
                self.ax.legend(facecolor=T()["panel"], edgecolor=T()["muted"],
                               labelcolor=T()["fg"], fontsize=8)
            elif kind == "polar":
                ths = np.linspace(0, 2 * math.pi, n)
                self.ax.remove()
                self.ax = self.fig.add_subplot(111, projection="polar")
                style_axes(self.ax)
                for i, ln in enumerate(lines):
                    expr = sp.sympify(Engine._preprocess(ln), locals=ns)
                    fr = sp.lambdify(theta, expr, "numpy")
                    rs = self._safe_eval(fr, ths)
                    self.ax.plot(ths, rs, color=self.PALETTE[i % len(self.PALETTE)], lw=1.6, label=ln)
            elif kind == "implicit":
                xs = np.linspace(xmin, xmax, 400)
                ys = np.linspace(ymin, ymax, 400)
                X, Y = np.meshgrid(xs, ys)
                for i, ln in enumerate(lines):
                    expr = sp.sympify(Engine._preprocess(ln), locals=ns)
                    F = sp.lambdify((x, y), expr, "numpy")
                    Z = F(X, Y)
                    self.ax.contour(X, Y, Z, levels=[0], colors=[self.PALETTE[i % len(self.PALETTE)]], linewidths=1.6)
            elif kind == "vfield":
                if lines and ";" in lines[0]:
                    a, b = lines[0].split(";", 1)
                    xs = np.linspace(xmin, xmax, 25)
                    ys = np.linspace(ymin, ymax, 25)
                    X, Y = np.meshgrid(xs, ys)
                    fxF = sp.lambdify((x, y), sp.sympify(Engine._preprocess(a), locals=ns), "numpy")
                    fyF = sp.lambdify((x, y), sp.sympify(Engine._preprocess(b), locals=ns), "numpy")
                    U = np.broadcast_to(fxF(X, Y), X.shape).astype(float)
                    V = np.broadcast_to(fyF(X, Y), X.shape).astype(float)
                    mag = np.sqrt(U**2 + V**2)
                    self.ax.streamplot(X, Y, U, V, color=mag, cmap="viridis", density=1.4)
            elif kind == "slope":
                if lines:
                    expr = sp.sympify(Engine._preprocess(lines[0]), locals=ns)
                    f = sp.lambdify((x, y), expr, "numpy")
                    xs = np.linspace(xmin, xmax, 30)
                    ys = np.linspace(ymin, ymax, 30)
                    X, Y = np.meshgrid(xs, ys)
                    S = np.broadcast_to(f(X, Y), X.shape).astype(float)
                    U = np.ones_like(S); V = S
                    L = np.hypot(U, V); U /= L; V /= L
                    self.ax.quiver(X, Y, U, V, S, cmap="plasma", pivot="middle",
                                   headwidth=0, headlength=0, headaxislength=0, scale=40)
            if kind not in ("polar",):
                self.ax.set_xlim(xmin, xmax); self.ax.set_ylim(ymin, ymax)
                self.ax.axhline(0, color=T()["muted"], lw=0.6, alpha=0.6)
                self.ax.axvline(0, color=T()["muted"], lw=0.6, alpha=0.6)
                self.ax.grid(True, color=T()["muted"], alpha=0.2)
            self.fig.tight_layout()
            self.canvas.draw()
        except Exception as ex:
            messagebox.showerror("Plot error", f"{ex.__class__.__name__}: {ex}")

    @staticmethod
    def _safe_eval(fn, xs):
        with np.errstate(all="ignore"):
            y = fn(xs)
        y = np.asarray(y, dtype=float)
        y = np.where(np.isfinite(y), y, np.nan)
        return y

    def _clear(self):
        self.expr_text.delete("1.0", tk.END)


# ---------------------------------------------------------------------------
# 3D GRAPH TAB
# ---------------------------------------------------------------------------
class Graph3DTab(tk.Frame):
    def __init__(self, parent, engine: Engine, app):
        super().__init__(parent, bg=T()["bg"])
        self.engine = engine
        self.app = app
        self._build()

    def _build(self):
        ctrl = make_scroll_frame(self, width=320)
        tk.Label(ctrl, text="3D Plot", bg=T()["panel"], fg=T()["accent"],
                 font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=8, pady=(8, 4))

        self.kind = tk.StringVar(value="surface")
        for txt, v in [("Surface z = f(x,y)", "surface"),
                       ("Wireframe", "wire"),
                       ("Filled contour", "contour"),
                       ("3D parametric curve", "param3"),
                       ("Complex domain coloring", "complex")]:
            tk.Radiobutton(ctrl, text=txt, variable=self.kind, value=v,
                           bg=T()["panel"], fg=T()["fg"], selectcolor=T()["entry"],
                           activebackground=T()["panel"], activeforeground=T()["accent"],
                           font=("Segoe UI", 9),
                           command=self._kind_changed).pack(anchor="w", padx=8)

        tk.Label(ctrl, text="Pick example:", bg=T()["panel"], fg=T()["muted"],
                 font=("Segoe UI", 9)).pack(anchor="w", padx=8, pady=(6, 0))
        self.preset_cb = ttk.Combobox(ctrl, state="readonly", width=24,
                                       values=EXPRESSION_LIBRARY["3d_surface"])
        self.preset_cb.pack(fill="x", padx=8)
        self.preset_cb.bind("<<ComboboxSelected>>", self._on_preset)

        tk.Label(ctrl, text="Expression:", bg=T()["panel"], fg=T()["fg"],
                 font=("Segoe UI", 10)).pack(anchor="w", padx=8, pady=(8, 2))
        self.expr_text = tk.Text(ctrl, height=4, bg=T()["entry"], fg=T()["fg"],
                                  insertbackground=T()["fg"], relief="flat",
                                  font=("Cascadia Code", 10))
        self.expr_text.pack(fill="x", padx=8)
        self.expr_text.insert("1.0", "sin(sqrt(x^2+y^2))")

        tk.Label(ctrl, text="Range preset:", bg=T()["panel"], fg=T()["fg"],
                 font=("Segoe UI", 10)).pack(anchor="w", padx=8, pady=(8, 2))
        self.range_preset = ttk.Combobox(ctrl, state="readonly",
                                          values=list(RANGE_PRESETS_3D.keys()), width=24)
        self.range_preset.pack(fill="x", padx=8)
        self.range_preset.bind("<<ComboboxSelected>>", self._on_range_preset)

        rng = tk.Frame(ctrl, bg=T()["panel"]); rng.pack(fill="x", padx=8, pady=6)
        tk.Label(rng, text="range:", bg=T()["panel"], fg=T()["fg"]).grid(row=0, column=0, sticky="w")
        self.r1 = ttk.Spinbox(rng, from_=-1000, to=1000, increment=1, width=8)
        self.r1.set(-6); self.r1.grid(row=0, column=1, padx=2)
        tk.Label(rng, text="→", bg=T()["panel"], fg=T()["fg"]).grid(row=0, column=2)
        self.r2 = ttk.Spinbox(rng, from_=-1000, to=1000, increment=1, width=8)
        self.r2.set(6); self.r2.grid(row=0, column=3, padx=2)

        tk.Label(ctrl, text="Resolution:", bg=T()["panel"], fg=T()["fg"],
                 font=("Segoe UI", 10)).pack(anchor="w", padx=8, pady=(8, 0))
        srow = tk.Frame(ctrl, bg=T()["panel"]); srow.pack(fill="x", padx=8)
        self.res_label = tk.Label(srow, text="70", bg=T()["panel"], fg=T()["accent"],
                                   font=("Cascadia Code", 10, "bold"), width=5)
        self.res_label.pack(side="right")
        self.res = ttk.Scale(srow, from_=20, to=200, orient="horizontal",
                              command=lambda v: self.res_label.config(text=str(int(float(v)))))
        self.res.set(70); self.res.pack(side="left", fill="x", expand=True)

        self.cmap = tk.StringVar(value="viridis")
        tk.Label(ctrl, text="Colormap:", bg=T()["panel"], fg=T()["fg"]).pack(anchor="w", padx=8, pady=(8, 0))
        ttk.Combobox(ctrl, textvariable=self.cmap,
                     values=["viridis", "plasma", "inferno", "magma", "cividis",
                             "coolwarm", "twilight", "turbo", "ocean", "terrain"],
                     state="readonly").pack(fill="x", padx=8, pady=2)
        styled_button(ctrl, "Plot", self._plot, kind="op").pack(fill="x", padx=8, pady=8, ipady=8)

        right = tk.Frame(self, bg=T()["bg"])
        right.pack(side="right", fill="both", expand=True, padx=(4, 10), pady=10)
        self.fig = themed_figure()
        self.ax = self.fig.add_subplot(111, projection="3d")
        self.ax.set_facecolor(T()["mpl_face"])
        self.canvas = FigureCanvasTkAgg(self.fig, master=right)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)
        toolbar = NavigationToolbar2Tk(self.canvas, right)
        toolbar.update(); toolbar.config(bg=T()["bg"])
        self._plot()

    def _kind_changed(self):
        k = self.kind.get()
        try:
            self.preset_cb["values"] = EXPRESSION_LIBRARY["3d_" + k]
            self.preset_cb.set("")
        except Exception:
            pass

    def _on_preset(self, _e=None):
        v = self.preset_cb.get()
        if not v:
            return
        if "  (" in v:
            v = v.split("  (")[0]
        self.expr_text.delete("1.0", tk.END)
        self.expr_text.insert("1.0", v)
        self.preset_cb.set("")

    def _on_range_preset(self, _e=None):
        key = self.range_preset.get()
        if key not in RANGE_PRESETS_3D:
            return
        a, b = RANGE_PRESETS_3D[key]
        self.r1.set(round(a, 4)); self.r2.set(round(b, 4))
        self._plot()

    def _plot(self):
        kind = self.kind.get()
        self.fig.clear()
        if kind in ("surface", "wire", "param3"):
            self.ax = self.fig.add_subplot(111, projection="3d")
        else:
            self.ax = self.fig.add_subplot(111)
        self.ax.set_facecolor(T()["mpl_face"])
        try:
            a = parse_num(self.r1.get(), self.engine)
            b = parse_num(self.r2.get(), self.engine)
            n = max(20, int(float(self.res.get())))
            expr_s = self.expr_text.get("1.0", tk.END).strip().splitlines()[0]
            ns = self.engine._ns()
            x = sp.Symbol("x"); y = sp.Symbol("y"); t = sp.Symbol("t"); z = sp.Symbol("z")
            for s, n2 in ((x, "x"), (y, "y"), (t, "t"), (z, "z")):
                ns[n2] = s
            expr = sp.sympify(Engine._preprocess(expr_s), locals=ns)
            cmap = self.cmap.get()
            if kind in ("surface", "wire", "contour"):
                f = sp.lambdify((x, y), expr, "numpy")
                xs = np.linspace(a, b, n); ys = np.linspace(a, b, n)
                X, Y = np.meshgrid(xs, ys)
                with np.errstate(all="ignore"):
                    Z = np.asarray(np.broadcast_to(f(X, Y), X.shape), dtype=float)
                if kind == "surface":
                    self.ax.plot_surface(X, Y, Z, cmap=cmap, edgecolor="none", rstride=1, cstride=1, alpha=0.95)
                elif kind == "wire":
                    self.ax.plot_wireframe(X, Y, Z, color=T()["accent"], lw=0.5, rstride=2, cstride=2)
                else:
                    cs = self.ax.contourf(X, Y, Z, levels=30, cmap=cmap)
                    self.fig.colorbar(cs, ax=self.ax)
                if kind != "contour":
                    self.ax.set_xlabel("x"); self.ax.set_ylabel("y"); self.ax.set_zlabel("z")
            elif kind == "param3":
                # expr should be like "cos(t); sin(t); t" or 't*cos(t); t*sin(t); t'
                parts = [p.strip() for p in expr_s.split(";")]
                if len(parts) != 3: raise ValueError("Need three parts separated by ';'")
                fx = sp.lambdify(t, sp.sympify(Engine._preprocess(parts[0]), locals=ns), "numpy")
                fy = sp.lambdify(t, sp.sympify(Engine._preprocess(parts[1]), locals=ns), "numpy")
                fz = sp.lambdify(t, sp.sympify(Engine._preprocess(parts[2]), locals=ns), "numpy")
                ts = np.linspace(a, b, n * 20)
                xs = np.asarray(np.broadcast_to(fx(ts), ts.shape), dtype=float)
                ys = np.asarray(np.broadcast_to(fy(ts), ts.shape), dtype=float)
                zs = np.asarray(np.broadcast_to(fz(ts), ts.shape), dtype=float)
                colors = get_cmap(cmap)(np.linspace(0, 1, len(ts)))
                for i in range(len(ts)-1):
                    self.ax.plot(xs[i:i+2], ys[i:i+2], zs[i:i+2], color=colors[i])
            elif kind == "complex":
                w = sp.Symbol("w")
                f = sp.lambdify(w, expr.subs(x, w), "numpy")
                xs = np.linspace(a, b, 600); ys = np.linspace(a, b, 600)
                X, Y = np.meshgrid(xs, ys)
                Z = X + 1j * Y
                with np.errstate(all="ignore"):
                    W = f(Z)
                hue = (np.angle(W) / (2 * math.pi)) % 1
                mag = np.abs(W)
                bright = 0.5 + 0.5 * np.tanh(np.log1p(mag) - 1)
                hsv = np.dstack([hue, np.ones_like(hue) * 0.9, bright])
                rgb = mcolors.hsv_to_rgb(np.clip(hsv, 0, 1))
                self.ax.imshow(rgb, extent=[a, b, a, b], origin="lower")
                self.ax.set_xlabel("Re(z)"); self.ax.set_ylabel("Im(z)")
            self.canvas.draw()
        except Exception as ex:
            messagebox.showerror("Plot error", f"{ex.__class__.__name__}: {ex}")


# ---------------------------------------------------------------------------
# DATA TAB (drag-and-drop CSV)
# ---------------------------------------------------------------------------
class DataTab(tk.Frame):
    def __init__(self, parent, engine: Engine, app):
        super().__init__(parent, bg=T()["bg"])
        self.engine = engine
        self.app = app
        self.headers: list[str] = []
        self.data: dict[str, list] = {}
        self._build()

    def _build(self):
        left = make_scroll_frame(self, width=330)

        # Drop zone
        zone_msg = "📂  Drop a .csv file here\n(or click to open)"
        if not DND_AVAILABLE:
            zone_msg += "\n(install tkinterdnd2 for native drag-drop)"
        self.dropzone = tk.Label(left, text=zone_msg, bg=T()["entry"], fg=T()["accent"],
                                  font=("Segoe UI", 11, "bold"), height=6, relief="flat")
        self.dropzone.pack(fill="x", padx=8, pady=8)
        self.dropzone.bind("<Button-1>", lambda e: self._open_csv())
        if DND_AVAILABLE:
            try:
                self.dropzone.drop_target_register(DND_FILES)
                self.dropzone.dnd_bind("<<Drop>>", self._on_drop)
            except Exception:
                pass

        tk.Label(left, text="Columns", bg=T()["panel"], fg=T()["accent"],
                 font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=8, pady=(4, 2))
        self.cols_box = tk.Listbox(left, bg=T()["entry"], fg=T()["fg"], relief="flat",
                                    font=("Cascadia Code", 9), height=8)
        self.cols_box.pack(fill="x", padx=8, pady=(0, 6))

        # Plot picker
        tk.Label(left, text="Plot:", bg=T()["panel"], fg=T()["fg"]).pack(anchor="w", padx=8)
        self.plot_kind = tk.StringVar(value="auto")
        ttk.Combobox(left, textvariable=self.plot_kind, state="readonly",
                     values=["auto", "histogram", "scatter", "line", "bar", "box",
                             "scatter-matrix", "correlation heatmap"]).pack(fill="x", padx=8, pady=2)

        sel = tk.Frame(left, bg=T()["panel"]); sel.pack(fill="x", padx=8, pady=4)
        tk.Label(sel, text="X col:", bg=T()["panel"], fg=T()["fg"]).grid(row=0, column=0, sticky="w")
        self.xcol = ttk.Combobox(sel, state="readonly", width=12); self.xcol.grid(row=0, column=1, pady=2)
        tk.Label(sel, text="Y col:", bg=T()["panel"], fg=T()["fg"]).grid(row=1, column=0, sticky="w")
        self.ycol = ttk.Combobox(sel, state="readonly", width=12); self.ycol.grid(row=1, column=1, pady=2)

        # Regression options
        self.reg_var = tk.StringVar(value="none")
        tk.Label(left, text="Fit:", bg=T()["panel"], fg=T()["fg"]).pack(anchor="w", padx=8, pady=(6,2))
        ttk.Combobox(left, textvariable=self.reg_var, state="readonly",
                     values=["none", "linear", "polynomial-2", "polynomial-3",
                             "exponential", "logarithmic", "power"]).pack(fill="x", padx=8, pady=2)

        styled_button(left, "Plot", self._plot, kind="op").pack(fill="x", padx=8, pady=6, ipady=6)
        styled_button(left, "Load sample (Iris)", self._load_sample).pack(fill="x", padx=8, pady=2, ipady=4)

        # Right: stats + plot
        right = tk.Frame(self, bg=T()["bg"]); right.pack(side="right", fill="both", expand=True, padx=(4,10), pady=10)
        stats_frame = tk.Frame(right, bg=T()["panel"]); stats_frame.pack(fill="x", pady=(0,6))
        tk.Label(stats_frame, text="Summary", bg=T()["panel"], fg=T()["accent"],
                 font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=8, pady=4)
        self.stats_text = tk.Text(stats_frame, height=7, bg=T()["entry"], fg=T()["fg"], relief="flat",
                                   font=("Cascadia Code", 9), insertbackground=T()["fg"])
        self.stats_text.pack(fill="x", padx=8, pady=(0,8))

        self.fig = themed_figure()
        self.ax = self.fig.add_subplot(111)
        style_axes(self.ax)
        self.canvas = FigureCanvasTkAgg(self.fig, master=right)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)
        NavigationToolbar2Tk(self.canvas, right).update()

    def _on_drop(self, event):
        path = event.data.strip().strip("{}")
        if path: self._load_csv(path)

    def _open_csv(self):
        p = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv *.tsv *.txt"), ("All", "*.*")])
        if p: self._load_csv(p)

    def _load_csv(self, path):
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                sniff = f.read(4096); f.seek(0)
                try:
                    dialect = csv.Sniffer().sniff(sniff, delimiters=",;\t|")
                except Exception:
                    dialect = csv.excel
                reader = csv.reader(f, dialect=dialect)
                rows = list(reader)
            if not rows:
                raise ValueError("CSV is empty")
            # detect header
            headers = rows[0]
            has_header = any(not _is_number(c) for c in headers) and len(rows) > 1
            if has_header:
                data_rows = rows[1:]
            else:
                headers = [f"col{i+1}" for i in range(len(rows[0]))]
                data_rows = rows
            self.headers = headers
            self.data = {h: [] for h in headers}
            for r in data_rows:
                for i, h in enumerate(headers):
                    if i < len(r):
                        self.data[h].append(r[i])
            self.dropzone.config(text=f"📂 Loaded:\n{os.path.basename(path)}\n{len(data_rows)} rows × {len(headers)} cols")
            self._after_load()
        except Exception as ex:
            messagebox.showerror("CSV error", str(ex))

    def _after_load(self):
        self.cols_box.delete(0, tk.END)
        numeric_cols = []
        for h in self.headers:
            vals = self.data[h]
            nums = [v for v in vals if _is_number(v)]
            kind = "num" if len(nums) > len(vals) * 0.6 else "cat"
            self.cols_box.insert(tk.END, f"{h}  [{kind}]")
            if kind == "num":
                numeric_cols.append(h)
        self.xcol["values"] = self.headers
        self.ycol["values"] = self.headers
        if numeric_cols:
            self.xcol.set(numeric_cols[0])
            if len(numeric_cols) > 1:
                self.ycol.set(numeric_cols[1])
            else:
                self.ycol.set(numeric_cols[0])
        self._compute_stats()
        self._plot()

    def _compute_stats(self):
        self.stats_text.delete("1.0", tk.END)
        lines = ["col            n     mean      std       min       max"]
        for h in self.headers:
            vals = [float(v) for v in self.data[h] if _is_number(v)]
            if not vals: continue
            arr = np.asarray(vals)
            lines.append(f"{h[:12]:12}  {len(arr):5d}  {arr.mean():9.4g}  {arr.std():9.4g}  {arr.min():9.4g}  {arr.max():9.4g}")
        self.stats_text.insert(tk.END, "\n".join(lines))

    def _load_sample(self):
        # Tiny inline iris-like sample so demo works without external files
        rows = [["sepal_len", "sepal_wid", "petal_len", "petal_wid", "species"]]
        random.seed(0)
        for sp_name, (mu_sl, mu_sw, mu_pl, mu_pw) in [
            ("setosa",      (5.0, 3.4, 1.5, 0.3)),
            ("versicolor",  (5.9, 2.8, 4.3, 1.3)),
            ("virginica",   (6.6, 3.0, 5.5, 2.0))]:
            for _ in range(40):
                rows.append([f"{mu_sl + random.gauss(0, 0.4):.2f}",
                             f"{mu_sw + random.gauss(0, 0.35):.2f}",
                             f"{mu_pl + random.gauss(0, 0.45):.2f}",
                             f"{mu_pw + random.gauss(0, 0.3):.2f}",
                             sp_name])
        self.headers = rows[0]
        self.data = {h: [] for h in self.headers}
        for r in rows[1:]:
            for i, h in enumerate(self.headers):
                self.data[h].append(r[i])
        self.dropzone.config(text="📂 Loaded sample: iris-like\n120 rows × 5 cols")
        self._after_load()

    def _plot(self):
        if not self.headers: return
        kind = self.plot_kind.get()
        self.fig.clear()
        self.ax = self.fig.add_subplot(111)
        style_axes(self.ax)
        xc = self.xcol.get(); yc = self.ycol.get()
        try:
            if kind == "auto":
                # pick by columns
                if xc == yc:
                    kind = "histogram"
                else:
                    kind = "scatter"
            if kind == "histogram":
                vals = [float(v) for v in self.data[xc] if _is_number(v)]
                self.ax.hist(vals, bins=30, color=T()["accent"], edgecolor=T()["bg"])
                self.ax.set_xlabel(xc); self.ax.set_ylabel("count")
            elif kind == "scatter":
                xs = np.array([float(v) for v in self.data[xc] if _is_number(v)])
                ys_raw = self.data[yc][:len(xs)] if len(self.data[yc]) >= len(xs) else self.data[yc]
                pairs = [(float(x), float(y)) for x, y in zip(self.data[xc], self.data[yc]) if _is_number(x) and _is_number(y)]
                if not pairs: raise ValueError("No numeric pairs to plot")
                xs = np.array([p[0] for p in pairs]); ys = np.array([p[1] for p in pairs])
                self.ax.scatter(xs, ys, c=T()["accent"], s=18, alpha=0.75, edgecolors="none")
                self.ax.set_xlabel(xc); self.ax.set_ylabel(yc)
                self._add_fit(xs, ys)
            elif kind == "line":
                pairs = [(float(x), float(y)) for x, y in zip(self.data[xc], self.data[yc]) if _is_number(x) and _is_number(y)]
                pairs.sort()
                xs = np.array([p[0] for p in pairs]); ys = np.array([p[1] for p in pairs])
                self.ax.plot(xs, ys, color=T()["accent"], lw=1.4)
                self.ax.set_xlabel(xc); self.ax.set_ylabel(yc)
            elif kind == "bar":
                vals = self.data[xc]
                counts = {}
                for v in vals: counts[v] = counts.get(v, 0) + 1
                items = sorted(counts.items(), key=lambda p: -p[1])[:20]
                self.ax.bar([k for k, _ in items], [v for _, v in items], color=T()["accent2"])
                self.ax.tick_params(axis="x", rotation=40)
            elif kind == "box":
                numeric_cols = [h for h in self.headers
                                if sum(1 for v in self.data[h] if _is_number(v)) > 5]
                arrs = [np.array([float(v) for v in self.data[h] if _is_number(v)]) for h in numeric_cols]
                self.ax.boxplot(arrs, tick_labels=numeric_cols, patch_artist=True,
                                boxprops=dict(facecolor=T()["accent"], alpha=0.6),
                                medianprops=dict(color=T()["err"]))
                self.ax.tick_params(axis="x", rotation=30)
            elif kind == "scatter-matrix":
                self.fig.clear()
                numeric_cols = [h for h in self.headers
                                if sum(1 for v in self.data[h] if _is_number(v)) > 5][:5]
                k = len(numeric_cols)
                if k < 2: raise ValueError("Need ≥ 2 numeric columns")
                for i, hi in enumerate(numeric_cols):
                    for j, hj in enumerate(numeric_cols):
                        ax = self.fig.add_subplot(k, k, i * k + j + 1)
                        ax.set_facecolor(T()["mpl_face"])
                        if i == j:
                            vals = [float(v) for v in self.data[hi] if _is_number(v)]
                            ax.hist(vals, bins=20, color=T()["accent"])
                        else:
                            pairs = [(float(x), float(y)) for x, y in zip(self.data[hj], self.data[hi]) if _is_number(x) and _is_number(y)]
                            xs = [p[0] for p in pairs]; ys = [p[1] for p in pairs]
                            ax.scatter(xs, ys, s=5, c=T()["accent2"], alpha=0.6)
                        if i == k-1: ax.set_xlabel(hj, color=T()["fg"], fontsize=7)
                        if j == 0: ax.set_ylabel(hi, color=T()["fg"], fontsize=7)
                        ax.tick_params(colors=T()["fg"], labelsize=6)
                self.fig.tight_layout()
                self.canvas.draw(); return
            elif kind == "correlation heatmap":
                numeric_cols = [h for h in self.headers
                                if sum(1 for v in self.data[h] if _is_number(v)) > 5]
                if len(numeric_cols) < 2: raise ValueError("Need ≥ 2 numeric columns")
                n_rows = min(len(self.data[h]) for h in numeric_cols)
                arr = np.array([[float(self.data[h][i]) if _is_number(self.data[h][i]) else np.nan
                                 for h in numeric_cols] for i in range(n_rows)])
                corr = np.corrcoef(arr.T)
                im = self.ax.imshow(corr, cmap="coolwarm", vmin=-1, vmax=1)
                self.ax.set_xticks(range(len(numeric_cols)), numeric_cols, rotation=40)
                self.ax.set_yticks(range(len(numeric_cols)), numeric_cols)
                for i in range(len(numeric_cols)):
                    for j in range(len(numeric_cols)):
                        self.ax.text(j, i, f"{corr[i,j]:.2f}", ha="center", va="center",
                                     color="white" if abs(corr[i,j]) > 0.5 else T()["bg"], fontsize=8)
                self.fig.colorbar(im, ax=self.ax)
            self.fig.tight_layout()
            self.canvas.draw()
        except Exception as ex:
            messagebox.showerror("Plot error", str(ex))

    def _add_fit(self, xs, ys):
        kind = self.reg_var.get()
        if kind == "none": return
        try:
            xs2 = np.linspace(xs.min(), xs.max(), 200)
            if kind == "linear":
                p = np.polyfit(xs, ys, 1); fit = np.polyval(p, xs2)
                eq = f"y = {p[0]:.4g}x + {p[1]:.4g}"
            elif kind == "polynomial-2":
                p = np.polyfit(xs, ys, 2); fit = np.polyval(p, xs2)
                eq = f"y = {p[0]:.4g}x² + {p[1]:.4g}x + {p[2]:.4g}"
            elif kind == "polynomial-3":
                p = np.polyfit(xs, ys, 3); fit = np.polyval(p, xs2)
                eq = f"y = {p[0]:.3g}x³ + {p[1]:.3g}x² + {p[2]:.3g}x + {p[3]:.3g}"
            elif kind == "exponential":
                mask = ys > 0
                p = np.polyfit(xs[mask], np.log(ys[mask]), 1)
                fit = np.exp(p[1]) * np.exp(p[0] * xs2)
                eq = f"y = {math.exp(p[1]):.4g}·exp({p[0]:.4g}·x)"
            elif kind == "logarithmic":
                mask = xs > 0
                p = np.polyfit(np.log(xs[mask]), ys[mask], 1)
                fit = p[0] * np.log(xs2[xs2 > 0]) + p[1]
                xs2 = xs2[xs2 > 0]
                eq = f"y = {p[0]:.4g}·ln(x) + {p[1]:.4g}"
            elif kind == "power":
                mask = (xs > 0) & (ys > 0)
                p = np.polyfit(np.log(xs[mask]), np.log(ys[mask]), 1)
                fit = np.exp(p[1]) * xs2[xs2 > 0] ** p[0]
                xs2 = xs2[xs2 > 0]
                eq = f"y = {math.exp(p[1]):.4g}·x^{p[0]:.4g}"
            else:
                return
            # R²
            try:
                pred = self._predict(kind, xs, ys)
                ss_res = np.sum((ys - pred) ** 2)
                ss_tot = np.sum((ys - ys.mean()) ** 2)
                r2 = 1 - ss_res / ss_tot if ss_tot else 0
                eq += f"   R² = {r2:.4f}"
            except Exception:
                pass
            self.ax.plot(xs2, fit, color=T()["err"], lw=2, label=eq)
            self.ax.legend(facecolor=T()["panel"], labelcolor=T()["fg"], fontsize=8)
        except Exception:
            pass

    def _predict(self, kind, xs, ys):
        if kind == "linear":
            p = np.polyfit(xs, ys, 1); return np.polyval(p, xs)
        if kind == "polynomial-2":
            p = np.polyfit(xs, ys, 2); return np.polyval(p, xs)
        if kind == "polynomial-3":
            p = np.polyfit(xs, ys, 3); return np.polyval(p, xs)
        if kind == "exponential":
            mask = ys > 0
            p = np.polyfit(xs[mask], np.log(ys[mask]), 1)
            return np.exp(p[1]) * np.exp(p[0] * xs)
        if kind == "logarithmic":
            mask = xs > 0
            p = np.polyfit(np.log(xs[mask]), ys[mask], 1)
            out = np.full_like(ys, np.nan, dtype=float)
            out[mask] = p[0] * np.log(xs[mask]) + p[1]
            return out
        if kind == "power":
            mask = (xs > 0) & (ys > 0)
            p = np.polyfit(np.log(xs[mask]), np.log(ys[mask]), 1)
            out = np.full_like(ys, np.nan, dtype=float)
            out[mask] = np.exp(p[1]) * xs[mask] ** p[0]
            return out
        return ys


def _is_number(s) -> bool:
    if not isinstance(s, str): return False
    s = s.strip()
    if not s: return False
    try:
        float(s); return True
    except ValueError:
        return False


# ---------------------------------------------------------------------------
# DEMOS TAB
# ---------------------------------------------------------------------------
class DemosTab(tk.Frame):
    def __init__(self, parent, engine: Engine, app):
        super().__init__(parent, bg=T()["bg"])
        self.engine = engine
        self.app = app
        self.current_demo = None
        self._anim = None
        self._after_id = None
        self._build()

    def _build(self):
        left = make_scroll_frame(self, width=280)

        tk.Label(left, text="Visualization Demos", bg=T()["panel"], fg=T()["accent"],
                 font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=8, pady=(8, 6))

        demos = [
            ("🌀  Mandelbrot Set", self.demo_mandelbrot),
            ("🎨  Julia Set", self.demo_julia),
            ("🦋  Lorenz Attractor", self.demo_lorenz),
            ("🎻  Fourier Series", self.demo_fourier),
            ("🌳  Fractal Tree", self.demo_tree),
            ("❄️  Koch Snowflake", self.demo_koch),
            ("🔺  Sierpinski Triangle", self.demo_sierpinski),
            ("🌸  Lissajous Curves", self.demo_lissajous),
            ("🪀  Double Pendulum", self.demo_double_pendulum),
            ("🌌  Game of Life", self.demo_life),
            ("🎯  Buffon's Needle (π)", self.demo_buffon),
            ("🎲  Monte Carlo π", self.demo_mcpi),
            ("🪐  N-body Orbits", self.demo_nbody),
            ("🌊  Wave Equation", self.demo_wave),
            ("🔢  Collatz Sequence", self.demo_collatz),
            ("🎢  Bifurcation (Logistic)", self.demo_bifurcation),
            ("🔄  Newton's Fractal", self.demo_newton),
        ]
        for label, fn in demos:
            b = tk.Button(left, text=label, command=fn, bg=T()["btn"], fg=T()["fg"],
                          activebackground=T()["btn_hover"], activeforeground=T()["fg"],
                          relief="flat", anchor="w", font=("Segoe UI", 9), padx=8)
            b.pack(fill="x", padx=6, pady=1, ipady=4)

        tk.Button(left, text="⏹  Stop animations", command=self._stop_anim, bg=T()["btn_fn"],
                  fg=T()["btn_fn_fg"], relief="flat", font=("Segoe UI", 10, "bold")).pack(fill="x", padx=8, pady=(20,6), ipady=8)

        right = tk.Frame(self, bg=T()["bg"])
        right.pack(side="right", fill="both", expand=True, padx=(4, 10), pady=10)
        self.right = right

        self.controls = tk.Frame(right, bg=T()["panel"], height=70)
        self.controls.pack(fill="x", pady=(0,6))
        self.controls.pack_propagate(False)
        self.info_label = tk.Label(self.controls, text="Pick a demo →", bg=T()["panel"], fg=T()["fg"],
                                    font=("Segoe UI", 10), justify="left", anchor="w")
        self.info_label.pack(fill="both", expand=True, padx=8, pady=4)

        self.fig = themed_figure()
        self.ax = self.fig.add_subplot(111)
        style_axes(self.ax)
        self.canvas = FigureCanvasTkAgg(self.fig, master=right)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

    # ---------------- shared helpers ----------------
    def _stop_anim(self):
        if self._anim is not None:
            try: self._anim.event_source.stop()
            except Exception: pass
            self._anim = None
        if self._after_id is not None:
            try: self.after_cancel(self._after_id)
            except Exception: pass
            self._after_id = None

    def _reset_axes(self, projection=None):
        self._stop_anim()
        self.fig.clear()
        for w in self.controls.winfo_children():
            if w is not self.info_label: w.destroy()
        if projection:
            self.ax = self.fig.add_subplot(111, projection=projection)
        else:
            self.ax = self.fig.add_subplot(111)
        self.ax.set_facecolor(T()["mpl_face"])
        style_axes(self.ax)

    def _set_info(self, text):
        self.info_label.config(text=text)

    # ---------------- demos ----------------
    def demo_mandelbrot(self, center=(-0.5, 0.0), span=3.0, max_iter=200):
        self._reset_axes()
        self._set_info("Mandelbrot set — click to zoom 4x at point. Right-click to zoom out.")
        self._mb_state = {"center": center, "span": span, "iter": max_iter}

        def draw():
            cx, cy = self._mb_state["center"]; sp_ = self._mb_state["span"]
            mi = self._mb_state["iter"]
            res = 500
            x = np.linspace(cx - sp_/2, cx + sp_/2, res)
            y = np.linspace(cy - sp_/2, cy + sp_/2, res)
            X, Y = np.meshgrid(x, y)
            C = X + 1j * Y
            Z = np.zeros_like(C); div = np.full(C.shape, mi, dtype=float)
            for i in range(mi):
                mask = (np.abs(Z) <= 2)
                Z[mask] = Z[mask] * Z[mask] + C[mask]
                newly = mask & (np.abs(Z) > 2)
                div[newly] = i + 1 - np.log2(np.log2(np.abs(Z[newly]) + 1e-9) + 1e-9)
            self.ax.clear(); style_axes(self.ax)
            self.ax.imshow(div, extent=[x.min(), x.max(), y.min(), y.max()],
                           origin="lower", cmap="twilight_shifted")
            self.ax.set_title("Mandelbrot", color=T()["fg"])
            self.canvas.draw()

        def on_click(event):
            if event.inaxes != self.ax or event.xdata is None: return
            if event.button == 1:
                self._mb_state["center"] = (event.xdata, event.ydata)
                self._mb_state["span"] *= 0.25
                self._mb_state["iter"] = int(self._mb_state["iter"] * 1.15)
            elif event.button == 3:
                self._mb_state["span"] *= 4.0
                self._mb_state["iter"] = max(80, int(self._mb_state["iter"] / 1.15))
            draw()

        self.canvas.mpl_connect("button_press_event", on_click)
        draw()

    def demo_julia(self):
        self._reset_axes()
        self._set_info("Julia set — drag the c slider to morph; the famous fractal family.")
        sl1 = ttk.Scale(self.controls, from_=-1.5, to=1.5, orient="horizontal", length=300)
        sl2 = ttk.Scale(self.controls, from_=-1.5, to=1.5, orient="horizontal", length=300)
        sl1.set(-0.7); sl2.set(0.27)
        tk.Label(self.controls, text="Re(c):", bg=T()["panel"], fg=T()["fg"]).pack(side="left", padx=(8,2))
        sl1.pack(side="left")
        tk.Label(self.controls, text="Im(c):", bg=T()["panel"], fg=T()["fg"]).pack(side="left", padx=(8,2))
        sl2.pack(side="left")

        def draw():
            cr = sl1.get(); ci = sl2.get()
            c = complex(cr, ci)
            res = 480
            x = np.linspace(-1.5, 1.5, res); y = np.linspace(-1.5, 1.5, res)
            X, Y = np.meshgrid(x, y)
            Z = X + 1j * Y; div = np.zeros(Z.shape)
            for i in range(150):
                mask = np.abs(Z) <= 2
                Z[mask] = Z[mask] ** 2 + c
                div[mask] = i
            self.ax.clear(); style_axes(self.ax)
            self.ax.imshow(div, extent=[-1.5,1.5,-1.5,1.5], origin="lower", cmap="magma")
            self.ax.set_title(f"Julia set c = {cr:.3f} + {ci:.3f}i", color=T()["fg"])
            self.canvas.draw()
        sl1.config(command=lambda v: draw())
        sl2.config(command=lambda v: draw())
        draw()

    def demo_lorenz(self):
        self._reset_axes(projection="3d")
        self._set_info("Lorenz attractor — the original chaos butterfly (σ=10, ρ=28, β=8/3).")
        sigma, rho, beta = 10.0, 28.0, 8/3
        dt = 0.005; N = 8000
        xs, ys, zs = [0.1], [0.0], [0.0]
        for _ in range(N):
            x, y, z = xs[-1], ys[-1], zs[-1]
            xs.append(x + sigma*(y-x)*dt)
            ys.append(y + (x*(rho-z)-y)*dt)
            zs.append(z + (x*y - beta*z)*dt)
        line, = self.ax.plot([], [], [], color=T()["accent"], lw=0.8)
        pt, = self.ax.plot([], [], [], "o", color=T()["err"])
        self.ax.set_xlim(-25, 25); self.ax.set_ylim(-30, 30); self.ax.set_zlim(0, 55)
        self.ax.set_facecolor(T()["mpl_face"])
        def init(): line.set_data([], []); line.set_3d_properties([]); return line, pt
        def upd(i):
            j = min(i*20, len(xs))
            line.set_data(xs[:j], ys[:j]); line.set_3d_properties(zs[:j])
            pt.set_data([xs[j-1]], [ys[j-1]]); pt.set_3d_properties([zs[j-1]])
            return line, pt
        self._anim = animation.FuncAnimation(self.fig, upd, frames=400, init_func=init,
                                              interval=30, blit=False, repeat=True)
        self.canvas.draw()

    def demo_fourier(self):
        self._reset_axes()
        self._set_info("Fourier series — slide N to add harmonics. Watch the square wave emerge.")
        sl = ttk.Scale(self.controls, from_=1, to=60, orient="horizontal", length=350)
        sl.set(5)
        kind_var = tk.StringVar(value="square")
        tk.Label(self.controls, text="N:", bg=T()["panel"], fg=T()["fg"]).pack(side="left", padx=(8,2))
        sl.pack(side="left", padx=4)
        ttk.Combobox(self.controls, textvariable=kind_var, state="readonly", width=10,
                     values=["square", "triangle", "sawtooth"]).pack(side="left", padx=8)
        def draw(*_):
            N = int(sl.get())
            xs = np.linspace(-2*math.pi, 2*math.pi, 2000)
            y = np.zeros_like(xs); target = np.zeros_like(xs)
            kind = kind_var.get()
            if kind == "square":
                target = np.sign(np.sin(xs))
                for k in range(1, N+1):
                    if k % 2: y += (4/math.pi) * np.sin(k*xs) / k
            elif kind == "triangle":
                target = (2/math.pi) * np.arcsin(np.sin(xs))
                for k in range(1, N+1):
                    if k % 2: y += (8/math.pi**2) * ((-1)**((k-1)//2)) * np.sin(k*xs) / (k*k)
            else:  # sawtooth, period 2π, amplitude 1
                u = xs / (2 * math.pi)
                target = 2 * (u - np.floor(u + 0.5))
                for k in range(1, N+1):
                    y += (2/math.pi) * ((-1)**(k+1)) * np.sin(k*xs) / k
            self.ax.clear(); style_axes(self.ax)
            self.ax.plot(xs, target, color=T()["muted"], lw=1, alpha=0.6, label="target")
            self.ax.plot(xs, y, color=T()["accent"], lw=1.8, label=f"N={N}")
            self.ax.set_title(f"Fourier {kind} wave — {N} harmonics", color=T()["fg"])
            self.ax.legend(facecolor=T()["panel"], labelcolor=T()["fg"], fontsize=9)
            self.canvas.draw()
        sl.config(command=draw); kind_var.trace_add("write", draw)
        draw()

    def demo_tree(self):
        self._reset_axes()
        self._set_info("Recursive fractal tree — drag sliders to change angle & depth.")
        ang = ttk.Scale(self.controls, from_=10, to=80, orient="horizontal", length=200)
        ang.set(28)
        dep = ttk.Scale(self.controls, from_=4, to=12, orient="horizontal", length=200)
        dep.set(10)
        tk.Label(self.controls, text="angle:", bg=T()["panel"], fg=T()["fg"]).pack(side="left", padx=(8,2))
        ang.pack(side="left")
        tk.Label(self.controls, text="depth:", bg=T()["panel"], fg=T()["fg"]).pack(side="left", padx=(8,2))
        dep.pack(side="left")

        def draw(*_):
            self.ax.clear(); style_axes(self.ax)
            angle = math.radians(ang.get())
            depth = int(dep.get())
            segs = []
            def rec(x, y, a, length, d):
                if d == 0: return
                x2 = x + length * math.cos(a); y2 = y + length * math.sin(a)
                segs.append(((x, y), (x2, y2), d))
                rec(x2, y2, a - angle, length * 0.72, d - 1)
                rec(x2, y2, a + angle, length * 0.72, d - 1)
            rec(0, 0, math.pi/2, 1.0, depth)
            from matplotlib.collections import LineCollection
            lcs = []
            for (p1, p2, d) in segs:
                lcs.append([p1, p2])
            colors_arr = [cm.YlGn(0.3 + 0.6 * d / depth) for (_, __, d) in segs]
            lc = LineCollection(lcs, colors=colors_arr, linewidths=[0.5 + 0.4*d for (_,_,d) in segs])
            self.ax.add_collection(lc)
            self.ax.set_xlim(-2, 2); self.ax.set_ylim(0, 3.5)
            self.ax.set_aspect("equal"); self.ax.set_axis_off()
            self.canvas.draw()
        ang.config(command=draw); dep.config(command=draw)
        draw()

    def demo_koch(self):
        self._reset_axes()
        self._set_info("Koch snowflake — increase order to see infinite perimeter emerge.")
        sl = ttk.Scale(self.controls, from_=0, to=6, orient="horizontal", length=300)
        sl.set(4)
        tk.Label(self.controls, text="order:", bg=T()["panel"], fg=T()["fg"]).pack(side="left", padx=(8,2))
        sl.pack(side="left")
        def koch(p1, p2, depth):
            if depth == 0: return [p1, p2]
            p1 = np.array(p1); p2 = np.array(p2)
            s = p1 + (p2 - p1) / 3
            t = p1 + 2 * (p2 - p1) / 3
            ang = math.pi / 3
            R = np.array([[math.cos(ang), -math.sin(ang)], [math.sin(ang), math.cos(ang)]])
            peak = s + R @ (t - s)
            return (koch(p1, s, depth-1)[:-1] + koch(s, peak, depth-1)[:-1] +
                    koch(peak, t, depth-1)[:-1] + koch(t, p2, depth-1))
        def draw(*_):
            self.ax.clear(); style_axes(self.ax)
            d = int(sl.get())
            tri = [(-1,-1/math.sqrt(3)), (1,-1/math.sqrt(3)), (0,2/math.sqrt(3))]
            pts = (koch(tri[0], tri[1], d)[:-1] + koch(tri[1], tri[2], d)[:-1] +
                   koch(tri[2], tri[0], d))
            xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
            self.ax.fill(xs, ys, color=T()["accent"], alpha=0.4)
            self.ax.plot(xs, ys, color=T()["accent2"], lw=0.8)
            self.ax.set_aspect("equal"); self.ax.set_axis_off()
            self.canvas.draw()
        sl.config(command=draw); draw()

    def demo_sierpinski(self):
        self._reset_axes()
        self._set_info("Chaos game — pick N vertices and points. Random midpoints form a fractal.")
        vtx_var = tk.IntVar(value=3)
        n_var = tk.IntVar(value=30000)
        tk.Label(self.controls, text="Vertices:", bg=T()["panel"], fg=T()["fg"]).pack(side="left", padx=(8,2))
        vsl = ttk.Scale(self.controls, from_=3, to=8, orient="horizontal", length=140); vsl.set(3)
        vsl.pack(side="left")
        v_lbl = tk.Label(self.controls, text="3", bg=T()["panel"], fg=T()["accent"],
                          font=("Cascadia Code", 10, "bold"), width=3); v_lbl.pack(side="left", padx=2)
        tk.Label(self.controls, text="Points:", bg=T()["panel"], fg=T()["fg"]).pack(side="left", padx=(8,2))
        psl = ttk.Scale(self.controls, from_=1000, to=80000, orient="horizontal", length=180); psl.set(30000)
        psl.pack(side="left")
        p_lbl = tk.Label(self.controls, text="30000", bg=T()["panel"], fg=T()["accent"],
                          font=("Cascadia Code", 10, "bold"), width=6); p_lbl.pack(side="left", padx=2)
        tk.Button(self.controls, text="🎲 Redraw", bg=T()["btn"], fg=T()["fg"],
                  relief="flat", font=("Segoe UI", 9),
                  command=lambda: draw()).pack(side="left", padx=4)

        def draw(*_):
            k = int(vsl.get()); N = int(psl.get())
            v_lbl.config(text=str(k)); p_lbl.config(text=str(N))
            angles = np.linspace(math.pi/2, math.pi/2 + 2*math.pi, k, endpoint=False)
            verts = np.column_stack([np.cos(angles), np.sin(angles)])
            # Restriction ratio: classic 1/2 for k=3, otherwise 1 - 1/(2*cos(pi/k))-ish
            # Use ratio = 1 / (1 + 2*sin(pi/(2*k)) / sin(pi/k)) ≈ nice gasket
            r = 0.5 if k == 3 else 1.0 - 1.0 / (2 * math.cos(math.pi / k))
            r = max(0.3, min(r, 0.65))
            pts = np.zeros((N, 2)); p = np.zeros(2)
            choices = np.random.randint(0, k, size=N)
            for i in range(N):
                p = p + (verts[choices[i]] - p) * r
                pts[i] = p
            self.ax.clear(); style_axes(self.ax)
            # Color by angle for visual appeal
            ths = np.arctan2(pts[:,1], pts[:,0])
            self.ax.scatter(pts[:, 0], pts[:, 1], s=0.4, c=ths, cmap="twilight", alpha=0.8)
            self.ax.scatter(verts[:,0], verts[:,1], s=80, c=T()["err"], marker="o",
                            edgecolors=T()["fg"], linewidths=1.5, zorder=5)
            self.ax.set_aspect("equal"); self.ax.set_axis_off()
            self.ax.set_title(f"Chaos game: {k}-gon, ratio={r:.3f}, N={N}", color=T()["fg"])
            self.canvas.draw()
        vsl.config(command=draw); psl.config(command=draw)
        draw()

    def demo_lissajous(self):
        self._reset_axes()
        self._set_info("Lissajous figures — set frequency ratio a:b and phase.")
        a = ttk.Scale(self.controls, from_=1, to=9, orient="horizontal", length=180); a.set(3)
        b = ttk.Scale(self.controls, from_=1, to=9, orient="horizontal", length=180); b.set(2)
        ph = ttk.Scale(self.controls, from_=0, to=math.pi*2, orient="horizontal", length=180); ph.set(math.pi/2)
        for lbl, w in [("a:", a), ("b:", b), ("phase:", ph)]:
            tk.Label(self.controls, text=lbl, bg=T()["panel"], fg=T()["fg"]).pack(side="left", padx=(8,2))
            w.pack(side="left")
        def draw(*_):
            ts = np.linspace(0, 2*math.pi, 2000)
            xs = np.sin(int(a.get())*ts + ph.get()); ys = np.sin(int(b.get())*ts)
            self.ax.clear(); style_axes(self.ax)
            self.ax.plot(xs, ys, color=T()["accent"], lw=1.5)
            self.ax.set_aspect("equal"); self.ax.set_axis_off()
            self.canvas.draw()
        for w in (a, b, ph): w.config(command=draw)
        draw()

    def demo_double_pendulum(self):
        self._reset_axes()
        self._set_info("Double pendulum — chaos in action. Two start nearly identical; watch them diverge.")
        g = 9.81; L1 = L2 = 1.0; m1 = m2 = 1.0
        def deriv(state):
            t1, w1, t2, w2 = state
            dt = t2 - t1
            den1 = (m1+m2)*L1 - m2*L1*math.cos(dt)*math.cos(dt)
            den2 = (L2/L1) * den1
            dw1 = (m2*L1*w1*w1*math.sin(dt)*math.cos(dt) +
                   m2*g*math.sin(t2)*math.cos(dt) +
                   m2*L2*w2*w2*math.sin(dt) -
                   (m1+m2)*g*math.sin(t1)) / den1
            dw2 = (-m2*L2*w2*w2*math.sin(dt)*math.cos(dt) +
                   (m1+m2)*g*math.sin(t1)*math.cos(dt) -
                   (m1+m2)*L1*w1*w1*math.sin(dt) -
                   (m1+m2)*g*math.sin(t2)) / den2
            return np.array([w1, dw1, w2, dw2])
        def step(s, dt):
            k1 = deriv(s); k2 = deriv(s + dt/2 * k1)
            k3 = deriv(s + dt/2 * k2); k4 = deriv(s + dt * k3)
            return s + dt/6 * (k1 + 2*k2 + 2*k3 + k4)
        s_a = np.array([math.pi/2+0.001, 0, math.pi/2, 0])
        s_b = np.array([math.pi/2, 0, math.pi/2, 0])
        trail_a, trail_b = [], []
        line_a, = self.ax.plot([], [], "-", lw=1.6, color=T()["accent"])
        line_b, = self.ax.plot([], [], "-", lw=1.6, color=T()["err"])
        tr_a, = self.ax.plot([], [], "-", lw=0.7, alpha=0.4, color=T()["accent"])
        tr_b, = self.ax.plot([], [], "-", lw=0.7, alpha=0.4, color=T()["err"])
        self.ax.set_xlim(-2.2, 2.2); self.ax.set_ylim(-2.2, 2.2)
        self.ax.set_aspect("equal"); self.ax.set_facecolor(T()["mpl_face"])
        def upd(_):
            nonlocal s_a, s_b
            for _ in range(4): s_a = step(s_a, 0.01)
            for _ in range(4): s_b = step(s_b, 0.01)
            for s, line, tr, trail in [(s_a, line_a, tr_a, trail_a), (s_b, line_b, tr_b, trail_b)]:
                x1 = L1*math.sin(s[0]); y1 = -L1*math.cos(s[0])
                x2 = x1 + L2*math.sin(s[2]); y2 = y1 - L2*math.cos(s[2])
                line.set_data([0, x1, x2], [0, y1, y2])
                trail.append((x2, y2))
                if len(trail) > 600: trail.pop(0)
                tr.set_data([p[0] for p in trail], [p[1] for p in trail])
            return line_a, line_b, tr_a, tr_b
        self._anim = animation.FuncAnimation(self.fig, upd, interval=20, blit=False, cache_frame_data=False)
        self.canvas.draw()

    def demo_life(self):
        self._reset_axes()
        self._set_info("Conway's Game of Life — click cells, then play. Preset = R-pentomino.")
        N = 80; grid = np.zeros((N, N), dtype=int)
        # R-pentomino preset
        cx, cy = N//2, N//2
        for dx, dy in [(0,0),(1,0),(-1,0),(0,1),(1,-1)]:
            grid[cy+dy, cx+dx] = 1
        img = self.ax.imshow(grid, cmap="Greys_r", vmin=0, vmax=1)
        self.ax.set_axis_off()
        running = {"on": True}
        def step():
            nonlocal grid
            n = sum(np.roll(np.roll(grid, i, 0), j, 1) for i in (-1,0,1) for j in (-1,0,1)) - grid
            grid = ((n == 3) | ((grid == 1) & (n == 2))).astype(int)
            img.set_data(grid); self.canvas.draw_idle()
        def loop():
            if running["on"]: step()
            self._after_id = self.after(80, loop)
        def toggle(): running["on"] = not running["on"]
        tk.Button(self.controls, text="⏯  Pause/Play", command=toggle, bg=T()["btn"], fg=T()["fg"],
                  relief="flat").pack(side="left", padx=4)
        def randomize():
            nonlocal grid
            grid = (np.random.rand(N, N) < 0.18).astype(int); img.set_data(grid); self.canvas.draw_idle()
        tk.Button(self.controls, text="🎲  Randomize", command=randomize, bg=T()["btn"], fg=T()["fg"],
                  relief="flat").pack(side="left", padx=4)
        def on_click(event):
            if event.inaxes != self.ax or event.xdata is None: return
            x, y = int(event.xdata), int(event.ydata)
            if 0 <= x < N and 0 <= y < N:
                grid[y, x] = 1 - grid[y, x]; img.set_data(grid); self.canvas.draw_idle()
        self.canvas.mpl_connect("button_press_event", on_click)
        loop()
        self.canvas.draw()

    def demo_buffon(self):
        self._reset_axes()
        self._set_info("Buffon's needle — needles dropped on a striped floor; π = (2L·N)/(d·hits).")
        sl = ttk.Scale(self.controls, from_=50, to=3000, orient="horizontal", length=240)
        sl.set(500)
        tk.Label(self.controls, text="N:", bg=T()["panel"], fg=T()["fg"]).pack(side="left", padx=(8,2))
        sl.pack(side="left")
        n_lbl = tk.Label(self.controls, text="500", bg=T()["panel"], fg=T()["accent"],
                         font=("Cascadia Code", 10, "bold"), width=5); n_lbl.pack(side="left", padx=2)
        tk.Button(self.controls, text="🎲 New drop", bg=T()["btn"], fg=T()["fg"],
                  relief="flat", command=lambda: draw()).pack(side="left", padx=4)

        # Left: needles on floor.  Right: running π estimate.
        self.fig.clear()
        ax1 = self.fig.add_subplot(121)
        ax2 = self.fig.add_subplot(122)
        for ax in (ax1, ax2):
            ax.set_facecolor(T()["mpl_face"]); style_axes(ax)
        self.ax = ax1

        def draw(*_):
            N = int(sl.get()); n_lbl.config(text=str(N))
            d_spacing = 1.0; L = 0.8
            rng = np.random.default_rng()
            cy = rng.uniform(-3, 3, size=N)
            cx = rng.uniform(-4, 4, size=N)
            ths = rng.uniform(0, math.pi, size=N)
            x1 = cx - (L/2) * np.cos(ths); x2 = cx + (L/2) * np.cos(ths)
            y1 = cy - (L/2) * np.sin(ths); y2 = cy + (L/2) * np.sin(ths)
            hits = np.floor(y1) != np.floor(y2)
            running = np.cumsum(hits).clip(min=1)
            pi_est_running = (2 * L * np.arange(1, N+1)) / (d_spacing * running)
            pi_est = pi_est_running[-1]
            # Left axis: floor with needles
            ax1.clear(); ax1.set_facecolor(T()["mpl_face"]); style_axes(ax1)
            for yy in range(-3, 4):
                ax1.axhline(yy, color=T()["muted"], lw=1, alpha=0.45)
            from matplotlib.collections import LineCollection
            segs_hit = [[(x1[i], y1[i]), (x2[i], y2[i])] for i in np.where(hits)[0]]
            segs_miss = [[(x1[i], y1[i]), (x2[i], y2[i])] for i in np.where(~hits)[0]]
            ax1.add_collection(LineCollection(segs_miss, colors=T()["accent"], linewidths=0.6, alpha=0.55))
            ax1.add_collection(LineCollection(segs_hit, colors=T()["err"], linewidths=0.9, alpha=0.85))
            ax1.set_xlim(-4.2, 4.2); ax1.set_ylim(-3.5, 3.5)
            ax1.set_aspect("equal"); ax1.set_axis_off()
            ax1.set_title(f"{N} needles, {hits.sum()} crossings (red)", color=T()["fg"])
            # Right axis: convergence
            ax2.clear(); ax2.set_facecolor(T()["mpl_face"]); style_axes(ax2)
            ax2.plot(pi_est_running, color=T()["accent"], lw=1)
            ax2.axhline(math.pi, color=T()["err"], lw=1, ls="--", label="π")
            ax2.set_ylim(2, 5)
            ax2.set_xlabel("needles", color=T()["fg"]); ax2.set_ylabel("estimate", color=T()["fg"])
            ax2.set_title(f"π ≈ {pi_est:.5f}", color=T()["fg"])
            ax2.legend(facecolor=T()["panel"], labelcolor=T()["fg"])
            self.fig.tight_layout()
            self.canvas.draw()
        sl.config(command=draw); draw()

    def demo_mcpi(self):
        self._reset_axes()
        self._set_info("Monte Carlo π — random points; π ≈ 4 · (inside circle) / (total points).")
        sl = ttk.Scale(self.controls, from_=200, to=30000, orient="horizontal", length=260)
        sl.set(4000)
        tk.Label(self.controls, text="N points:", bg=T()["panel"], fg=T()["fg"]).pack(side="left", padx=(8,2))
        sl.pack(side="left")
        n_lbl = tk.Label(self.controls, text="4000", bg=T()["panel"], fg=T()["accent"],
                         font=("Cascadia Code", 10, "bold"), width=6); n_lbl.pack(side="left", padx=2)
        tk.Button(self.controls, text="🎲 Redraw", bg=T()["btn"], fg=T()["fg"],
                  relief="flat", command=lambda: draw()).pack(side="left", padx=4)

        self.fig.clear()
        ax1 = self.fig.add_subplot(121)
        ax2 = self.fig.add_subplot(122)
        for ax in (ax1, ax2):
            ax.set_facecolor(T()["mpl_face"]); style_axes(ax)
        self.ax = ax1

        def draw(*_):
            N = int(sl.get()); n_lbl.config(text=str(N))
            x = np.random.rand(N) * 2 - 1
            y = np.random.rand(N) * 2 - 1
            inside = x*x + y*y <= 1
            running_est = 4 * np.cumsum(inside) / np.arange(1, N+1)
            pi_est = running_est[-1]
            ax1.clear(); ax1.set_facecolor(T()["mpl_face"]); style_axes(ax1)
            ax1.scatter(x[inside], y[inside], s=4, c=T()["accent"], alpha=0.7, edgecolors="none")
            ax1.scatter(x[~inside], y[~inside], s=4, c=T()["err"], alpha=0.7, edgecolors="none")
            th = np.linspace(0, 2*math.pi, 200)
            ax1.plot(np.cos(th), np.sin(th), color=T()["fg"], lw=1.5)
            ax1.set_aspect("equal"); ax1.set_xlim(-1.05, 1.05); ax1.set_ylim(-1.05, 1.05)
            ax1.set_title(f"N={N}  |  inside={inside.sum()}", color=T()["fg"])
            ax2.clear(); ax2.set_facecolor(T()["mpl_face"]); style_axes(ax2)
            ax2.plot(running_est, color=T()["accent"], lw=1)
            ax2.axhline(math.pi, color=T()["err"], lw=1, ls="--", label="π")
            ax2.set_xlabel("samples", color=T()["fg"]); ax2.set_ylabel("estimate", color=T()["fg"])
            ax2.set_ylim(2.5, 3.7)
            ax2.set_title(f"π ≈ {pi_est:.5f}", color=T()["fg"])
            ax2.legend(facecolor=T()["panel"], labelcolor=T()["fg"])
            self.fig.tight_layout()
            self.canvas.draw()
        sl.config(command=draw); draw()

    def demo_nbody(self):
        self._reset_axes()
        self._set_info("3-body sandbox — three masses + gravity. Beautiful, often chaotic.")
        G = 1.0
        m = np.array([1.0, 1.0, 1.0])
        pos = np.array([[-1.0, 0.0], [1.0, 0.0], [0.0, 1.0]])
        vel = np.array([[0.3, -0.3], [-0.3, -0.3], [0.0, 0.5]]) * 0.5
        trails = [[] for _ in range(3)]
        lines = [self.ax.plot([], [], "-", lw=0.6, alpha=0.6)[0] for _ in range(3)]
        dots = [self.ax.plot([], [], "o", ms=8)[0] for _ in range(3)]
        for i, c in enumerate([T()["accent"], T()["accent2"], T()["err"]]):
            lines[i].set_color(c); dots[i].set_color(c)
        self.ax.set_xlim(-3, 3); self.ax.set_ylim(-3, 3)
        self.ax.set_aspect("equal"); self.ax.set_facecolor(T()["mpl_face"])
        def upd(_):
            nonlocal pos, vel
            dt = 0.01
            for _ in range(3):
                acc = np.zeros_like(pos)
                for i in range(3):
                    for j in range(3):
                        if i == j: continue
                        r = pos[j] - pos[i]
                        d2 = r @ r + 0.05
                        acc[i] += G * m[j] * r / d2**1.5
                vel += acc * dt; pos += vel * dt
            for i in range(3):
                trails[i].append(pos[i].copy())
                if len(trails[i]) > 500: trails[i].pop(0)
                arr = np.array(trails[i])
                lines[i].set_data(arr[:,0], arr[:,1])
                dots[i].set_data([pos[i,0]], [pos[i,1]])
            return *lines, *dots
        self._anim = animation.FuncAnimation(self.fig, upd, interval=20, blit=False, cache_frame_data=False)
        self.canvas.draw()

    def demo_wave(self):
        self._reset_axes()
        self._set_info("2D wave equation — drop a ripple in the middle and watch it propagate.")
        N = 80; c = 1.0; dt = 0.04; dx = 0.1
        u = np.zeros((N, N)); u_prev = np.zeros((N, N))
        u[N//2-3:N//2+3, N//2-3:N//2+3] = 1.0
        img = self.ax.imshow(u, cmap="seismic", vmin=-1, vmax=1)
        self.ax.set_axis_off()
        def upd(_):
            nonlocal u, u_prev
            lap = (np.roll(u, 1, 0) + np.roll(u, -1, 0) + np.roll(u, 1, 1) + np.roll(u, -1, 1) - 4*u) / dx**2
            u_new = 2*u - u_prev + (c*dt)**2 * lap
            u_new[0, :] = u_new[-1, :] = u_new[:, 0] = u_new[:, -1] = 0  # fixed boundary
            u_new *= 0.999
            u_prev = u; u = u_new
            img.set_data(u)
            return img,
        self._anim = animation.FuncAnimation(self.fig, upd, interval=25, blit=False, cache_frame_data=False)
        self.canvas.draw()

    def demo_collatz(self):
        self._reset_axes()
        self._set_info("Collatz — pick a starting number (use arrows or type) and trace its journey to 1.")
        tk.Label(self.controls, text="Start n:", bg=T()["panel"], fg=T()["fg"],
                 font=("Segoe UI", 10)).pack(side="left", padx=(8,2))
        entry = ttk.Spinbox(self.controls, from_=1, to=10**9, increment=1, width=12,
                             font=("Cascadia Code", 11))
        entry.set("27")
        entry.pack(side="left", padx=(0,4))
        for n_preset in ("6", "27", "97", "703", "871", "6171", "77031"):
            tk.Button(self.controls, text=n_preset, width=5, bg=T()["btn"], fg=T()["fg"],
                      activebackground=T()["btn_hover"], relief="flat", font=("Segoe UI", 9),
                      command=lambda v=n_preset: (entry.set(v), draw())).pack(side="left", padx=1)
        def draw():
            try: n = int(float(entry.get()))
            except ValueError: return
            seq = [n]
            while seq[-1] != 1 and len(seq) < 2000:
                v = seq[-1]; seq.append(v // 2 if v % 2 == 0 else 3*v + 1)
            self.ax.clear(); style_axes(self.ax)
            self.ax.plot(seq, color=T()["accent"], lw=1.3, marker="o", ms=3)
            self.ax.set_title(f"n={n}, length={len(seq)}, max={max(seq)}", color=T()["fg"])
            self.ax.set_xlabel("step"); self.ax.set_ylabel("value")
            self.canvas.draw()
        tk.Button(self.controls, text="Go", command=draw, bg=T()["btn_op"], fg=T()["btn_op_fg"], relief="flat").pack(side="left", padx=4)
        draw()

    def demo_bifurcation(self):
        self._reset_axes()
        self._set_info("Logistic map bifurcation — period-doubling route to chaos. Click to zoom in.")
        self._bif = {"rmin": 2.5, "rmax": 4.0}
        def draw():
            rmin, rmax = self._bif["rmin"], self._bif["rmax"]
            R = 1200
            rs = np.linspace(rmin, rmax, R)
            xs = np.full(R, 0.5)
            warmup = 400; collect = 200
            pts_r = []; pts_x = []
            for _ in range(warmup):
                xs = rs * xs * (1 - xs)
            for _ in range(collect):
                xs = rs * xs * (1 - xs)
                pts_r.append(rs.copy()); pts_x.append(xs.copy())
            pts_r = np.concatenate(pts_r); pts_x = np.concatenate(pts_x)
            self.ax.clear(); style_axes(self.ax)
            self.ax.scatter(pts_r, pts_x, s=0.1, c=T()["accent"], alpha=0.5)
            self.ax.set_xlabel("r"); self.ax.set_ylabel("x_∞")
            self.ax.set_title("Logistic map", color=T()["fg"])
            self.canvas.draw()
        def on_click(event):
            if event.xdata is None or event.button != 1: return
            r = event.xdata
            span = (self._bif["rmax"] - self._bif["rmin"]) * 0.3
            self._bif["rmin"] = max(0, r - span/2)
            self._bif["rmax"] = min(4, r + span/2)
            draw()
        self.canvas.mpl_connect("button_press_event", on_click)
        draw()

    def demo_newton(self):
        self._reset_axes()
        self._set_info("Newton's fractal — pick a polynomial; each pixel colored by which root it converges to.")
        # Polynomial choices: name -> (f(z), f'(z))  — written as lambdas
        polys = {
            "z³ − 1":      (lambda z: z**3 - 1,             lambda z: 3*z**2),
            "z⁴ − 1":      (lambda z: z**4 - 1,             lambda z: 4*z**3),
            "z⁵ − 1":      (lambda z: z**5 - 1,             lambda z: 5*z**4),
            "z⁶ − 1":      (lambda z: z**6 - 1,             lambda z: 6*z**5),
            "z³ − z":      (lambda z: z**3 - z,             lambda z: 3*z**2 - 1),
            "z⁴ − z":      (lambda z: z**4 - z,             lambda z: 4*z**3 - 1),
            "z⁵ − z²+1":   (lambda z: z**5 - z**2 + 1,      lambda z: 5*z**4 - 2*z),
            "z³ + z − 1":  (lambda z: z**3 + z - 1,         lambda z: 3*z**2 + 1),
        }
        poly_var = tk.StringVar(value="z³ − 1")
        tk.Label(self.controls, text="f(z) =", bg=T()["panel"], fg=T()["fg"]).pack(side="left", padx=(8,2))
        cb = ttk.Combobox(self.controls, state="readonly", textvariable=poly_var,
                          width=14, values=list(polys.keys()))
        cb.pack(side="left", padx=2)
        cb.bind("<<ComboboxSelected>>", lambda e: draw())
        tk.Label(self.controls, text="Iters:", bg=T()["panel"], fg=T()["fg"]).pack(side="left", padx=(8,2))
        it_sl = ttk.Scale(self.controls, from_=15, to=80, orient="horizontal", length=140); it_sl.set(40)
        it_sl.pack(side="left")
        tk.Button(self.controls, text="Redraw", bg=T()["btn"], fg=T()["fg"], relief="flat",
                  command=lambda: draw()).pack(side="left", padx=4)

        def find_roots(f):
            # numerically find roots by sampling many starts.
            seeds = [complex(math.cos(t), math.sin(t)) * r
                     for t in np.linspace(0, 2*math.pi, 17)[:-1]
                     for r in (0.3, 0.7, 1.1)]
            seeds.append(0.5+0.5j); seeds.append(0.01+0.01j)
            found = []
            f_fn, fp_fn = f
            for s in seeds:
                z = complex(s)
                for _ in range(80):
                    fp = fp_fn(z)
                    if abs(fp) < 1e-14: break
                    z = z - f_fn(z) / fp
                if abs(f_fn(z)) < 1e-6 and all(abs(z - r) > 0.05 for r in found):
                    found.append(z)
            return found[:8]

        def draw(*_):
            f_fn, fp_fn = polys[poly_var.get()]
            roots = find_roots(polys[poly_var.get()])
            max_iter = int(it_sl.get())
            res = 480
            xs = np.linspace(-1.5, 1.5, res); ys = np.linspace(-1.5, 1.5, res)
            X, Y = np.meshgrid(xs, ys); Z = X + 1j*Y
            attractor = np.full(Z.shape, -1, dtype=np.int8)
            iters = np.zeros(Z.shape, dtype=np.float32)
            with np.errstate(all="ignore"):
                for k in range(max_iter):
                    fp = fp_fn(Z)
                    Z = np.where(np.abs(fp) > 1e-14, Z - f_fn(Z) / fp, Z)
                    for ri, root in enumerate(roots):
                        close = (np.abs(Z - root) < 1e-3) & (attractor == -1)
                        attractor[close] = ri
                        iters[close] = k
            col = np.zeros((res, res, 3))
            base_palette = get_cmap("twilight")(np.linspace(0.05, 0.95, max(len(roots), 1)))[:, :3]
            for i in range(len(roots)):
                mask = attractor == i
                shade = 1 - iters[mask] / max_iter
                col[mask] = base_palette[i] * shade[:, None]
            self.ax.clear()
            self.ax.imshow(col, extent=[-1.5,1.5,-1.5,1.5], origin="lower")
            for r in roots:
                self.ax.plot(r.real, r.imag, "o", ms=6, mfc="white", mec="black", mew=1)
            self.ax.set_title(f"f(z) = {poly_var.get()}, {len(roots)} roots", color=T()["fg"])
            self.ax.set_axis_off()
            self.canvas.draw()
        draw()


# ---------------------------------------------------------------------------
# TEMPLATES TAB
# ---------------------------------------------------------------------------
class TemplatesTab(tk.Frame):
    TEMPLATES = [
        # (name, description, tab_key, payload)
        ("Quadratic solver", "Roots of ax²+bx+c using the quadratic formula", "cas",
         {"expr": "a*x**2 + b*x + c", "op": "solve"}),
        ("Derivative chain rule", "d/dx of sin(x²·exp(x))", "cas",
         {"expr": "sin(x**2 * exp(x))", "op": "diff"}),
        ("Integration by parts (∫x·eˣ)", "Definite ∫₀¹ x·eˣ dx", "cas",
         {"expr": "x*exp(x)", "op": "defint", "aux": "0,1"}),
        ("Taylor of cos(x) at 0", "Series to order 10", "cas",
         {"expr": "cos(x)", "op": "series", "aux": "0,10"}),
        ("Limit (sin x)/x at 0", "Classic", "cas",
         {"expr": "sin(x)/x", "op": "limit", "aux": "0"}),
        ("Damped oscillator (plot)", "y = e^(-0.2x)·cos(2x)", "graph2d",
         {"kind": "explicit", "expr": "exp(-0.2*x)*cos(2*x)\nexp(-0.2*x)\n-exp(-0.2*x)",
          "xmin": "0", "xmax": "20", "ymin": "-1.2", "ymax": "1.2"}),
        ("Lissajous-like 2D parametric", "Heart curve", "graph2d",
         {"kind": "parametric", "expr": "16*sin(t)**3 ; 13*cos(t)-5*cos(2*t)-2*cos(3*t)-cos(4*t)",
          "xmin": "-20", "xmax": "20", "ymin": "-20", "ymax": "20"}),
        ("Polar rose r=cos(4θ)", "Four-petal rose", "graph2d",
         {"kind": "polar", "expr": "cos(4*theta)"}),
        ("Implicit ellipse + hyperbola", "Conic sections", "graph2d",
         {"kind": "implicit", "expr": "x**2/9 + y**2/4 - 1\nx**2/4 - y**2/9 - 1",
          "xmin": "-6", "xmax": "6", "ymin": "-4", "ymax": "4"}),
        ("Slope field y' = y-x", "Direction field of a simple ODE", "graph2d",
         {"kind": "slope", "expr": "y - x", "xmin": "-4", "xmax": "4", "ymin": "-4", "ymax": "4"}),
        ("Vector field (−y, x)", "Pure rotation", "graph2d",
         {"kind": "vfield", "expr": "-y ; x", "xmin": "-4", "xmax": "4", "ymin": "-4", "ymax": "4"}),
        ("3D ripple", "sin(√(x²+y²))", "graph3d",
         {"kind": "surface", "expr": "sin(sqrt(x**2 + y**2))"}),
        ("3D saddle", "x² − y²", "graph3d",
         {"kind": "surface", "expr": "x**2 - y**2"}),
        ("Complex domain coloring of z²", "Phase plot", "graph3d",
         {"kind": "complex", "expr": "x**2"}),
        ("Compound interest", "FV of $1000 at 5% for 30y", "calc",
         {"expr": "1000*(1+0.05)^30"}),
        ("RLC resonant frequency", "f = 1/(2π√(LC)) with L=10mH, C=1µF", "calc",
         {"expr": "1/(2*pi*sqrt(0.01*1e-6))"}),
        ("Projectile range", "v² sin(2θ)/g, θ=45°, v=20 m/s", "calc",
         {"expr": "20^2 * sin(2*pi/4) / 9.81"}),
        ("Prime factorize 360", "Number theory", "cas",
         {"expr": "360", "op": "factor"}),
    ]

    def __init__(self, parent, engine: Engine, app):
        super().__init__(parent, bg=T()["bg"])
        self.engine = engine
        self.app = app
        self._build()

    def _build(self):
        tk.Label(self, text="Templates — click to load a ready example",
                 bg=T()["bg"], fg=T()["accent"], font=("Segoe UI", 13, "bold")).pack(anchor="w", padx=14, pady=(12, 6))
        wrap = tk.Frame(self, bg=T()["bg"])
        wrap.pack(fill="both", expand=True, padx=10, pady=4)
        canvas = tk.Canvas(wrap, bg=T()["bg"], highlightthickness=0)
        canvas.pack(side="left", fill="both", expand=True)
        sb = ttk.Scrollbar(wrap, orient="vertical", command=canvas.yview)
        sb.pack(side="right", fill="y")
        canvas.config(yscrollcommand=sb.set)
        inner = tk.Frame(canvas, bg=T()["bg"])
        canvas.create_window((0, 0), window=inner, anchor="nw")
        inner.bind("<Configure>", lambda e: canvas.config(scrollregion=canvas.bbox("all")))

        for i, (name, desc, tab, payload) in enumerate(self.TEMPLATES):
            card = tk.Frame(inner, bg=T()["panel"], padx=12, pady=10)
            card.grid(row=i // 2, column=i % 2, padx=8, pady=6, sticky="nsew")
            inner.grid_columnconfigure(0, weight=1); inner.grid_columnconfigure(1, weight=1)
            tk.Label(card, text=name, bg=T()["panel"], fg=T()["accent"],
                     font=("Segoe UI", 11, "bold")).pack(anchor="w")
            tk.Label(card, text=desc, bg=T()["panel"], fg=T()["fg"],
                     font=("Segoe UI", 9), wraplength=380, justify="left").pack(anchor="w", pady=(2,6))
            tk.Button(card, text=f"Load → {tab}", command=lambda t=tab, p=payload: self._load(t, p),
                      bg=T()["btn_op"], fg=T()["btn_op_fg"], relief="flat", font=("Segoe UI", 9, "bold")).pack(anchor="w")

    def _load(self, tab, payload):
        self.app.load_template(tab, payload)


# ---------------------------------------------------------------------------
# UNITS / CONSTANTS TAB
# ---------------------------------------------------------------------------
class UnitsTab(tk.Frame):
    def __init__(self, parent, engine: Engine, app):
        super().__init__(parent, bg=T()["bg"])
        self.engine = engine
        self.app = app
        self._build()

    def _build(self):
        left = tk.Frame(self, bg=T()["panel"], width=460)
        left.pack(side="left", fill="y", padx=(10,4), pady=10)
        left.pack_propagate(False)
        tk.Label(left, text="Unit converter", bg=T()["panel"], fg=T()["accent"],
                 font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=8, pady=(8, 4))
        self.cat = tk.StringVar(value=list(UNIT_CATEGORIES.keys())[0])
        ttk.Combobox(left, textvariable=self.cat, state="readonly",
                     values=list(UNIT_CATEGORIES.keys())).pack(fill="x", padx=8, pady=4)
        self.cat.trace_add("write", lambda *a: self._refresh_units())

        row = tk.Frame(left, bg=T()["panel"]); row.pack(fill="x", padx=8, pady=8)
        self.val_entry = ttk.Spinbox(row, from_=-1e15, to=1e15, increment=1,
                                      width=14, font=("Cascadia Code", 13),
                                      command=lambda: self._convert())
        self.val_entry.set("1"); self.val_entry.pack(side="left", padx=(0,6))
        self.from_unit = ttk.Combobox(row, state="readonly", width=8); self.from_unit.pack(side="left")
        tk.Label(row, text="→", bg=T()["panel"], fg=T()["fg"], font=("Segoe UI", 14)).pack(side="left", padx=8)
        self.to_unit = ttk.Combobox(row, state="readonly", width=8); self.to_unit.pack(side="left")

        # Quick-value chips for common amounts.
        chips = tk.Frame(left, bg=T()["panel"]); chips.pack(fill="x", padx=8)
        tk.Label(chips, text="Quick set:", bg=T()["panel"], fg=T()["muted"],
                 font=("Segoe UI", 9)).pack(side="left", padx=(0,4))
        for v in ("0.1", "0.5", "1", "2", "5", "10", "100", "1000"):
            tk.Button(chips, text=v, width=4, bg=T()["btn"], fg=T()["fg"],
                      activebackground=T()["btn_hover"], relief="flat", font=("Segoe UI", 8),
                      command=lambda val=v: (self.val_entry.set(val), self._convert())).pack(side="left", padx=1)

        self.conv_result = tk.Label(left, text="", bg=T()["panel"], fg=T()["accent2"], font=("Cascadia Code", 16, "bold"))
        self.conv_result.pack(fill="x", padx=8, pady=10)

        self.val_entry.bind("<KeyRelease>", lambda e: self._convert())
        self.from_unit.bind("<<ComboboxSelected>>", lambda e: self._convert())
        self.to_unit.bind("<<ComboboxSelected>>", lambda e: self._convert())

        self._refresh_units()
        self._convert()

        # Constants table on the right
        right = tk.Frame(self, bg=T()["bg"]); right.pack(side="right", fill="both", expand=True, padx=(4,10), pady=10)
        tk.Label(right, text="Physical & mathematical constants", bg=T()["bg"], fg=T()["accent"],
                 font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=8, pady=6)
        cols = ("Name", "Value", "Description")
        tv = ttk.Treeview(right, columns=cols, show="headings", height=20)
        for c in cols: tv.heading(c, text=c)
        tv.column("Name", width=110); tv.column("Value", width=180); tv.column("Description", width=440)
        for name, (val, desc) in CONSTANTS.items():
            tv.insert("", tk.END, values=(name, f"{val:g}", desc))
        tv.pack(fill="both", expand=True, padx=8, pady=4)
        tv.bind("<Double-1>", lambda e: self._copy_const(tv))
        tk.Label(right, text="(double-click to insert into the Calculator display)",
                 bg=T()["bg"], fg=T()["muted"], font=("Segoe UI", 9)).pack(anchor="w", padx=8)

    def _refresh_units(self):
        units = list(UNIT_CATEGORIES[self.cat.get()].keys())
        self.from_unit["values"] = units; self.to_unit["values"] = units
        self.from_unit.set(units[0]); self.to_unit.set(units[1] if len(units) > 1 else units[0])
        self._convert()

    def _convert(self):
        try:
            v = float(self.val_entry.get())
            ufrom = self.from_unit.get(); uto = self.to_unit.get()
            if not ufrom or not uto: return
            ratios = UNIT_CATEGORIES[self.cat.get()]
            base = v * ratios[ufrom]
            result = base / ratios[uto]
            self.conv_result.config(text=f"{v:g} {ufrom}  =  {result:.10g} {uto}")
        except Exception:
            self.conv_result.config(text="")

    def _copy_const(self, tv):
        sel = tv.selection()
        if not sel: return
        name = tv.item(sel[0], "values")[0]
        self.app.calc_tab.display.insert(tk.END, name)
        self.app.nb.select(self.app.calc_tab)


# ---------------------------------------------------------------------------
# SETTINGS / ABOUT TAB
# ---------------------------------------------------------------------------
class SettingsTab(tk.Frame):
    def __init__(self, parent, engine: Engine, app):
        super().__init__(parent, bg=T()["bg"])
        self.engine = engine
        self.app = app
        self._build()

    def _build(self):
        tk.Label(self, text="Settings", bg=T()["bg"], fg=T()["accent"],
                 font=("Segoe UI", 14, "bold")).pack(anchor="w", padx=14, pady=(14, 4))

        # Theme
        box = tk.Frame(self, bg=T()["panel"], padx=12, pady=12)
        box.pack(fill="x", padx=14, pady=8)
        tk.Label(box, text="Theme", bg=T()["panel"], fg=T()["accent2"],
                 font=("Segoe UI", 11, "bold")).pack(anchor="w")
        self.theme_var = tk.StringVar(value=CURRENT_THEME)
        for name in THEMES:
            tk.Radiobutton(box, text=name, value=name, variable=self.theme_var,
                           bg=T()["panel"], fg=T()["fg"], selectcolor=T()["entry"],
                           activebackground=T()["panel"], activeforeground=T()["accent"],
                           command=self._change_theme).pack(anchor="w")

        # Default angle mode
        box = tk.Frame(self, bg=T()["panel"], padx=12, pady=12)
        box.pack(fill="x", padx=14, pady=8)
        tk.Label(box, text="Angle mode (default)", bg=T()["panel"], fg=T()["accent2"],
                 font=("Segoe UI", 11, "bold")).pack(anchor="w")
        self.am_var = tk.StringVar(value=self.engine.angle_mode)
        for v in ("rad", "deg"):
            tk.Radiobutton(box, text=v.upper(), value=v, variable=self.am_var,
                           bg=T()["panel"], fg=T()["fg"], selectcolor=T()["entry"],
                           activebackground=T()["panel"], activeforeground=T()["accent"],
                           command=lambda: self._set_angle_mode()).pack(side="left", padx=8)

        # Precision
        box = tk.Frame(self, bg=T()["panel"], padx=12, pady=12)
        box.pack(fill="x", padx=14, pady=8)
        tk.Label(box, text="Display precision (significant digits)",
                 bg=T()["panel"], fg=T()["accent2"], font=("Segoe UI", 11, "bold")).pack(anchor="w")
        prec_var = tk.IntVar(value=self.engine.precision)
        s = ttk.Scale(box, from_=4, to=30, orient="horizontal",
                      command=lambda v: self._set_precision(int(float(v))))
        s.set(self.engine.precision); s.pack(fill="x", pady=4)

        # About
        about = tk.Frame(self, bg=T()["panel"], padx=12, pady=12)
        about.pack(fill="both", expand=True, padx=14, pady=8)
        tk.Label(about, text="About", bg=T()["panel"], fg=T()["accent2"],
                 font=("Segoe UI", 11, "bold")).pack(anchor="w")
        tk.Label(about, text=f"{APP_NAME} v{APP_VERSION}", bg=T()["panel"], fg=T()["fg"],
                 font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(4,0))
        tk.Label(about, text="An all-in-one scientific calculator with CAS, 2D/3D plotting,\n"
                              "drag-and-drop CSV analysis, and a library of interactive math demos.\n"
                              "Built with Python, NumPy, SciPy, SymPy, Matplotlib, Tkinter, and PyInstaller.",
                 bg=T()["panel"], fg=T()["fg"], font=("Segoe UI", 10),
                 justify="left").pack(anchor="w", pady=4)
        tk.Label(about, text="Keyboard shortcuts:\n"
                              "  Enter — evaluate calculator\n"
                              "  Ctrl+1..7 — switch tabs\n"
                              "  Esc — stop running demo animation",
                 bg=T()["panel"], fg=T()["muted"], font=("Cascadia Code", 9),
                 justify="left").pack(anchor="w", pady=(8, 0))

    def _change_theme(self):
        global CURRENT_THEME
        CURRENT_THEME = self.theme_var.get()
        try: plt.style.use(T()["mpl"])
        except Exception: pass
        self.app.rebuild_tabs()

    def _set_angle_mode(self):
        self.engine.angle_mode = self.am_var.get()
        try: self.app.calc_tab.mode_var.set(self.engine.angle_mode.upper())
        except Exception: pass

    def _set_precision(self, n):
        self.engine.precision = int(n)


# ---------------------------------------------------------------------------
# MAIN APP
# ---------------------------------------------------------------------------
class App:
    def __init__(self):
        if DND_AVAILABLE:
            self.root = TkinterDnD.Tk()
        else:
            self.root = tk.Tk()
        self.root.title(f"{APP_NAME} v{APP_VERSION}")
        self.root.geometry("1280x800")
        try:
            self.root.iconphoto(True, _build_icon())
        except Exception:
            pass
        self.engine = Engine()
        self._apply_root_bg()
        self._build_style()
        self._build_tabs()
        self._bind_shortcuts()
        try: plt.style.use(T()["mpl"])
        except Exception: pass

    def _apply_root_bg(self):
        self.root.configure(bg=T()["bg"])

    def _build_style(self):
        style = ttk.Style()
        try: style.theme_use("clam")
        except Exception: pass
        style.configure("TNotebook", background=T()["bg"], borderwidth=0)
        style.configure("TNotebook.Tab", background=T()["panel"], foreground=T()["fg"],
                        padding=[14, 8], font=("Segoe UI", 10, "bold"))
        style.map("TNotebook.Tab",
                  background=[("selected", T()["accent"])],
                  foreground=[("selected", T()["bg"])])
        style.configure("Treeview", background=T()["entry"], foreground=T()["fg"],
                        fieldbackground=T()["entry"], rowheight=22)
        style.configure("Treeview.Heading", background=T()["panel"], foreground=T()["accent"],
                        font=("Segoe UI", 9, "bold"))
        style.configure("TCombobox", fieldbackground=T()["entry"], background=T()["btn"],
                        foreground=T()["fg"], arrowcolor=T()["accent"])
        style.map("TCombobox",
                  fieldbackground=[("readonly", T()["entry"])],
                  foreground=[("readonly", T()["fg"])])
        style.configure("TSpinbox", fieldbackground=T()["entry"], background=T()["btn"],
                        foreground=T()["fg"], arrowcolor=T()["accent"],
                        bordercolor=T()["muted"], lightcolor=T()["btn"], darkcolor=T()["btn"])
        style.map("TSpinbox", fieldbackground=[("readonly", T()["entry"])])
        style.configure("Horizontal.TScale", background=T()["panel"],
                        troughcolor=T()["entry"], lightcolor=T()["btn"], darkcolor=T()["btn"])
        style.configure("TButton", background=T()["btn"], foreground=T()["fg"],
                        bordercolor=T()["muted"], focuscolor=T()["accent"])
        style.map("TButton", background=[("active", T()["btn_hover"])])

    def _build_tabs(self):
        if hasattr(self, "nb"):
            self.nb.destroy()
        self.nb = ttk.Notebook(self.root)
        self.nb.pack(fill="both", expand=True)
        self.calc_tab = CalcTab(self.nb, self.engine, self)
        self.cas_tab = CASTab(self.nb, self.engine, self)
        self.g2d_tab = Graph2DTab(self.nb, self.engine, self)
        self.g3d_tab = Graph3DTab(self.nb, self.engine, self)
        self.data_tab = DataTab(self.nb, self.engine, self)
        self.demos_tab = DemosTab(self.nb, self.engine, self)
        self.tmpl_tab = TemplatesTab(self.nb, self.engine, self)
        self.units_tab = UnitsTab(self.nb, self.engine, self)
        self.settings_tab = SettingsTab(self.nb, self.engine, self)
        for tab, name in [
            (self.calc_tab, "🧮 Calculator"),
            (self.cas_tab, "ƒ(x) Symbolic"),
            (self.g2d_tab, "📈 Graph 2D"),
            (self.g3d_tab, "🧊 Graph 3D"),
            (self.data_tab, "📊 Data"),
            (self.demos_tab, "✨ Demos"),
            (self.tmpl_tab, "📂 Templates"),
            (self.units_tab, "📏 Units"),
            (self.settings_tab, "⚙ Settings"),
        ]:
            self.nb.add(tab, text=name)

    def rebuild_tabs(self):
        self._apply_root_bg()
        self._build_style()
        self._build_tabs()

    def _bind_shortcuts(self):
        for i, key in enumerate("123456789"):
            self.root.bind(f"<Control-Key-{key}>", lambda e, idx=i: self.nb.select(idx))
        self.root.bind("<Escape>", lambda e: self._stop_demo())

    def _stop_demo(self):
        try: self.demos_tab._stop_anim()
        except Exception: pass

    def load_template(self, tab_key, payload):
        if tab_key == "calc":
            self.nb.select(self.calc_tab)
            self.calc_tab.display.delete(0, tk.END)
            self.calc_tab.display.insert(0, payload["expr"])
        elif tab_key == "cas":
            self.nb.select(self.cas_tab)
            self.cas_tab.expr_entry.delete(0, tk.END)
            self.cas_tab.expr_entry.insert(0, payload["expr"])
            if "aux" in payload: self.cas_tab.aux_entry.delete(0, tk.END); self.cas_tab.aux_entry.insert(0, payload["aux"])
            op = payload.get("op")
            if op: self.cas_tab._do(op)
        elif tab_key == "graph2d":
            self.nb.select(self.g2d_tab)
            self.g2d_tab.kind.set(payload.get("kind", "explicit"))
            self.g2d_tab._kind_changed()
            self.g2d_tab.expr_text.delete("1.0", tk.END); self.g2d_tab.expr_text.insert("1.0", payload["expr"])
            for k, w in [("xmin", self.g2d_tab.xmin), ("xmax", self.g2d_tab.xmax),
                         ("ymin", self.g2d_tab.ymin), ("ymax", self.g2d_tab.ymax)]:
                if k in payload:
                    w.delete(0, tk.END); w.insert(0, payload[k])
            self.g2d_tab._plot()
        elif tab_key == "graph3d":
            self.nb.select(self.g3d_tab)
            self.g3d_tab.kind.set(payload.get("kind", "surface"))
            self.g3d_tab.expr_text.delete("1.0", tk.END); self.g3d_tab.expr_text.insert("1.0", payload["expr"])
            self.g3d_tab._plot()

    def run(self):
        self.root.mainloop()


# ---------------------------------------------------------------------------
# ICON (drawn programmatically — avoids bundling external files)
# ---------------------------------------------------------------------------
def _build_icon() -> tk.PhotoImage:
    from PIL import Image, ImageDraw, ImageTk
    size = 64
    img = Image.new("RGBA", (size, size), (30, 30, 46, 255))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([4, 4, size-4, size-4], radius=10, fill=(37, 37, 55, 255), outline=(122, 162, 247, 255), width=2)
    d.text((14, 10), "Σ", fill=(122, 162, 247, 255))
    d.text((34, 10), "π", fill=(187, 154, 247, 255))
    d.text((14, 32), "√", fill=(247, 118, 142, 255))
    d.text((34, 32), "∫", fill=(158, 206, 106, 255))
    return ImageTk.PhotoImage(img)


def main():
    app = App()
    app.run()


if __name__ == "__main__":
    main()
