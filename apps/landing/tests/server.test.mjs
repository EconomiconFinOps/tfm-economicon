import assert from 'node:assert/strict';
import { mkdir, mkdtemp, rm, symlink, writeFile } from 'node:fs/promises';
import { request } from 'node:http';
import os from 'node:os';
import path from 'node:path';
import test from 'node:test';
import { createPreviewServer, requestFilename } from '../serve.mjs';

async function fixture(t) {
  const directory = await mkdtemp(path.join(os.tmpdir(), 'economicon-landing-server-'));
  const rootDir = path.join(directory, 'dist');
  await mkdir(path.join(rootDir, 'assets'), { recursive: true });
  for (const [filename, value] of Object.entries({
    'index.html': '<h1>Economicon</h1>', '404.html': '<h1>Página no encontrada</h1><a href="/">Volver</a>',
    'styles.css': 'body {}', 'robots.txt': 'User-agent: *\nDisallow: /\n',
    'assets/economicon-mark.png': 'png-image', 'assets/dashboard-concept.png': 'png-image',
    'assets/Inter.woff2': 'font-bytes',
    '.env': 'SECRET=must-not-publish', 'export.csv': 'private-export', '_headers': 'hosting-configuration',
  })) await writeFile(path.join(rootDir, filename), value);
  await writeFile(path.join(directory, 'private.txt'), 'outside-secret');
  const server = await createPreviewServer({ rootDir });
  await new Promise((resolve) => server.listen(0, '127.0.0.1', resolve));
  t.after(async () => {
    await new Promise((resolve, reject) => server.close((error) => error ? reject(error) : resolve()));
    await rm(directory, { recursive: true, force: true });
  });
  function get(target, method = 'GET') {
    return new Promise((resolve, reject) => {
      const req = request({ hostname: '127.0.0.1', port: server.address().port, path: target, method }, (response) => {
        const chunks = [];
        response.on('data', (chunk) => chunks.push(chunk));
        response.on('end', () => resolve({ status: response.statusCode, headers: response.headers, body: Buffer.concat(chunks).toString('utf8') }));
      });
      req.on('error', reject);
      req.end();
    });
  }
  return { get, rootDir, directory };
}

test('preview serves known resources with correct MIME, restrictive headers and HEAD without body', async (t) => {
  const { get } = await fixture(t);
  const home = await get('/?utm_source=review');
  assert.equal(home.status, 200);
  assert.match(home.headers['content-type'], /^text\/html/u);
  assert.match(home.body, /Economicon/u);
  assert.match(home.headers['content-security-policy'], /script-src 'none'/u);
  assert.match(home.headers['content-security-policy'], /connect-src 'none'/u);
  assert.equal(home.headers['x-content-type-options'], 'nosniff');
  assert.equal(home.headers['x-frame-options'], 'DENY');
  assert.equal(home.headers['referrer-policy'], 'no-referrer');
  assert.equal(home.headers['x-robots-tag'], 'noindex, nofollow');
  assert.equal(home.headers['cache-control'], 'no-store');
  for (const [target, mime] of [['/styles.css', 'text/css'], ['/assets/economicon-mark.png', 'image/png'], ['/assets/dashboard-concept.png', 'image/png'], ['/assets/Inter.woff2', 'font/woff2'], ['/robots.txt', 'text/plain']]) {
    const response = await get(target);
    assert.equal(response.status, 200, target);
    assert.ok(response.headers['content-type'].startsWith(mime), target);
  }
  const head = await get('/', 'HEAD');
  assert.equal(head.status, 200);
  assert.equal(head.body, '');
  assert.equal(head.headers['content-length'], home.headers['content-length']);
});

test('unknown and private routes return a real branded 404, never the homepage or private bytes', async (t) => {
  const { get } = await fixture(t);
  for (const target of [
    '/does-not-exist', '/404.html', '/sitemap.xml', '/.env', '/export.csv', '/_headers', '/api/costs', '/login',
    '/../private.txt', '/%2e%2e/private.txt', '/assets/../../private.txt', '/assets/%2e%2e/%2e%2e/private.txt',
    '/%252e%252e%252fprivate.txt', '/assets%5c..%5c..%5cprivate.txt', '//index.html', '/%00index.html', '/%ZZ',
    '/C:/Windows/win.ini', '/assets/', 'http://example.org/',
  ]) {
    const response = await get(target);
    assert.equal(response.status, 404, target);
    assert.match(response.body, /Página no encontrada/u, target);
    assert.doesNotMatch(response.body, /outside-secret|must-not-publish|private-export|<h1>Economicon/u, target);
    assert.equal(response.headers['x-robots-tag'], 'noindex, nofollow');
  }
  const head = await get('/missing', 'HEAD');
  assert.equal(head.status, 404);
  assert.equal(head.body, '');
});

test('preview rejects write methods and never creates a form/API endpoint', async (t) => {
  const { get } = await fixture(t);
  for (const method of ['POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS']) {
    const response = await get('/', method);
    assert.equal(response.status, 405);
    assert.equal(response.headers.allow, 'GET, HEAD');
  }
});

test('an asset directory symlink cannot expose files outside dist', async (t) => {
  const { get, rootDir, directory } = await fixture(t);
  const outside = path.join(directory, 'outside');
  await mkdir(outside);
  await writeFile(path.join(outside, 'economicon-mark.png'), 'outside-secret');
  await rm(path.join(rootDir, 'assets'), { recursive: true });
  await symlink(outside, path.join(rootDir, 'assets'), process.platform === 'win32' ? 'junction' : 'dir');
  const response = await get('/assets/economicon-mark.png');
  assert.equal(response.status, 404);
  assert.doesNotMatch(response.body, /outside-secret/u);
  await assert.rejects(createPreviewServer({ rootDir: directory }), /real dist directory/u);
});

test('request parsing does not normalize traversal into a permitted public file', () => {
  assert.equal(requestFilename('/'), 'index.html');
  assert.equal(requestFilename('/index.html?review=yes'), 'index.html');
  for (const target of ['/assets/../index.html', '/./index.html', '/%2e/index.html', '/%2e%2e/index.html', '/%252e/index.html', '/index.html%00', '//index.html', '/index.html:stream']) {
    assert.equal(requestFilename(target), undefined, target);
  }
});
