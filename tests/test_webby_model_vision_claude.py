"""Actual Claude CLI image transport against a local SSE fixture; no real login."""
import base64
import http.server
import json
import os
from pathlib import Path
import shutil
import runpy
import tempfile
import threading
import unittest
from unittest.mock import patch

fixtures = runpy.run_path(str(Path(__file__).with_name('test_webby_model_vision.py')))
M, G, png, review = (fixtures[name] for name in ('M', 'G', 'png', 'review'))


@unittest.skipUnless(shutil.which('claude'), 'Claude CLI is not installed')
class InstalledClaudeVisionTest(unittest.TestCase):
    def test_native_image_bytes_no_tools_and_completed_stream(self):
        model = 'claude-sonnet-4-6'
        raw = png()
        image = {'path': 'mobile.png', **M['image_info'](raw), 'data': raw}
        requests = []
        answer = review()
        class Handler(http.server.BaseHTTPRequestHandler):
            def do_POST(self):
                requests.append(json.loads(self.rfile.read(int(self.headers.get('Content-Length', '0')))))
                self.send_response(200)
                self.send_header('content-type', 'text/event-stream')
                self.end_headers()
                events = [
                    ('message_start', {'type': 'message_start', 'message': {
                        'id': 'msg_offline', 'type': 'message', 'role': 'assistant', 'model': model,
                        'content': [], 'stop_reason': None, 'stop_sequence': None,
                        'usage': {'input_tokens': 10, 'output_tokens': 0}}}),
                    ('content_block_start', {'type': 'content_block_start', 'index': 0,
                                             'content_block': {'type': 'text', 'text': ''}}),
                    ('content_block_delta', {'type': 'content_block_delta', 'index': 0,
                                             'delta': {'type': 'text_delta', 'text': json.dumps(answer)}}),
                    ('content_block_stop', {'type': 'content_block_stop', 'index': 0}),
                    ('message_delta', {'type': 'message_delta',
                                       'delta': {'stop_reason': 'end_turn', 'stop_sequence': None},
                                       'usage': {'output_tokens': 20}}),
                    ('message_stop', {'type': 'message_stop'}),
                ]
                for event, data in events:
                    self.wfile.write(('event: ' + event + '\ndata: ' + json.dumps(data) + '\n\n').encode())

            def log_message(self, *args): pass

        server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        with tempfile.TemporaryDirectory(prefix='webby-offline-claude-image-') as temporary:
            # No inherited credentials or state, and a localhost-only provider.
            environment = {
                'PATH': os.environ['PATH'], 'HOME': temporary, 'CLAUDE_CONFIG_DIR': temporary,
                'ANTHROPIC_BASE_URL': f'http://127.0.0.1:{server.server_port}',
                'ANTHROPIC_API_KEY': 'fake-local-capture-only',
                'CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC': '1', 'DISABLE_TELEMETRY': '1',
                'DISABLE_ERROR_REPORTING': '1', 'CLAUDE_CODE_MAX_RETRIES': '0',
                'CLAUDE_CODE_DISABLE_AUTO_MODEL_FALLBACK': '1',
            }
            with patch.dict(G, {'clean_env': lambda profile: environment}):
                result, metadata = M['cli_call']({'kind': 'claude'}, {
                    'model': model, 'timeout_seconds': 15, 'max_output_tokens': 512, '_images': [image],
                }, 'Review the attached fixture. Get Webby', M['VISUAL_REVIEW_SCHEMA'], Path(temporary))
            validated = M['validate_output'](result, 'review', 'Get Webby', [image])
        self.assertEqual(len(requests), 1)
        self.assertEqual(requests[0]['model'], model)
        self.assertEqual(requests[0].get('tools', []), [])
        images = [block for message in requests[0].get('messages', []) for block in message.get('content', [])
                  if isinstance(block, dict) and block.get('type') == 'image']
        self.assertEqual(len(images), 1)
        self.assertEqual(images[0]['source']['type'], 'base64')
        self.assertEqual(images[0]['source']['media_type'], 'image/png')
        self.assertEqual(base64.b64decode(images[0]['source']['data']), raw)
        self.assertEqual(metadata['reported_model'], model)
        self.assertEqual(validated['image_access'], 'viewed')


if __name__ == '__main__': unittest.main()
