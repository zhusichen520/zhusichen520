import unittest,json,threading
from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
from local_connection import local_models,test_model,lan_addresses
from unittest.mock import patch
class FakeOllama(BaseHTTPRequestHandler):
 def log_message(self,*args):pass
 def do_GET(self):
  self.send_response(200);self.end_headers();self.wfile.write(json.dumps({'models':[{'name':'qwen2.5:3b'},{'name':'cloud-one','remote_host':'https://example.test'},{'name':'big-cloud'}]}).encode())
 def do_POST(self):
  request=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
  self.send_response(200);self.end_headers();self.wfile.write(json.dumps({'choices':[{'message':{'content':'连接成功'}}]},ensure_ascii=False).encode())
class ConnectionTest(unittest.TestCase):
 def test_local_model_selection_and_real_request(self):
  server=ThreadingHTTPServer(('127.0.0.1',3009),FakeOllama);threading.Thread(target=server.serve_forever,daemon=True).start()
  try:self.assertEqual(local_models('http://127.0.0.1:3009'),['qwen2.5:3b']);self.assertEqual(test_model('qwen2.5:3b','http://127.0.0.1:3009'),'连接成功')
  finally:server.shutdown();server.server_close()
 def test_lan_addresses_exclude_loopback_and_linklocal(self):
  rows=[(None,None,None,None,(ip,0)) for ip in ['127.0.0.1','169.254.2.3','192.168.1.15','10.0.0.2']]
  with patch('local_connection.socket.getaddrinfo',return_value=rows):self.assertEqual([x['ip'] for x in lan_addresses()],['192.168.1.15','10.0.0.2'])
if __name__=='__main__':unittest.main()
