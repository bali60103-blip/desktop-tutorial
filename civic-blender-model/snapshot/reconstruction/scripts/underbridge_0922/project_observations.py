import json,math,sys
from pyproj import Transformer
p=sys.argv[1]
a=json.load(open(p));t=Transformer.from_crs(4326,3826,always_xy=True)
r=math.radians(-7.824973748058551e-05);s=.9999980676451855
for o in a:
 x,y=t.transform(o['lon'],o['lat']);x-=301495.60874932667;y-=2770459.509396812
 xx=(math.cos(r)*x+math.sin(r)*y)/s;yy=(-math.sin(r)*x+math.cos(r)*y)/s
 o['camera_model_xy']=[round(xx,3),round(yy,3)];o['camera_easting_strip']='UB_X'+format(math.floor(xx/100),'+04d');o['coverage_limit']='Camera strip is not visibility coverage or measured object position'
print(json.dumps(a,ensure_ascii=False))
