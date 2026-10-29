"""Exercise AI transport against a local fake provider; no live model credentials."""
import unittest,threading,tempfile,subprocess,os,json,time,urllib.request,http.cookiejar
from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
class Provider(BaseHTTPRequestHandler):
 captured=None
 def log_message(self,*args):pass
 def do_POST(self):
  Provider.captured=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
  body=json.dumps({'choices':[{'message':{'content':'我在。'}}]}).encode()
  self.send_response(200);self.send_header('Content-Type','application/json');self.end_headers();self.wfile.write(body)
class AITest(unittest.TestCase):
 def test_role_context_and_private_published_settings(self):
  tmp=tempfile.TemporaryDirectory();provider=ThreadingHTTPServer(('127.0.0.1',3005),Provider);thread=threading.Thread(target=provider.serve_forever,daemon=True);thread.start()
  proc=subprocess.Popen(['python3','server.py'],env={**os.environ,'PORT':'3004','STORY_DB':tmp.name+'/story.db','AUTHOR_PASSWORD':'test-only-password','COOKIE_SECURE':'0','MODEL_API_KEY':'test-only-placeholder','MODEL_BASE_URL':'http://127.0.0.1:3005/v1'})
  client=urllib.request.build_opener(urllib.request.ProxyHandler({}),urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
  def call(path,body=None):
   req=urllib.request.Request('http://127.0.0.1:3004'+path,data=json.dumps(body).encode() if body is not None else None,headers={'Content-Type':'application/json'})
   with client.open(req) as r:return json.load(r)
  try:
   for _ in range(50):
    try:call('/api/status');break
    except Exception:time.sleep(.1)
   with open('kun-template.json') as f:t=json.load(f)
   c=t['contact'];c['messages'].append({'id':'locked','type':'text','text':'尚未解锁的秘密','trigger':'note:secret'})
   d={'title':'KUN测试','owner':'雨昕','names':{},'contacts':[c],'notes':[],'photos':[],'moments':[]}
   call('/api/login',{'password':'test-only-password'});call('/api/draft',{'draft':d});call('/api/publish',{})
   self.assertEqual(call('/api/chat',{'contact':c['id'],'messages':[{'role':'user','content':'蔡徐坤'}]})['reply'],'我在。')
   prompt=Provider.captured['messages'][0]['content']
   self.assertIn(c['ai']['scene'],prompt);self.assertIn(c['ai']['examples'],prompt);self.assertIn(c['ai']['boundaries'],prompt)
   self.assertNotIn('尚未解锁的秘密',prompt)
   public=call('/api/story')['story']['contacts'][0]['ai'];self.assertEqual(public,{'enabled':True})
   self.assertEqual(Provider.captured['messages'][-1],{'role':'user','content':'蔡徐坤'})
  finally:
   proc.terminate();proc.wait();provider.shutdown();provider.server_close();tmp.cleanup()
if __name__=='__main__':unittest.main()
