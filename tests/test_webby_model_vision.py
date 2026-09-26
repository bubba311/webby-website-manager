"""Screenshot validation, native image adapters, and honest visual receipts."""
import base64
import hashlib
import json
from pathlib import Path
import runpy
import struct
import tempfile
import unittest
from unittest.mock import patch
import zlib

CLI = Path(__file__).resolve().parents[1] / 'scripts' / 'webby-model-draft'
M = runpy.run_path(str(CLI), run_name='webby_model_vision_test')
G = M['main'].__globals__
Error = M['DraftError']


def chunk(kind, data):
    return struct.pack('>I', len(data)) + kind + data + struct.pack('>I', zlib.crc32(kind + data) & 0xffffffff)


def png(width=2, height=2, color=b'\x40\x80\xc0', extra=b''):
    return (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0))
            + extra + chunk(b'IDAT', zlib.compress((b'\x00' + color * min(width, 2)) * min(height, 2))) + chunk(b'IEND', b''))


def review():
    return {'offer': 'Website design', 'audience': 'Founders', 'next_action': 'Get Webby',
            'evidence': [{'claim': 'There is a start action', 'quote': 'Get Webby'}],
            'uncertainties': ['Button behavior was not tested'], 'improvements': [], 'image_access': 'viewed',
            'visual_observations': [{'image': 'mobile.png', 'location': 'Hero at top',
                'observation': 'Blue background behind a heading', 'recommendation': 'Keep the legible heading'}]}


class ImageInputTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.repo = self.root / 'captures'; self.repo.mkdir()
        (self.repo / 'visible.txt').write_text('Get Webby')
        self.raw = png()
        (self.repo / 'mobile.png').write_bytes(self.raw)
        self.config = {'version': 1, 'providers': {'vision': {'kind': 'openai', 'api_key_env': 'KEY'}}}
        self.job = {'id': 'visual', 'operation': 'review', 'provider': 'vision', 'model': 'vision-model',
                    'path': 'visible.txt', 'images': ['mobile.png'], 'task': 'Inspect the screenshots'}

    def prepare(self):
        plan_path = self.root / 'plan.json'
        plan_path.write_text(json.dumps({'version': 1, 'brief': 'Website review', 'jobs': [self.job]}))
        return M['load_plan'](plan_path, self.config, self.repo)

    def test_valid_png_records_real_dimensions_and_exact_bytes(self):
        plan, _ = self.prepare()
        info = plan['jobs'][0]['_images'][0]
        self.assertEqual((info['width'], info['height'], info['media_type']), (2, 2, 'image/png'))
        self.assertEqual(info['data'], self.raw)
        self.assertEqual(info['sha256'], hashlib.sha256(self.raw).hexdigest())
        self.assertNotIn('data', M['image_metadata']([info])[0])

    def test_broken_animated_large_and_mislabeled_images_are_rejected(self):
        bad_crc = bytearray(self.raw); bad_crc[31] ^= 1
        for raw in [bytes(bad_crc), self.raw[:-1], self.raw + b'trailing', b'GIF89a',
                    png(8193, 1), png(5000, 5000), png(extra=chunk(b'acTL', struct.pack('>II', 1, 0))),
                    b'x' * (M['MAX_IMAGE_BYTES'] + 1)]:
            with self.subTest(prefix=raw[:12]), self.assertRaises(Error): M['image_info'](raw)
        (self.repo / 'fake.jpg').write_bytes(self.raw)
        with self.assertRaises(Error): M['load_images'](self.repo, ['fake.jpg'])

    def test_paths_duplicates_count_and_total_size_are_bounded(self):
        (self.repo / 'link.png').symlink_to(self.repo / 'mobile.png')
        for paths in [['../mobile.png'], ['/tmp/mobile.png'], ['.hidden.png'], ['credentials.png'], ['link.png'],
                      ['mobile.png', 'mobile.png'], ['1.png', '2.png', '3.png', '4.png', '5.png']]:
            with self.subTest(paths=paths), self.assertRaises(Error): M['load_images'](self.repo, paths)
        with patch.dict(G, {'MAX_TOTAL_IMAGE_BYTES': len(self.raw) - 1}), self.assertRaises(Error):
            M['load_images'](self.repo, ['mobile.png'])

    def test_images_cannot_be_assigned_to_drafts_or_unrendered_proposals(self):
        for changes in [{'operation': 'draft'}, {'review_proposed': True}]:
            with self.subTest(changes=changes):
                old = dict(self.job); self.job.update(changes)
                with self.assertRaises(Error): self.prepare()
                self.job = old

    def test_visual_review_requires_actual_access_and_every_attachment(self):
        images = M['load_images'](self.repo, ['mobile.png'])
        for changes in [{'image_access': 'unavailable'}, {'visual_observations': []},
                        {'visual_observations': [{**review()['visual_observations'][0], 'image': 'not-attached.png'}]}]:
            with self.subTest(changes=changes), self.assertRaises(Error):
                M['validate_output'](json.dumps({**review(), **changes}), 'review', 'Get Webby', images)
        with self.assertRaises(Error):
            M['validate_output'](json.dumps(review()), 'review', 'Get Webby', images + [{**images[0], 'path': 'desktop.png'}])
        text_only = {k: v for k, v in review().items() if k not in {'image_access', 'visual_observations'}}
        with self.assertRaises(Error): M['validate_output'](json.dumps(text_only), 'review', 'Get Webby', images)

    def test_visual_prompt_includes_explicit_capture_context_without_brief(self):
        plan, _ = self.prepare()
        data = json.loads(M['prompt_for']({'brief': 'Answer not on page'}, plan['jobs'][0], 'Get Webby',
                            {'desktop.txt': 'Desktop heading'}).split('Task data:\n')[1])
        self.assertEqual(data['context_files'], {'desktop.txt': 'Desktop heading'})
        self.assertNotIn('brief', data)

    def test_success_receipt_has_hashes_and_no_image_payload_or_source_changes(self):
        plan, snapshots = self.prepare()
        original = (self.repo / 'visible.txt').read_bytes()
        def generate(profile, job, prompt, schema, repo):
            self.assertEqual(schema, M['VISUAL_REVIEW_SCHEMA'])
            self.assertNotIn(base64.b64encode(self.raw).decode(), prompt)
            return json.dumps(review()), {'reported_model': 'vision-model', 'usage': {'output_tokens': 55}}
        with patch.dict(G, {'doctor_profile': lambda *a: {'ready': True}, 'api_call': generate}):
            receipt = M['run_plan'](plan, self.config, self.repo, self.root / 'result', snapshots)
        self.assertEqual(receipt['status'], 'review_ready')
        job = receipt['jobs'][0]
        self.assertEqual(job['images'][0]['sha256'], hashlib.sha256(self.raw).hexdigest())
        self.assertEqual(job['image_transport'], 'responses_input_image')
        self.assertEqual(job['reported_model'], 'vision-model')
        self.assertNotIn('data', job['images'][0])
        self.assertEqual((self.repo / 'visible.txt').read_bytes(), original)
        self.assertEqual((self.root / 'result/changes.patch').read_text(), '')

    def test_replaced_screenshot_invalidates_the_review(self):
        plan, snapshots = self.prepare()
        def generate(*args):
            (self.repo / 'mobile.png').write_bytes(png(color=b'\xff\x00\x00'))
            return json.dumps(review()), {'reported_model': 'vision-model'}
        with patch.dict(G, {'doctor_profile': lambda *a: {'ready': True}, 'api_call': generate}), self.assertRaises(Error):
            M['run_plan'](plan, self.config, self.repo, self.root / 'result', snapshots)
        self.assertEqual(json.loads((self.root / 'result/receipt.json').read_text())['status'], 'failed')
        self.assertFalse((self.root / 'result/changes.patch').exists())


