from __future__ import annotations

import copy
import json
import os
import warnings
from pathlib import Path

from behaviz.spec.plot_spec import PlotSpec
from behaviz.spec.serialization import PRESET_VERSION, spec_from_dict, spec_to_dict


# ---------------------------------------------------------------------------
# Locations
# ---------------------------------------------------------------------------
def behaviz_home() -> Path:
    """Root behaviz config directory (``~/.behaviz`` unless ``BEHAVIZ_HOME`` set)."""
    env = os.environ.get("BEHAVIZ_HOME")
    return Path(env).expanduser() if env else Path.home() / ".behaviz"


def presets_dir() -> Path:
    """Directory holding user preset JSON files (on the load path)."""
    return behaviz_home() / "presets"


def examples_dir() -> Path:
    """Directory holding read-only reference copies of the built-in presets.

    This is **not** on the load path — files here are starting points to copy
    into ``presets/`` and edit, so they never shadow (or go stale against) the
    in-code built-ins.
    """
    return behaviz_home() / "examples"


def _preset_file(name: str) -> Path:
    return presets_dir() / f"{name}.json"


def _validate_name(name: str) -> None:
    if not name or not isinstance(name, str):
        raise ValueError("Preset name must be a non-empty string.")
    if name != Path(name).name or name in {".", ".."} or "/" in name or "\\" in name:
        raise ValueError(f"Invalid preset name {name!r}: use a plain name without path separators.")


# ---------------------------------------------------------------------------
# Built-in presets (shipped with behaviz, always available)
# ---------------------------------------------------------------------------
def _builtin_specs() -> dict[str, PlotSpec]:
    # Imported lazily to avoid an import cycle (core imports the spec/plot stack).
    from behaviz.core.core import DEFAULT_SPEC

    return {
        "default": DEFAULT_SPEC,
        "paper": PlotSpec.preset("paper"),
        "poster": PlotSpec.preset("poster"),
        "notebook": PlotSpec.preset("notebook"),
        "dark": PlotSpec.preset("dark"),
        "presentation": PlotSpec.preset("presentation"),
        "presentation_dark": PlotSpec.preset("presentation_dark"),
        "print": PlotSpec.preset("print"),
    }


# ---------------------------------------------------------------------------
# Setup / scaffolding
# ---------------------------------------------------------------------------
_README_TEXT = """\
behaviz preset library
======================

This directory stores your behaviz plot presets.

  presets/   Your saved presets. Each <name>.json here is loadable with
             bv.load_preset("<name>"). Create them from Python with
             bv.save_preset("<name>", spec), or just drop a JSON file here.

  examples/  Read-only reference copies of the built-in presets (default,
             paper, poster, notebook, dark). These are NOT loaded from disk —
             the built-ins always live inside behaviz itself. Copy one into
             presets/ and edit it as a starting point, e.g.:

               cp examples/paper.json presets/my_paper.json

The built-in presets are always available via bv.load_preset(name) even with no
files here. A preset in presets/ with the same name as a built-in shadows it.

Storage location can be redirected with the BEHAVIZ_HOME environment variable.
"""


def init_home(with_examples: bool = True) -> dict:
    """Scaffold the behaviz home directory.

    Creates ``~/.behaviz/presets/`` and a ``README.txt``, and (by default) writes
    the built-in presets as reference copies into ``~/.behaviz/examples/``.

    Deliberately does **not** seed ``presets/`` with built-ins: doing so would
    shadow the in-code built-ins permanently and freeze them at install time.
    The ``examples/`` copies are off the load path, so they are safe to refresh
    and never go stale against an upgraded behaviz.

    Idempotent — safe to re-run; it refreshes README/examples in place.

    Returns
    -------
    dict
        ``{"home", "presets", "readme", "examples": [paths...]}`` describing what
        was written, for callers (e.g. the CLI) to report.
    """
    home = behaviz_home()
    presets = presets_dir()
    presets.mkdir(parents=True, exist_ok=True)

    readme = home / "README.txt"
    readme.write_text(_README_TEXT)

    written: dict = {"home": home, "presets": presets, "readme": readme, "examples": []}

    if with_examples:
        ex_dir = examples_dir()
        ex_dir.mkdir(parents=True, exist_ok=True)
        for name, spec in _builtin_specs().items():
            f = ex_dir / f"{name}.json"
            f.write_text(json.dumps(_to_payload(spec), indent=2))
            written["examples"].append(f)

    return written


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def save_preset(name: str, spec: PlotSpec, overwrite: bool = True) -> Path:
    """Save a :class:`PlotSpec` as a user preset under ``~/.behaviz/presets/``.

    Parameters
    ----------
    name : str
        Plain preset name (no path separators) — becomes ``<name>.json``.
    spec : PlotSpec
        The spec to persist. A ``post_hook``, if set, is dropped (callables
        cannot be serialized) with a warning.
    overwrite : bool, default True
        When False, raise ``FileExistsError`` instead of replacing an existing
        user preset of the same name.

    Returns
    -------
    pathlib.Path
        The path the preset was written to.
    """
    _validate_name(name)
    if not isinstance(spec, PlotSpec):
        raise TypeError(f"save_preset expects a PlotSpec, got {type(spec).__name__}.")

    target = _preset_file(name)
    if target.exists() and not overwrite:
        raise FileExistsError(f"Preset {name!r} already exists at {target}. Pass overwrite=True to replace it.")

    presets_dir().mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(_to_payload(spec), indent=2))
    return target


