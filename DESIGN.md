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
| battery in | J1, F1 (1 A), D1 (reverse), D2 (SMAJ58A TVS), C1/C2/C3 | 1.2 A fuse as fitted; D2 clamps at 93.6 V against the LM5164's 100 V rating |
| buck | U1 LM5164DDA, 47 uH, RON 41.2k (300 kHz), RFB 100k/31.6k | 5 V from about 20 V (UVLO divider R1/R2) up. Ripple injection type 3: R6 200k, C5 3.3 nF, C6 330 pF |
| LDO | U2 AP2112K-3.3, C9/C10 | 3V3 for the ESP32, IMU and gates |
| USB | J2, U4 USBLC6, R12/R13 5.1k, D3 SS14 | USB-C for flashing only; VBUS is ORed into +5V through D3 so it cannot drive the battery |

Peak input current is about 0.1 A (WiFi bursts), well inside the fuse.

### Throttle path

J6 PEDAL is a Hall throttle on its own 5 V through F2 (100 mA PTC). The signal goes to the ADC
through a 10k/15k divider (0.4 x) and drives an MCP6002 gain-of-1.5 filter (R36 20k, R37 10k)
after a two-pole 20 kHz PWM filter (R34/R35 10k, C22/C23 100 nF). The op-amp output goes to
J7 ESC_THR through 470 R; the divider R39/R40 takes it back to an ADC so the firmware can see
what the ESC sees. Q5 (2N7002) shorts the throttle output to ground whenever KILL is high, so a
stuck PWM or a hung output stage still lands on zero throttle.

### Safety logic

```
SAFE = ARM AND WDOK
KILL = NOT (SAFE AND NOT BRK_REL)
```

| net | from | to |
|---|---|---|
| WDOK | TPS3430 WDO (open-drain, 10k pull-up), LSM6DS3 INT1 through R19 1k, 74AHCT1G08 pin 2 | U7 (ARM AND) |
| ARM | ESP32-S3 IO15, 100k pull-down R22 | U7 pin 1 |
| SAFE | U7 out, 100k pull-down R24 | U8 NAND pin 1, Q2 gate, green LED D7 |
| KILL | U8 out | Q4 gate (e-brake), Q5 gate (throttle shunt) |
| IGN_G | Q2 (DMN10H220L) drain | Q3 IRFR9120N gate via R27 33k, D8 BZT52C15 clamp, R28 10k to source |

Q3 switches the ESC's power-lock wire between J4.1 (VIN) and J4.3 (IGN_OUT). J4.2 (ESTOP_RET) is
the e-stop loop: opening it floats the Q3 source, R28 pulls the gate up and the lock drops. The
firmware sees the e-stop as a divider R30/R31 on ESTOP_ADC.

The TPS3430 runs with SET0 = 0, SET1 = 1, CWD = 10k pull-up, which is a 7.7 ms to 165 ms window
(10k: 7.65 ms max short, 165.8 ms min long). The ESP must toggle IO12 at about 100 ms. A firmware
hang, an infinite loop with interrupts off, or a crashed task stops WDOK within 165 ms. The
watchdog never resets the ESP: it only drops SAFE, so flashing over USB is not disturbed. The IMU
is configured with INT1 as an open-drain wake-up interrupt (PP_OD set in CTRL3_C); on an impact
above the threshold it pulls WDOK low itself and the throttle is dead before the firmware even
sees it. The kill is latched in firmware until the pedal is at zero and the fob resets.

## Parts

| ref | value | part |
|---|---|---|
| U1 | LM5164 | TI LM5164DDAR |
| U2 | AP2112K-3.3 | Diodes AP2112K-3.3TRG1 |
| U3 | ESP32-S3-WROOM-1U-N16R8 | 16 MB flash, 8 MB PSRAM, u.FL antenna (the module has no PCB antenna) |
| U5 | TPS3430 | TI TPS3430WDRCR, window watchdog with a separate WDO |
| U6 | LSM6DS3TR-C | ST, 16 g accelerometer for the impact latch |
| U7, U8 | 74AHCT1G08, 74AHCT1G00 | AHCT so 3.3 V is a valid high |
| U9 | MCP6002T | throttle filter amplifier, unit 3 unused (tied as a follower) |
| Q2 | DMN10H220L | ignition low-side driver, 100 V |
| Q3 | IRFR9120N | ignition power-lock switch, 100 V PFET in DPAK |
| Q4, Q5 | 2N7002 | e-brake and throttle shunt |
| D2 | SMAJ58A | 58 V standoff TVS |
| F1 | 0451 series 1 A | Littelfuse 0451001.MRL |
| F2, F3 | MF-100MA, MF-200MA | Bourns resettable PTCs for the pedal and sensor 5 V |
| BZ1 | 12x9.5 mm magnetic 5 V | CUI CEM-1205C or equal |

