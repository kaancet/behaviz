# Installation

behaviz requires **Python ≥ 3.10**. And it's recommended to use [uv](https://github.com/astral-sh/uv) for package and environement management

## With pip

```bash
uv pip install behaviz
```

## With uv

```bash
uv pip install behaviz
```

Or add it directly through git:

```bash
uv add git+https://github.com/kaancet/behaviz.git
# or with pip
pip install git+https://github.com/kaancet/behaviz.git
```

Once installed, initialize the `~/.behaviz` preset directory (not necessary but it's convenient for discoverability and manually dropping/editting preset files)

```bash
behaviz init
```

## Dependencies

Installing behaviz pulls in all three backends so you can switch freely:

- `matplotlib`
- `seaborn`
- `bokeh`
- `numpy`, `scipy`
- optional but useful: `polars`

## Backend image export (bokeh)

PNG/SVG export from the **bokeh** backend renders through a headless browser. If you only
save bokeh figures to HTML, nothing extra is needed. For `.png`/`.svg`, install a browser
driver:

```bash
uv pip install selenium
# plus a geckodriver/chromedriver on PATH
```

matplotlib and seaborn export to all raster/vector formats with no extra setup.

## Verify

```python
import behaviz as bv
print(bv.__version__)
```
