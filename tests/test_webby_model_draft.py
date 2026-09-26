"""Model adapters, scope boundaries, failure receipts, and credential isolation."""
import copy
import http.server
import threading
import shutil
import json
import os
from pathlib import Path
import runpy
import socket
import tempfile
import time
import signal
import subprocess
import sys
import unittest
from unittest.mock import patch

CLI = Path(__file__).resolve().parents[1] / 'scripts' / 'webby-model-draft'
M = runpy.run_path(str(CLI), run_name='webby_model_draft_test')
G = M['main'].__globals__
Error = M['DraftError']


class DraftTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.repo = self.root / 'site'
        self.repo.mkdir()
        self.html = '<header>Keep</header><!-- A -->old hero<!-- /A --><aside>Keep</aside><!-- B -->old faq<!-- /B -->\n'
        (self.repo / 'index.html').write_text(self.html)
        self.config = {'version': 1, 'providers': {'writer': {'kind': 'openai', 'api_key_env': 'WEBBY_TEST_KEY'}}}
        self.job = {'id': 'hero', 'provider': 'writer', 'model': 'exact-model', 'path': 'index.html',
                    'task': 'Write the hero.', 'section': {'start': '<!-- A -->', 'end': '<!-- /A -->'}}
        self.plan = {'version': 1, 'brief': 'A real offer', 'jobs': [self.job]}

    def prepare(self):
        path = self.root / 'plan.json'
        path.write_text(json.dumps(self.plan))
        return M['load_plan'](path, self.config, self.repo)

    def run_fixture(self, results, output='review'):
        plan, snapshots = self.prepare()
        calls = []
        def generate(profile, job, prompt, schema, repo):
            calls.append((job['id'], prompt))
            value = results[len(calls) - 1]
            if isinstance(value, Exception):
                raise value
            return json.dumps(value), {'reported_model': 'exact-model', 'usage': {'input_tokens': 20, 'output_tokens': 10}}
        with patch.dict(G, {'doctor_profile': lambda *a: {'ready': True}, 'api_call': generate}):
            receipt = M['run_plan'](plan, self.config, self.repo, self.root / output, snapshots)
        return receipt, calls

    def test_two_models_can_replace_disjoint_sections_in_same_file(self):
        self.config['providers']['other'] = {'kind': 'anthropic', 'api_key_env': 'OTHER_KEY'}
        self.plan['jobs'].append({**self.job, 'id': 'faq', 'provider': 'other', 'model': 'other-exact',
                                 'section': {'start': '<!-- B -->', 'end': '<!-- /B -->'}})
        receipt, calls = self.run_fixture([{'content': '<h1>New hero</h1>'}, {'content': '<p>New faq</p>'}])
        proposed = (self.root / 'review/proposed/index.html').read_text()
        self.assertEqual(proposed, self.html.replace('old hero', '<h1>New hero</h1>').replace('old faq', '<p>New faq</p>'))
        self.assertEqual((self.repo / 'index.html').read_text(), self.html)
        self.assertEqual([j['provider'] for j in receipt['jobs']], ['writer', 'other'])
        self.assertEqual(len(calls), 2)
        self.assertNotIn('old faq', json.loads(calls[0][1].split('Task data:\n')[1])['selected_source'])

    def test_overlapping_jobs_rejected_before_generation(self):
        for second in [{**self.job, 'id': 'again'}, {**self.job, 'id': 'whole', 'section': None}]:
            with self.subTest(second=second):
                self.plan['jobs'] = [self.job, second]
                with self.assertRaises(Error): self.prepare()

    def test_ambiguous_missing_reversed_markers_fail(self):
        for value in ['<!-- A --><!-- A --><!-- /A -->', '<!-- /A --><!-- A -->', 'No markers']:
            (self.repo / 'index.html').write_text(value)
            with self.subTest(value=value), self.assertRaises(Error): self.prepare()

    def test_paths_cannot_traverse_or_use_hidden_credentials(self):
        for path in ['../outside.html', '/tmp/out.html', '.env', '.git/config', 'public/../index.html',
                     'secret.json', 'credentials.txt', 'a\\b.html', 'index.html\nmalicious']:
            self.plan['jobs'][0]['path'] = path
            with self.subTest(path=path), self.assertRaises(Error): self.prepare()

    def test_symlink_file_and_parent_rejected(self):
        (self.repo / 'linked.html').symlink_to(self.repo / 'index.html')
        (self.repo / 'alias').symlink_to(self.repo, target_is_directory=True)
        for path in ['linked.html', 'alias/index.html']:
            self.plan['jobs'][0]['path'] = path
            with self.subTest(path=path), self.assertRaises(Error): self.prepare()

    def test_secret_like_source_rejected(self):
        (self.repo / 'index.html').write_text('<p>sk-proj-' + 'A' * 50 + '</p>')
        with self.assertRaises(Error): self.prepare()

    def test_source_changed_during_generation_gets_no_patch(self):
        plan, snapshots = self.prepare()
        def generate(*a):
            (self.repo / 'index.html').write_text('An owner edit')
            return '{"content":"Draft"}', {}
        with patch.dict(G, {'doctor_profile': lambda *a: {'ready': True}, 'api_call': generate}), self.assertRaises(Error):
            M['run_plan'](plan, self.config, self.repo, self.root / 'review', snapshots)
        self.assertFalse((self.root / 'review/changes.patch').exists())
        self.assertEqual(json.loads((self.root / 'review/receipt.json').read_text())['status'], 'failed')
        self.assertEqual((self.repo / 'index.html').read_text(), 'An owner edit')

    def test_failure_stops_later_jobs_and_records_spend_uncertainty(self):
        self.plan['jobs'].append({**self.job, 'id': 'faq', 'section': {'start': '<!-- B -->', 'end': '<!-- /B -->'}})
        plan, snapshots = self.prepare()
        called = []
        def generate(*a):
            called.append(1)
            raise Error('Provider timeout; usage may have been charged.')
        with patch.dict(G, {'doctor_profile': lambda *a: {'ready': True}, 'api_call': generate}), self.assertRaises(Error):
            M['run_plan'](plan, self.config, self.repo, self.root / 'review', snapshots)
        receipt = json.loads((self.root / 'review/receipt.json').read_text())
        self.assertEqual(len(called), 1)
        self.assertEqual(receipt['jobs'][0]['status'], 'failed_or_unknown')
        self.assertEqual(receipt['requests_retried_by_webby'], 0)
        self.assertFalse((self.root / 'review/changes.patch').exists())

    def test_reader_check_reads_proposal_and_does_not_edit_source(self):
        self.plan['jobs'].append({**self.job, 'id': 'read', 'operation': 'review', 'review_proposed': True})
        review = {'offer': 'Websites', 'audience': 'Founders', 'next_action': 'Chat',
                  'evidence': [{'claim': 'Creates sites', 'quote': 'We create websites'}], 'uncertainties': [], 'improvements': []}
        receipt, calls = self.run_fixture([{'content': '<p>We create websites</p>'}, review])
        self.assertIn('We create websites', calls[1][1])
        self.assertEqual(receipt['jobs'][1]['reader_check'], review)
        self.assertEqual((self.repo / 'index.html').read_text(), self.html)

    def test_reader_invented_quote_rejected(self):
        review = {'offer': 'Websites', 'audience': 'Founders', 'next_action': 'Chat',
                  'evidence': [{'claim': 'Creates sites', 'quote': 'invented'}], 'uncertainties': [], 'improvements': []}
        with self.assertRaises(Error): M['validate_output'](json.dumps(review), 'review', self.html)

    def test_whole_new_file_produces_applicable_patch_without_source_write(self):
        self.plan['jobs'][0] = {**self.job, 'path': 'new.html', 'section': None}
        self.run_fixture([{'content': '<h1>New file</h1>'}])
        change = (self.root / 'review/changes.patch').read_text()
        self.assertIn('--- /dev/null', change)
        self.assertIn('\\ No newline at end of file', change)
        self.assertFalse((self.repo / 'new.html').exists())

    def test_output_inside_source_or_existing_directory_rejected(self):
        plan, snapshots = self.prepare()
        for out in [self.repo / 'review', self.root]:
            with self.subTest(out=out), self.assertRaises(Error):
                M['run_plan'](plan, self.config, self.repo, out, snapshots)

    def test_max_jobs_and_output_cap_validated(self):
        self.job['max_output_tokens'] = 9999999
        with self.assertRaises(Error): self.prepare()
        self.job.pop('max_output_tokens')
        self.plan['jobs'] *= 13
        with self.assertRaises(Error): self.prepare()

    def test_new_file_can_be_reviewed_after_drafting(self):
        self.plan['jobs'][0] = {**self.job, 'path': 'new.html', 'section': None}
        self.plan['jobs'].append({**self.plan['jobs'][0], 'id': 'check', 'operation': 'review', 'review_proposed': True})
        review = {'offer': 'New', 'audience': 'Unknown', 'next_action': 'Unknown',
                  'evidence': [], 'uncertainties': ['No audience'], 'improvements': ['Add audience']}
        result, calls = self.run_fixture([{'content': '<h1>New</h1>'}, review])
        self.assertEqual(result['status'], 'review_ready')
        self.assertIn('<h1>New</h1>', calls[1][1])

    def test_malformed_provider_failure_receipt_is_final(self):
        plan, snapshots = self.prepare()
        def malformed(*a): raise TypeError('secret provider details')
        with patch.dict(G, {'doctor_profile': lambda *a: {'ready': True}, 'api_call': malformed}), self.assertRaises(Error):
            M['run_plan'](plan, self.config, self.repo, self.root / 'review', snapshots)
        receipt = json.loads((self.root / 'review/receipt.json').read_text())
        self.assertEqual(receipt['status'], 'failed')
        self.assertEqual(receipt['jobs'][0]['status'], 'failed_or_unknown')
        self.assertNotIn('secret provider details', json.dumps(receipt))

    def test_accepted_job_artifact_survives_later_failure(self):
        self.plan['jobs'].append({**self.job, 'id': 'faq', 'section': {'start': '<!-- B -->', 'end': '<!-- /B -->'}})
        with self.assertRaises(Error):
            self.run_fixture([{'content': '<h1>Accepted</h1>'}, Error('Stopped')])
        self.assertEqual(json.loads((self.root / 'review/jobs/hero.json').read_text()), {'content': '<h1>Accepted</h1>'})
        self.assertFalse((self.root / 'review/changes.patch').exists())

    def test_reader_prompt_does_not_leak_answers_from_brief_or_context(self):
        job = {**self.job, 'operation': 'review'}
        prompt = M['prompt_for']({'brief': 'Secret answer to question'}, job, 'Actual page', {'context.txt': 'Secret answer'})
        self.assertNotIn('Secret answer', prompt)

    def test_section_preserves_original_crlf_outside_its_bounds(self):
        original = b'<main>\r\n<!-- A -->old hero<!-- /A -->\r\n</main>\r\n'
        (self.repo / 'index.html').write_bytes(original)
        receipt, _ = self.run_fixture([{'content': 'new hero'}])
        self.assertEqual((self.root / 'review/proposed/index.html').read_bytes(), original.replace(b'old hero', b'new hero'))
        self.assertEqual((self.repo / 'index.html').read_bytes(), original)