## Board

`buggy-guard.board.toml`: 100 x 80 mm, JLC04161H-7628 4 layer, ENIG, black mask.

- F.Cu and B.Cu carry signals and power, In1.Cu is a solid ground plane, In2.Cu is a +3V3 plane.
  Every net class is confined to F.Cu/B.Cu (plus In2 for signals), so In1 is never routed through.
- HV class (battery, ignition, e-stop loop) is 0.6 mm with 0.5 mm clearance, on the outer layers
  only, and confined to the left edge of the board.
- The buck's switch node is F.Cu only, 0.8 mm wide, with the input caps, U1, C4, L1 and the
  ripple network placed as one block in the top-left corner.

## Layout notes for whoever places it

- U3's escape corridors (left, bottom and right of the module) are keepouts in `[place]`. Do not
  put 0603s inside them: the auto-placer will, and WDI/WDOK/ARM then have nowhere to go.
- The USB-C connector sits on the bottom edge so the D+/D- pair runs to U4 and then to the ESP's
  bottom-left pins without crossing the 5 V cluster.
- F3, C27 and F2 are in a line above U9 with F3's body vertical; the sensor 5 V filter cap has to
  be within a few mm of F3.2 or the ultrasonic echo lines pick up noise.

## Connectors

| ref | fits | pinout |
|---|---|---|
| J1 | 2 way 5.08 terminal | 1 BATT+, 2 GND |
| J4 | 4 way 5.08 terminal | 1 VIN (keyed), 2 e-stop return, 3 IGN_OUT to ESC lock, 4 GND |
| J6 | JST XH 3 way | 1 +5V, 2 GND, 3 pedal signal |
| J7 | JST XH 3 way | 1 +5V (unused, ESC supplies its own), 2 GND, 3 throttle out |
| J5 | JST XH 2 way | 1 e-brake (active low), 2 GND |
| J8..J11 | JST XH 4 way | 1 SENS_5V, 2 TRIG, 3 ECHO, 4 GND, one per ultrasonic sensor |
| J12 | JST XH 3 way | 1 SENS_5V, 2 GND, 3 wheel hall signal |
| J13 | JST XH 3 way | 1 AUX1, 2 AUX2 (to +3V3, switch to ground), 3 GND |
| J3 | JST SH 4 way | 1 GND, 2 +3V3, 3 SDA, 4 SCL |

## Firmware contract

The hardware is the safety net; the firmware only ever removes throttle. It must:

1. Feed WDI every 100 ms (7.7 to 165 ms window).
2. Hold ARM low until the fob heartbeat is present, the pedal is at zero, the battery is above the
   UVLO and no impact is latched. Release ARM only when it wants to move.
3. Hold BRK_REL low (brake released) only while armed.
4. Latch on impact: on any IMU wake-up above the threshold, drop ARM immediately, then brake and
   cut ignition once speed is near zero. Re-arm only when the pedal has been at zero for a second
   and the fob reset is pressed.
5. Compare the commanded throttle (PWM) against THR_FB_ADC and cut power if they disagree by more
   than about 100 mV.
6. Cap speed from the hall input and slow to a stop before applying the collision-avoidance cut.

## Still to do

- Firmware has not been written. The board is the safety layer; the behaviour above is the
  contract the firmware must meet.
- The e-brake output is an open-drain pull-down, correct for the low-active brake input on most
  e-bike controllers. A controller with a 12 V high-level brake input needs a high-side driver
  instead of Q4.
- Check the ESC's power-lock input draws no more than about 0.3 A (some controllers charge a
  capacitor through it); Q3 is rated for 6 A so there is margin, but the value is unverified.
- The IMU impact threshold is a firmware number (start around 2.5 g, measure on the real chassis).
- No fob PCB yet: the ESP-12F is meant to be the handheld remote, speaking ESP-NOW.
- The board has no fiducials; JLCPCB adds them for assembly panels, but add three if the board
  is to be assembled bare.