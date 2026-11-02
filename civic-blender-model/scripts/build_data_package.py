"""Collect every Blender-model record from a devteam-del/civic checkout into
this folder: version register, key metrics, open issues, official sources,
report index, registration comparison and a raw snapshot of the files.

Usage (from the repository root):
    python3 civic-blender-model/scripts/build_data_package.py /path/to/civic

The civic checkout needs its git history (for report dates). Nothing here
opens a .blend file; every number is copied from a report already committed
to civic, and each row names that report.
"""
import collections
import csv
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys

CIVIC = os.path.abspath(sys.argv[1])
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(HERE, "data")
SNAP = os.path.join(HERE, "snapshot")
os.makedirs(DATA, exist_ok=True)


def git(*args):
    return subprocess.run(["git", "-C", CIVIC, *args], capture_output=True,
                          text=True, check=True).stdout


HEAD = git("rev-parse", "HEAD").strip()
TRACKED = git("ls-files", "-z").split("\0")
TRACKED = [p for p in TRACKED if p]

# Files that belong to the Blender model work.
SNAPSHOT_FILES = [p for p in TRACKED if p.startswith("reconstruction/")] + [
    "src/blender/export_site_model.py",
    "src/blender/export_site_model_part2.py",
    "src/measure_blend_model.py",
    "src/register_blend_model.py",
    "src/config.py",
    "CLAUDE.md",
    "README.md",
]


def load(rel):
    with open(os.path.join(CIVIC, rel), encoding="utf-8") as fh:
        return json.load(fh)


def write_csv(name, rows, fields):
    with open(os.path.join(DATA, name), "w", newline="", encoding="utf-8-sig") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    print(f"{name}: {len(rows)} rows")


# --------------------------------------------------------------- versions --
HEX = re.compile(r"[0-9a-f]{64}")


def walk_hashes(x, rel, out):
    if isinstance(x, dict):
        blend = next((v for v in x.values()
                      if isinstance(v, str) and v.lower().endswith(".blend")), None)
        sha = next((v for k, v in x.items() if isinstance(v, str)
                    and HEX.fullmatch(v) and "sha" in k.lower()), None)
        size = next((v for k, v in x.items() if isinstance(v, (int, float))
                     and ("size" in k.lower() or "bytes" in k.lower())), None)
        if blend and sha:
            out.append((blend.replace("\\", "/").split("/")[-1], sha, size, rel))
        for v in x.values():
            walk_hashes(v, rel, out)
    elif isinstance(x, list):
        for v in x:
            walk_hashes(v, rel, out)


hashes = []
for rel in TRACKED:
    if rel.endswith(".json"):
        try:
            walk_hashes(load(rel), rel, hashes)
        except (ValueError, UnicodeDecodeError):
            pass
# Two hashes are written only in Markdown, next to the model path.
for rel in ("reconstruction/underground_cavity/README.md",
            "reconstruction/ramp_retaining_walls/README.md"):
    text = open(os.path.join(CIVIC, rel), encoding="utf-8").read()
    name = re.search(r"([A-Za-z0-9_\-]+\.blend)", text).group(1)
    sha = HEX.search(text).group(0)
    hashes.append((name, sha, None, rel))

NAME = re.compile(r"([A-Za-z0-9_\-]+\.blend|site model 市民大道new\.blend)")
mentions = collections.defaultdict(set)
for rel in TRACKED:
    try:
        text = open(os.path.join(CIVIC, rel), encoding="utf-8").read()
    except (UnicodeDecodeError, IsADirectoryError):
        continue
    for m in NAME.finditer(text):
        if m.group(1) != "probe.blend":  # temporary copy used by save checks
            mentions[m.group(1)].add(rel)

versions = collections.OrderedDict()
for name, sha, size, rel in hashes:
    e = versions.setdefault((name, sha), {"bytes": size, "recorded": set()})
    e["recorded"].add(rel)
    if size and not e["bytes"]:
        e["bytes"] = size
for name in mentions:
    if not any(k[0] == name for k in versions):
        versions[(name, "")] = {"bytes": None, "recorded": set()}


