#!/bin/sh
set -e
cd "$(dirname "$0")/.."

agentee render pcb:buggy-guard -o docs/images/buggy-guard-layout.png --canvas-only --width 1600 --height 1100
agentee render pcb:pendant -o docs/images/pendant-layout.png --canvas-only --width 900 --height 1000

agentee export pcb:buggy-guard -o buggy-guard.step
agentee export pcb:pendant -o pendant.step
(cd enclosure && gcad export pendant.gasm pendant.step)

f3d="uv run --with f3d --with pillow python docs/render_3d.py"
$f3d buggy-guard.step docs/images/buggy-guard-3d.png 1400 0 40
$f3d pendant.step docs/images/pendant-3d.png 900 0 40
$f3d enclosure/pendant.step docs/images/pendant-case.png 900 30 35

python3 docs/wiring.py
