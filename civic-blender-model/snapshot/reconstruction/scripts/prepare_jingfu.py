import json,math,pathlib,os
from pyproj import Transformer
p=(pathlib.Path(os.environ['CIVIC_MODEL_ROOT'])/'CalibrationRound3')
t=Transformer.from_crs(4326,3826,always_xy=True)
def xy(u,v):
 lon=((219583+u/256)/2**18)*360-180
 lat=math.degrees(math.atan(math.sinh(math.pi*(1-2*(112224+v/256)/2**18))))
 x,y=t.transform(lon,lat);return [x-301495.6087493267,y-2770459.509396812]
polys={'roof':[[480,341],[490,339],[491,330],[503,330],[503,340],[497,342],[497,350],[480,351]],'canopy':[[478,352],[497,351],[497,364],[478,364]]}
r={'name':'Jingfu Temple','evidence_level':'L1','source_image':'Calibration/stations_current/03K800.jpg','imagery':'NLSC PHOTO2 orthophoto bearing 2024 watermark','photo_source':'https://commons.wikimedia.org/wiki/File:Checeng_Jingfu_Temple_front_view_20221129.jpg','registry':'https://crgis.rchss.sinica.edu.tw/temples/TaipeiCity/daan/63003054-DACCJFG','pixel_polygons':polys,'live_polygons':{k:[xy(*a) for a in v] for k,v in polys.items()},'assumptions':{'eave_height_m':3.4,'ridge_height_m':5.0,'canopy_height_m':2.7,'trace_pick_uncertainty_px':3,'absolute_registration_error':'unknown','footprint':'roof-outline proxy, not surveyed wall footprint','front_orientation':'west inferred from photograph and Yanji Street'},'unresolved':['Temple interior and roof ornaments not surveyed','OSM POI and Commons category coordinate differ by approximately 30m; neither treated as precise footprint','Orthophoto roof occlusion and manual trace uncertainty','Ground road and bridge clearance require integrated review']}
(p/'jingfu_evidence.json').write_text(json.dumps(r,indent=2))
