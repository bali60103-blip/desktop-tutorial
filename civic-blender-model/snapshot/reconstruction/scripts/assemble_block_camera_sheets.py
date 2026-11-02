import pathlib,json,html,math
from PIL import Image,ImageDraw,ImageFont
root=pathlib.Path('/Users/ktlu/Desktop/Civic_Rebuild_20260909_201934/BlockFacades');font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Unicode.ttf',12);files=sorted((root/'camera_renders').glob('*.png'));sheets=root/'camera_sheets';sheets.mkdir(exist_ok=True)
for start in range(0,len(files),16):
 im=Image.new('RGB',(1280,832),(24,28,33));d=ImageDraw.Draw(im)
 for j,p in enumerate(files[start:start+16]):
  x=j%4*320;y=j//4*208;im.paste(Image.open(p).convert('RGB').resize((320,180)),(x,y));d.text((x+4,y+184),p.stem,fill='white',font=font)
 im.save(sheets/('sheet_'+str(start//16+1).zfill(2)+'.jpg'))
print({'renders':len(files),'sheets':math.ceil(len(files)/16)})
