import csv
import math
import re
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SHEETS = ["power", "mcu", "safety", "io"]
OUT = ROOT / "docs" / "bom-order.csv"


def parts():
    seen = {}
    for sheet in SHEETS:
        for p in tomllib.loads((ROOT / f"{sheet}.sch.toml").read_text()).get("parts", []):
            ref = p["ref"]
            fields = p.get("fields", {})
            if ref in seen:
                seen[ref]["fields"] = {**fields, **seen[ref]["fields"]}
                continue
            seen[ref] = {"ref": ref, "value": p.get("value", ""), "fields": fields}
    return [
        p
        for p in seen.values()
        if p["fields"].get("assembly") != "no" and not p["ref"].startswith("H")
    ]


def natural(ref):
    m = re.match(r"([A-Z]+)(\d+)", ref)
    return (m.group(1), int(m.group(2))) if m else (ref, 0)


def order_qty(per_board, boards, small, spare):
    need = per_board * boards
    if small:
        return max(10, math.ceil((need + 5) / 10) * 10)
    return need + spare


def spare(refs):
    return 1 if any(re.match(r"(D|Q|U(?!3$)|F[23]$)", r) for r in refs) else 0


def main():
    boards = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    groups = {}
    for p in parts():
        f = p["fields"]
        key = (f.get("mfr", ""), f.get("mpn", ""))
        g = groups.setdefault(key, {"refs": [], "values": [], "lcsc": f.get("lcsc")})
        g["refs"].append(p["ref"])
        if p["value"] not in g["values"]:
            g["values"].append(p["value"])
    rows = []
    for (mfr, mpn), g in groups.items():
        refs = sorted(g["refs"], key=natural)
        small = mpn.startswith(("RC0603", "CL10"))
        source = f"LCSC {g['lcsc']}, not stocked at Mouser" if g["lcsc"] else "Mouser"
        qty = order_qty(len(refs), boards, small, spare(refs))
        rows.append([mfr, mpn, qty, len(refs), " ".join(refs), "/".join(g["values"]), source])
    rows.sort(key=lambda r: natural(r[4].split()[0]))

    xh = {2: 0, 3: 0, 4: 0}
    for (mfr, mpn), g in groups.items():
        m = re.match(r"B(\d)B-XH-A", mpn)
        if m:
            xh[int(m.group(1))] += len(g["refs"])
    contacts = sum(n * count for n, count in xh.items())
    extras = [
        ["Molex", "1461530100", boards, 1, "U3", "2.4 GHz flex antenna, U.FL, 100 mm lead", "Mouser"],
        *[
            ["JST", f"XHP-{n}", count * boards, count, "harness", f"XH {n}-way plug housing", "Mouser"]
            for n, count in xh.items()
            if count
        ],
        ["JST", "SXH-001T-P0.6", contacts * boards + 10, contacts, "harness", "XH crimp contact, 26-22 AWG", "Mouser"],
    ]

    with OUT.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Manufacturer", "Manufacturer Part Number", "Quantity", "Per Board", "Designators", "Value", "Source"])
        w.writerows(rows + extras)
    print(f"{OUT.relative_to(ROOT)}: {len(rows)} board lines, {len(extras)} extras, {boards} board(s)")


main()