class AdapterTest(unittest.TestCase):
    def setUp(self):
        self.job = {'model': 'chosen-model', 'max_output_tokens': 768, 'timeout_seconds': 30}
        self.content = '{"content":"<h1>Draft</h1>"}'

    def invoke(self, kind, response, allow_alias=False):
        calls = []
        def post(url, headers, payload, timeout):
            calls.append((url, headers, payload, timeout))
            return response
        profile = {'kind': kind, 'api_key_env': 'KEY'}
        if kind == 'compatible': profile['base_url'] = 'https://provider.example/v1'
        job = {**self.job, 'allow_model_alias': allow_alias}
        with patch.dict(G, {'post_json': post, 'credential': lambda *a: 'private-key'}):
            result = M['api_call'](profile, job, 'a prompt', M['DRAFT_SCHEMA'], Path('/source'))
        return result, calls

    def test_openai_responses_request_and_usage(self):
        result, calls = self.invoke('openai', {'status': 'completed', 'model': 'chosen-model', 'output': [
            {'type': 'message', 'content': [{'type': 'output_text', 'text': self.content}]}], 'usage': {'output_tokens': 20}})
        self.assertEqual(result[0], self.content)
        self.assertEqual(calls[0][2]['max_output_tokens'], 768)
        self.assertFalse(calls[0][2]['store'])
        self.assertEqual(calls[0][2]['tools'], [])
        self.assertEqual(result[1]['usage']['output_tokens'], 20)

    def test_anthropic_messages_request_and_stop(self):
        result, calls = self.invoke('anthropic', {'stop_reason': 'end_turn', 'model': 'chosen-model', 'content': [{'type': 'text', 'text': self.content}]})
        self.assertEqual(result[0], self.content)
        self.assertEqual(calls[0][2]['max_tokens'], 768)
        self.assertEqual(calls[0][1]['anthropic-version'], '2023-06-01')
        self.assertNotIn('tools', calls[0][2])

    def test_gemini_generates_one_candidate_with_no_tools(self):
        result, calls = self.invoke('gemini', {'modelVersion': 'chosen-model', 'candidates': [
            {'finishReason': 'STOP', 'content': {'parts': [{'text': self.content}]}}]})
        self.assertEqual(result[0], self.content)
        self.assertEqual(calls[0][2]['generationConfig']['maxOutputTokens'], 768)
        self.assertNotIn('private-key', calls[0][0])
        self.assertNotIn('tools', calls[0][2])

    def test_generic_compatible_preserves_model(self):
        result, calls = self.invoke('compatible', {'model': 'chosen-model', 'choices': [
            {'finish_reason': 'stop', 'message': {'content': self.content}}]})
        self.assertTrue(calls[0][0].endswith('/v1/chat/completions'))
        self.assertEqual(calls[0][2]['model'], 'chosen-model')
        self.assertEqual(result[1]['reported_model'], 'chosen-model')

    def test_all_backends_reject_truncation(self):
        bad = {'openai': {'status': 'incomplete'}, 'anthropic': {'stop_reason': 'max_tokens'},
               'gemini': {'candidates': [{'finishReason': 'MAX_TOKENS'}]},
               'compatible': {'choices': [{'finish_reason': 'length'}]}}
        for kind, response in bad.items():
            with self.subTest(kind=kind), self.assertRaises(Error): self.invoke(kind, response)

    def test_different_served_model_rejected_unless_alias_explicit(self):
        response = {'model': 'resolved-model', 'choices': [{'finish_reason': 'stop', 'message': {'content': self.content}}]}
        with self.assertRaises(Error): self.invoke('compatible', response)
        result, _ = self.invoke('compatible', response, allow_alias=True)
        self.assertEqual(result[1]['reported_model'], 'resolved-model')

    def test_tool_request_rejected(self):
        response = {'model': 'chosen-model', 'choices': [{'finish_reason': 'stop', 'message': {'content': self.content, 'tool_calls': [{}]}}]}
        with self.assertRaises(Error): self.invoke('compatible', response)

    def test_private_endpoints_and_redirect_style_urls_rejected(self):
        for url in ['http://api.example/v1', 'https://localhost/v1', 'https://127.0.0.1/v1',
                    'https://169.254.169.254/v1', 'https://[::1]/v1', 'https://api.example:8443/v1',
                    'https://key@api.example/v1', 'https://api.example/v1?key=secret', 'https://api.example/v1#x']:
            with self.subTest(url=url), self.assertRaises(Error): M['endpoint_parts'](url)
        self.assertEqual(M['endpoint_parts']('https://openrouter.ai/api/v1'), ('openrouter.ai', '/api/v1'))

    def test_public_dns_rejects_mixed_private_answers(self):
        addresses = [(socket.AF_INET, socket.SOCK_STREAM, 6, '', ('1.1.1.1', 443)),
                     (socket.AF_INET, socket.SOCK_STREAM, 6, '', ('127.0.0.1', 443))]
        with patch('socket.getaddrinfo', return_value=addresses), self.assertRaises(Error): M['public_addresses']('provider.example')

    def test_credential_env_not_forwarded_to_subscription_cli(self):
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'secret', 'ANTHROPIC_API_KEY': 'secret', 'GH_TOKEN': 'secret',
                                     'NODE_OPTIONS': '--import=/tmp/hostile.js', 'ANTHROPIC_BASE_URL': 'https://wrong.example'}):
            for kind in ['codex', 'claude']:
                env = M['clean_env']({'kind': kind})
                self.assertFalse(set(env) & {'OPENAI_API_KEY', 'ANTHROPIC_API_KEY', 'GH_TOKEN', 'NODE_OPTIONS', 'ANTHROPIC_BASE_URL'})

    def test_private_key_file_permissions_and_source_boundary(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); path = root / 'api.key'; path.write_text('secret-key-value'); path.chmod(0o600)
            profile = {'kind': 'openai', 'api_key_file': str(path)}
            self.assertEqual(M['credential'](profile), 'secret-key-value')
            path.chmod(0o644)
            with self.assertRaises(Error): M['credential'](profile)
            path.chmod(0o600)
            with self.assertRaises(Error): M['credential'](profile, root)

    def test_cli_commands_disable_tools_and_feed_prompt_on_stdin(self):
        calls = []
        def command(argv, env, cwd, timeout, input_text=''):
            if argv[:3] == ['codex', 'debug', 'models']:
                return 0, json.dumps({'models': [{'slug': 'chosen-model', 'shell_type': 'unified_exec', 'apply_patch_tool_type': 'freeform'}]}), ''
            calls.append((argv, env, cwd, input_text))
            if argv[0] == 'codex':
                return 0, '\n'.join(json.dumps(e) for e in [
                    {'type': 'thread.started'}, {'type': 'turn.started'},
                    {'type': 'item.completed', 'item': {'type': 'agent_message', 'text': self.content}},
                    {'type': 'turn.completed', 'usage': {'output_tokens': 20}}]), ''
            return 0, json.dumps({'type': 'result', 'subtype': 'success', 'is_error': False,
                                  'result': self.content, 'modelUsage': {'chosen-model': {}}, 'usage': {'output_tokens': 20}}), ''
        with patch.dict(G, {'command': command}):
            for kind in ['codex', 'claude']:
                M['cli_call']({'kind': kind}, self.job, 'private prompt', M['DRAFT_SCHEMA'], Path('/source'))
        self.assertTrue(all('private prompt' not in args and supplied == 'private prompt' for args, _, _, supplied in calls))
        self.assertIn('features.shell_tool=false', calls[0][0])
        self.assertIn('features.code_mode=false', calls[0][0])
        self.assertEqual(calls[1][0][calls[1][0].index('--tools') + 1], '')
        self.assertIn('--strict-mcp-config', calls[1][0])
        self.assertNotEqual(calls[0][2], '/source')

    def test_cli_failure_does_not_echo_secret_stderr(self):
        with patch.dict(G, {'command': lambda *a: (1, '', 'secret credential in provider stderr')}):
            with self.assertRaises(Error) as caught:
                M['cli_call']({'kind': 'claude'}, self.job, 'p', M['DRAFT_SCHEMA'], Path('/source'))
        self.assertNotIn('secret credential', str(caught.exception))

    def test_total_deadline_interrupts_slow_request(self):
        started = time.monotonic()
        with patch.dict(G, {'_post_json': lambda *a: time.sleep(1)}), self.assertRaises(Error):
            M['post_json']('https://provider.example/v1', {}, {}, .03)
        self.assertLess(time.monotonic() - started, .5)

    def test_interrupted_cli_is_terminated_and_reaped(self):
        started = []
        original = subprocess.Popen
        def process(*a, **k):
            p = original(*a, **k); started.append(p); return p
        with tempfile.TemporaryDirectory() as directory, patch('subprocess.Popen', side_effect=process), patch('time.sleep', side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):
                M['command']([sys.executable, '-c', 'import time; time.sleep(10)'], dict(os.environ), directory, 20)
        self.assertEqual(len(started), 1)
        self.assertIsNotNone(started[0].poll())

    def test_subscription_cli_preserves_explicit_ca_file(self):
        with tempfile.TemporaryDirectory() as directory:
            ca = Path(directory) / 'corporate.pem'; ca.write_text('public certificate')
            with patch.dict(os.environ, {'NODE_EXTRA_CA_CERTS': str(ca), 'CODEX_CA_CERTIFICATE': str(ca)}):
                env = M['clean_env']({'kind': 'codex'})
            self.assertEqual(env['NODE_EXTRA_CA_CERTS'], str(ca))
            self.assertEqual(env['CODEX_CA_CERTIFICATE'], str(ca))


