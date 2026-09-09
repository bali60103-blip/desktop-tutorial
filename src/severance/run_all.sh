#!/bin/sh
# Run the whole severance pipeline in dependency order.
# The last two stages feed measured values back into the project's other two
# standalone tools (boundary_comparison.html, boundary_overlay_map.html), so a
# rerun keeps all three tools consistent with the same numbers.
#   cd src/severance && sh run_all.sh
# Every stage is independently re-runnable; each writes JSON to
# ../../data/processed/ so a later stage can be verified on its own.
#
# NOT included here: the two Blender export scripts under blender/. Those must
# run inside Blender and only need re-running when the .blend model changes:
#   /Applications/Blender.app/Contents/MacOS/Blender -b "$BLEND_MODEL" \
#       --python blender/export_site_model.py
set -e
for stage in \
  extract_osm \
  build_axis \
  measure_permeability \
  measure_detour \
  measure_structure \
  measure_industry \
  measure_gradient \
  register_blend_model \
  measure_blend_model \
  build_verdict \
  build_bundle \
  build_overlay_tool \
  build_boundary_rows \
  build_overlay_strip
do
  echo "=== $stage ==="
  python3 "$stage.py"
done
