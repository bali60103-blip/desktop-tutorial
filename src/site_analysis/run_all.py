"""跑完整條基地分析管線:邊界 -> 四項分析 -> 總覽地圖。"""

import build_overview_map
import build_site_boundary
import analysis1_green_volume
import analysis2_block_character
import analysis3_riverside_connectivity
import analysis4_crowd_hotspots


def main():
    print("== 1/6 建立基地邊界 ==")
    build_site_boundary.main()
    print("\n== 2/6 分析① 綠帶體量 ==")
    analysis1_green_volume.main()
    print("\n== 3/6 分析② 街區特色(土地使用分區) ==")
    analysis2_block_character.main()
    print("\n== 4/6 分析③ 綠帶連結延平河濱公園可行性 ==")
    analysis3_riverside_connectivity.main()
    print("\n== 5/6 分析④ 人潮聚集地點 ==")
    analysis4_crowd_hotspots.main()
    print("\n== 6/6 產生總覽地圖 ==")
    build_overview_map.main()


if __name__ == "__main__":
    main()
