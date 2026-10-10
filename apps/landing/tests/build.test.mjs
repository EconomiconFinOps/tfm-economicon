import assert from 'node:assert/strict';
import { cp, lstat, mkdir, mkdtemp, readFile, readdir, rm, symlink, writeFile } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import test from 'node:test';
import { build, PUBLIC_FILES, publicHttpsUrl, renderIndex } from '../build.mjs';

const SOURCE = '<!doctype html><html lang="es"><head><title>Economicon</title><!-- PUBLIC_METADATA --><link rel="stylesheet" href="/styles.css"></head><body><main id="producto"><h1>FinOps sin fricción.</h1><a href="#producto">Producto</a><!-- VIDEO_SECTION --></main></body></html>';

async function fixture(t) {
  const directory = await mkdtemp(path.join(os.tmpdir(), 'economicon-landing-build-'));
  t.after(() => rm(directory, { recursive: true, force: true }));
  const sourceDir = path.join(directory, 'src');
  for (const filename of PUBLIC_FILES) {
    await mkdir(path.dirname(path.join(sourceDir, filename)), { recursive: true });
    await writeFile(path.join(sourceDir, filename), filename === 'index.html' ? SOURCE
      : filename === '404.html' ? '<html lang="es"><head><meta name="robots" content="noindex,nofollow"></head><body><h1>404</h1><a href="/">Volver</a></body></html>'
      : filename === 'styles.css' ? 'body { color: #14121f; }'
      : filename.endsWith('.svg') ? '<svg xmlns="http://www.w3.org/2000/svg"><path d="M0 0"/></svg>' : 'reviewed-image-fixture');
  }
  return { sourceDir, outputDir: path.join(directory, 'dist'), siteUrl: '', videoUrl: '', videoTitle: '' };
}

async function allFiles(directory, prefix = '') {
  const files = [];
  for (const item of await readdir(directory, { withFileTypes: true })) {
    const name = prefix + item.name;
    if (item.isDirectory()) files.push(...await allFiles(path.join(directory, item.name), `${name}/`));
    else files.push(name);
  }
  return files.sort();
}

test('default build publishes only reviewed files and regenerates a stale dist without private material', async (t) => {
  const config = await fixture(t);
  await writeFile(path.join(config.sourceDir, '.env'), 'TOKEN=private-value');
  await writeFile(path.join(config.sourceDir, 'cost-export.csv'), 'subscription,cost');
  await writeFile(path.join(config.sourceDir, 'assets', 'unreviewed.txt'), 'private');
  await mkdir(config.outputDir);
  await writeFile(path.join(config.outputDir, 'old-export.json'), 'private');
  const result = await build(config);
  assert.equal(result.indexable, false);
  assert.equal(result.hasConceptVideo, false);
  assert.deepEqual(await allFiles(config.outputDir), [...PUBLIC_FILES, '_headers', 'robots.txt'].sort());
  const html = await readFile(path.join(config.outputDir, 'index.html'), 'utf8');
  assert.match(html, /name="robots" content="noindex,nofollow"/u);
  assert.doesNotMatch(html, /rel="canonical"|og:url|og:image|class="concept-video"|PUBLIC_METADATA|VIDEO_SECTION|private-value/u);
  assert.match(html, /Material audiovisual pendiente de publicación pública/u);
  assert.equal(await readFile(path.join(config.outputDir, 'robots.txt'), 'utf8'), 'User-agent: *\nDisallow: /\n');
  assert.match(await readFile(path.join(config.outputDir, '_headers'), 'utf8'), /connect-src 'none'/u);
});

test('approved root adds consistent canonical, absolute social image, sitemap and robots', async (t) => {
  const config = await fixture(t);
  const result = await build({ ...config, siteUrl: 'https://economicon.example.org' });
  assert.equal(result.indexable, true);
  const html = await readFile(path.join(config.outputDir, 'index.html'), 'utf8');
  assert.match(html, /rel="canonical" href="https:\/\/economicon\.example\.org\/"/u);
  assert.match(html, /property="og:image" content="https:\/\/economicon\.example\.org\/assets\/dashboard-concept\.png"/u);
  assert.match(html, /content="index,follow"/u);
  assert.match(await readFile(path.join(config.outputDir, 'sitemap.xml'), 'utf8'), /<loc>https:\/\/economicon\.example\.org\/<\/loc>/u);
  assert.match(await readFile(path.join(config.outputDir, 'robots.txt'), 'utf8'), /Sitemap: https:\/\/economicon\.example\.org\/sitemap\.xml/u);
  assert.match(await readFile(path.join(config.outputDir, '404.html'), 'utf8'), /noindex,nofollow/u);
  // Rebuilding preview after a public configuration must remove the old sitemap.
  await build(config);
  await assert.rejects(lstat(path.join(config.outputDir, 'sitemap.xml')), { code: 'ENOENT' });
});

test('concept video remains an escaped, explicitly marked external link, with no embeds or fetches', () => {
  const html = renderIndex(SOURCE, {
    videoUrl: 'https://video.example.org/watch?v=concept&source=landing',
    videoTitle: 'Concepto "Economicon" <prueba> & equipo',
  });
  assert.match(html, /href="https:\/\/video\.example\.org\/watch\?v=concept&amp;source=landing"/u);
  assert.match(html, /Concepto &quot;Economicon&quot; &lt;prueba&gt; &amp; equipo/u);
  assert.match(html, /Pieza conceptual; no demuestra capacidades funcionales ni resultados/u);
  assert.doesNotMatch(html, /pendiente de publicación pública/u);
  assert.doesNotMatch(html, /<iframe|<script|<video/u);
});

