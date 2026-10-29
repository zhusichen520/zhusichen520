"""Non-secret, local-only Ollama and LAN checks used by the launcher."""
import json,urllib.request,socket,ipaddress,subprocess,sys

def local_models(base='http://127.0.0.1:11434'):
    with urllib.request.build_opener(urllib.request.ProxyHandler({})).open(base.rstrip('/')+'/api/tags',timeout=8) as response:data=json.load(response)
    return [m['name'] for m in data.get('models',[]) if isinstance(m.get('name'),str) and not m.get('remote_host') and not m.get('remote_model') and not m['name'].endswith('-cloud') and ':cloud' not in m['name']]

def test_model(model,base='http://127.0.0.1:11434'):
    payload=json.dumps({'model':model,'messages':[{'role':'user','content':'不要展开分析，只回复：连接成功'}],'max_tokens':256,'stream':False}).encode()
    req=urllib.request.Request(base.rstrip('/')+'/v1/chat/completions',data=payload,headers={'Content-Type':'application/json'})
    with urllib.request.build_opener(urllib.request.ProxyHandler({})).open(req,timeout=180) as response:data=json.load(response)
    text=data['choices'][0]['message']['content']
    if not isinstance(text,str) or not text.strip():raise ValueError('模型返回空回复，请确认选择的是聊天模型')
    return text.strip()

def lan_addresses():
    found={}
    if sys.platform=='win32':
        try:
            cmd=['powershell.exe','-NoProfile','-Command','[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new(); Get-NetIPAddress -AddressFamily IPv4 | Select-Object InterfaceAlias,IPAddress | ConvertTo-Json -Compress']
            run=subprocess.run(cmd,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=8,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
            rows=json.loads(run.stdout)
            if isinstance(rows,dict):rows=[rows]
            for row in rows:found[row['IPAddress']]=row.get('InterfaceAlias','本机网络')
        except Exception:pass
    try:
        for row in socket.getaddrinfo(socket.gethostname(),None,socket.AF_INET):found.setdefault(row[4][0],'本机网络')
    except OSError:pass
    result=[]
    for ip,label in found.items():
        try:
            address=ipaddress.ip_address(ip)
            if address.is_private and not address.is_loopback and not address.is_link_local:result.append({'ip':ip,'label':label})
        except ValueError:pass
    result.sort(key=lambda x:(any(v in x['label'].lower() for v in ['vethernet','vmware','virtual','tailscale','loopback']),0 if x['ip'].startswith('192.168.') else 1 if x['ip'].startswith('10.') else 2,x['ip']))
    return result
