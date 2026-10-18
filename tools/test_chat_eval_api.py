import importlib.util
import json
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import threading
import unittest

spec = importlib.util.spec_from_file_location('api', Path(__file__).with_name('chat-eval-api.py'))
a = importlib.util.module_from_spec(spec)
spec.loader.exec_module(a)


class APITests(unittest.TestCase):
    def setUp(self):
        self.calls = []
        self.mode = 'sse'
        owner = self
        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass
            def reply(self, code, content, mime='application/json'):
                self.send_response(code); self.send_header('Content-Type', mime)
                self.send_header('Content-Length', str(len(content))); self.end_headers()
                self.wfile.write(content)
            def do_POST(self):
                payload = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
                owner.calls.append(('POST', self.path, payload))
                if self.path == '/assistant/conversations':
                    self.reply(201, b'{"id":"conversation"}'); return
                operation = {'operation_id': 'operation', 'request_id': payload['request_id'], 'state': 'active'}
                if owner.mode == 'json':
                    self.reply(200, json.dumps(operation).encode()); return
                event = {'operation_id': 'wrong' if owner.mode == 'mismatch' else 'operation', 'operation': operation}
                self.reply(200, ('event: started\ndata: ' + json.dumps(event) + '\n\n').encode(), 'text/event-stream')
            def do_GET(self):
                owner.calls.append(('GET', self.path, None))
                self.reply(200, json.dumps({'items': [{'conversation_id': 'conversation',
                             'operation': {'request_id': 'request', 'operation_id': 'operation'}}]}).encode())
        self.server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        self.worker = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.worker.start()
        self.addCleanup(self.close)
        self.api = a.API(f'http://127.0.0.1:{self.server.server_port}', 'synthetic', 'synthetic')

    def close(self):
        self.server.shutdown(); self.server.server_close(); self.worker.join(2)

    def test_creation_and_sse_handle_preserve_request_identity(self):
        self.assertEqual(self.api.create_conversation('synthetic'), 'conversation')
        self.assertEqual(self.api.generate('conversation', 'request', 'question', {}), 'operation')
        self.assertEqual(self.calls[-1][2]['content'], 'question')
        self.assertEqual(len(self.calls), 2)

    def test_existing_json_response_is_observed_without_retry(self):
        self.mode = 'json'
        self.assertEqual(self.api.generate('conversation', 'request', 'question', {}), 'operation')
        self.assertEqual(len(self.calls), 1)

    def test_mismatched_sse_handle_is_rejected_without_reposting(self):
        self.mode = 'mismatch'
        with self.assertRaisesRegex(ValueError, 'Inconsistent'):
            self.api.generate('conversation', 'request', 'question', {})
        self.assertEqual(len(self.calls), 1)

    def test_recovery_only_reads_and_matches_conversation_and_request(self):
        self.assertEqual(self.api.recover_handle('conversation', 'request'), 'operation')
        self.assertIsNone(self.api.recover_handle('other-conversation', 'request'))
        self.assertTrue(all(call[0] == 'GET' for call in self.calls))


if __name__ == '__main__':
    unittest.main()
