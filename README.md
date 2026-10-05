# buggy-guard

A safety and throttle-gating controller for a 48 V kids buggy, and the handheld remote that drives
it.

| directory | what is in it |
|---|---|
| `hardware/` | The main board and the pendant (remote): schematics, layouts, symbols, footprints, simulations and 3D models, all as [agentee](https://github.com/v0l/agentee) TOML. `hardware/DESIGN.md` explains the design, `hardware/docs/INSTALL.md` the wiring into the buggy. |
| `software/` | Firmware for both boards. Not written yet. |

Run `agentee check hardware` to check the designs, and `agentee view hardware` to open them.
