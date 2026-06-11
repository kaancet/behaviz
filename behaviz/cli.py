"""
Command-line interface for behaviz preset management.

Installed as the ``behaviz`` console command (see ``[project.scripts]`` in
pyproject.toml). All commands are thin wrappers over :mod:`behaviz.presets`.

    behaviz init [--no-examples]   scaffold ~/.behaviz (presets/ + README + examples/)
    behaviz list                   list available presets (builtin / user)
    behaviz where                  print the presets directory path
"""

from __future__ import annotations

import argparse

from behaviz.presets import init_home, list_presets, presets_dir


def _cmd_init(args: argparse.Namespace) -> None:
    info = init_home(with_examples=not args.no_examples)
    print(f"Initialized behaviz home at {info['home']}")
    print(f"  presets:  {info['presets']}/")
    print(f"  readme:   {info['readme']}")
    if info["examples"]:
        ex_dir = info["examples"][0].parent
        print(f"  examples: {ex_dir}/  ({len(info['examples'])} reference presets)")
    print("\nSaved presets go in presets/. Built-ins are always available via "
          "bv.load_preset(name).")


def _cmd_list(args: argparse.Namespace) -> None:
    presets = list_presets()
    if not presets:
        print("No presets found.")
        return
    width = max(len(name) for name in presets)
    for name, source in presets.items():
        print(f"  {name:<{width}}  {source}")


def _cmd_where(args: argparse.Namespace) -> None:
    print(presets_dir())


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="behaviz", description="behaviz preset management")
    sub = parser.add_subparsers(dest="command", required=True)

    p_init = sub.add_parser("init", help="scaffold ~/.behaviz with presets/, a README, and example presets")
    p_init.add_argument("--no-examples", action="store_true", help="do not write the example presets")
    p_init.set_defaults(func=_cmd_init)

    p_list = sub.add_parser("list", help="list available presets (builtin and user)")
    p_list.set_defaults(func=_cmd_list)

    p_where = sub.add_parser("where", help="print the presets directory path")
    p_where.set_defaults(func=_cmd_where)

    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
