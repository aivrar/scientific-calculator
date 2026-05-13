# 📈 Graphs (2D and 3D)

## Graph 2D

Six plot kinds, all in one tab. The control panel scrolls if the window is small.

![Explicit plot](images/05_graph2d_explicit.png)

### Plot kinds

| Kind | Input shape | Variable |
|------|------------|---------|
| **Explicit** `y = f(x)` | one expression per line | `x` |
| **Parametric** `(x(t), y(t))` | `x_of_t ; y_of_t` per line | `t` in `[0, 2π]` |
| **Polar** `r = f(θ)` | one expression per line | `theta` in `[0, 2π]` |
| **Implicit** `F(x, y) = 0` | one expression per line, drawn at zero-level | `x`, `y` |
| **Vector field** `(Fx, Fy)` | `Fx ; Fy` (one pair) | streamlines computed automatically |
| **Slope field** `dy/dx = f(x, y)` | one expression | quiver arrows along the slope |

### Controls

- **Pick** dropdown — each kind has its own curated examples (heart curve, butterfly, cardioid, Lissajous, folium of Descartes, etc.). Picking *appends* to the function list so you can overlay multiple curves.
- **Range preset** — one-click sets all four bounds to common ranges (Trigonometric, Unit, Wide, Square, etc.).
- **x/y spinboxes** — click arrows or type. They accept symbolic values like `pi`, `-2*pi`.
- **Points slider** — resolution from 50 to 3000.

### Examples

**Polar roses** — `cos(4*theta)` overlaid with `sin(5*theta)`:

![Polar rose](images/06_graph2d_polar.png)

**Vector field** — `-y - 0.1*x ; x - 0.1*y` (damped rotation, with streamlines colored by speed):

![Vector field](images/07_graph2d_vfield.png)

**Implicit heart** — `(x²+y²-1)³ − x²y³ = 0`:

![Heart curve](images/08_graph2d_heart.png)

### Matplotlib toolbar

The toolbar above the plot lets you zoom (rectangle), pan, undo, and **save the figure as PNG/SVG/PDF**. Click the home icon to reset the view.

---

## Graph 3D

Five rendering kinds.

![3D peaks function](images/09_graph3d_peaks.png)

| Kind | Input | Renders |
|------|------|--------|
| **Surface** `z = f(x, y)` | one expression | filled surface with chosen colormap |
| **Wireframe** | one expression | mesh of lines |
| **Filled contour** | one expression | 2D contour plot |
| **3D parametric curve** | `x_of_t ; y_of_t ; z_of_t` | line in 3-space (helices, knots) |
| **Complex domain coloring** | `f(z)` (write as `f(x)`) | HSV phase plot — hue = arg(f), brightness = |f| |

### Complex domain coloring

A way to visualize a complex function as a single image. Hue encodes argument, brightness encodes magnitude. Zeros appear as dark spots; poles as bright spots.

![Complex domain coloring of z³−1](images/10_graph3d_complex.png)

Try these in the **Pick example** dropdown:
- `z^2` (basic squaring map)
- `1/z` (pole at origin)
- `z^3 - 1` (three zeros at the cube roots of unity)
- `sin(z)` (zeros at π·k)
- `tan(z)` (alternating zeros and poles)
- `(z^2 - 1)/(z^2 + 1)` (Möbius-style transform)

### Controls

- **Pick example** — curated functions per kind.
- **Range preset** — `(-6, 6)`, `(-2π, 2π)`, etc.
- **Range spinboxes** — symmetric range `[a, b]` for both x and y.
- **Resolution slider** — 20 to 200 (sweet spot is 70–100; 200 looks great but slow).
- **Colormap** — `viridis`, `plasma`, `inferno`, `magma`, `cividis`, `coolwarm`, `twilight`, `turbo`, `ocean`, `terrain`.

### Rotate / zoom

Drag inside the 3D plot to rotate. Use the matplotlib toolbar to pan and zoom. The home button resets the camera.
