import os,pathlib
p=pathlib.Path(os.environ['CIVIC_SCRIPT_DIR'])/'build_miramar_photo_shell.py'
code=p.read_text().replace("name='MIRAMAR_PHOTO_SHELL_0912_EST'","name='MIRAMAR_PHOTO_SHELL_0912_V2_EST'").replace("old=[o for o in s.objects if 'w238513441' in o.name and o.visible_get()]\nassert len(old)==2","old=[s.objects[n] for n in json.load(open(out/'miramar_photo_shell_report.json'))['objects']]\nassert all(o.visible_get() for o in old)").replace("'MIRAMAR_PHOTO_REVIEW_0912'","'MIRAMAR_PHOTO_REVIEW_0912_V2'")
exec(compile(code,str(p),'exec'))