@unittest.skipUnless(shutil.which('codex'), 'Codex CLI is not installed')
class InstalledCodexIsolationTest(unittest.TestCase):
    def test_actual_request_has_no_tools_with_no_real_credentials(self):
        self.capture_request()

    def test_actual_screenshot_request_has_native_image_and_no_tools(self):
        png = runpy.run_path(str(Path(__file__).with_name('test_webby_model_vision.py')))['png']
        raw = png()
        images = [{'path': 'mobile.png', **M['image_info'](raw), 'data': raw}]
        captured = self.capture_request(images)
        blocks = [block for item in captured['input'] for block in item.get('content', [])
                  if isinstance(block, dict) and block.get('type') == 'input_image']
        self.assertEqual(len(blocks), 1)
        import base64
        self.assertEqual(base64.b64decode(blocks[0]['image_url'].split(',', 1)[1]), raw)

    def capture_request(self, images=()):
        captured = []
        class Handler(http.server.BaseHTTPRequestHandler):
            def do_POST(self):
                captured.append(json.loads(self.rfile.read(int(self.headers.get('Content-Length', '0')))))
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b'{"error":{"message":"offline capture complete","type":"invalid_request_error"}}')
            def log_message(self, *args): pass
        server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        real_command = G['command']
        model = 'gpt-6-luna'
        with tempfile.TemporaryDirectory(prefix='webby-offline-tools-') as directory:
            environment = {'PATH': os.environ['PATH'], 'HOME': directory, 'CODEX_HOME': directory}
            def local_command(argv, env, cwd, timeout, input_text=''):
                if argv[:2] == ['codex', 'exec']:
                    argv = [('forced_login_method="api"' if item == 'forced_login_method="chatgpt"' else
                             'model_provider="capture"' if item == 'model_provider="openai"' else item)
                            for item in argv[:-1]]
                    overrides = {'model_providers.capture.name': 'Offline capture',
                                 'model_providers.capture.base_url': f'http://127.0.0.1:{server.server_port}/v1',
                                 'model_providers.capture.wire_api': 'responses',
                                 'model_providers.capture.requires_openai_auth': False,
                                 'model_providers.capture.request_max_retries': 0,
                                 'model_providers.capture.stream_max_retries': 0,
                                 'check_for_update_on_startup': False}
                    for key, value in overrides.items():
                        argv += ['-c', key + '=' + json.dumps(value)]
                    argv += ['-']
                return real_command(argv, environment, cwd, min(timeout, 15), input_text)
            with patch.dict(G, {'command': local_command, 'clean_env': lambda profile: environment}):
                with self.assertRaises(Error):
                    M['cli_call']({'kind': 'codex'}, {'model': model, 'timeout_seconds': 15, 'max_output_tokens': 256, '_images': images},
                                  'Review the fixture' if images else 'Return only {"content":"offline"}',
                                  M['VISUAL_REVIEW_SCHEMA'] if images else M['DRAFT_SCHEMA'], Path(directory))
        self.assertEqual(len(captured), 1)
        self.assertEqual(captured[0]['model'], model)
        self.assertEqual(captured[0].get('tools', []), [])
        return captured[0]


if __name__ == '__main__': unittest.main()
