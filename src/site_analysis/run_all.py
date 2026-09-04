"""跑完整條基地分析管線:邊界 -> 四項分析 -> 總覽地圖。"""

import build_overview_map
import build_site_boundary
import building_stats
import analysis1_green_volume
import analysis2_block_character
import analysis3_riverside_connectivity
import analysis4_crowd_hotspots


def main():
    print("== 1/7 建立基地邊界 ==")
    build_site_boundary.main()
    print("\n== 2/7 分析① 綠帶體量 ==")
    analysis1_green_volume.main()
    print("\n== 3/7 分析② 街區特色(土地使用分區) ==")
    analysis2_block_character.main()
    print("\n== 4/7 建物樓高/密度細部統計(依賴分析②的分區裁切輸出) ==")
    building_stats.main()
    print("\n== 5/7 分析③ 綠帶連結延平河濱公園可行性 ==")
    analysis3_riverside_connectivity.main()
    print("\n== 6/7 分析④ 人潮聚集地點 ==")
    analysis4_crowd_hotspots.main()
    print("\n== 7/7 產生總覽地圖 ==")
    build_overview_map.main()


if __name__ == "__main__":
    main()
