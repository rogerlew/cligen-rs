#!/usr/bin/env python3
"""Independent nearest-station oracle for SPEC-STATION-DB acceptance.

Independent of the Rust implementation in both halves: catalog rows
are read with python's sqlite3, distance is an independently written
haversine (R = 6371.0088 km). Two modes:

  nearest-oracle.py generate <db-root>            # emit expected.json
  nearest-oracle.py compare  <cache-root> <cligen-binary>
                                                  # run cligen, diff

`generate` reads the original python-produced catalogs from
<db-root> (the jimf-cligen532/db tree). `compare` runs
`cligen stations nearest --json` per case against a synced cache and
asserts id order matches exactly and distances agree within 1e-4 km.
Exit 0 = all rows match.
"""

import json
import math
import os
import sqlite3
import subprocess
import sys

R = 6371.0088

# (collection, catalog file, query lat, query lon) — 7 fixed points
# spanning all five collections (au uses east-positive longitudes as
# of payload 2026.07.1).
CASES = [
    ("us-2015", "2015_stations.db", 44.97, -116.28),
    ("us-2015", "2015_stations.db", 46.73, -117.00),
    ("us-legacy", "stations.db", 46.73, -117.00),
    ("ghcn-intl", "ghcn_stations.db", -30.58, 152.11),
    ("ghcn-intl", "ghcn_stations.db", 48.0, 11.0),
    ("au", "au_stations.db", -37.5, 145.5),
    ("chile", "chile.db", -36.7, -72.4),
]

EXPECTED = os.path.join(os.path.dirname(__file__), "expected.json")


def haversine(lat1, lon1, lat2, lon2):
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def generate(db_root):
    out = []
    for name, db, qlat, qlon in CASES:
        con = sqlite3.connect(os.path.join(db_root, db))
        rows = [
            (par, haversine(qlat, qlon, lat, lon))
            for par, lat, lon in con.execute(
                "select par, latitude, longitude from stations"
            )
        ]
        rows.sort(key=lambda r: (r[1], r[0]))
        out.append(
            {
                "collection": name,
                "lat": qlat,
                "lon": qlon,
                "top": [{"id": p, "km": round(d, 6)} for p, d in rows[:5]],
            }
        )
    with open(EXPECTED, "w") as handle:
        json.dump(out, handle, indent=1)
        handle.write("\n")
    print(f"wrote {EXPECTED}")


def compare(cache_root, binary):
    expected = json.load(open(EXPECTED))
    env = dict(os.environ, CLIGEN_DATA_DIR=cache_root)
    failures = 0
    for case in expected:
        result = subprocess.run(
            [
                binary, "stations", "nearest",
                "--lat", str(case["lat"]), "--lon", str(case["lon"]),
                "--collection", case["collection"], "-n", "5", "--json",
            ],
            env=env, capture_output=True, text=True, check=True,
        )
        rows = json.loads(result.stdout)
        for got, want in zip(rows, case["top"]):
            if got["id"] != want["id"] or abs(got["distance_km"] - want["km"]) > 1e-4:
                failures += 1
                print("MISMATCH", case, got["id"], want["id"],
                      got["distance_km"], want["km"])
        print(f'{case["collection"]} @ ({case["lat"]},{case["lon"]}): '
              f'nearest={rows[0]["id"]} {rows[0]["distance_km"]:.3f} km')
    print("failures:", failures)
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    if sys.argv[1] == "generate":
        generate(sys.argv[2])
    elif sys.argv[1] == "compare":
        compare(sys.argv[2], sys.argv[3])
    else:
        sys.exit(__doc__)
