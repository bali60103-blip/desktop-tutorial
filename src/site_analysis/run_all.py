"""跑完整條基地分析管線:邊界 -> 各項分析 -> 出圖。"""

import build_overview_map
import build_site_boundary
import building_stats
import analysis1_green_volume
import analysis2_block_character
import analysis3_riverside_connectivity
import analysis4_crowd_hotspots
import analysis5_permeability
import analysis6_park_profiles
import analysis8_osm_poi
import analysis7_park_neighborhood
import analysis9_building_activity
import map1_green_volume
import map2_block_character
import map5_permeability
import map7_park_neighborhood
import render_site_figure_ground
import render_activity_coverage

STEPS = [
    ("建立基地邊界", build_site_boundary.main),
    ("分析① 綠帶體量", analysis1_green_volume.main),
    ("分析② 街區特色(土地使用分區)", analysis2_block_character.main),
    ("建物樓高/密度細部統計(依賴分析②的分區裁切輸出)", building_stats.main),
    ("分析③ 綠帶連結延平河濱公園可行性", analysis3_riverside_connectivity.main),
    ("分析④ 人潮聚集地點", analysis4_crowd_hotspots.main),
    ("分析⑤ 綠帶滲透性(Sennett/Gehl/Jacobs)", analysis5_permeability.main),
    ("分析⑥ 公園基本資料共通性", analysis6_park_profiles.main),
    ("分析⑧ OSM POI(餐飲/公園/辦公室/零售,分析⑦要用)", analysis8_osm_poi.main),
    ("分析⑦ 公園設施類型 x 400m 連結設施/人潮", analysis7_park_neighborhood.main),
    ("分析⑨ 建築量體商業活動密度(依賴分析⑦⑧)", analysis9_building_activity.main),
    ("產生總覽地圖", build_overview_map.main),
    ("出圖① 綠帶體量", map1_green_volume.main),
    ("出圖② 街區特色", map2_block_character.main),
    ("出圖⑤ 綠帶滲透性", map5_permeability.main),
    ("出圖⑦ 公園設施類型連結", map7_park_neighborhood.main),
    ("基地紋理圖(figure-ground)", render_site_figure_ground.main),
    ("建築活動密度覆蓋圖", render_activity_coverage.main),
]


def main():
    total = len(STEPS)
    for i, (label, fn) in enumerate(STEPS, 1):
        print(f"\n== {i}/{total} {label} ==")
        fn()


if __name__ == "__main__":
    main()
