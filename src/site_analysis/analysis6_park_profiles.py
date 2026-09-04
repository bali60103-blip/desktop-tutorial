"""⑥ 對照基地內各公園的共通性 —— 用臺北市公園處官方「公園基本資料」點位資料
(818 筆,使用者提供,data/raw/parks_basic_info.json)。

這份資料是公園管理處官方登記的公園(pm_type 含「公園」「綠地」「兒童遊戲場」等
分類),跟先前 J0301/L01015/L02015 等都市計畫圖層是不同來源、不同分類邏輯,
不強行合併,只用這份資料本身做基地內公園的共通性分析:
- 公園類型(pm_type)分布
- 闢建年代分布
- 設施關鍵字(運動/遊憩/服務/遊具,逗號分隔文字,拆解後計次)
- 生態旗標(pm_ecology)比例
- 面積分布
"""

import json
import os
from collections import Counter

from shapely.geometry import Point, shape
from shapely.ops import transform

from clip_utils import site_boundary_3826
from config import PROCESSED_DIR, RAW_DIR
from gis_utils import load_geojson, wgs84_to_proj


def split_keywords(text):
    if not text:
        return []
    for sep in ["、", "，", "/", "\n", "；"]:
        text = text.replace(sep, ",")
    return [t.strip() for t in text.split(",") if t.strip()]


def main():
    os.makedirs(PROCESSED_DIR, exist_ok=True)
    d = load_geojson(os.path.join(RAW_DIR, "parks_basic_info.json"))

    boundary = site_boundary_3826()
    in_site = []
    no_geom = 0
    for f in d["features"]:
        if not f.get("geometry") or not f["geometry"].get("coordinates"):
            no_geom += 1
            continue
        lon, lat = f["geometry"]["coordinates"]
        x, y = wgs84_to_proj(lon, lat)
        if boundary.contains(Point(x, y)):
            in_site.append(f)

    with open(os.path.join(PROCESSED_DIR, "parks_basic_info_clipped.geojson"), "w", encoding="utf-8") as f:
        json.dump({"type": "FeatureCollection", "features": in_site}, f, ensure_ascii=False)

    type_counter = Counter()
    year_counter = Counter()
    sports_counter = Counter()
    recreation_counter = Counter()
    service_counter = Counter()
    playeq_counter = Counter()
    ecology_count = 0
    areas = []
    park_list = []

    for f in in_site:
        p = f["properties"]
        type_counter[p.get("pm_type") or "未分類"] += 1
        year = p.get("pm_const_year")
        if year:
            decade = f"{str(year)[:3]}0年代" if str(year).isdigit() and len(str(year)) == 4 else year
            year_counter[decade] += 1
        # 用「這座公園有沒有這項設施」(set)計次,不是逐字串出現次數——像龍圖公園
        # pm_playeq 欄位把每一件遊具都列出來(同一項目可能重複列上百次,因為公園
        # 內有多組同款遊具),用原始出現次數算會被少數超大公園的落落長清單洗版,
        # 完全蓋過「有多少座公園共同擁有這項設施」這個真正要問的問題。
        for kw in set(split_keywords(p.get("pm_sports"))):
            sports_counter[kw] += 1
        for kw in set(split_keywords(p.get("pm_recreation"))):
            recreation_counter[kw] += 1
        for kw in set(split_keywords(p.get("pm_service"))):
            service_counter[kw] += 1
        for kw in set(split_keywords(p.get("pm_playeq"))):
            playeq_counter[kw] += 1
        if p.get("pm_ecology"):
            ecology_count += 1
        area = p.get("pm_LandPublicArea")
        if area:
            areas.append(area)
        park_list.append(
            {
                "name": p.get("pm_name"),
                "type": p.get("pm_type"),
                "const_year": p.get("pm_const_year"),
                "area_m2": area,
                "unit": p.get("pm_unit"),
                "sports": p.get("pm_sports"),
                "recreation": p.get("pm_recreation"),
                "service": p.get("pm_service"),
                "ecology": bool(p.get("pm_ecology")),
            }
        )

    result = {
        "CAVEAT": (
            "這份公園基本資料(pm_ 開頭欄位)是公園處官方登記資料,跟先前都市計畫"
            "分區圖層(J0301/L01015/L02015 等)是不同來源、不同分類方式,沒有互相"
            "核對比對,兩邊筆數/範圍不會完全一致,是正常的——不同機關的資料本來就"
            "不會完全對齊,不強行調和。"
        ),
        "parks_in_site_count": len(in_site),
        "parks_total_citywide": len(d["features"]),
        "parks_citywide_missing_geometry": no_geom,
        "park_list": sorted(park_list, key=lambda x: -(x["area_m2"] or 0)),
        "type_distribution": dict(type_counter.most_common()),
        "const_year_distribution": dict(sorted(year_counter.items())),
        "avg_area_m2": round(sum(areas) / len(areas), 1) if areas else None,
        "median_area_m2": round(sorted(areas)[len(areas) // 2], 1) if areas else None,
        "ecology_flagged_count": ecology_count,
        "ecology_flagged_pct": round(100 * ecology_count / len(in_site), 1) if in_site else None,
        "common_sports_facilities_park_count": sports_counter.most_common(15),
        "common_recreation_facilities_park_count": recreation_counter.most_common(15),
        "common_service_facilities_park_count": service_counter.most_common(15),
        "common_play_equipment_park_count_UNRELIABLE": playeq_counter.most_common(15),
        "facility_counts_are": "有幾座公園擁有這項設施(每座公園最多算1次),不是設施出現的總次數",
        "playeq_field_quality_warning": (
            "pm_playeq 這個欄位的原始資料本身有問題:160座基地內公園裡,有非空值的110筆"
            "pm_playeq 文字**全部以一模一樣的開頭字串起始**(彈跳床,搖滾盤,攀爬組,磨石滑梯…"
            "這一長串),疑似原始資料匯出/建檔時把某種共用清單誤植/累加進每一筆紀錄,不是"
            "每座公園真的都有這些遊具。這個欄位的逐項統計不可信,common_play_equipment_"
            "park_count_UNRELIABLE 只留供參考,**不要拿來當作論述依據**,除非另外核實。"
        ),
    }
    with open(os.path.join(PROCESSED_DIR, "analysis6_summary.json"), "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"parks in site: {len(in_site)}")
    print("type_distribution:", result["type_distribution"])
    print("common_sports_facilities_park_count:", result["common_sports_facilities_park_count"][:8])
    print("common_recreation_facilities_park_count:", result["common_recreation_facilities_park_count"][:8])
    print("common_service_facilities_park_count:", result["common_service_facilities_park_count"][:8])
    print("common_play_equipment_UNRELIABLE (see warning):", result["common_play_equipment_park_count_UNRELIABLE"][:5])
    print("ecology_flagged_pct:", result["ecology_flagged_pct"])
    print("avg_area_m2:", result["avg_area_m2"], "median:", result["median_area_m2"])


if __name__ == "__main__":
    main()
