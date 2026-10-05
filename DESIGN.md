# buggy-guard

A safety and throttle-gating board for a 48 V kids buggy with a sine wave ESC. It sits between the
pedal and the ESC and never lets the pedal alone drive the motor: the ESP32-S3 must keep feeding a
hardware window watchdog, the IMU must not have latched an impact, and the remote fob must be in
range, before a throttle signal reaches the controller. Three independent hardware paths can cut
power, so a hung MCU, a dead MCU or a dead radio all stop the vehicle.

The schematic is split into four sheets (`buggy-guard.sch.toml` lists `power`, `mcu`, `safety`,
`io`), the layout is `buggy-guard.pcb.toml`, and the board spec is `buggy-guard.board.toml`.
`agentee check` is clean.

## Circuit

### Power chain

| stage | part | notes |
|---|---|---|
| battery in | J1, F1 (1 A), D1 (reverse), D2 (SMAJ58A TVS), C1/C2/C3 | D2 clamps at 93.6 V against the LM5164's 100 V rating |
| buck | U1 LM5164DDA, 47 uH, RON 41.2k (300 kHz), RFB 100k/31.6k | 5 V from about 20 V (UVLO divider R1/R2) up. Ripple injection type 3: R6 200k, C5 3.3 nF, C6 330 pF |
| LDO | U2 AP2112K-3.3, C9/C10 | 3V3 for the ESP32, IMU and gates |
| USB | J2, U4 USBLC6, R12/R13 5.1k, D3 SS14 | USB-C for flashing only; VBUS is ORed into +5V through D3 so it cannot drive the battery |

Peak input current is about 0.1 A (WiFi bursts), well inside the fuse.

### Throttle path

J6 PEDAL is a Hall throttle on its own 5 V through F2 (100 mA PTC). The signal goes to the ADC
through a 10k/15k divider (0.6 x, 5 V reads 3.0 V). The throttle the ESC sees is generated, not
passed through: THR_PWM goes through a two-pole 20 kHz filter (R34/R35 10k, C22/C23 100 nF) into
an MCP6002 gain-of-1.5 stage (R36 20k, R37 10k). The op-amp output goes to
J7 ESC_THR through 470 R; the divider R39/R40 takes it back to an ADC so the firmware can see
what the ESC sees. Q5 (2N7002) shorts the throttle output to ground whenever KILL is high, so a
stuck PWM or a hung output stage still lands on zero throttle.

### Safety logic

```
WD_LATCH = cleared while WDOK is low, set on an ARM rising edge
SAFE = ARM AND WD_LATCH
KILL = NOT (SAFE AND BRK_REL)
```

BRK_REL is active high: R23 holds it low, so the brake is applied and the throttle shunted
until the firmware drives it high.

| net | from | to |
|---|---|---|
| WDOK | TPS3430 WDO (open-drain, 10k pull-up), LSM6DS3 INT1 through R19 1k | U10 74LVC1G74 CLR, ESP32-S3 IO18 |
| WD_LATCH | U10 Q (D and PRE tied to +3V3) | U7 pin 2 |
| ARM | ESP32-S3 IO15, 100k pull-down R22 | U7 pin 1, U10 CLK |
| SAFE | U7 out, 100k pull-down R24 | U8 NAND pin 1, Q2 gate, green LED D7 |
| KILL | U8 out | Q4 gate (e-brake), Q5 gate (throttle shunt) |
| IGN_G | Q2 (DMN10H220L) drain | Q3 IRFR9120N gate via R27 33k, D8 BZT52C15 clamp, R28 10k to source |

Q3 switches the ESC's power-lock wire, J4.1 (IGN_OUT). Its source is fed from VIN through the
normally closed e-stop loop on J15 (J15.1 VIN, J15.2 ESTOP_RET): opening it floats the Q3 source, R28 pulls the gate up and the lock drops. The
firmware sees the e-stop as a divider R30/R31 on ESTOP_ADC.

