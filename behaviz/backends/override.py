from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


KwargDict = dict[str, Any]
PlotType = str  # "line" | "scatter" | "errorbar" | …
NativeKey = str
CanonKey = str


class Overrider(ABC):
    """
    Abstract base for backend kwarg overriders.

    Subclasses must supply:
        CANON_TO_NATIVE : dict[CanonKey, list[NativeKey]]
            Canonical user-facing name → list of backend-native names it
            expands to.  A canonical name that maps to multiple native names
            will fan the value out to all of them (useful for Bokeh where
            ``color`` sets both ``line_color`` and ``fill_color``).

        VALID_CALL_KWARGS : dict[PlotType, set[NativeKey]]
            The native kwarg names that each plot-type's *call* accepts
            directly (i.e. can be passed to the function at call time, not
            applied post-hoc).

    Subclasses may additionally override:
        apply_post(result, post_kwargs)   — post-hoc artist styling
    """

    CANON_TO_NATIVE: dict[CanonKey, list[NativeKey]] = {}
    VALID_CALL_KWARGS: dict[PlotType, set[NativeKey]] = {}

    def route(
        self,
        plot_type: PlotType,
        kwargs: KwargDict,
    ) -> tuple[KwargDict, KwargDict]:
        """
        Translate and partition user kwargs into call-kwargs and post-kwargs.

        Steps
        -----
        1. Expand canonical aliases into their native equivalents.
        2. Keep any key that was *already* native (transparent passthrough).
        3. Split the resulting dict into:
             call_kwargs  — accepted by the plot-type call itself
             post_kwargs  — everything else (for post-hoc application)

        Parameters
        ----------
        plot_type : str
            One of "line", "scatter", "errorbar", "bar", "step", "violin",etc
        kwargs : dict
            Raw kwargs from the user (mix of canonical and native names).

        Returns
        -------
        call_kwargs : dict
            Kwargs to pass directly to the plot call.
        post_kwargs : dict
            Kwargs to apply after the call (via ``apply_post``).
        """
        translated = self._translate(kwargs)
        valid = self.VALID_CALL_KWARGS.get(plot_type, set())

        call_kwargs = {k: v for k, v in translated.items() if k in valid}
        post_kwargs = {k: v for k, v in translated.items() if k not in valid}

        return call_kwargs, post_kwargs

    def apply_post(self, result: Any, post_kwargs: KwargDict) -> None:
        """
        Apply remaining kwargs to the artist(s) returned by the plot call.

        Default implementation is a no-op.  Override in backends where
        post-hoc styling is possible (matplotlib artist setters, etc.).

        Parameters
        ----------
        result
            Whatever the underlying plot function returned.
        post_kwargs
            The kwargs that were not consumed by the call itself.
        """
        pass

    def _translate(self, kwargs: KwargDict) -> KwargDict:
        """
        Expand canonical names to their native equivalents.

        A canonical key that fans out to *multiple* native keys (e.g. Bokeh
        ``color → [line_color, fill_color]``) will write to all of them,
        *unless* the user already supplied the native key explicitly (explicit
        always wins).

        Keys that are not in CANON_TO_NATIVE are passed through unchanged
        so that backend-native kwargs always work directly.
        """
        out: KwargDict = {}

        for key, value in kwargs.items():
            native_keys = self.CANON_TO_NATIVE.get(key)
            if native_keys is None:
                # Not in the translation table at all — pass through unchanged
                # (transparent native kwarg or unknown user kwarg)
                out[key] = value
            elif len(native_keys) == 0:
                # Explicitly mapped to [] — intentionally dropped for this backend
                pass
            else:
                for nk in native_keys:
                    # Explicit native key from the user wins over a canonical expansion,
                    # but only when the native key is *different* from the source key.
                    # If they are the same (e.g. mpl "color" → ["color"]) we must
                    # always write it — otherwise the value is silently dropped.
                    if nk == key or nk not in kwargs:
                        out[nk] = value

        return out
