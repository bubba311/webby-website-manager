'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');
const http = require('node:http');
const { publicAddress, validateUrl, resolveTarget, prepareOutput, render } = require('../scripts/webby-render-check');

test('public address filter excludes private, metadata, documentation, and transition ranges', () => {
  for (const address of ['0.0.0.0', '10.1.2.3', '127.0.0.1', '100.100.100.200', '169.254.169.254',
    '172.16.0.1', '172.31.1.1', '192.168.1.1', '192.0.0.1', '192.0.2.1', '198.18.1.1',
    '198.51.100.1', '203.0.113.1', '224.0.0.1', '255.255.255.255', '::', '::1',
    '::ffff:127.0.0.1', 'fc00::1', 'fe80::1', '2001:0000::1', '2001:0db8::1', '2002:7f00:1::', '3fff::1']) {
    assert.equal(publicAddress(address), false, address);
  }
  for (const address of ['1.1.1.1', '8.8.8.8', '93.184.216.34', '2001:4860:4860::8888', '2606:4700:4700::1111'])
    assert.equal(publicAddress(address), true, address);
});

test('URL policy permits only public HTTPS or the exact approved loopback origin', () => {
  const origin = 'http://127.0.0.1:8765';
  assert.equal(validateUrl('https://example.com/page').hostname, 'example.com');
  assert.equal(validateUrl(`${origin}/page`, origin).origin, origin);
  for (const url of ['http://example.com', 'file:///etc/passwd', 'https://user:pass@example.com',
    'https://169.254.169.254', 'https://2130706433', 'https://localhost', 'https://secret.local',
    'https://example.com:8443', 'http://127.0.0.1:8766', 'http://localhost:8765'])
    assert.throws(() => validateUrl(url, origin), undefined, url);
});

test('DNS results are checked together and returned as a pinned address', async () => {
  const mixed = async () => [{ address: '93.184.216.34', family: 4 }, { address: '127.0.0.1', family: 4 }];
  await assert.rejects(resolveTarget('https://example.com', null, mixed), /private/);
  const pinned = await resolveTarget('https://example.com', null, async () => [{ address: '93.184.216.34', family: 4 }]);
  assert.equal(pinned.address, '93.184.216.34');
  const preview = await resolveTarget('http://localhost:8765', 'http://localhost:8765', () => { throw new Error('must not resolve preview DNS'); });
  assert.equal(preview.address, '127.0.0.1');
});

test('artifact directory is new, private, and outside a repository', () => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'webby-render-policy-'));
  try {
    const output = prepareOutput(path.join(root, 'review'));
    assert.equal(fs.statSync(output).mode & 0o777, 0o700);
    assert.throws(() => prepareOutput(output), /EEXIST/);
    fs.mkdirSync(path.join(root, '.git'));
    assert.throws(() => prepareOutput(path.join(root, 'in-source')), /outside source/);
  } finally { fs.rmSync(root, { recursive: true, force: true }); }
});

test('real browser captures responsive evidence and blocks private resources including redirects',
  { skip: process.env.WEBBY_RENDER_BROWSER_TEST !== '1', timeout: 120000 }, async () => {
    const root = fs.mkdtempSync(path.join(os.tmpdir(), 'webby-render-browser-'));
    let forbiddenHits = 0;
    const forbidden = http.createServer((_req, res) => { forbiddenHits++; res.end('private'); });
    await new Promise(resolve => forbidden.listen(0, '127.0.0.1', resolve));
    const privateUrl = `http://127.0.0.1:${forbidden.address().port}/private`;
    const preview = http.createServer((req, res) => {
      if (req.url === '/redirect-image') { res.writeHead(302, { location: privateUrl }); res.end(); return; }
      if (req.url === '/favicon.ico') { res.writeHead(204); res.end(); return; }
      res.setHeader('content-type', 'text/html');
      res.end(`<!doctype html><html lang="en"><head><title>Rendered fixture</title><style>
        body{font:18px sans-serif;margin:16px}#wide{width:500px}button{min-height:44px}
        button:focus{outline:3px solid blue}@media(min-width:700px){#wide{width:auto}}
        </style></head><body><h1>Useful website</h1><p id="wide">A deliberate narrow-screen overflow.</p>
        <span hidden>HIDDEN_FIXTURE_TEXT</span><button>Start a project</button>
        <img alt="Blocked direct resource" src="${privateUrl}"><img alt="Blocked redirect" src="/redirect-image">
        <script>fetch('/submit', {method:'POST'}).catch(()=>{});</script></body></html>`);
    });
    await new Promise(resolve => preview.listen(0, '127.0.0.1', resolve));
    try {
      const report = await render({ url: `http://127.0.0.1:${preview.address().port}`, allowLoopback: true, output: path.join(root, 'artifacts') });
      assert.deepEqual(report.errors, []);
      assert.equal(report.views.length, 5);
      assert.equal(forbiddenHits, 0, 'private destination must never receive a connection');
      assert.ok(report.blockedRequests.some(item => item.reason.includes('State-changing')));
      assert.ok(report.blockedRequests.some(item => item.target.includes('/private')));
      const narrow = report.views.find(view => view.width === 320);
      assert.ok(narrow.measurements.documentWidth > 320);
      assert.ok(narrow.measurements.overflowCandidates.some(item => item.id === 'wide'));
      assert.ok(narrow.keyboardSample.some(item => item.name === 'Start a project'));
      const text = fs.readFileSync(path.join(report.output, narrow.visibleText), 'utf8');
      assert.match(text, /Useful website/);
      assert.doesNotMatch(text, /HIDDEN_FIXTURE_TEXT/);
      assert.equal(report.views.find(view => view.reducedMotion).measurements.reducedMotion, true);
      for (const view of report.views) {
        assert.deepEqual(view.errors, []);
        assert.equal(path.extname(view.accessibilitySnapshot), '.txt', 'snapshot can enter the model review as plain text');
        assert.equal(fs.readFileSync(path.join(report.output, view.screenshots.viewport)).subarray(1, 4).toString(), 'PNG');
        assert.match(fs.readFileSync(path.join(report.output, view.accessibilitySnapshot), 'utf8'), /Start a project/);
      }
    } finally {
      preview.closeAllConnections(); forbidden.closeAllConnections();
      await Promise.all([new Promise(resolve => preview.close(resolve)), new Promise(resolve => forbidden.close(resolve))]);
      fs.rmSync(root, { recursive: true, force: true });
    }
  });