class NativeImageAdapterTest(unittest.TestCase):
    def setUp(self):
        raw = png()
        self.images = [{'path': 'mobile.png', **M['image_info'](raw), 'data': raw}]
        self.job = {'model': 'vision-model', 'operation': 'review', '_images': self.images,
                    'max_output_tokens': 768, 'timeout_seconds': 30}

    def test_all_api_payloads_contain_native_image_bytes_and_no_tools(self):
        content = json.dumps(review())
        replies = {'openai': {'status': 'completed', 'model': 'vision-model', 'output': [
                       {'type': 'message', 'content': [{'type': 'output_text', 'text': content}]}]},
                   'anthropic': {'stop_reason': 'end_turn', 'model': 'vision-model', 'content': [{'type': 'text', 'text': content}]},
                   'gemini': {'modelVersion': 'vision-model', 'candidates': [{'finishReason': 'STOP', 'content': {'parts': [{'text': content}]}}]},
                   'compatible': {'model': 'vision-model', 'choices': [{'finish_reason': 'stop', 'message': {'content': content}}]}}
        for kind, reply in replies.items():
            with self.subTest(kind=kind):
                calls = []
                def post(url, headers, payload, timeout):
                    calls.append(payload); return reply
                profile = {'kind': kind, 'api_key_env': 'KEY', 'base_url': 'https://provider.example/v1'}
                with patch.dict(G, {'post_json': post, 'credential': lambda *a: 'private-key'}):
                    output, metadata = M['api_call'](profile, self.job, 'Get Webby', M['VISUAL_REVIEW_SCHEMA'], Path('/source'))
                self.assertEqual(len(calls), 1)
                self.assertEqual(output, content)
                payload = calls[0]
                self.assertEqual(payload.get('tools', []), [])
                if kind == 'openai':
                    blocks = payload['input'][0]['content']; native = [b for b in blocks if b['type'] == 'input_image'][0]
                    encoded = native['image_url'].split(',', 1)[1]
                elif kind == 'anthropic':
                    blocks = payload['messages'][0]['content']; native = [b for b in blocks if b['type'] == 'image'][0]
                    encoded = native['source']['data']
                    self.assertEqual(native['source']['media_type'], 'image/png')
                elif kind == 'gemini':
                    blocks = payload['contents'][0]['parts']; native = [b for b in blocks if 'inlineData' in b][0]
                    encoded = native['inlineData']['data']
                    self.assertEqual(native['inlineData']['mimeType'], 'image/png')
                else:
                    blocks = payload['messages'][1]['content']; native = [b for b in blocks if b['type'] == 'image_url'][0]
                    encoded = native['image_url']['url'].split(',', 1)[1]
                self.assertEqual(base64.b64decode(encoded), self.images[0]['data'])
                self.assertIn('Get Webby', json.dumps(blocks))

    def test_codex_attaches_private_snapshot_and_rejects_nonvision_catalog(self):
        calls = []
        def command(argv, env, cwd, timeout, input_text=''):
            if argv[:3] == ['codex', 'debug', 'models']:
                return 0, json.dumps({'models': [{'slug': 'vision-model', 'input_modalities': ['text', 'image']}]}), ''
            path = Path(argv[argv.index('--image') + 1])
            calls.append((path.read_bytes(), path.stat().st_mode & 0o777, input_text, cwd))
            return 0, '\n'.join(json.dumps(e) for e in [{'type': 'turn.started'},
                {'type': 'item.completed', 'item': {'type': 'agent_message', 'text': json.dumps(review())}}, {'type': 'turn.completed'}]), ''
        with patch.dict(G, {'command': command}):
            result, metadata = M['cli_call']({'kind': 'codex'}, self.job, 'Get Webby', M['VISUAL_REVIEW_SCHEMA'], Path('/source'))
        self.assertEqual(calls[0][:3], (self.images[0]['data'], 0o600, 'Get Webby'))
        self.assertFalse(Path(calls[0][3]).exists())
        self.assertIsNone(metadata['reported_model'])
        with tempfile.TemporaryDirectory() as directory, patch.dict(G, {'command': lambda *a: (0,
                json.dumps({'models': [{'slug': 'vision-model', 'input_modalities': ['text']}]}), '')}), self.assertRaises(Error):
            M['codex_catalog']('vision-model', {}, directory, images=True)

    def test_claude_uses_stream_input_and_parses_one_final_result(self):
        calls = []
        final = {'type': 'result', 'subtype': 'success', 'is_error': False, 'result': json.dumps(review()),
                 'modelUsage': {'vision-model': {}}, 'usage': {'output_tokens': 77}}
        def command(argv, env, cwd, timeout, input_text=''):
            calls.append((argv, input_text))
            return 0, '\n'.join(json.dumps(e) for e in [{'type': 'system'}, final]), ''
        with patch.dict(G, {'command': command}):
            _, metadata = M['cli_call']({'kind': 'claude'}, self.job, 'Get Webby', M['VISUAL_REVIEW_SCHEMA'], Path('/source'))
        argv, supplied = calls[0]
        for flag in ['--input-format', '--output-format']:
            self.assertEqual(argv[argv.index(flag) + 1], 'stream-json')
        self.assertIn('--verbose', argv)
        self.assertEqual(argv[argv.index('--tools') + 1], '')
        message = json.loads(supplied)
        self.assertEqual(message['type'], 'user')
        self.assertEqual(message['message']['role'], 'user')
        block = next(b for b in message['message']['content'] if b['type'] == 'image')
        self.assertEqual(base64.b64decode(block['source']['data']), self.images[0]['data'])
        self.assertEqual(metadata['reported_model'], 'vision-model')
        for stream in [json.dumps({'type': 'system'}), json.dumps(final) + '\n' + json.dumps(final),
                       json.dumps({'type': 'assistant', 'message': {'content': [{'type': 'tool_use'}]}}) + '\n' + json.dumps(final)]:
            with self.subTest(stream=stream[:40]), patch.dict(G, {'command': lambda *a: (0, stream, '')}), self.assertRaises(Error):
                M['cli_call']({'kind': 'claude'}, self.job, 'Get Webby', M['VISUAL_REVIEW_SCHEMA'], Path('/source'))


if __name__ == '__main__': unittest.main()
