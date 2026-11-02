"""Inside Blender, read world-space geometry for support connectivity QA. OUTPUT provided."""
import bpy,json,pathlib
from mathutils import Vector
rows={}
for key,colname in [('supports','07_Piers_legacy_UNVERIFIED'),('decks','04_Elevated_deck_estimated')]:
 rows[key]=[]
 for o in bpy.data.collections[colname].objects:
  if o.type!='MESH':continue
  pts=[list(o.matrix_world@v.co) for v in o.data.vertices]
  rows[key].append({'name':o.name,'vertices':pts,'source':str(o.get('source','')),'confidence':str(o.get('confidence',''))})
pathlib.Path(OUTPUT).write_text(json.dumps(rows));result={'export':OUTPUT,'supports':len(rows['supports']),'decks':len(rows['decks'])}
