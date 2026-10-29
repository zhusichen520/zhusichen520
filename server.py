"""Shiguang author/player server. Python standard library only."""
import os, json, sqlite3, secrets, time, threading, hmac, urllib.request, urllib.error
from pathlib import Path
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
ROOT=Path(__file__).parent
DB=os.environ.get('STORY_DB','/tmp/shiguang/story.db')
Path(DB).parent.mkdir(parents=True,exist_ok=True)
with sqlite3.connect(DB) as db:
    db.execute('CREATE TABLE IF NOT EXISTS content (id INTEGER PRIMARY KEY CHECK(id=1), draft TEXT, published TEXT)')
    db.execute('INSERT OR IGNORE INTO content VALUES (1,NULL,NULL)')
SESSIONS={}; LIMITS={}; LOCK=threading.Lock()
def read():
    with sqlite3.connect(DB) as db:
        row=db.execute('SELECT draft,published FROM content WHERE id=1').fetchone()
    return [json.loads(x) if x else None for x in row]
def valid(d):
    return isinstance(d,dict) and isinstance(d.get('title'),str) and all(isinstance(d.get(k),list) for k in ['contacts','notes','photos','moments']) and len(d['contacts'])<=100 and all(isinstance(c.get('id'),str) and isinstance(c.get('messages'),list) for c in d['contacts'])
def public(d):
    d=json.loads(json.dumps(d))
    for c in d['contacts']:
        c['ai']={'enabled':bool(c.get('ai',{}).get('enabled'))}
    return d