test('rejects unsafe, non-public or non-root publication URLs', () => {
  for (const value of [
    'http://economicon.example.org', 'javascript:alert(1)', 'https://user:secret@example.org/',
    'https://localhost/', 'https://localhost.example/', 'https://dev.internal/', 'https://service.local/',
    'https://router.lan/', 'https://127.0.0.1/', 'https://10.0.0.1/', 'https://169.254.169.254/',
    'https://2130706433/', 'https://0x7f000001/', 'https://[::1]/', 'https://example.org:8443/',
    'https://example.org/path', 'https://example.org/?query=x', 'https://example.org/#fragment', 'https://example.org/a/..',
    'https://example.org./', ' https://example.org/', 'https://example.org/\n', 'https://example.org\\secret',
    'https://-invalid.example.org/', '//example.org/',
  ]) {
    assert.throws(() => publicHttpsUrl(value, { rootOnly: true }), undefined, value);
  }
  assert.equal(publicHttpsUrl('https://economicon.example.org', { rootOnly: true }), 'https://economicon.example.org/');
  assert.equal(publicHttpsUrl(undefined), undefined);
  assert.equal(publicHttpsUrl(''), undefined);
});

test('invalid configuration fails before replacing existing output', async (t) => {
  const config = await fixture(t);
  await mkdir(config.outputDir);
  await writeFile(path.join(config.outputDir, 'sentinel.txt'), 'preserve until validated');
  await assert.rejects(build({ ...config, videoUrl: 'https://127.0.0.1/' }), /public DNS hostname/u);
  assert.equal(await readFile(path.join(config.outputDir, 'sentinel.txt'), 'utf8'), 'preserve until validated');
  await assert.rejects(build({ ...config, outputDir: config.sourceDir }), /sibling dist/u);
  assert.equal(await readFile(path.join(config.sourceDir, 'index.html'), 'utf8'), SOURCE);
});

test('missing anchors/resources, scripts, forms and external imports fail the build', async (t) => {
  const config = await fixture(t);
  for (const fragment of ['<a href="#missing">Missing</a>', '<img src="/assets/private.csv">', '<link rel="stylesheet" href="https://example.org/font.css">', '<script>alert(1)</script>', '<form action="/signup"></form>', '<div onclick="alert(1)"></div>', '<div style="color:red"></div>']) {
    await writeFile(path.join(config.sourceDir, 'index.html'), SOURCE.replace('</main>', `${fragment}</main>`));
    await assert.rejects(build(config), /not allowed|unsupported or missing/u);
  }
  await writeFile(path.join(config.sourceDir, 'index.html'), SOURCE);
  await writeFile(path.join(config.sourceDir, 'styles.css'), '@import "https://example.org/font.css";');
  await assert.rejects(build(config), /external imports/u);
  await writeFile(path.join(config.sourceDir, 'styles.css'), 'body { background: url(https://example.org/tracker.png); }');
  await assert.rejects(build(config), /unsupported resource/u);
});

test('required placeholders are unique and video titles cannot introduce controls or huge text', () => {
  assert.throws(() => renderIndex(SOURCE.replace('<!-- PUBLIC_METADATA -->', '')), /exactly one/u);
  assert.throws(() => renderIndex(SOURCE + '<!-- VIDEO_SECTION -->'), /exactly one/u);
  assert.throws(() => renderIndex(SOURCE, { videoTitle: '\nunsafe' }), /printable/u);
  assert.throws(() => renderIndex(SOURCE, { videoTitle: 'a'.repeat(161) }), /160/u);
});

test('source and output symlinks cannot publish outside files', async (t) => {
  const config = await fixture(t);
  const outside = path.join(path.dirname(config.sourceDir), 'outside');
  await mkdir(outside);
  await writeFile(path.join(outside, 'economicon-mark.png'), 'secret-image');
  const assets = path.join(config.sourceDir, 'assets');
  await rm(assets, { recursive: true });
  // Windows junctions do not require the symbolic-link privilege.
  await symlink(outside, assets, process.platform === 'win32' ? 'junction' : 'dir');
  await assert.rejects(build(config), /symlinks/u);
  await symlink(outside, config.outputDir, process.platform === 'win32' ? 'junction' : 'dir');
  await assert.rejects(build(config), /symlinked dist/u);
  assert.equal(await readFile(path.join(outside, 'economicon-mark.png'), 'utf8'), 'secret-image');
});

test('the actual authored landing builds without external runtime resources', async (t) => {
  const config = await fixture(t);
  const source = fileURLToPath(new URL('../src/', import.meta.url));
  await cp(source, config.sourceDir, { recursive: true });
  await build(config);
  const html = await readFile(path.join(config.outputDir, 'index.html'), 'utf8');
  assert.match(html, /<html[^>]*lang="es"/u);
  assert.match(html, /<h1[\s>]/u);
  assert.match(html, /Proyecto en desarrollo/u);
  assert.match(html, /github\.com\/EconomiconFinOps\/tfm-economicon/u);
  assert.doesNotMatch(html, /<script|<iframe|<form|<img[^>]+src="https?:/iu);
});
