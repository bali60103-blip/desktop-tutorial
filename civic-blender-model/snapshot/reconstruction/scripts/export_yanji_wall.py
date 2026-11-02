import bpy,json,pathlib
from mathutils import Vector
o=bpy.data.objects['COMP_延吉_B1_PERIMETER'];r={'name':o.name,'vertices':[list(o.matrix_world@v.co) for v in o.data.vertices],'faces':[list(p.vertices) for p in o.data.polygons]}
pathlib.Path('/tmp/yanji_wall.json').write_text(json.dumps(r));result={'vertices':len(r['vertices']),'faces':len(r['faces'])}