def stamp(name):
    m = re.search(r"(20\d{6})(?:_(\d{6}))?", name)
    if not m:
        return ""
    d, t = m.group(1), m.group(2) or ""
    return f"{d[:4]}-{d[4:6]}-{d[6:]}" + (f" {t[:2]}:{t[2:4]}:{t[4:]}" if t else "")


ROLE = {
    "site model 市民大道new.blend": "使用者原始基地模型（~/Desktop）；civic src/ 南北分隔分析讀這個檔",
    "00_original_live_snapshot.blend": "重建工作開始時的原始模型快照",
    "01_civic_georeferenced_rebuild.blend": "重建基準版（已配準 EPSG:3826）",
    "CIVIC_FULL_CORRIDOR_WORKING_20260912.blend": "09-12 全段工作檔（場景 CIVIC_BLOCKS_FACADES_WORKING）",
    "CIVIC_UNDERBRIDGE_WORKING_20260916.blend": "09-16 橋下空間工作檔（使用者選定的簡報場景為基準）",
    "BEFORE_SPAN_HEIGHT_MARKERS_20260922.blend": "09-22 柱間高度標記前的快照",
}
rows = []
for (name, sha), e in versions.items():
    rows.append({
        "file": name,
        "time_from_name": stamp(name),
        "role": ROLE.get(name, "操作前快照" if name.lower().startswith("before") else ""),
        "sha256": sha,
        "bytes": int(e["bytes"]) if e["bytes"] else "",
        "hash_recorded_in": ";".join(sorted(e["recorded"])),
        "mentioned_in_files": len(mentions.get(name, ())),
    })
order = {"site model 市民大道new.blend": 0, "00_original_live_snapshot.blend": 1,
         "01_civic_georeferenced_rebuild.blend": 2}
rows.sort(key=lambda r: (order.get(r["file"], 9), r["time_from_name"] or "9999", r["file"]))
write_csv("model_versions.csv", rows, list(rows[0]))
n_hash = sum(1 for r in rows if r["sha256"])
VERSION_STATS = {"versions": len(rows), "with_sha256": n_hash, "without_sha256": len(rows) - n_hash}

# ------------------------------------------------------------ open issues --
issues = []
for x in load("reconstruction/checkpoints/completion_20260910/all_deferred_issues.json"):
    xy = x.get("xy") or ["", ""]
    detail = x.get("detail", "")
    if "estimated_height_m" in x:
        detail = f"估算高度 {x['estimated_height_m']} m"
    if "source" in x:
        detail = (detail + " " if detail else "") + "來源 " + x["source"]
    issues.append({"source_file": "reconstruction/checkpoints/completion_20260910/all_deferred_issues.json",
                   "date": "2026-09-10", "issue_id": x["id"], "type": x["type"],
                   "name": x.get("name", ""), "x_local": xy[0], "y_local": xy[1],
                   "detail": detail, "status": "deferred"})

hr = load("reconstruction/reports/headroom_checkpoint_0912.json")
for x in hr["issues"]:
    issues.append({"source_file": "reconstruction/reports/headroom_checkpoint_0912.json",
                   "date": "2026-09-12", "issue_id": x["path"], "type": "headroom_obstruction",
                   "name": "", "x_local": "", "y_local": "",
                   "detail": f"命中 {x['hit_count']} 次；最小取樣淨空 {x['minimum_sampled_clearance_m']:.2f} m；"
                             + ", ".join(f"{k}×{v}" for k, v in x["objects"].items()),
                   "status": "open"})

bc = load("reconstruction/reports/bottom_core_edge_conflicts.json")
for core, v in bc.items():
    s = v.get("samples", [])
    issues.append({"source_file": "reconstruction/reports/bottom_core_edge_conflicts.json",
                   "date": "2026-09-12", "issue_id": core, "type": "lowest_floor_support_miss",
                   "name": v.get("floor", ""), "x_local": s[0]["xy"][0] if s else "",
                   "y_local": s[0]["xy"][1] if s else "",
                   "detail": f"{len(s)} 個樓梯取樣點落在估算樓板外", "status": "open"})

