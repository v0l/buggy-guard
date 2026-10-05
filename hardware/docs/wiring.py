import html
from pathlib import Path

W, H = 1720, 1200
BX, BY, S = 640, 300, 5.2

RED = "#c93a3a"
AMBER = "#d68a12"
TEAL = "#1f8a7e"
GREY = "#8a8f98"
BLACK = "#222"

out = []


def p(s):
    out.append(s)


def esc(t):
    return html.escape(t, quote=False)


def mm(x, y):
    return BX + x * S, BY + y * S


def text(x, y, t, size=13, weight="normal", fill=BLACK, anchor="start", rotate=None, family=None):
    tr = f' transform="rotate({rotate} {x} {y})"' if rotate is not None else ""
    fam = f' font-family="{family}"' if family else ""
    p(f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" font-weight="{weight}" fill="{fill}" text-anchor="{anchor}"{tr}{fam}>{esc(t)}</text>')


def cable(points, color, dashed=False, width=6):
    d = " ".join(f"{x:.1f},{y:.1f}" for x, y in points)
    dash = ' stroke-dasharray="10 7"' if dashed else ""
    p(f'<polyline points="{d}" fill="none" stroke="{color}" stroke-width="{width}" stroke-linejoin="round" stroke-linecap="round"{dash}/>')


def box(x, y, w, h, title, lines, color, dashed=False):
    dash = ' stroke-dasharray="8 5"' if dashed else ""
    p(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="#fff" stroke="{color}" stroke-width="2.5"{dash}/>')
    p(f'<rect x="{x}" y="{y}" width="{w}" height="30" rx="8" fill="{color}"/>')
    p(f'<rect x="{x}" y="{y + 20}" width="{w}" height="10" fill="{color}"/>')
    text(x + 10, y + 21, title, 14, "bold", "#fff")
    ty = y + 52
    for ln in lines:
        if isinstance(ln, tuple):
            cols, xs = ln
            for c, dx in zip(cols, xs):
                text(x + 10 + dx, ty, c, 13, family="DejaVu Sans Mono, Menlo, monospace")
        elif ln == "":
            ty -= 8
        else:
            weight = "bold" if ln.startswith("!") else "normal"
            text(x + 10, ty, ln.lstrip("!"), 13, weight)
        ty += 19


def connector(cx, cy, pins, vertical):
    pitch = 11
    if vertical:
        w, h = 16, pins * pitch + 6
    else:
        w, h = pins * pitch + 6, 16
    p(f'<rect x="{cx - w / 2:.1f}" y="{cy - h / 2:.1f}" width="{w}" height="{h}" rx="2" fill="#f2f2f2" stroke="#fff" stroke-width="1"/>')
    for i in range(pins):
        o = (i - (pins - 1) / 2) * pitch
        px, py = (cx, cy + o) if vertical else (cx + o, cy)
        p(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="3" fill="#b08d2c"/>')


p(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" font-family="DejaVu Sans, Helvetica, Arial, sans-serif">')
p(f'<rect width="{W}" height="{H}" fill="#fafafa"/>')

text(40, 58, "buggy-guard wiring", 30, "bold")
text(40, 88, "Wire everything with the battery unplugged. Connector names match the white print on the board.", 15)
text(40, 110, "Pin 1 of each connector is marked on the board. Cables from the buggy that are not shown here stay as they are.", 15)

lx, ly = 1310, 22
p(f'<rect x="{lx}" y="{ly}" width="380" height="150" rx="8" fill="#fff" stroke="#ccc"/>')
text(lx + 14, ly + 24, "Cables", 14, "bold")
legend = [
    (RED, False, "Battery voltage, 48 V"),
    (AMBER, False, "To the motor controller's throttle and brake"),
    (TEAL, False, "Sensors and switches, 5 V or less"),
    (GREY, True, "Optional, or for setup only"),
    (BLACK, True, "Existing buggy wiring, unchanged"),
]
for i, (c, dsh, label) in enumerate(legend):
    yy = ly + 46 + i * 22
    cable([(lx + 16, yy - 4), (lx + 66, yy - 4)], c, dsh, 5)
    text(lx + 80, yy + 1, label, 13)

j = {
    "J1": mm(6.5, 12), "J15": mm(5, 47), "J4": mm(6.5, 58),
    "J7": mm(11, 75), "J5": mm(22, 75), "J12": mm(31, 75), "J6": mm(42, 75),
    "J13": mm(53, 75), "J2": mm(66.5, 75), "J14": mm(82, 75),
    "J8": mm(95, 20), "J9": mm(95, 34.5), "J3": mm(45, 4),
}

cable([(90, 330), (90, 790)], BLACK, True, 9)
text(78, 560, "main battery leads to the ESC, unchanged", 13, rotate=-90, anchor="middle")

cable([j["J1"], (560, j["J1"][1]), (560, 250), (420, 250)], RED)
cable([j["J15"], (420, j["J15"][1])], RED)
cable([j["J4"], (500, j["J4"][1]), (500, 790)], RED)
cable([j["J7"], (j["J7"][0], 905), (540, 905)], AMBER)
cable([j["J5"], (j["J5"][0], 1000), (540, 1000)], AMBER)
cable([j["J12"], (j["J12"][0], 830), (870, 830), (870, 890)], TEAL)
cable([j["J6"], (j["J6"][0], 815), (1050, 815), (1050, 890)], TEAL)
cable([j["J13"], (j["J13"][0], 800), (1230, 800), (1230, 890)], TEAL)
cable([j["J2"], (j["J2"][0], 785), (1405, 785), (1405, 890)], GREY, True)
cable([j["J14"], (j["J14"][0], 770), (1580, 770), (1580, 890)], GREY, True)
cable([j["J8"], (1300, j["J8"][1])], TEAL)
cable([j["J9"], (1300, j["J9"][1])], TEAL)
cable([j["J3"], (j["J3"][0], 250)], GREY, True)
p(f'<path d="M 905 505 C 850 420, 1060 330, 1150 262" fill="none" stroke="{GREY}" stroke-width="3" stroke-dasharray="6 5"/>')

p(f'<rect x="{BX}" y="{BY}" width="{100 * S}" height="{80 * S}" rx="10" fill="#15191a" stroke="#555" stroke-width="2"/>')
for hx, hy in [(4, 4), (96, 4), (4, 76), (96, 76)]:
    x, y = mm(hx, hy)
    p(f'<circle cx="{x}" cy="{y}" r="9" fill="#fafafa" stroke="#c8a64a" stroke-width="4"/>')
text(790, 455, "buggy-guard", 20, "bold", "#fff", "middle")
text(790, 477, "top side", 12, fill="#bbb", anchor="middle")

mx, my = mm(62.55, 43.55)
p(f'<rect x="{mx - 66:.1f}" y="{my - 47:.1f}" width="133" height="94" rx="3" fill="#3a3f44" stroke="#888"/>')
text(mx, my + 4, "ESP32-S3", 13, "bold", "#ddd", "middle")
p(f'<circle cx="905" cy="505" r="5" fill="#c8a64a"/>')
text(897, 498, "U.FL", 10, fill="#ddd", anchor="end")

for label, x_mm, y_mm, color, dx, anchor in [
    ("PWR", 14.9, 11.9, "#3c3", 22, "middle"),
    ("SAFE", 36.1, 48.75, "#3c3", 0, "middle"),
    ("FAULT", 62.05, 55.41, "#e33", 0, "middle"),
]:
    x, y = mm(x_mm, y_mm)
    p(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5" fill="{color}" stroke="#fff" stroke-width="1"/>')
    text(x + dx, y + (4 if dx else 18), label, 10, fill="#fff", anchor=anchor)

for label, x_mm, y_mm in [("EN", 66.088, 27.177), ("BOOT", 47.7, 55.95)]:
    x, y = mm(x_mm, y_mm)
    p(f'<rect x="{x - 7:.1f}" y="{y - 7:.1f}" width="14" height="14" fill="#666" stroke="#ddd"/>')
    text(x, y + 20, label, 10, fill="#fff", anchor="middle")

connector(*j["J1"], 2, True)
text(j["J1"][0] - 8, j["J1"][1] + 30, "J1 BATT 20-58V", 11, "bold", "#fff")
connector(*j["J15"], 2, True)
text(j["J15"][0] + 14, j["J15"][1] + 4, "J15 E-STOP", 11, "bold", "#fff")
connector(*j["J4"], 2, True)
text(j["J4"][0] + 14, j["J4"][1] + 4, "J4 ESC LOCK", 11, "bold", "#fff")
for ref, pins, name in [("J7", 3, "ESC THR"), ("J5", 2, "BRAKE"), ("J12", 3, "SPEED"),
                        ("J6", 3, "PEDAL"), ("J13", 3, "AUX"), ("J2", 0, "USB"), ("J14", 4, "UART")]:
    x, y = j[ref]
    if pins:
        connector(x, y, pins, False)
    else:
        p(f'<rect x="{x - 15:.1f}" y="{y - 8:.1f}" width="30" height="16" rx="6" fill="#ccc" stroke="#fff"/>')
    text(x, y - 32, ref, 11, "bold", "#fff", "middle")
    text(x, y - 18, name, 10, "bold", "#fff", "middle")
for ref, name in [("J8", "J8 SONAR F"), ("J9", "J9 SONAR R")]:
    x, y = j[ref]
    connector(x, y, 4, True)
    text(x - 14, y + 4, name, 11, "bold", "#fff", "end")
connector(*j["J3"], 4, False)
text(j["J3"][0], j["J3"][1] + 26, "J3 I2C", 11, "bold", "#fff", "middle")

MONO = [0, 70, 150]
box(60, 160, 360, 170, "Battery, 48 V (13S, 54.6 V full)", [
    (["+", "battery +", "J1 pin 1"], [0, 30, 190]),
    (["-", "battery -", "J1 pin 2"], [0, 30, 190]),
    "",
    "Take + from after the buggy's main fuse",
    "and switch. 0.5 mm² (20 AWG) wire is plenty:",
    "the board draws about 0.1 A.",
], RED)

box(140, 400, 280, 180, "E-stop button", [
    "Normally closed (opens when pressed).",
    "Its two wires go to J15 E-STOP pins 1",
    "and 2, either way round.",
    "!Carries battery voltage.",
    "Optional: wire the old key switch in",
    "series with it.",
], RED)

box(60, 790, 480, 290, "Motor controller (ESC)", [
    "!Power lock wire (the thin key switch wire)",
    (["lock wire", "J4 ESC LOCK pin 1"], [0, 150]),
    (["key switch +", "cap it off: live battery +"], [0, 150]),
    "J4 pin 2 is ground, only if your lock input has one.",
    "",
    "!Throttle plug (unplug the pedal from it)",
    (["signal", "J7 ESC THR pin 3"], [0, 150]),
    (["ground", "J7 pin 2"], [0, 150]),
    (["+5 V", "cap it off, do not connect"], [0, 150]),
    "",
    "!Brake plug (low-level e-brake input)",
    (["signal", "J5 BRAKE pin 1"], [0, 150]),
    (["ground", "J5 pin 2"], [0, 150]),
], AMBER)

box(790, 890, 165, 175, "Speed sensor", [
    (["+5V", "pin 1"], [0, 60]),
    (["GND", "pin 2"], [0, 60]),
    (["out", "pin 3"], [0, 60]),
    "5 V Hall sensor,",
    "magnet on a wheel",
], TEAL)

box(970, 890, 165, 175, "Pedal", [
    (["red", "pin 1"], [0, 70]),
    (["black", "pin 2"], [0, 70]),
    (["green", "pin 3"], [0, 70]),
    "Hall throttle that",
    "was on the ESC",
], TEAL)

box(1150, 890, 165, 175, "AUX switches", [
    (["switch 1", "pin 1"], [0, 80]),
    (["switch 2", "pin 2"], [0, 80]),
    (["common", "pin 3"], [0, 80]),
    "Each switch closes",
    "to common (ground)",
], TEAL)

box(1330, 890, 165, 175, "USB-C", [
    "Laptop, for",
    "firmware updates.",
    "Not a power input",
    "for driving.",
], GREY, True)

box(1510, 890, 180, 175, "Serial console", [
    "3.3 V USB serial",
    (["GND", "pin 1"], [0, 92]),
    (["adapter TX", "pin 3"], [0, 92]),
    (["adapter RX", "pin 4"], [0, 92]),
    "Pin 2 (3.3 V): empty",
], GREY, True)

for (y, title, ref) in [(300, "Front ultrasonic sensor", "J8"), (460, "Rear ultrasonic sensor", "J9")]:
    box(1300, y, 390, 140, title, [
        (["VCC", f"{ref} pin 1"], [0, 70]),
        (["Trig", f"{ref} pin 2"], [0, 70]),
        (["Echo", f"{ref} pin 3"], [0, 70]),
        (["GND", f"{ref} pin 4"], [0, 70]),
    ], TEAL)
    text(1530, y + 60, "5 V sensor:", 13)
    text(1530, y + 79, "HC-SR04 or", 13)
    text(1530, y + 98, "JSN-SR04T", 13)

box(1080, 160, 210, 100, "2.4 GHz antenna", [
    "U.FL plug onto the ESP32.",
    "Mount it outside metal.",
], GREY, True)

box(720, 160, 300, 90, "I2C expansion, optional", [
    "Qwiic or STEMMA QT cable, 3.3 V",
], GREY, True)

text(40, H - 30, "Diagram matches the board layout of the current design files. If a label on your board differs, trust the board.", 13, fill="#555")

p("</svg>")
open(Path(__file__).with_name("wiring.svg"), "w").write("\n".join(out))
