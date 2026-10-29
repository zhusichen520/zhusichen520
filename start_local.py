"""Double-click launcher for a private local Ollama story server."""
import os,sys,json,urllib.request,webbrowser,threading,socket
from pathlib import Path
os.chdir(Path(__file__).parent)
try:
 import tkinter as tk
 from tkinter import simpledialog,messagebox
 root=tk.Tk();root.withdraw()
 password=simpledialog.askstring('拾光 · 本机作者登录','设置本次启动的作者密码（不是故事解锁密码）：',show='*')
 if not password:sys.exit()
 req=urllib.request.Request('http://127.0.0.1:11434/api/tags')
 try:
  with urllib.request.urlopen(req,timeout=5) as r:models=[m['name'] for m in json.load(r).get('models',[])]
 except Exception:models=[]
 if not models:
  messagebox.showwarning('先启动 Ollama','没有找到本机模型。请先打开 Ollama，并下载至少一个聊天模型，再重新启动。')
  sys.exit()
 model=simpledialog.askstring('选择本机模型','填写已安装的模型名：\n'+', '.join(models),initialvalue=models[0])
 if not model:sys.exit()
 if model not in models:messagebox.showerror('模型未安装','请填写上面列表中的完整模型名。');sys.exit()
 os.environ.update(MODEL_PROVIDER='ollama',MODEL_NAME=model,AUTHOR_PASSWORD=password,COOKIE_SECURE='0',STORY_DB=str(Path('data/story.db').resolve()))
 port=int(os.environ.get('PORT','3000'))
 with socket.socket() as sock:
  try:sock.bind(('0.0.0.0',port))
  except OSError:messagebox.showerror('端口被占用','3000 端口已被占用，请关闭之前启动的拾光窗口后重试。');sys.exit()
 host=socket.gethostbyname(socket.gethostname())
 from server import Handler,ThreadingHTTPServer
 httpd=ThreadingHTTPServer(('0.0.0.0',port),Handler)
 worker=threading.Thread(target=httpd.serve_forever,daemon=True);worker.start()
 webbrowser.open(f'http://127.0.0.1:{port}/studio.html')
 messagebox.showinfo('启动本地版',f'不收模型 API 调用费；使用本机算力。\n\n电脑网址：http://127.0.0.1:{port}\n手机与电脑同 Wi-Fi 时可尝试：http://{host}:{port}\n（手机访问需要本机防火墙允许局域网连接，不能在外网访问。）\n\n先导入 GitHub Pages 上的完整备份，再登录、保存并发布。不要把作者密码当成故事密码；故事密码是 420802。\n关闭启动窗口会停止服务。')
 root.destroy()
 try:worker.join()
 except KeyboardInterrupt:httpd.shutdown()
except ImportError:
 print('需要安装 Python 3，并包含 Tkinter 图形界面支持。');input('按回车关闭')