The TPS3430 runs with SET0 = 0, SET1 = 1, CWD = 10k pull-up, which gives a guaranteed window of
10.35 ms (tWDL max) to 165.8 ms (tWDU min). The ESP must give WDI (IO17) a falling edge about
every 100 ms. A firmware
hang, an infinite loop with interrupts off, or a crashed task stops WDOK within 165 ms. WDO only
holds low for tRST (200 ms, CRST open) and then lets go, and a hung ESP still holds ARM high and
keeps LEDC running THR_PWM, so U10 latches the fault: once WDOK has gone low, SAFE stays low until
the firmware drives ARM low and high again with WDOK high. The watchdog never resets the ESP: it only drops SAFE, so flashing over USB is not disturbed. The IMU
is configured with INT1 as an open-drain, active-low, latched wake-up interrupt (PP_OD and
H_LACTIVE set in CTRL3_C, LIR set in TAP_CFG). INT1 powers up as a push-pull output driven low,
so WDOK sits at about 0.3 V through R19 until the firmware has done this. On an impact
above the threshold it pulls WDOK low itself and the throttle is dead before the firmware even
sees it. The kill is latched in firmware until the pedal is at zero and the fob resets.

## Parts

| ref | value | part |
|---|---|---|
| U1 | LM5164 | TI LM5164DDAR |
| U2 | AP2112K-3.3 | Diodes AP2112K-3.3TRG1 |
| U3 | ESP32-S3-WROOM-1U-N16R8 | 16 MB flash, 8 MB PSRAM. The -1U has a U.FL socket on the module and no PCB antenna |
| U5 | TPS3430 | TI TPS3430WDRCR, window watchdog with a separate WDO |
| U6 | LSM6DS3TR-C | ST, 16 g accelerometer for the impact latch |
| U7, U8 | 74AHCT1G08, 74AHCT1G00 | AHCT so 3.3 V is a valid high |
| U10 | 74LVC1G74 | TI SN74LVC1G74DCUR, on +3V3, latches a WDOK fault until ARM is re-asserted |
| U9 | MCP6002T | throttle filter amplifier, unit B unused (tied as a grounded follower) |
| Q2 | DMN10H220L | ignition low-side driver, 100 V |
| Q3 | IRFR9120N | ignition power-lock switch, 100 V PFET in DPAK |
| Q4, Q5 | 2N7002 | e-brake and throttle shunt |
| D2 | SMAJ58A | 58 V standoff TVS |
| F1 | 0451 series 1 A | Littelfuse 0451001.MRL |
| F2, F3 | MF-NSMF010/30X-2, MF-NSMF020-2 | Bourns 1206 resettable PTCs for the pedal and sensor 5 V |
| BZ1 | 12x9.5 mm magnetic 5 V | Same Sky CEM-1205-IC, 7.6 mm pitch. It has its own 2.4 kHz driver, so the firmware switches BUZZ on and off and never sends it a tone. The CUI CEM-1205C first picked is discontinued |
| C1 | 47 uF 100 V | Nichicon UUX2A470MNL1GS, 10 x 10 mm SMD |
| Q1 | DMN3404L | Diodes DMN3404L-7, buzzer low-side switch, 82 mohm at 3 V gate; same SOT-23 pinout as the AO3400A |
| J2 | USB-C | HRO TYPE-C-31-M-12, from LCSC (C165948). Mouser does not stock it |

Every part carries `mfr` and `mpn` fields. `python3 docs/order_bom.py N` writes
`docs/bom-order.csv` for N boards, and `docs/bom-mouser.csv` in the column layout of Mouser's
BOM import template, without J2. 0603 resistors and capacitors are rounded up to 10, each small semiconductor
and PTC gets one spare for hand assembly, and the U.FL antenna, XH housings and crimps are added
at the end.

## Board

`buggy-guard.board.toml`: 100 x 80 mm, JLC04161H-7628 4 layer, ENIG, black mask.

- F.Cu and B.Cu carry signals and power, In1.Cu is a solid ground plane, In2.Cu is a +3V3 plane.
  Every net class is confined to F.Cu/B.Cu (plus In2 for signals), so In1 is never routed through.
- HV class (battery, ignition, e-stop loop) is 0.6 mm with 0.5 mm clearance, on the outer layers
  only, and confined to the left edge of the board.
- The buck's switch node is F.Cu only, 0.8 mm wide, with the input caps, U1, C4, L1 and the
  ripple network placed as one block in the top-left corner.

## Layout notes for whoever places it

- Placed and routed by the layout engine (`agentee layout`, seed 2). Only the holes, the
  connectors, BZ1 and the buck block (F1, D1, D2, C1-C8, R1-R6, U1, L1) are locked. The engine
  has no switch-loop term yet, and every unlocked run stretched SW to 24-34 mm. Locked, it is 11 mm.
