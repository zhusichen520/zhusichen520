"""Start a local-only setup browser, without depending on Tkinter."""
import os,sys,secrets,threading,webbrowser,traceback
from pathlib import Path
ROOT=Path(__file__).resolve().parent

def redact(text):
    for name in ['LOCAL_SETUP_TOKEN','AUTHOR_PASSWORD','MODEL_API_KEY']:
        value=os.environ.get(name)
        if value:text=text.replace(value,'[hidden]')
    return text

def main():
    os.chdir(ROOT)
    for name in ['server.py','setup.html','setup.js','app.js','experience.js','daily.js','local_connection.py']:
        if not (ROOT/name).is_file():raise FileNotFoundError('缺少 '+name+'。请右键 ZIP，选择“全部解压缩”，再运行启动文件。')
    token=secrets.token_urlsafe(32)
    os.environ.update(LOCAL_LAUNCHER='1',LOCAL_SETUP_TOKEN=token,LOCAL_CONFIGURED='0',MODEL_PROVIDER='ollama',MODEL_NAME='qwen2.5:3b',AUTHOR_PASSWORD=secrets.token_urlsafe(24),COOKIE_SECURE='0',STORY_DB=str(ROOT/'data'/'story.db'))
    from server import Handler,ThreadingHTTPServer
    server=None
    ports=[int(os.environ['PORT'])] if os.environ.get('PORT') else range(3000,3011)
    for port in ports:
        try:server=ThreadingHTTPServer(('0.0.0.0',port),Handler);break
        except OSError:pass
    if not server:raise OSError('3000—3010 端口已被占用，请关闭之前的拾光窗口再启动。')
    port=server.server_address[1]
    threading.Thread(target=server.serve_forever,daemon=True).start()
    print('拾光本机服务已经启动。这个窗口必须保持打开。',flush=True)
    print('正在打开浏览器设置页：选择模型、导入网页备份、发布到手机。',flush=True)
    print('电脑端口：'+str(port)+'。未完成设置前，手机 AI 暂不可用。',flush=True)
    opened=webbrowser.open(f'http://127.0.0.1:{port}/setup.html#token={token}')
    if not opened:print('默认浏览器没有打开。请检查 Windows 默认浏览器，修好后关闭此窗口并重新启动。',flush=True)
    try:threading.Event().wait()
    except KeyboardInterrupt:server.shutdown();server.server_close()

def run():
    if hasattr(sys.stdout,'reconfigure'):sys.stdout.reconfigure(errors='replace')
    try:main()
    except Exception:
        error=redact(traceback.format_exc())
        try:(ROOT/'startup-errors.log').write_text(error,encoding='utf-8')
        except OSError:pass
        print('\n启动未成功。窗口会保留，请查看下方报错：\n'+error,flush=True)
        print('如果提示缺少文件，请先“全部解压缩”；如果提示找不到 Python，请安装 Python 3。',flush=True)
        try:input('按回车结束；Windows 启动窗口仍会保留。')
        except EOFError:pass
if __name__=='__main__':run()
