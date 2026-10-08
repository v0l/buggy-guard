# buggy-guard

A safety and vehicle controller for 12-60 V electric scooters, kids buggies and ride-on cars, and
the handheld remote that drives it. It gates the ESC's throttle, brake and power lock behind a
hardware watchdog, and talks to the ESC over CAN or serial and switches lights and a horn.

| directory | what is in it |
|---|---|
| `hardware/` | The main board and the pendant (remote): schematics, layouts, symbols, footprints, simulations and 3D models, all as [agentee](https://github.com/v0l/agentee) TOML. `hardware/DESIGN.md` explains the design, `hardware/docs/INSTALL.md` the wiring into the vehicle. |
| `software/` | Firmware for both boards. Not written yet. |

Run `agentee check hardware` to check the designs, and `agentee view hardware` to open them.