- Connectors sit along the edges by job: 48 V on the left (J1 battery, J15 e-stop, J4 ESC lock),
  then along the bottom the ESC plugs (J7, J5, J12), the rider inputs (J6, J13) and service
  (J2 USB, J14 UART). Sonar is on the right, I2C on top. Each one carries a silk label with its
  ref and job instead of the bare ref. The `[place]` keepouts are the strips under those labels.
- `agentee layout` drops every `[[graphics]]` item, so after a rerun put the connector and
  button labels back from git.
- U10 and C28 were added after the engine run: placed with `agentee place --keep-placed`, their
  nets routed with `agentee route`. U7.3 ties to GND through a via beside the pad.
- The refs of C20, R17, R18, R23 and U10 are hidden because the silk pass found no clear spot.
- H1-H4 are plated M3 holes on no net, so board GND never bonds to the frame. They have no silk.
- In2 is one +3V3 pour. The engine had cut 27 rail regions into it for the 48 V nets, +5V,
  BUZZ_N and SW; every connection is carried by tracks, so they were removed.
- The GND and +3V3 pours join through-hole pads by thermal relief (`relief_tht_only`), so the
  connector pins solder; SMD pads and the U1 and U3 thermal pads stay solid.
- The thermal vias in the U1 and U3 pads are 0.3 mm drills on 0.6 mm pads, JLC's standard drill.
- J2's shell front sits on the board edge (0.25 mm in), so an overmoulded USB-C plug seats fully.
- Test points are bare pads with `assembly = "no"`, so they stay off the BOM and CPL and the
  assembly stays one-sided.
- The USB-C connector sits on the bottom edge so the D+/D- pair runs to U4 and then to the ESP's
  bottom-left pins without crossing the 5 V cluster.
- F3, C27 and F2 are in a line above U9 with F3's body vertical; the sensor 5 V filter cap has to
  be within a few mm of F3.2 or the ultrasonic echo lines pick up noise.
- U3's u.FL socket is on the -x side of the module, so the antenna pigtail exits toward the left
  (inboard). Leave that space clear and keep the coax away from the buck and the ignition wiring.
- The two 3D models in `3dmodels/` are the vendor ESP32 STEP (from the datasheet link) and a
  community HRO USB-C STEP, neither of which exists in the KiCad library. Their `model_offset`
  and `model_rotate` were derived from the measured bounding boxes, not by eye: the ESP sits at
  z 0..3.2 with no offset in z, the USB-C needs `rotate = [90, 0, 0]` because it was exported
  lying on its side. `agentee check` cannot catch a bad transform, so verify in the 3D view
  or by walking the STEP vertices.

## Connectors

The installer's guide is `docs/INSTALL.md`, with the wiring diagram `docs/wiring.svg`. The
diagram is drawn by `python3 docs/wiring.py`; its connector positions are copied from the
layout, so rerun it after moving a connector.

