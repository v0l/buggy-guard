from pathlib import Path

from build123d import import_step

HERE = Path(__file__).parent
PCB_TOP = 1.62
FIT = 0.1
MOUNTS = [(4.0, -62.0), (56.0, -62.0)]
SKIP = {"JST_B2B_PH_K"}


def touching(a, b):
    return all(a[k] <= b[k + 3] and b[k] <= a[k + 3] for k in range(3))


def merged(boxes):
    boxes = [list(b) for b in boxes]
    changed = True
    while changed:
        changed = False
        for i in range(len(boxes)):
            for j in range(i + 1, len(boxes)):
                if touching(boxes[i], boxes[j]):
                    a, b = boxes[i], boxes.pop(j)
                    boxes[i] = [min(a[k], b[k]) for k in range(3)] + [max(a[k], b[k]) for k in range(3, 6)]
                    changed = True
                    break
            if changed:
                break
    return boxes


board = import_step(str(HERE.parent / "pendant.step"))
pcb = next(c for c in board.children if c.label == "pendant_PCB").bounding_box()
lines = [
    "plane XY",
    f"rect {pcb.size.X:.3f} {pcb.size.Y:.3f} r=3 at={pcb.center().X:.3f},{pcb.center().Y:.3f}",
    f"pcb: extrude {PCB_TOP}",
    "plane pcb.end",
    *(f"mount{i + 1}: hole 2.7 {x},{y}" for i, (x, y) in enumerate(MOUNTS)),
]
switches = 0
boxes = []
for child in board.children:
    if child.label in SKIP or child.label == "pendant_PCB":
        continue
    bb = child.bounding_box()
    lo, hi = bb.min, bb.max
    if child.label == "SW_PUSH-12mm":
        switches += 1
        cx, cy = bb.center().X, bb.center().Y
        lines += [
            f"plane XY offset={PCB_TOP}",
            f"rect {12 + 2 * FIT} {12 + 2 * FIT} at={cx:.3f},{cy:.3f}",
            f"sw{switches}: extrude 3.6",
            f"plane sw{switches}.end",
            f"rect {11.3 + 2 * FIT} {11.3 + 2 * FIT} at={cx:.3f},{cy:.3f}",
            f"top{switches}: extrude 0.3",
            f"plane top{switches}.end",
            f"circle {7.2 + 2 * FIT} at={cx:.3f},{cy:.3f}",
            f"plunger{switches}: extrude 3.4",
        ]
        continue
    if hi.Z > PCB_TOP + 0.01:
        boxes.append((lo.X - FIT, lo.Y - FIT, PCB_TOP, hi.X + FIT, hi.Y + FIT, hi.Z + FIT))
    if lo.Z < -0.01:
        boxes.append((lo.X - FIT, lo.Y - FIT, lo.Z - FIT, hi.X + FIT, hi.Y + FIT, 0.0))
for x0, y0, z0, x1, y1, z1 in merged(boxes):
    up = z0 >= PCB_TOP
    lines += [
        f"plane XY offset={z0 if up else z1:.3f}",
        f"rect {x1 - x0:.3f} {y1 - y0:.3f} at={(x0 + x1) / 2:.3f},{(y0 + y1) / 2:.3f}",
        f"extrude {(z1 - z0) if up else (z0 - z1):.3f}",
    ]
lines += ["color #1f6f3f"]
(HERE / "pendant-board.gcad").write_text("\n".join(lines) + "\n")
