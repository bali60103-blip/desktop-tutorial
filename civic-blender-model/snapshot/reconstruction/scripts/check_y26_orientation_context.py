import json,math
from pathlib import Path
from pyproj import Transformer
from shapely.geometry import Polygon,LineString
from shapely import affinity
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
root=Path('/Users/ktlu/Desktop/Civic_Rebuild_20260909_201934');out=root/'Y26Orientation';p=json.load(open(out/'orientation.json'));ctx=json.load(open(out/'osm_context.json'));reg=json.load(open(root/'registration.json'));fit=reg['live_to_twd97'];ang=math.radians(fit['rotation_degrees']);org=[reg['origin_epsg3826'][i]+fit['translation'][i] for i in range(2)];tr=Transformer.from_crs(4326,3826,always_xy=True)
def live(q):
 x,y=tr.transform(*q);x-=org[0];y-=org[1];return((math.cos(ang)*x+math.sin(ang)*y)/fit['scale'],(-math.sin(ang)*x+math.cos(ang)*y)/fit['scale'])
anchor=p['anchor_live_xy'];models={}
for name,key in [('A: original estimate','original_axis_degrees_from_live_x'),('B: building-axis estimate','alternative_axis_degrees_from_live_x')]:
 g=affinity.rotate(Polygon([(-2.4,-2.9),(9,-2.9),(9,2.9),(-2.4,2.9)]),p[key],origin=(0,0));models[name]=affinity.translate(g,*anchor)
lines=[];buildings=[]
for w in ctx['ways']:
 t=w['tags'];xy=[live(q) for q in w['coords']]
 if t.get('building'):buildings.append((w['id'],Polygon(xy)))
 elif 'highway' in t and t.get('layer','0')=='0' and t.get('indoor')!='yes' and t['highway'] in ['tertiary','service','footway','pedestrian']:lines.append((w['id'],t,LineString(xy)))
checks=[]
for label,g in models.items():
 checks.append({'variant':label,'building_overlaps':[bid for bid,b in buildings if g.intersection(b).area>.01],'surface_line_distances_m':[{'osm_id':wid,'type':t['highway'],'distance':g.distance(l),'intersects':g.intersects(l)} for wid,t,l in lines],'limit':'OSM line clearance only, no road width or sidewalk-edge proof; canopy dimensions estimated'})
fig,ax=plt.subplots(figsize=(11,8));
for bid,g in buildings:
 x,y=g.exterior.xy;ax.fill(x,y,color='#e5e7eb',edgecolor='#88919e',linewidth=1)
 if bid==p['reference_building_osm_id']:ax.text(g.centroid.x,g.centroid.y,'Reference building\nOSM '+str(bid),ha='center',va='center',fontsize=8)
for wid,t,l in lines:
 x,y=l.xy;ax.plot(x,y,color='#687581',linewidth=2,linestyle='--' if t.get('footway')=='crossing' else '-');mid=l.interpolate(.5,normalized=True)
 if t['highway']=='tertiary':ax.text(mid.x+1,mid.y,'Yanping N. Rd.\nOSM centerline',fontsize=8)
 if t.get('footway')=='crossing':ax.text(mid.x,mid.y-4,'Mapped crossing',fontsize=8)
for (label,g),color in zip(models.items(),['#e05c45','#168e85']):
 x,y=g.exterior.xy;ax.fill(x,y,color=color,alpha=.22);ax.plot(x,y,color=color,linewidth=2,label=label)
ax.scatter(*anchor,c='black',s=24,zorder=5);ax.annotate('Y26 OSM entrance\n(shared anchor)',anchor,xytext=(anchor[0]-5,anchor[1]+20),arrowprops={'arrowstyle':'->'},ha='center',fontsize=9)
ax.set_xlim(anchor[0]-65,anchor[0]+65);ax.set_ylim(anchor[1]-55,anchor[1]+45);ax.set_aspect('equal');ax.grid(alpha=.2);ax.set_xlabel('Blender local X (m)');ax.set_ylabel('Blender local Y (m)');ax.set_title('Y26 orientation alternatives — not surveyed');ax.legend(loc='upper left');fig.text(.08,.025,'Both variants retain the entrance anchor. No road widths or photographed pose have been calibrated.',fontsize=9);fig.savefig(out/'Y26_context_comparison.png',dpi=160,bbox_inches='tight');plt.close(fig)
r={'checks':checks,'decision':'Neither alternative proven correct. Preserve both; no main-model rotation authorized by this check.','sources':['local taiwan-260908.osm.pbf','https://www.studiox4.com/works/y26/']};(out/'context_check.json').write_text(json.dumps(r,indent=2));print(json.dumps(r))
