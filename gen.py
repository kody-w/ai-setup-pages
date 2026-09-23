#!/usr/bin/env python3
"""Generate one "paste one line into <AI app>" setup page per AI host for any local MCP server.

    python gen.py products/rapp-brainstem.json            # every host in hosts/
    python gen.py products/rapp-brainstem.json codex vscode

A product file describes YOUR server (install, prepare, how to launch it over stdio).
A host file describes ONE AI app (how to register an MCP server there, how to confirm it).
New AI app? Add hosts/<slug>.json. New product? Add products/<name>.json. See README.md.
No dependencies beyond Python 3.8.
"""
from __future__ import annotations

import html
import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
TEMPLATE = (HERE / "template.html").read_text()


def load_hosts() -> list[dict]:
    return [json.loads(p.read_text()) for p in sorted((HERE / "hosts").glob("*.json"))]


def tokens(product: dict, host: dict, hosts: list[dict]) -> dict:
    s = product["stdio"]
    links = ", ".join(f'<a href="{product["page_url"].format(slug=h["slug"])}">{html.escape(h["name"])}</a>'
                      for h in hosts if h["slug"] != "mcp")
    t = {
        "PRODUCT": product["product"], "SHORT": product["short"], "SERVER": product["server"],
        "TAGLINE": product["tagline"], "NAME": host["name"], "HOST_SHORT": host["short"],
        "CMD_U": s["cmd_unix"], "ARG_U": s["arg_unix"], "CMD_W": s["cmd_windows"], "ARG_W": s["arg_windows"],
        "HOME_CMD_U": "$HOME/" + s["home_rel_cmd"], "HOME_ARG_U": "$HOME/" + s["home_rel_arg"],
        "HOME_EXAMPLE": "/Users/you",
        "ABS_CMD_U": "/Users/you/" + s["home_rel_cmd"], "ABS_ARG_U": "/Users/you/" + s["home_rel_arg"],
        "WIN_CMD_TXT": "C:\\\\Users\\\\you\\\\" + s["win_rel_cmd"].replace("\\", "\\\\"),
        "ABS_NOTE": ("Use the user's real absolute paths (run <code>echo $HOME</code>; on Windows "
                     "<code>$env:USERPROFILE</code>) in place of <code>/Users/you</code>. Config files do not expand <code>~</code>."),
        "WIN_ABS_NOTE": ("On Windows the command is <code>{{WIN_CMD_TXT}}</code> "
                         "and the argument is <code>C:\\\\Users\\\\you\\\\" + s["win_rel_arg"].replace("\\", "\\\\") + "</code> "
                         "(backslashes doubled inside JSON)."),
        "TIMEOUT_MS": str(product.get("timeout_ms", 300000)),
        "INSTALL_U": (product.get("install") or {}).get("unix", ""), "INSTALL_W": (product.get("install") or {}).get("windows", ""),
        "CHECK": (product.get("check") or {}).get("cmd", ""), "MCPB_URL": product.get("mcpb_url", ""), "HOST_LINKS": links,
    }
    if s.get("command"):  # a command found on PATH (e.g. python3) instead of a file under the home folder
        t.update(CMD_U=s["command"], HOME_CMD_U=s["command"], ABS_CMD_U=s["command"],
                 CMD_W=s.get("command_windows", s["command"]), WIN_CMD_TXT=s.get("command_windows", s["command"]))
    t["WIN_ABS_NOTE"] = fill(t["WIN_ABS_NOTE"], t)
    return t


def fill(text: str, t: dict) -> str:
    return re.sub(r"\{\{([A-Z_]+)\}\}", lambda m: t.get(m.group(1), m.group(0)), text)


def pre(text: str) -> str:
    return f"<pre>{html.escape(text.strip())}</pre>"


def blocks(items: list, t: dict) -> str:
    out = []
    for b in items:
        (kind, val), = b.items()
        out.append(pre(fill(val, t)) if kind == "pre" else f"<p>{fill(val, t)}</p>")
    return "\n".join(out)