| ref | fits | pinout |
|---|---|---|
| J1 | 2 way 5.08 terminal | 1 BATT+, 2 GND |
| J4 | 2 way 5.08 terminal | 1 IGN_OUT to ESC lock, 2 GND |
| J15 | JST XH 2 way | 1 VIN, 2 e-stop return (NC button loop, 48 V) |
| J6 | JST XH 3 way | 1 +5V, 2 GND, 3 pedal signal |
| J7 | JST XH 3 way | 1 +5V (unused, ESC supplies its own), 2 GND, 3 throttle out |
| J5 | JST XH 2 way | 1 e-brake (active low), 2 GND |
| J8..J11 | JST XH 4 way | 1 SENS_5V, 2 TRIG, 3 ECHO, 4 GND, one per ultrasonic sensor |
| J12 | JST XH 3 way | 1 SENS_5V, 2 GND, 3 wheel hall signal (R53 4.7k pull-up, R54/R55 10k/20k divider: an open-collector high reads 2.9 V, above the ESP's 2.48 V VIH even on USB power) |
| J13 | JST XH 3 way | 1 AUX1, 2 AUX2 (to +3V3, switch to ground), 3 GND |
| J3 | JST SH 4 way | 1 GND, 2 +3V3, 3 SDA, 4 SCL |
| J14 | JST XH 4 way | 1 GND, 2 +3V3, 3 RX (into the MCU), 4 TX (out of it). A console without USB |

Two ultrasonic ports, not four: J8 front, J9 rear. Four ports left no spare GPIO, and with
ESP-NOW gating reverse there is nothing useful a rear pair of corners would add over one
rear-centre sensor. That freed TXD0/RXD0 for the J14 console header and left IO42, IO47 and IO48
still unused.

## Test access

17 pads on the bottom side, all 1.0 mm, listed in `fab/testpoints.csv`: VBAT_ADC, PWR_LED, EN,
I2C_SDA, I2C_SCL, THR_FB_ADC, WDOK, WDI, BRK_REL, SAFE, KILL, US1/US2 trigger and echo,
PEDAL_ADC, SPEED and IGN_PD. +3V3, +5V and GND are reached through their plane pads.

Not probed: VBAT_F, VBUS and IGN_G. The autorouter found no path for a bottom pad next to those
three nets, and they are reachable from a probe on the top side or at the connector.

## Simulations

Three, all in `*.sim.toml`. `agentee sim NAME` regenerates each; the result files are not in
git because the DC one is 98 MB.

### `buggy-guard-dc`, resistive DC drop

50 V at F1.1, grounds at J1.2 and J4.2, the e-stop loop J15 linked at 50 mohm, 500 mA into the ESP32's 3V3 pad, 20 mA into the LDO
output, 2 mA into the IMU, and 300 mA out of the ignition lock line through Q3 (linked at 50 mohm).
Inductor DCR is the SRR1260's 170 mohm, the reverse diode 400 mohm, the fuse 95 mohm.

| reading | value |
|---|---|
| 3V3 at the ESP32 pad | 3.295 V from a 3.3 V rail, 5 mV drop |
| ignition lock line | 49.79 V at J4.1, 210 mV below the supply at 300 mA, 120 mV of it across D1 |
| peak current density | 121 A/mm2 on the In2.Cu 3V3 plane under the ESP32 |

The +3V3 plane and its vias carry the WiFi burst without a measurable drop. The peak density is
the ESP32's own pad current funnelling into the plane, which is what the thermal run then heats.

### `buggy-guard-thermal`, steady state

40 C ambient (a buggy in summer sun), 12 W/m2K on both faces, 0.9 W into the buck, 0.75 W into the
ESP32, 0.15 W into the buzzer and 0.02 W into the ignition FET.

| reading | value |
|---|---|
| board peak | 71.7 C, under U1 |
| U1 junction | 112.2 C (0.9 W x 45 C/W onto the pad temperature) |
| U3 junction | 94.2 C |
| buzzer pads | 58.2 C |
| ignition FET | 49.4 C |

Both junctions are the number to watch. The buck is the hot spot because it dissipates in a small
area with only the ground pad to lose heat through, and 112.2 C leaves 37.8 C to the LM5164's
150 C junction limit at 40 C ambient. That number is an estimate from a fitted theta-jc, not a
measurement, and it assumes the pad ties into the ground plane well. If the real thing runs hot,
the fix is copper under U1 rather than a bigger inductor.

### `buggy-guard-thermal-enclosed`, sealed box

The same sources at 50 C ambient with 5 W/m2K on both faces, for a board shut in a box under the
seat with no air moving.

| reading | value |
|---|---|
| board peak | 95.8 C, under U1 |
| U1 junction | 136.3 C, 13.7 C under the 150 C limit |
| U3 pads | 88.5 C |
| U3 junction | 117.9 C |
| buzzer pads | 81.4 C |

The buck still clears its limit, but with little margin, and 0.75 W of continuous WiFi into the
ESP32 is pessimistic. A sealed box wants vent holes or a thermal pad from U1 to the lid.

### `buggy-guard-dc-5v`, +5V rail

5 V held at L1.2 and 0 V at C8.2, the output caps' ground. Loads: 520 mA into the LDO, 40 mA
through the buzzer and Q1, 15 mA per sonar port, 10 mA hall, 20 mA pedal, and the op-amp and
gates. F2 and F3 are linked at 50 mohm, so the readings are copper only and leave out the PTCs'
own drop.

| reading | value |
|---|---|
| LDO input | 4.990 V, 10 mV drop at 520 mA |
| worst sensor feed | 4.981 V at J8.1, 19 mV drop |
| peak current density | 72 A/mm2, F.Cu at (49.6, 27.7) |

### `buggy-guard-dc-hv`, 48 V path at the fuse limit

50 V at J1.1 and 0 V at J1.2, 1 A into U1's VIN pin (the fuse rating, far above the buck's
real 0.1 A) and the 300 mA ignition line out of J4.1. F1 at 95 mohm, D1 at 400 mohm, Q3 and the
e-stop loop at 50 mohm each.

