# 🧮 Calculator

The default tab. Standard scientific arithmetic plus programmer mode, history, named variables, constants, and an "anything that takes a function" dropdown.

![Calculator](images/01_calculator.png)

## Layout

- **Top toolbar** — angle mode (RAD/DEG) indicator, toggle button, programmer-mode toggle, **Functions** dropdown (30+ math functions for one-click insertion), **Constants** dropdown (17 physical and mathematical constants).
- **Display** — the expression line. Press **Enter** to evaluate.
- **Result line** — shows the evaluation result. Errors appear here in red.
- **Button grid** — sin/cos/tan, ln/log/exp, x²/x³/x^y/1/x/n!/|x|, digits, operators, parens, `Ans` (last result), `C` (clear), `⌫` (backspace).
- **Side panel** — searchable history (double-click to re-load), named variables (e.g. `radius = 5`, double-click to insert), and a quick-pick constants block.

## Expression syntax

The expression parser is sympy-based — safe (no `eval`) and forgiving:

| You type | Means |
|---------|------|
| `2^3` or `2**3` | Power |
| `5!` | Factorial — works after numbers, identifiers, and parens |
| `pi`, `e`, `phi`, `tau` | Math constants |
| `c`, `G`, `h`, `hbar`, `k_B`, `N_A`, `R`, `e_charge`, `m_e`, `m_p`, `g`, `epsilon_0`, `mu_0`, `atm` | Physical constants |
| `sin(x)`, `cos(x)`, `tan(x)`, `asin/acos/atan` | Trig (respect angle mode) |
| `sinh/cosh/tanh/asinh/acosh/atanh` | Hyperbolic |
| `ln(x)` | Natural log |
| `log(x, b)` | Log base b (defaults to 10) |
| `log10(x)`, `log2(x)` | Common shortcuts |
| `exp(x)`, `sqrt(x)`, `cbrt(x)`, `root(x, n)` | Standard |
| `floor`, `ceil`, `round`, `sign`, `abs` | Rounding / absolute |
| `gcd(a, b)`, `lcm(a, b)`, `mod(a, b)` | Number theory |
| `nCr(n, k)`, `nPr(n, k)`, `factorial(n)` | Combinatorics |
| `isprime(n)` | Primality test (returns 0/1) |
| `re(z)`, `im(z)`, `arg(z)`, `conj(z)` | Complex parts |
| `i`, `I` | Imaginary unit |
| `inf`, `oo` | Infinity |
| `Ans` | Last computed result |
| `name = value` | Define a variable (it joins the side panel) |
| `π`, `√`, `×`, `÷`, `²`, `³` | Unicode shortcuts (auto-translated) |

## Programmer mode

Click **Programmer mode** to swap the keypad to a bitwise layout.

![Programmer mode](images/02_calculator_programmer.png)

- Hex digits **A–F** insert literally; `AC` clears (renamed from `C` to avoid clobbering the hex digit).
- **BIN / OCT / HEX** insert the `0b` / `0o` / `0x` Python-style prefix.
- Operators: `AND` (`&`), `OR` (`|`), `XOR` (`^`), `NOT` (`~`), `<<`, `>>`.
- Result line shows the value simultaneously in DEC, HEX, OCT, and BIN.

Example: `0xFF & 0x1A` → `DEC: 26`, `HEX: 0x1a`, `OCT: 0o32`, `BIN: 0b11010`.

## History and variables

Every successful evaluation appends to the history list (last 50 visible). Double-click any line to re-load it into the display.

Assigning a name (e.g. `radius = 5`) stores it in the variables panel and makes it usable in subsequent expressions: `area = pi * radius^2`.

## Keyboard shortcuts

| Key | Action |
|-----|--------|
| Enter | Evaluate current expression |
| Ctrl+1 … Ctrl+9 | Switch to tab 1–9 |
| Esc | Stop any running demo animation |
