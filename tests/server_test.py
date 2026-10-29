import unittest, subprocess, tempfile, os, time, urllib.request, urllib.error, json, http.cookiejar
class ServerTest(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.tmp=tempfile.TemporaryDirectory();cls.p=subprocess.Popen(['python3','server.py'],env={**os.environ,'PORT':'3001','STORY_DB':cls.tmp.name+'/story.db','AUTHOR_PASSWORD':'test-only-password','COOKIE_SECURE':'0'})
  cls.client=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()),urllib.request.ProxyHandler({}))
  for _ in range(50):
   try:cls.call('/api/status');break
   except Exception:time.sleep(.1)
 @classmethod
 def tearDownClass(cls):cls.p.terminate();cls.p.wait();cls.tmp.cleanup()
 @classmethod
 def call(cls,path,body=None):
  req=urllib.request.Request('http://127.0.0.1:3001'+path,data=None if body is None else json.dumps(body).encode(),headers={} if body is None else {'Content-Type':'application/json'})
  with cls.client.open(req) as r:return json.load(r)
 def test_author_publish_and_isolation(self):
  with self.assertRaises(urllib.error.HTTPError) as cm:self.call('/api/draft')
  self.assertEqual(cm.exception.code,401)
  self.call('/api/login',{'password':'test-only-password'})
  draft={'title':'第一版','owner':'林','names':{},'notes':[],'photos':[],'moments':[],'contacts':[{'id':'c1','messages':[],'ai':{'enabled':True,'persona':'不可公开的人设'}}]}
  self.call('/api/draft',{'draft':draft});self.call('/api/publish',{})
  draft['title']='未发布的新草稿';self.call('/api/draft',{'draft':draft})
  story=self.call('/api/story')['story'];self.assertEqual(story['title'],'第一版');self.assertNotIn('persona',story['contacts'][0]['ai'])
  self.assertEqual(self.call('/api/draft')['draft']['title'],'未发布的新草稿')
  self.call('/api/logout',{})
  with self.assertRaises(urllib.error.HTTPError) as cm:self.call('/api/publish',{})
  self.assertEqual(cm.exception.code,401)
  with self.assertRaises(urllib.error.HTTPError) as cm:self.call('/api/chat',{'contact':'c1','messages':[{'role':'user','content':'你好'}]})
  self.assertEqual(cm.exception.code,503)
 def test_no_private_files(self):
  for path in ['/server.py','/.env','/README.md','/../server.py']:
   with self.assertRaises(urllib.error.HTTPError) as cm:self.call(path)
   self.assertEqual(cm.exception.code,404)
if __name__=='__main__':unittest.main()
