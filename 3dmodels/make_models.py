from pathlib import Path

INCH = 2.54
HERE = Path(__file__).parent


def box(x0, y0, z0, x1, y1, z1, color):
    pts = [(x, y, z) for z in (z0, z1) for y in (y0, y1) for x in (x0, x1)]
    pts = [(x / INCH, -y / INCH, z / INCH) for x, y, z in pts]
    faces = [(0, 2, 3, 1), (4, 5, 7, 6), (0, 1, 5, 4), (2, 6, 7, 3), (0, 4, 6, 2), (1, 3, 7, 5)]
    return shape(pts, faces, color)


def cylinder(cx, cy, r, z0, z1, color, sides=24):
    import math
    ring = [(cx + r * math.cos(2 * math.pi * i / sides), cy + r * math.sin(2 * math.pi * i / sides)) for i in range(sides)]
    pts = [(x / INCH, -y / INCH, z0 / INCH) for x, y in ring] + [(x / INCH, -y / INCH, z1 / INCH) for x, y in ring]
    faces = [tuple(reversed(range(sides))), tuple(range(sides, 2 * sides))]
    for i in range(sides):
        j = (i + 1) % sides
        faces.append((i, j, sides + j, sides + i))
    return shape(pts, faces, color)


def shape(pts, faces, color):
    p = ", ".join(f"{x:.5f} {y:.5f} {z:.5f}" for x, y, z in pts)
    f = ", ".join(" ".join(map(str, fc)) + " -1" for fc in faces)
    r, g, b = color
    return (
        "Shape {\n appearance Appearance { material Material { diffuseColor "
        f"{r} {g} {b} }} }}\n geometry IndexedFaceSet {{\n  solid FALSE\n  coord Coordinate {{ point [ {p} ] }}\n"
        f"  coordIndex [ {f} ]\n }}\n}}\n"
    )


def write(name, shapes):
    (HERE / f"{name}.wrl").write_text("#VRML V2.0 utf8\n" + "".join(shapes))


BLACK = (0.08, 0.08, 0.08)
PCB = (0.1, 0.12, 0.2)
METAL = (0.78, 0.78, 0.8)
GOLD = (0.85, 0.7, 0.3)
GLASS = (0.05, 0.05, 0.07)
WHITE = (0.9, 0.9, 0.88)


write("SW_PUSH-12mm", [
    box(0.25, -3.5, 0.0, 12.25, 8.5, 3.6, BLACK),
    box(0.6, -3.15, 3.6, 11.9, 8.15, 3.9, METAL),
    cylinder(6.25, 2.5, 3.6, 3.9, 7.3, BLACK),
])

write("Buzzer_Murata_PKLCS1212E", [
    box(-6.0, -6.0, 0.0, 6.0, 6.0, 3.0, BLACK),
    cylinder(0.0, 0.0, 0.9, 3.0, 3.02, (0.02, 0.02, 0.02)),
])

holes = [(-9.65, 0.0), (24.89, 0.0), (-9.65, 25.15), (24.89, 25.15)]
oled = [
    box(-1.27, -1.27, 0.0, 16.51, 1.27, 2.5, BLACK),
    box(-12.1, -2.41, 2.5, 27.4, 27.59, 4.1, (0.1, 0.3, 0.75)),
    box(-9.6, 4.79, 4.1, 26.2, 21.89, 5.6, GLASS),
    box(-6.9, 5.7, 5.6, 23.1, 21.0, 5.61, (0.02, 0.02, 0.03)),
]
for i in range(7):
    x = 2.54 * i
    oled.append(box(x - 0.32, -0.32, -3.0, x + 0.32, 0.32, 4.6, GOLD))
for hx, hy in holes:
    oled.append(cylinder(hx, hy, 2.5, 0.0, 2.5, WHITE, sides=6))
    oled.append(cylinder(hx, hy, 2.2, 4.1, 5.7, METAL))
write("OLED_Waveshare_1.3in_C", oled)