for x in load("reconstruction/reports/underbridge_0922/new_model_issues.json"):
    issues.append({"source_file": "reconstruction/reports/underbridge_0922/new_model_issues.json",
                   "date": "2026-09-22", "issue_id": x["id"], "type": "underbridge_model",
                   "name": ";".join(x.get("objects", [])), "x_local": "", "y_local": "",
                   "detail": x["issue"] + "；處理：" + x.get("action", ""), "status": x["status"]})

sp = load("reconstruction/reports/underbridge_0922/span_height_summary.json")
for x in sp["ambiguous_assignments"]:
    issues.append({"source_file": "reconstruction/reports/underbridge_0922/span_height_summary.json",
                   "date": "2026-09-22", "issue_id": x["pier"], "type": "pier_deck_assignment_ambiguous",
                   "name": "", "x_local": "", "y_local": "",
                   "detail": "候選橋面：" + ", ".join(f"{c['deck']}({c['distance']:.2f} m)" for c in x["candidates"]),
                   "status": "open"})
for x in sp["boundary_review"]:
    issues.append({"source_file": "reconstruction/reports/underbridge_0922/span_height_summary.json",
                   "date": "2026-09-22", "issue_id": "+".join(x["decks"]), "type": "span_endpoint_review",
                   "name": "", "x_local": "", "y_local": "", "detail": x["reason"], "status": "open"})
gaps = load("reconstruction/reports/underbridge_0922/span_height_coverage_gaps.json")
for p in gaps["piers_not_in_any_candidate_span"]:
    issues.append({"source_file": "reconstruction/reports/underbridge_0922/span_height_coverage_gaps.json",
                   "date": "2026-09-22", "issue_id": p, "type": "pier_not_in_span",
                   "name": "", "x_local": "", "y_local": "", "detail": "未組成任何候選跨段", "status": "open"})
for d in gaps["decks_without_candidate_spans"]:
    issues.append({"source_file": "reconstruction/reports/underbridge_0922/span_height_coverage_gaps.json",
                   "date": "2026-09-22", "issue_id": d, "type": "deck_without_span_measurement",
                   "name": "", "x_local": "", "y_local": "", "detail": "此橋面路徑沒有柱間淨高量測", "status": "open"})
long_spans = [s for s in sp["spans"] if (s.get("plan_length_m") or 0) > 60]
for s in long_spans:
    issues.append({"source_file": "reconstruction/reports/underbridge_0922/span_height_summary.json",
                   "date": "2026-09-22", "issue_id": s["span_id"], "type": "span_longer_than_60m",
                   "name": ";".join(s["decks"]), "x_local": "", "y_local": "",
                   "detail": f"平面跨距 {s['plan_length_m']:.1f} m，需檢查漏柱或誤配", "status": "open"})
write_csv("open_issues.csv", issues, list(issues[0]))
ISSUE_COUNTS = collections.Counter(i["type"] for i in issues)

# -------------------------------------------------------- official sources --
URL = re.compile(r"https?://[^\s)\]\"'<>`，。；、]+")
src = collections.OrderedDict()
for rel in SNAPSHOT_FILES:
    if not rel.endswith((".md", ".json", ".py")):
        continue
    text = open(os.path.join(CIVIC, rel), encoding="utf-8").read()
    for u in URL.findall(text):
        u = u.rstrip(".,")
        e = src.setdefault(u, {"files": set()})
        e["files"].add(rel)
srows = [{"url": u, "domain": re.sub(r"^https?://", "", u).split("/")[0],
          "cited_in_files": len(e["files"]), "first_file": sorted(e["files"])[0]}
         for u, e in src.items()]
srows.sort(key=lambda r: (r["domain"], r["url"]))
write_csv("sources_cited.csv", srows, list(srows[0]))

