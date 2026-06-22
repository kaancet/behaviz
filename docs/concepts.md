# Core concepts

!!! note "Stub — to be expanded"
    This page is scaffolded. Fill in from the README "Core concepts" section.

## The return contract

Every `plot_*` function returns `(fig, ax)`. `ax` is the drawable surface for the active
backend (a matplotlib `Axes`, or — for bokeh — the `figure` itself, since bokeh has no
separate axes object).

## Canonical calls → native backends

You call one high-level function. A `Renderer` per backend translates it into native
matplotlib / seaborn / bokeh calls. An `Overrider` routes your keyword arguments to the
right native property. This is what lets the same call render three ways.

## The registry guarantee

At import, a registry validates that **every** plot type is implemented on **every**
backend, so gaps fail loudly during development rather than at call time.

## Philosophy: you bring the numbers

behaviz does no hidden aggregation, binning, or statistics unless you ask via an explicit
[manipulator](manipulations.md). One row in, one mark out.

_TODO: expand with examples; pull narrative from README §"Core concepts"._