def agent_section(product: dict, host: dict, t: dict) -> str:
    name = host["name"]
    has_install = bool(product.get("install"))
    n = (lambda k: k) if has_install else (lambda k: k - 2)
    parts = [
        f"<p>{fill(product['intro'], t)}</p>",
        "<h3>0. Ask the user first</h3>\n<p>Before you run anything, tell the user in a few lines what this setup does "
        f"and ask them to confirm. {fill(product['consent'], t)} Only continue once they say yes. "
        "It is fine to show them the commands below before running them.</p>",
    ]
    if has_install:
        parts += [
            f"<h3>1. Check whether the {html.escape(product['short'])} is already running</h3>\n"
            + pre(product["check"]["cmd"]) + f"\n<p>{product['check']['note']}</p>",
            "<h3>2. Install it</h3>\n<p>macOS / Linux:</p>\n" + pre(product["install"]["unix"])
            + "\n<p>Windows (PowerShell):</p>\n" + pre(product["install"]["windows"])
            + f"\n<p>{product['install']['note']}</p>",
        ]
    parts += [
        f"<h3>{n(3)}. Connect {html.escape(name)}</h3>\n<p>{product['prepare']['title']} macOS / Linux:</p>\n"
        + pre(product["prepare"]["unix"]) + "\n<p>Windows (PowerShell):</p>\n" + pre(product["prepare"]["windows"])
        + "\n" + blocks(host["register"], t),
        f"<h3>{n(4)}. Confirm</h3>\n" + blocks(host["confirm"], t) + f"\n<p>{fill(product['tools_note'], t)}</p>",
    ]
    return "\n\n".join(parts)


def render(product: dict, host: dict, hosts: list[dict]) -> str:
    t = tokens(product, host, hosts)
    slug = host["slug"]
    short = host["short"]
    steps = host.get("steps") or product.get("steps") or [
        [f"Installs the {product['short']}", "Using the official installer."],
        ["You approve it", f"{short} says what it will install and waits for your yes."],
        [f"Connects {short}", f"After that, ask {short} to “ask my {product['short']}…” and it hands the work over."],
    ]
    page = {
        "PRODUCT": html.escape(product["product"]), "SHORT": html.escape(product["short"]),
        "NAME": html.escape(host["name"]), "PAGE_URL": product["page_url"].format(slug=slug),
        "ACCENT": product.get("accent", "#0f766e"),
        "LEDE": fill(host.get("lede", "{{TAGLINE}} {{HOST_SHORT}} sets it up and connects to it for you."), t),
        "PASTE_LABEL": fill(host.get("paste_label", f"Paste this into {host['name']}"), t),
        "PASTE": html.escape(fill(host.get("paste", product["paste"].format(slug=slug)), t)),
        "CHIPS": "".join(f'<span class="chip">{html.escape(c)}</span>' for c in product.get("chips", [])),
        "STEPS_TITLE": fill(host.get("steps_title", f"{short} sets it up for you."), t),
        "STEPS_SUB": fill(host.get("steps_sub", "Give it the link. It reads this page, tells you what it will install, "
                                                "and waits for your yes before it runs anything."), t),
        "STEPS": "\n".join(f"    <li><b>{fill(a, t)}</b><small>{fill(b, t)}</small></li>" for a, b in steps),
        "AGENT": fill(host["agent_html"], t) if host.get("agent_html") else agent_section(product, host, t),
        "EXTRA": fill(host.get("extra_html", ""), t),
        "FOOTER": product.get("footer", ""),
    }
    return re.sub(r"\{\{([A-Z_]+)\}\}", lambda m: page.get(m.group(1), m.group(0)), TEMPLATE)


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 2
    product_path = pathlib.Path(argv[0]).resolve()
    product = json.loads(product_path.read_text())
    hosts = load_hosts()
    only = set(argv[1:])
    for host in hosts:
        if only and host["slug"] not in only:
            continue
        missing = [k for k in host.get("requires", []) if not product.get(k.lower())]
        if missing:
            print(f"skip {host['slug']}: product has no {', '.join(missing)}")
            continue
        out = (product_path.parent / product["out_dir"].format(slug=host["slug"])).resolve() / "index.html"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(render(product, host, hosts))
        leftover = sorted(set(re.findall(r"\{\{[A-Z_]+\}\}", out.read_text())))
        print("wrote", out, f"UNFILLED {leftover}" if leftover else "")
        if product.get("root_index") == host["slug"]:
            root = (product_path.parent / product["out_dir"].format(slug="")).resolve() / "index.html"
            root.write_text(out.read_text())
            print("wrote", root, "(root index)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
