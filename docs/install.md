# Installation

behaviz requires **Python ≥ 3.10**.

## With pip

```bash
pip install behaviz
```

## With uv

```bash
uv add behaviz
```

## Dependencies

Installing behaviz pulls in all three backends so you can switch freely:

- `matplotlib`
- `seaborn`
- `bokeh`
- `numpy`, `scipy`

## Backend image export (bokeh)

PNG/SVG export from the **bokeh** backend renders through a headless browser. If you only
save bokeh figures to HTML, nothing extra is needed. For `.png`/`.svg`, install a browser
driver:

```bash
pip install selenium
# plus a geckodriver/chromedriver on PATH
```

matplotlib and seaborn export to all raster/vector formats with no extra setup.

## Verify

```python
import behaviz as bv
print(bv.__version__)
```
