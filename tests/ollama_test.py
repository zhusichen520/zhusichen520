"""Verify local Ollama-compatible transport without a paid or real model API."""
import unittest,threading,tempfile,subprocess,os,json,time,urllib.request,http.cookiejar
from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
class OllamaStub(BaseHTTPRequestHandler):
 captured=None;auth=None
 def log_message(self,*args):pass
 def do_POST(self):
  OllamaStub.captured=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
  OllamaStub.auth=self.headers.get('Authorization')
  self.send_response(200);self.send_header('Content-Type','application/json');self.end_headers();self.wfile.write(json.dumps({'choices':[{'message':{'content':'水喝两口，别的等你有空再说。'}}]},ensure_ascii=False).encode())
class OllamaTest(unittest.TestCase):
 def test_no_api_key_provider_and_locked_character_stage(self):
  tmp=tempfile.TemporaryDirectory();stub=ThreadingHTTPServer(('127.0.0.1',3007),OllamaStub);threading.Thread(target=stub.serve_forever,daemon=True).start()
  proc=subprocess.Popen(['python3','server.py'],env={**os.environ,'PORT':'3006','STORY_DB':tmp.name+'/data.db','AUTHOR_PASSWORD':'test-only-password','COOKIE_SECURE':'0','OLLAMA_BASE_URL':'http://127.0.0.1:3007/v1'})
  client=urllib.request.build_opener(urllib.request.ProxyHandler({}),urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
  def call(path,body=None):
   req=urllib.request.Request('http://127.0.0.1:3006'+path,data=json.dumps(body).encode() if body is not None else None,headers={'Content-Type':'application/json'})
   with client.open(req) as r:return json.load(r)
  try:
   for _ in range(50):
    try:call('/api/status');break
    except Exception:time.sleep(.1)
   call('/api/login',{'password':'test-only-password'})
   call('/api/ai-config',{'provider':'ollama','model':'qwen2.5:7b'})
   status=call('/api/status');self.assertTrue(status['aiConfigured']);self.assertEqual(status['aiProvider'],'ollama')
   with open('mom-template.json') as f:t=json.load(f)
   call('/api/draft',{'draft':{'title':'妈妈的故事','contacts':[t['contact']],'photos':[],'moments':[],'notes':[]}});call('/api/publish',{})
   reply=call('/api/chat',{'contact':t['contact']['id'],'stage':'定局期','messages':[{'role':'user','content':'妈，我先忙了'}]})
   self.assertIn('水喝两口',reply['reply']);self.assertEqual(OllamaStub.captured['model'],'qwen2.5:7b');self.assertIsNone(OllamaStub.auth)
   self.assertIn('【作者锁定的关系阶段】\n沉默期',OllamaStub.captured['messages'][0]['content'])
   call('/api/ai-config',{'remove':True});self.assertFalse(call('/api/status')['aiConfigured'])
  finally:proc.terminate();proc.wait();stub.shutdown();stub.server_close();tmp.cleanup()
if __name__=='__main__':unittest.main()