| reading | value |
|---|---|
| U1 VIN | 49.33 V, 670 mV down, 644 mV of it across F1 and D1 |
| ignition line | 49.28 V at J4.1 |
| peak current density | 123 A/mm2 at a track-to-pad corner by C2.1. The bulk of the 0.6 mm track carries 62 A/mm2 |

The first run peaked at 163 A/mm2 in a single via: the engine had dropped VIN onto B.Cu for
2 mm beside D2. That jog is now on F.Cu, so the full input current never passes through a via.

### `buggy-guard-sw-xtalk`, switch node coupling

FDTD of the buck corner (x 30-52, y 3-26 mm) at 0.1 mm cells, 10 MHz to 1 GHz, driving U1.8
(SW) and listening on R21.2 (I2C_SCL, which runs on In2 straight under the SW copper) and R7.2
(VBAT_ADC, on B.Cu under it). Two minutes on the GPU.

| path | worst | 48 V edge |
|---|---|---|
| SW to I2C_SCL | -73 dB at 1 GHz | 1.7 mV step |
| SW to VBAT_ADC | -90 dB at 1 GHz | 0.3 mV step |

The solid In1 ground between F.Cu and the inner signals shields them. Both are far under any
logic or ADC threshold. Check warns that the R7 and R21 models are dropped: the ports sit on
their pads, which is intended.

### `buggy-guard-safety`, logic

The full truth table. ARM, BRK_REL and WDOK are driven as the ESP32 and the watchdog would
drive them, the rails are driven as constants, and every resistor is ignored (the sim joins nets
through resistors, and the FB divider would otherwise short +5V to GND). U7, U8 and U10 are
built from their real 74AHCT1G08, 74AHCT1G00 and 74LVC1G74 values.

Fourteen assertions, all passing, no contention or timing violations: disarmed at power up,
armed with the brake held, armed and released (the only KILL low state), a WDOK fault, the fault
staying latched after WDOK returns while ARM is still high, a re-arm on a fresh ARM edge, and no
re-arm from an ARM edge during a fault. With U7.2 wired straight to WDOK, as before U10, four of
them fail.

## Firmware contract

The hardware is the safety net; the firmware only ever removes throttle. It must:

1. Feed WDI every 100 ms (10.35 to 165.8 ms window).
2. Hold ARM low until the fob heartbeat is present, the pedal is at zero, the battery is above the
   UVLO and no impact is latched. Raise ARM only when it wants to move, and only once WDOK (IO18)
   reads high: the rising edge is what sets U10, so ARM must go low and high again after any fault.
3. Drive BRK_REL high (brake released) only while armed.
4. Latch on impact: on any IMU wake-up above the threshold, drop ARM immediately, then brake and
   cut ignition once speed is near zero. Re-arm only when the pedal has been at zero for a second
   and the fob reset is pressed.
5. Compare the commanded throttle (PWM) against THR_FB_ADC and cut power if they disagree by more
   than about 100 mV.
6. Cap speed from the hall input and slow to a stop before applying the collision-avoidance cut.
7. Never command more than 4.2 V on THR_OUT. The Fardriver ND72240 treats its high throttle
   threshold plus 0.6 V as a broken throttle, and the stage can reach 4.95 V.
8. Keep BRK_REL low for a while after raising ARM. Arming is what powers the ESC through the lock
   wire, and it has to boot before it sees throttle. Start at 2 s; the ND72240's boot time is
   not measured.

## Pendant

The handheld remote is a separate board in the same project: `pendant.board.toml`,
`pendant.sch.toml` and `pendant.pcb.toml`, fab package in `fab-pendant/`. It is a 60 x 66 mm
4 layer JLC board (JLC04161H-7628, like the main board): In1 is solid GND, F, In2 and B carry
signals with GND poured around them. 2 layers did not leave room for every ground pad around
the ESP32-C3 to reach the pour. It talks ESP-NOW to the buggy and is the "fob" in the firmware
contract above.

