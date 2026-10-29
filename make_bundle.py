"""Build a source-only local package; excludes databases, keys, caches and Git."""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
ROOT=Path(__file__).parent
FILES=['demo.html','demo.webmanifest','demo-story.js','index.html','studio.html','play.html','app.js','experience.js','style.css','experience.css','portal.js','app-icon.svg','manifest.webmanifest','kun-template.json','mom-template.json','server.py','start_local.py','启动本地版.bat','启动本地版.command','本地版使用说明.txt']
def build():
 with ZipFile(ROOT/'local-ollama.zip','w',ZIP_DEFLATED) as archive:
  for name in FILES:archive.write(ROOT/name,'拾光本机版/'+name)
if __name__=='__main__':build()