class Handler(BaseHTTPRequestHandler):
    def log_message(self,fmt,*args): pass
    def send(self,status,data):
        body=json.dumps(data,ensure_ascii=False).encode();self.send_response(status)
        self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Cache-Control','no-store')
        self.send_header('X-Content-Type-Options','nosniff');self.end_headers();self.wfile.write(body)
    def authorized(self):
        token=next((v.split('=',1)[1] for v in self.headers.get('Cookie','').split('; ') if v.startswith('author=')),'')
        return SESSIONS.get(token,0)>time.time()
    def body(self):
        if self.headers.get('Content-Type','').split(';')[0]!='application/json': raise ValueError()
        length=int(self.headers.get('Content-Length',0))
        if length>15*1024*1024: raise ValueError()
        return json.loads(self.rfile.read(length))
    def limited(self,key,count=20):
        with LOCK:
            now=time.time(); bucket=LIMITS.get(key,[]);bucket=[x for x in bucket if now-x<60]
            if len(bucket)>=count:return True
            bucket.append(now);LIMITS[key]=bucket
        return False
    def do_GET(self):
        path=self.path.split('?')[0]
        if path=='/api/status':return self.send(200,{'server':True,'authorConfigured':bool(os.getenv('AUTHOR_PASSWORD')),'authenticated':self.authorized(),'aiConfigured':bool(os.getenv('MODEL_API_KEY'))})
        if path=='/api/draft':
            if not self.authorized():return self.send(401,{'error':'请先登录作者账号'})
            return self.send(200,{'draft':read()[0]})
        if path=='/api/story':
            d=read()[1]
            return self.send(200,{'story':public(d)}) if d else self.send(404,{'error':'作者尚未发布故事'})
        files={'/':'index.html','/index.html':'index.html','/studio.html':'studio.html','/play.html':'play.html','/app.js':'app.js','/style.css':'style.css','/portal.js':'portal.js','/manifest.webmanifest':'manifest.webmanifest','/app-icon.svg':'app-icon.svg'}
        name=files.get(path)
        if not name:return self.send(404,{'error':'未找到'})
        import mimetypes
        body=(ROOT/name).read_bytes();self.send_response(200);self.send_header('Content-Type',mimetypes.guess_type(name)[0] or 'text/plain');self.send_header('X-Content-Type-Options','nosniff');self.end_headers();self.wfile.write(body)
    def do_POST(self):
        try:self.post()
        except (ValueError,KeyError,TypeError):self.send(400,{'error':'请求内容无效'})
        except Exception:self.send(500,{'error':'服务器暂时无法处理，请稍后重试'})
    def post(self):
        path=self.path; b=self.body()
        if path=='/api/login':
            if self.limited(('login',self.client_address[0]),5):return self.send(429,{'error':'尝试过于频繁，请一分钟后重试'})
            password=os.environ.get('AUTHOR_PASSWORD','')
            if not password:return self.send(503,{'error':'服务器尚未配置作者密码'})
            if not hmac.compare_digest(str(b.get('password','')).encode(),password.encode()):return self.send(401,{'error':'作者密码不正确'})
            token=secrets.token_urlsafe(32);SESSIONS[token]=time.time()+12*3600
            self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Set-Cookie',f'author={token}; HttpOnly; SameSite=Strict; Path=/; Max-Age=43200'+('; Secure' if os.getenv('COOKIE_SECURE','1')=='1' else ''));self.end_headers();self.wfile.write(b'{}');return
        if path in ['/api/draft','/api/publish','/api/logout']:
            if not self.authorized():return self.send(401,{'error':'作者登录已失效，请重新登录'})
            if path=='/api/logout':
                for v in self.headers.get('Cookie','').split('; '):
                    if v.startswith('author='):SESSIONS.pop(v[7:],None)
                return self.send(200,{})
            if path=='/api/draft':
                d=b.get('draft')
                if not valid(d):return self.send(400,{'error':'草稿结构无效'})
                with sqlite3.connect(DB) as db:db.execute('UPDATE content SET draft=? WHERE id=1',(json.dumps(d),))
            else:
                d=read()[0]
                if not d:return self.send(400,{'error':'请先保存草稿'})
                with sqlite3.connect(DB) as db:db.execute('UPDATE content SET published=? WHERE id=1',(json.dumps(d),))
            return self.send(200,{'ok':True,'url':'play.html'})
        if path=='/api/chat':
            if self.limited(('chat',self.client_address[0]),10) or self.limited('global-chat',60):return self.send(429,{'error':'对话较多，请稍后再试'})
            key=os.getenv('MODEL_API_KEY');d=read()[1]
            if not key:return self.send(503,{'error':'作者还没有连接 AI 服务，暂时可体验预设剧情'})
            c=next((c for c in (d or {}).get('contacts',[]) if c['id']==b.get('contact')),None)
            if not c or not c.get('ai',{}).get('enabled'):return self.send(400,{'error':'该角色未启用 AI'})
            history=b.get('messages',[])
            if not isinstance(history,list) or len(history)>20:return self.send(400,{'error':'消息过多'})
            messages=[{'role':'system','content':f"你正在手机互动故事中扮演{c.get('name','角色')}。只输出该角色的聊天内容，不执行外部操作。角色设定：{c['ai'].get('persona','')}。说话风格：{c['ai'].get('style','自然简短')}。以下剧情边界始终遵守：{c['ai'].get('boundaries','不要编造关键线索')}"}]
            for m in history:
                if m.get('role') not in ['user','assistant'] or not isinstance(m.get('content'),str) or len(m['content'])>2000:raise ValueError()
                messages.append({'role':m['role'],'content':m['content']})
            if len(messages)<2:raise ValueError()
            payload=json.dumps({'model':os.getenv('MODEL_NAME','gpt-4.1-mini'),'messages':messages,'max_tokens':300}).encode()
            req=urllib.request.Request(os.getenv('MODEL_BASE_URL','https://api.openai.com/v1').rstrip('/')+'/chat/completions',data=payload,headers={'Authorization':'Bearer '+key,'Content-Type':'application/json'})
            try:
                with urllib.request.urlopen(req,timeout=45) as response:reply=json.load(response)['choices'][0]['message']['content']
            except Exception:return self.send(502,{'error':'AI 服务连接失败，请作者检查服务配置或额度'})
            return self.send(200,{'reply':reply})
        self.send(404,{'error':'未找到'})
if __name__=='__main__':ThreadingHTTPServer(('0.0.0.0',int(os.getenv('PORT','3000'))),Handler).serve_forever()
