"""A visible Windows/macOS dashboard for the local Ollama story phone."""
import os,sys,threading,webbrowser
from pathlib import Path
from local_connection import local_models,test_model,lan_addresses

def main():
    import tkinter as tk
    from tkinter import ttk,messagebox
    os.chdir(Path(__file__).parent)
    root=tk.Tk();root.title('拾光 · Ollama 连接助手');root.geometry('720x'+str(min(930,root.winfo_screenheight()-100)));root.minsize(600,650);root.configure(bg='#f4f6f1')
    style=ttk.Style();style.theme_use('clam');style.configure('TFrame',background='#f4f6f1');style.configure('TLabel',background='#f4f6f1',font=('Segoe UI',11));style.configure('TButton',font=('Segoe UI',10),padding=9);style.configure('Header.TLabel',font=('Segoe UI',22,'bold'),foreground='#2e594e')
    canvas=tk.Canvas(root,highlightthickness=0,bg='#f4f6f1');scroll=ttk.Scrollbar(root,orient='vertical',command=canvas.yview);scroll.pack(side='right',fill='y');canvas.pack(side='left',fill='both',expand=True);canvas.configure(yscrollcommand=scroll.set)
    frame=ttk.Frame(canvas,padding=25);item=canvas.create_window((0,0),window=frame,anchor='nw');frame.bind('<Configure>',lambda e:canvas.configure(scrollregion=canvas.bbox('all')));canvas.bind('<Configure>',lambda e:canvas.itemconfigure(item,width=e.width));canvas.bind_all('<MouseWheel>',lambda e:canvas.yview_scroll(-int(e.delta/120),'units'))
    ttk.Label(frame,text='让手机里的角色，连上你的 Ollama',style='Header.TLabel').pack(anchor='w')
    ttk.Label(frame,text='电脑负责 AI，手机只负责打开网页。不需要云模型密钥。',wraplength=620).pack(anchor='w',pady=(8,20))
    state={'server':None,'worker':None,'port':3000,'models':[],'tested':None};status=tk.StringVar(value='先打开 Ollama，再点下面的「1 刷新模型」。')
    ttk.Label(frame,textvariable=status,wraplength=620,foreground='#607a60').pack(anchor='w',pady=(0,12))
    model=tk.StringVar();models=ttk.Combobox(frame,textvariable=model,state='readonly');models.pack(fill='x',pady=5)
    buttonrow=ttk.Frame(frame);buttonrow.pack(fill='x',pady=8)
    def background(work,done):
        def task():
            try:value=work();root.after(0,lambda:done(value,None))
            except Exception as exc:
                error=str(exc);root.after(0,lambda:done(None,error))
        threading.Thread(target=task,daemon=True).start()
    def scan():
        status.set('正在找本机已下载的模型…')
        def done(names,error):
            if error:status.set('没连上 Ollama。请先打开 Ollama，等几秒后重试。');return
            state['models']=names;models['values']=names
            if names:model.set(names[0]);status.set('找到本地模型了。选一个，然后点「2 测试 AI」。')
            else:status.set('Ollama 已打开，但没有本地聊天模型。先去左侧 Chat 下载模型；云端模型不会列在这里。')
        background(local_models,done)
    def check():
        selected=model.get()
        if selected not in state['models']:messagebox.showinfo('先选模型','请先点「1 刷新模型」，再从列表选一个。');return
        status.set('正在等模型回复，第一次可能要等 1—3 分钟。不要重复点击。');testbtn['state']='disabled'
        def done(text,error):
            testbtn['state']='normal'
            if error:status.set('测试没成功。先在 Ollama 的 Chat 里选同一个模型，确认它能回复，再试一次。');return
            state['tested']=selected;status.set('AI 已真实回复：'+text[:80]+'。现在可以启动手机。')
        background(lambda:test_model(selected),done)
    scanbtn=ttk.Button(buttonrow,text='1 刷新模型',command=scan);scanbtn.pack(side='left',padx=(0,8));testbtn=ttk.Button(buttonrow,text='2 测试 AI',command=check);testbtn.pack(side='left')
    ttk.Label(frame,text='设置本次作者登录密码（6 位以上，自己记住，不是锁屏密码）').pack(anchor='w',pady=(15,4))
    password=tk.StringVar();passwordbox=ttk.Entry(frame,textvariable=password,show='●');passwordbox.pack(fill='x')
    mobile=tk.StringVar(value='启动后，这里会显示手机该打开的网址。');computer=tk.StringVar(value='尚未启动')
    addresses=lan_addresses();address_map={row['label']+'  '+row['ip']:row['ip'] for row in addresses};network=tk.StringVar(value=next(iter(address_map),''))
    def mobile_update(*args):
        ip=address_map.get(network.get())
        mobile.set(f'http://{ip}:{state["port"]}/play.html' if ip and state['server'] else '找不到手机地址时，请看教程里的「查 IPv4 地址」。')
    def start():
        if state['server']:messagebox.showinfo('已经启动','下面的电脑和手机入口已经可以用了。');return
        if model.get() not in state['models']:messagebox.showinfo('先选模型','先刷新并选一个已下载的本地模型。');return
        if len(password.get())<6:messagebox.showinfo('设置作者密码','请填一个至少 6 位的作者密码。不要发给玩家。');return
        os.environ.update(MODEL_PROVIDER='ollama',MODEL_NAME=model.get(),AUTHOR_PASSWORD=password.get(),COOKIE_SECURE='0',STORY_DB=str(Path('data/story.db').resolve()))
        try:
            from server import Handler,ThreadingHTTPServer
            server=ThreadingHTTPServer(('0.0.0.0',state['port']),Handler)
        except OSError:messagebox.showerror('端口被占用','请关闭之前启动的拾光窗口，再重新启动。');return
        models['state']='disabled';scanbtn['state']='disabled';passwordbox['state']='disabled'
        state['server']=server;state['worker']=threading.Thread(target=server.serve_forever,daemon=True);state['worker'].start()
        computer.set(f'http://127.0.0.1:{state["port"]}/studio.html');mobile_update();status.set('手机服务已启动。先在电脑导入内容、作者登录、保存并发布，再用手机打开下面的地址。')
        for b in [authorbtn,playerbtn,copybtn]:b['state']='normal'
        webbrowser.open(computer.get())
    ttk.Button(frame,text='3 启动手机服务',command=start).pack(fill='x',pady=(16,18))
    ttk.Separator(frame).pack(fill='x',pady=4)
    ttk.Label(frame,text='电脑设计入口').pack(anchor='w',pady=(12,3));ttk.Label(frame,textvariable=computer,foreground='#2e594e').pack(anchor='w')
    actions=ttk.Frame(frame);actions.pack(fill='x',pady=8)
    authorbtn=ttk.Button(actions,text='打开设计端',command=lambda:webbrowser.open(computer.get()),state='disabled');authorbtn.pack(side='left',padx=(0,8))
    playerbtn=ttk.Button(actions,text='电脑先试着玩',command=lambda:webbrowser.open(f'http://127.0.0.1:{state["port"]}/play.html'),state='disabled');playerbtn.pack(side='left')
    ttk.Label(frame,text='手机入口：手机和电脑连同一个路由器').pack(anchor='w',pady=(10,4))
    networks=ttk.Combobox(frame,textvariable=network,values=list(address_map),state='readonly');networks.pack(fill='x');network.trace_add('write',mobile_update)
    ttk.Label(frame,textvariable=mobile,foreground='#2e594e',font=('Segoe UI',13,'bold'),wraplength=620).pack(anchor='w',pady=10)
    def copy():root.clipboard_clear();root.clipboard_append(mobile.get());status.set('手机网址已复制，可以发给自己的手机。')
    copybtn=ttk.Button(frame,text='复制手机网址',command=copy,state='disabled');copybtn.pack(fill='x')
    ttk.Button(frame,text='打开一步一步的 Windows 教程',command=lambda:webbrowser.open('https://zhusichen520.github.io/zhusichen520/help-ollama.html')).pack(fill='x',pady=9)
    ttk.Label(frame,text='锁屏密码默认 420802。这个窗口和 Ollama 都要保持打开；电脑不能睡眠。修改模型或作者密码时，请关闭助手再重新打开。\n手机打不开时，只允许 Python 通过 Windows 的“专用网络”防火墙，不要关闭整个防火墙。',wraplength=620,font=('Segoe UI',9)).pack(anchor='w',pady=5)
    def close():
        if state['server']:state['server'].shutdown();state['server'].server_close()
        root.destroy()
    root.protocol('WM_DELETE_WINDOW',close);root.mainloop()
if __name__=='__main__':
    try:main()
    except ImportError:print('需要安装 Python 3，并包含 Tkinter。Windows 安装时请勾选 Add python.exe to PATH。');input('按回车关闭')