def export_preset(name: str, path) -> Path:
    """Write a preset out to a standalone JSON file for sharing.

    Unlike :func:`save_preset` (which writes into ``~/.behaviz``), this exports
    to an arbitrary location so you can email/commit/copy the file to another
    machine. Works for both user and built-in presets.

    Parameters
    ----------
    name : str
        Name of an existing preset (user or built-in).
    path : str | pathlib.Path
        Destination. If it points at an existing directory, the file is written
        there as ``<name>.json``; otherwise it is treated as the full file path.

    Returns
    -------
    pathlib.Path
        The path the preset was written to.
    """
    spec = load_preset(name)  # resolves user → built-in, raises if unknown
    dest = Path(path).expanduser()
    if dest.is_dir():
        dest = dest / f"{name}.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(_to_payload(spec), indent=2))
    return dest


def import_preset(path, name: str | None = None, overwrite: bool = True) -> Path:
    """Install a standalone preset JSON file into your ``~/.behaviz`` library.

    The reverse of :func:`export_preset`: after importing, the preset is
    loadable by name via :func:`load_preset`.

    Parameters
    ----------
    path : str | pathlib.Path
        The preset file to import.
    name : str, optional
        Name to store it under. Defaults to the file's stem (``cool.json`` →
        ``"cool"``).
    overwrite : bool, default True
        When False, raise ``FileExistsError`` if a user preset of that name
        already exists.

    Returns
    -------
    pathlib.Path
        The path the preset was installed to inside ``~/.behaviz/presets``.
    """
    src = Path(path).expanduser()
    if not src.is_file():
        raise FileNotFoundError(f"No preset file at {src}.")

    try:
        data = json.loads(src.read_text())
    except json.JSONDecodeError as exc:
        raise ValueError(f"{src} is not valid JSON: {exc}") from exc

    if not isinstance(data, dict) or not _looks_like_preset(data):
        raise ValueError(f"{src} does not look like a behaviz preset file.")

    spec = _payload_to_spec(data, src.name)
    target_name = name if name is not None else src.stem
    return save_preset(target_name, spec, overwrite=overwrite)


def load_preset(name: str) -> PlotSpec:
    """Load a preset by name and return a fresh :class:`PlotSpec`.

    User presets take precedence over built-ins of the same name.
    """
    _validate_name(name)

    target = _preset_file(name)
    if target.exists():
        return _load_file(target)

    builtins = _builtin_specs()
    if name in builtins:
        # Deep-copy so callers can mutate the result without touching the shared
        # built-in definition.
        return copy.deepcopy(builtins[name])

    available = ", ".join(list_presets()) or "(none)"
    print(f"No preset named {name!r}. Falling back on default. Available presets: {available}")
    return copy.deepcopy(builtins["default"])


def list_presets() -> dict[str, str]:
    """Return ``{name: source}`` for every available preset, sorted by name.

    ``source`` is ``"builtin"`` or ``"user"``; a user preset shadowing a
    built-in is reported as ``"user"``.
    """
    out: dict[str, str] = {name: "builtin" for name in _builtin_specs()}
    if presets_dir().exists():
        for f in sorted(presets_dir().glob("*.json")):
            out[f.stem] = "user"
    return dict(sorted(out.items()))


def delete_preset(name: str) -> None:
    """Delete a user preset. Built-ins cannot be deleted."""
    _validate_name(name)
    target = _preset_file(name)
    if target.exists():
        target.unlink()
        return
    if name in _builtin_specs():
        raise ValueError(f"{name!r} is a built-in preset and cannot be deleted.")
    raise FileNotFoundError(f"No user preset named {name!r} to delete.")


# ---------------------------------------------------------------------------
# Internal
# ---------------------------------------------------------------------------
def _to_payload(spec: PlotSpec) -> dict:
    """Serialize a spec to the on-disk payload (spec dict + schema version)."""
    return {"behaviz_preset_version": PRESET_VERSION, **spec_to_dict(spec)}


def _looks_like_preset(data: dict) -> bool:
    """Heuristic: does this dict resemble a behaviz preset payload?"""
    return "behaviz_preset_version" in data or any(k in data for k in ("title", "x", "y", "figure"))


def _payload_to_spec(data: dict, label: str) -> PlotSpec:
    """Strip the version stamp (warning if too new) and build the PlotSpec."""
    data = dict(data)
    version = data.pop("behaviz_preset_version", None)
    if version is not None and version > PRESET_VERSION:
        warnings.warn(
            f"Preset {label} was written with schema version {version}, but this "
            f"behaviz supports up to {PRESET_VERSION}. Loading on a best-effort basis.",
            stacklevel=2,
        )
    return spec_from_dict(data)


def _load_file(path: Path) -> PlotSpec:
    return _payload_to_spec(json.loads(path.read_text()), path.name)