| block | parts | notes |
|---|---|---|
| radio | U1 ESP32-C3-MINI-1-N4 | antenna at the top edge, top right, so the hand holding the bottom does not cover it; copper keepout under it on both layers |
| charging | J1 USB-C, U4 USBLC6, U2 MCP73831-2 (4.2 V), R3 4.7k | 213 mA charge, red D2 while charging |
| power path | D1 B5819W from VBUS, Q1 AO3401A from the cell | Microchip AN1149 load sharing: runs from USB when plugged in, the cell is never charged and loaded at once |
| 3V3 | U3 AP2112K-3.3, SW1 slide switch on its EN | off means only the charger and the 4.5 uA battery divider draw from the cell |
| display | J3, Waveshare 1.3inch OLED Module (C), SH1107 128x64 | soldered down on its own header, centred on the board, rear connector through a slot |
| controls | SW2 START/STOP, SW3 SPEED, 12 mm tactile | SPEED is on GPIO9: hold it while powering on for download mode |
| sound | BZ1 Murata PKLCS1212E4001 piezo, bottom side | driven differentially from two pins through 100 R each, 6.6 V p-p |

ESP32-C3 pins:

| GPIO | net | notes |
|---|---|---|
| 0 | VBUS_SENSE | 100k/100k, high while USB is plugged in |
| 1 | VBAT_ADC | 470k/470k with 100 nF, half the cell voltage |
| 2 | OLED_CS | 10k pull-up, strapping pin |
| 3 | BTN_START | 10k pull-up, deep sleep wake capable |
| 4 | OLED_DC | |
| 5, 10 | BUZZ_A, BUZZ_B | one LEDC channel, the second pin inverted in the GPIO matrix |
| 6, 7 | OLED_DIN, OLED_CLK | 4.7k pull-ups so the module's I2C mode also works |
| 8 | OLED_RST | 10k pull-up, strapping pin |
| 9 | BTN_SPEED | 10k pull-up, BOOT strap |
| 18, 19 | USB D-, D+ | native USB serial/JTAG for flashing |
| 20, 21 | U0RXD, U0TXD | bottom test pads |

The OLED stack: the module's own 1x07 male header is soldered straight into J3, so its 2.5 mm
plastic spacer sets the gap and the module PCB sits 2.5 mm above the pendant, with 2.5 mm
spacers and M2.5 screws in its four holes (they are part of the J3 footprint). The top of the
glass is about 5.6 mm above the board. The module's rear 7 pin connector would hang 6 mm below
it, so it drops through a 22.5 x 9.8 mm slot in the pendant and sticks out about 1.9 mm under
the board; the enclosure needs room for that. No parts sit under the module on the top side,
since its own rear parts leave about 1 mm. The module ships in 4-wire SPI mode, which is how it
is wired; moving its IM resistor to 1 selects I2C on DIN/CLK instead.

The ESP32-C3, 12 mm switch, piezo and OLED 3D models are boxes drawn by
`python3 3dmodels/make_models.py`. The vendor ESP32-C3 STEP and VRML do not mesh correctly in
the agentee viewer.

## Still to do

- Pendant: check the 7 pin order (VCC GND DIN CLK CS DC RST) and the rear connector position
  on an actual Waveshare module before soldering it down. The slot assumes the connector sits
  centred on the module's bottom edge, measured off Waveshare's drawing to about 1 mm,
  `footprints/OLED_Waveshare_1.3in_C.fp.toml` and the cutout in `pendant.board.toml`.
- Pendant: J2 pin 1 is battery +. JST PH LiPo leads come wired both ways round; check before
  plugging in, a reversed cell destroys U2 and U3.
- Firmware has not been written. The board is the safety layer; the behaviour above is the
  contract the firmware must meet.
- The e-brake output is an open-drain pull-down, correct for the low-active brake input on most
  e-bike controllers. A controller with a 12 V high-level brake input needs a high-side driver
  instead of Q4.
- Check the ESC's power-lock input draws no more than about 0.3 A (some controllers charge a
  capacitor through it); Q3 is rated for 6 A so there is margin, but the value is unverified.
- The IMU impact threshold is a firmware number (start around 2.5 g, measure on the real chassis).
- The board has no fiducials; JLCPCB adds them for assembly panels, but add three if the board
  is to be assembled bare.
- The ESP32-S3-WROOM-1U carries a U.FL socket on the module itself (datasheet section 10.2), so the
  antenna is a pigtail plugging into the module, not a board net. Mount the board with the u.FL end
  of the module pointing wherever the pigtail can reach, and keep the pigtail short and away from
  the buck switch node and the ignition wiring.