# ------------------------------------------------------------ report index --
irows = []
for rel in SNAPSHOT_FILES:
    log = git("log", "-1", "--format=%h%x09%ad%x09%s", "--date=short", "--", rel).strip().split("\t")
    p = os.path.join(CIVIC, rel)
    kind = os.path.splitext(rel)[1].lstrip(".") or "file"
    irows.append({"path": rel, "type": kind, "bytes": os.path.getsize(p),
                  "last_commit": log[0] if log else "", "last_commit_date": log[1] if len(log) > 1 else "",
                  "last_commit_subject": log[2] if len(log) > 2 else ""})
write_csv("file_index.csv", irows, list(irows[0]))

# ----------------------------------------------------------- registration --
reg_a = load("reconstruction/archive/registration.json")
ox = reg_a["origin_epsg3826"][0] + reg_a["live_to_twd97"]["translation"][0]
oy = reg_a["origin_epsg3826"][1] + reg_a["live_to_twd97"]["translation"][1]
reg_b = {"tx": 301499.60, "ty": 2770462.78, "scale_check": 0.9998, "rotation_check_deg": 0.07}
dx, dy = reg_b["tx"] - ox, reg_b["ty"] - oy
registration = {
    "note": "兩套都是把模型對到 OpenStreetMap 求出的平移，不是測量控制點。兩者的建物分量數都是 19,592，"
            "應是同一個原始模型；平移量相差約 5.2 m，本彙整沒有判定哪一套較準。",
    "reconstruction_registration": {
        "source": "reconstruction/archive/registration.json",
        "method": reg_a["registration_method"],
        "applied_origin_epsg3826": [ox, oy],
        "scale": reg_a["live_to_twd97"]["scale"],
        "rotation_degrees": reg_a["live_to_twd97"]["rotation_degrees"],
        "building_components": reg_a["building_components"],
        "osm_buildings": reg_a["osm_buildings"],
        "matches_within_20m": reg_a["building_matches_within20m"],
        "match_median_m": reg_a["building_match_median_m"],
        "holdout_count": reg_a["holdout_count"],
        "holdout_median_m": reg_a["holdout_median_m"],
        "holdout_p90_m": reg_a["holdout_p90_m"],
    },
    "severance_pipeline_registration": {
        "source": "CLAUDE.md；src/register_blend_model.py（結果檔 data/processed/blend_georef.json 未進版控）",
        "method": "對模型內 OSM_Major_Roads 點雲做最近鄰擬合，只解平移；再用相似轉換驗證",
        **reg_b,
    },
    "difference_m": {"dx": round(dx, 3), "dy": round(dy, 3), "distance": round((dx * dx + dy * dy) ** 0.5, 2)},
}
with open(os.path.join(DATA, "registration_comparison.json"), "w", encoding="utf-8") as fh:
    json.dump(registration, fh, ensure_ascii=False, indent=2)
print("registration difference", registration["difference_m"])

# --------------------------------------------------------------- snapshot --
if os.path.isdir(SNAP):
    shutil.rmtree(SNAP)
sums = {}
# civic's CLAUDE.md holds instructions for sessions working in civic itself;
# under its own name it would be auto-loaded as instructions for this folder.
RENAMED = {"CLAUDE.md": "CLAUDE.civic.md"}
for rel in SNAPSHOT_FILES:
    dst = os.path.join(SNAP, RENAMED.get(rel, rel))
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copyfile(os.path.join(CIVIC, rel), dst)
    sums[rel] = hashlib.sha256(open(dst, "rb").read()).hexdigest()
with open(os.path.join(SNAP, "SNAPSHOT.json"), "w", encoding="utf-8") as fh:
    json.dump({"source_repository": "https://github.com/devteam-del/civic",
               "source_commit": HEAD, "files": len(sums), "renamed_in_snapshot": RENAMED,
               "sha256": sums},
              fh, ensure_ascii=False, indent=1)
print(f"snapshot: {len(sums)} files from civic {HEAD[:7]}")

with open(os.path.join(DATA, "build_stats.json"), "w", encoding="utf-8") as fh:
    json.dump({"civic_commit": HEAD, "model_versions": VERSION_STATS,
               "open_issue_counts": dict(ISSUE_COUNTS.most_common()),
               "sources_cited": len(srows), "files_indexed": len(irows)},
              fh, ensure_ascii=False, indent=2)
