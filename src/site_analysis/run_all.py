"""跑完整條基地分析管線:邊界 -> 四項分析 -> 總覽地圖。"""

import build_overview_map
import build_site_boundary
import building_stats
import analysis1_green_volume
import analysis2_block_character
import analysis3_riverside_connectivity
import analysis4_crowd_hotspots
import analysis5_permeability
import analysis6_park_profiles
import map1_green_volume
import map2_block_character
import map5_permeability
import render_site_figure_ground


def main():
    print("== 1/12 建立基地邊界 ==")
    build_site_boundary.main()
    print("\n== 2/12 分析① 綠帶體量 ==")
    analysis1_green_volume.main()
    print("\n== 3/12 分析② 街區特色(土地使用分區) ==")
    analysis2_block_character.main()
    print("\n== 4/12 建物樓高/密度細部統計(依賴分析②的分區裁切輸出) ==")
    building_stats.main()
    print("\n== 5/12 分析③ 綠帶連結延平河濱公園可行性 ==")
    analysis3_riverside_connectivity.main()
    print("\n== 6/12 分析④ 人潮聚集地點 ==")
    analysis4_crowd_hotspots.main()
    print("\n== 7/13 分析⑤ 綠帶滲透性(Sennett/Gehl/Jacobs) ==")
    analysis5_permeability.main()
    print("\n== 8/13 分析⑥ 公園基本資料共通性 ==")
    analysis6_park_profiles.main()
    print("\n== 9/13 產生總覽地圖 ==")
    build_overview_map.main()
    print("\n== 10/13 出圖① 綠帶體量 ==")
    map1_green_volume.main()
    print("\n== 11/13 出圖② 街區特色 ==")
    map2_block_character.main()
    print("\n== 12/13 出圖⑤ 綠帶滲透性 ==")
    map5_permeability.main()
    print("\n== 13/13 基地紋理圖(figure-ground) ==")
    render_site_figure_ground.main()


if __name__ == "__main__":
    main()
