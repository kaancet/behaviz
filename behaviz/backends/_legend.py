"""Shared legend helper for the matplotlib-based backends."""

from __future__ import annotations


def dedup_legend(handles_labels):
    """Drop repeated labels (keeping the first) from ``get_legend_handles_labels()``.

    Grouped/hued plots can attach the same label to several artists — e.g. every
    rectangle of a bar container, or one line per subject sharing a hue label —
    which would otherwise produce duplicate legend entries.
    """
    handles, labels = handles_labels
    seen: set = set()
    h_out, l_out = [], []
    for h, l in zip(handles, labels):
        if l in seen:
            continue
        seen.add(l)
        h_out.append(h)
        l_out.append(l)
    return h_out, l_out
