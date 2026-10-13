"""Backend sends authenticated cancel to the agreed attempt-specific endpoint."""
import asyncio
import hashlib
import hmac
import json
import threading
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer

from app.services.chat_transport import PrivateChatTransport


def test_backend_cancel_uses_attempt_specific_signed_route_and_complete_control():
    key=b'jup035-synthetic-private-key-32-bytes-only';calls=[]
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args): pass
        def do_POST(self):
            raw=self.rfile.read(int(self.headers['Content-Length']))
            message=f"chat-v2\nPOST\n{self.path}\n{self.headers['X-Chat-Time']}\n{self.headers['X-Chat-Nonce']}\n{hashlib.sha256(raw).hexdigest()}".encode()
            calls.append((self.path,json.loads(raw),hmac.compare_digest(self.headers['X-Chat-Signature'],hmac.new(key,message,hashlib.sha256).hexdigest())))
            self.send_response(200);self.send_header('Content-Length','0');self.end_headers()
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    payload={'operation_id':'synthetic-op','attempt_id':'synthetic-attempt','tenant_id':'tenant','user_id':'alice','conversation_id':'chat',
             'boot_id':'synthetic-boot','capability':'synthetic-capability','input_hash':'synthetic-hash','number':1}
    try:
        transport=PrivateChatTransport(f'http://127.0.0.1:{server.server_port}',key)
        asyncio.run(transport.cancel(payload))
        assert calls==[('/internal/chat/v2/attempts/synthetic-attempt/cancel',{'v':2,**payload},True)]
    finally:
        server.shutdown();server.server_close();thread.join()
