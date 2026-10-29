import unittest,subprocess,os,time,json,tempfile,threading,urllib.request,urllib.error,http.cookiejar,io
from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
from unittest.mock import patch
from pathlib import Path
import launch_web
class Model(BaseHTTPRequestHandler):
 def log_message(self,*args):pass
 def do_GET(self):
  self.send_response(200);self.end_headers();self.wfile.write(b'{"models":[{"name":"qwen2.5:3b"}]}')
 def do_POST(self):
  self.rfile.read(int(self.headers['Content-Length']));self.send_response(200);self.end_headers();self.wfile.write(json.dumps({'choices':[{'message':{'content':'连接成功'}}]},ensure_ascii=False).encode())
class LocalSetupTest(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.tmp=tempfile.TemporaryDirectory();cls.model=ThreadingHTTPServer(('127.0.0.1',3014),Model);threading.Thread(target=cls.model.serve_forever,daemon=True).start()
  cls.proc=subprocess.Popen(['python3','server.py'],env={**os.environ,'PORT':'3013','STORY_DB':cls.tmp.name+'/db.sqlite','COOKIE_SECURE':'0','AUTHOR_PASSWORD':'initial-test-password','LOCAL_LAUNCHER':'1','LOCAL_CONFIGURED':'0','LOCAL_SETUP_TOKEN':'test-only-bootstrap-token','OLLAMA_BASE_URL':'http://127.0.0.1:3014/v1','MODEL_PROVIDER':'ollama','MODEL_NAME':'qwen2.5:3b'})
  cls.client=urllib.request.build_opener(urllib.request.ProxyHandler({}),urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
  for _ in range(50):
   try:cls.call('/api/status');break
   except Exception:time.sleep(.1)
 @classmethod
 def tearDownClass(cls):cls.proc.terminate();cls.proc.wait();cls.model.shutdown();cls.model.server_close();cls.tmp.cleanup()
 @classmethod
 def call(cls,path,body=None,host=None):
  headers={'Content-Type':'application/json'}
  if host:headers['Host']=host
  req=urllib.request.Request('http://127.0.0.1:3013'+path,data=None if body is None else json.dumps(body).encode(),headers=headers)
  with cls.client.open(req) as r:return json.load(r)
 def test_bootstrap_model_migration_publish_and_host_guard(self):
  with self.assertRaises(urllib.error.HTTPError) as cm:self.call('/api/backup')
  self.assertEqual(cm.exception.code,401)
  with self.assertRaises(urllib.error.HTTPError) as cm:self.call('/api/local/bootstrap',{'token':'test-only-bootstrap-token'},host='attacker.example:3013')
  self.assertEqual(cm.exception.code,403)
  self.call('/api/local/bootstrap',{'token':'test-only-bootstrap-token'})
  with self.assertRaises(urllib.error.HTTPError) as cm:self.call('/api/local/bootstrap',{'token':'test-only-bootstrap-token'})
  self.assertEqual(cm.exception.code,403)
  self.assertEqual(self.call('/api/local/models')['models'],['qwen2.5:3b'])
  self.assertIn('连接成功',self.call('/api/local/test',{'model':'qwen2.5:3b'})['reply'])
  self.call('/api/local/config',{'model':'qwen2.5:3b','password':'my-test-author-password'})
  image='data:image/png;base64,c3RvcnktdGVzdA=='
  draft={'title':'我原网页的故事','owner':'雨昕','names':{'chat':'微信'},'wallpaper':image,'contacts':[{'id':'kun','name':'KUN','background':image,'messages':[],'options':[],'ai':{'enabled':True,'persona':'private-role-test'}}],'photos':[{'id':'photo','title':'我的图片','src':image}],'notes':[],'moments':[],'profiles':{'moments':{'cover':image}}}
  self.call('/api/draft',{'draft':draft});self.assertEqual(self.call('/api/draft')['draft'],draft)
  self.call('/api/publish',{})
  public=self.call('/api/story')['story'];self.assertEqual(public['wallpaper'],image);self.assertEqual(public['contacts'][0]['background'],image);self.assertEqual(public['photos'],draft['photos']);self.assertNotIn('persona',public['contacts'][0]['ai'])
  backup=self.call('/api/backup');self.assertEqual(backup['draft'],draft);self.assertEqual(backup['published'],draft)
  status=self.call('/api/local/status');self.assertTrue(status['configured']);self.assertTrue(status['draft']['hasWallpaper']);self.assertTrue(status['published']);self.assertNotIn('test-only-bootstrap-token',json.dumps(status))
 def test_startup_errors_remain_readable_without_secret_values(self):
  with tempfile.TemporaryDirectory() as tmp,patch('launch_web.ROOT',Path(tmp)),patch('launch_web.main',side_effect=RuntimeError('failure test-author-secret')),patch.dict(os.environ,{'AUTHOR_PASSWORD':'test-author-secret'}),patch('builtins.input',side_effect=EOFError),patch('sys.stdout',new_callable=io.StringIO) as out:
   launch_web.run();log=(Path(tmp)/'startup-errors.log').read_text();self.assertIn('RuntimeError',log);self.assertNotIn('test-author-secret',log);self.assertNotIn('test-author-secret',out.getvalue())
if __name__=='__main__':unittest.main()
