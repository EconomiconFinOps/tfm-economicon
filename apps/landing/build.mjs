import { lstat, mkdir, readFile, realpath, rm, writeFile } from 'node:fs/promises';
import { isIP } from 'node:net';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const APP_DIR = path.dirname(fileURLToPath(import.meta.url));

// Reviewed public material only. Never copy a directory or the workspace recursively.
export const PUBLIC_FILES = Object.freeze([
  'index.html', '404.html', 'styles.css',
  'assets/economicon-mark.png',
  'assets/dashboard-concept.png',
  'assets/executive-cost-test.png',
  'assets/SpaceGrotesk.woff2',
  'assets/SpaceGrotesk-OFL.txt',
  'assets/Inter.woff2',
  'assets/Inter-OFL.txt',
]);
export const GENERATED_FILES = Object.freeze(['robots.txt', 'sitemap.xml', '_headers']);
export const SECURITY_HEADERS = Object.freeze({
  'Content-Security-Policy': "default-src 'none'; base-uri 'none'; script-src 'none'; style-src 'self'; img-src 'self'; font-src 'self'; connect-src 'none'; object-src 'none'; frame-src 'none'; frame-ancestors 'none'; form-action 'none'",
  'X-Content-Type-Options': 'nosniff',
  'Referrer-Policy': 'no-referrer',
  'Permissions-Policy': 'camera=(), microphone=(), geolocation=(), payment=()',
  'X-Frame-Options': 'DENY',
});

export function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (character) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
  })[character]);
}

// This is syntactic validation, not a DNS lookup or an assertion of publication approval.
// The build and browser never fetch video resources; an approved link remains opt-in.
export function publicHttpsUrl(value, { rootOnly = false, name = 'URL' } = {}) {
  if (value === undefined || value === '') return undefined;
  if (typeof value !== 'string' || value !== value.trim() || /[\\\u0000-\u0020\u007f]/u.test(value)) {
    throw new Error(`${name} must be a public HTTPS URL without whitespace or backslashes`);
  }
  let url;
  try { url = new URL(value); } catch { throw new Error(`${name} must be a valid absolute URL`); }
  const hostname = url.hostname.toLowerCase();
  const blockedSuffixes = /(?:^|\.)(?:localhost|local|localdomain|internal|intranet|lan|home|corp|test|invalid|example|onion|arpa)$/u;
  const labels = hostname.split('.');
  if (url.protocol !== 'https:' || url.username || url.password || url.port || isIP(hostname) ||
      hostname.includes(':') || hostname.length > 253 || labels.length < 2 ||
      blockedSuffixes.test(hostname) || !/^[a-z]{2,63}$/u.test(labels.at(-1)) ||
      labels.some((label) => !/^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$/u.test(label))) {
    throw new Error(`${name} requires HTTPS on a public DNS hostname, without credentials or custom ports`);
  }
  if (rootOnly && (url.pathname !== '/' || url.search || url.hash)) {
    throw new Error(`${name} must be a domain root without a path, query or fragment`);
  }
  if (rootOnly && !/^https:\/\/[^/?#]+\/?$/iu.test(value)) {
    throw new Error(`${name} must be a domain root without a path, query or fragment`);
  }
  return url.href;
}

function replaceOnce(source, token, replacement) {
  if (source.split(token).length !== 2) throw new Error(`index.html must contain exactly one ${token}`);
  return source.replace(token, replacement);
}

export function renderIndex(source, { siteUrl, videoUrl, videoTitle } = {}) {
  const site = publicHttpsUrl(siteUrl, { rootOnly: true, name: 'PUBLIC_SITE_URL' });
  const video = publicHttpsUrl(videoUrl, { name: 'PUBLIC_VIDEO_URL' });
  const title = videoTitle || 'Ver vídeo conceptual';
  if (typeof title !== 'string' || title.length > 160 || /[\u0000-\u001f\u007f]/u.test(title)) {
    throw new Error('PUBLIC_VIDEO_TITLE must contain at most 160 printable characters');
  }
  const metadata = [
    `<meta name="robots" content="${site ? 'index,follow' : 'noindex,nofollow'}">`,
    ...(site ? [
      `<link rel="canonical" href="${escapeHtml(site)}">`,
      `<meta property="og:url" content="${escapeHtml(site)}">`,
      `<meta property="og:image" content="${escapeHtml(new URL('assets/dashboard-concept.png', site).href)}">`,
    ] : []),
  ].join('\n    ');
  const videoSection = video
    ? `<p class="concept-video"><a href="${escapeHtml(video)}" rel="noopener noreferrer">${escapeHtml(title)}</a> · Pieza conceptual; no demuestra capacidades funcionales ni resultados.</p>`
    : '<p class="concept-video-status">Material audiovisual pendiente de publicación pública.</p>';
  return replaceOnce(replaceOnce(source, '<!-- PUBLIC_METADATA -->', metadata), '<!-- VIDEO_SECTION -->', videoSection);
}

function validateSources(files) {
  for (const filename of ['index.html', '404.html']) {
    const html = files.get(filename).toString('utf8');
    if (/<(?:script|iframe|form|object|embed)\b|\son[a-z]+\s*=|\sstyle\s*=/iu.test(html)) {
      throw new Error(`${filename}: scripts, forms, frames and inline handlers/styles are not allowed`);
    }
    const ids = new Set([...html.matchAll(/\bid=["']([^"']+)["']/gu)].map((match) => match[1]));
    for (const tag of html.matchAll(/<([a-z][a-z0-9:-]*)\b[^>]*>/giu)) {
      if (/\bsrcset\s*=/iu.test(tag[0])) throw new Error(`${filename}: srcset resources require an explicit review`);
      for (const match of tag[0].matchAll(/\b(href|src)=["']([^"']+)["']/giu)) {
        const [, attribute, target] = match;
        const link = tag[1].toLowerCase() === 'a' && attribute.toLowerCase() === 'href';
        if (target.startsWith('#') && ids.has(target.slice(1)) && link) continue;
        if ((target === '/' || target.startsWith('/#')) && link) continue;
        if (target.startsWith('/') && PUBLIC_FILES.includes(target.slice(1))) continue;
        if (link && target.startsWith('https://')) {
          publicHttpsUrl(target.replaceAll('&amp;', '&'));
          continue;
        }
        throw new Error(`${filename}: unsupported or missing link/resource ${target}`);
      }
    }
  }
  const css = files.get('styles.css').toString('utf8');
  if (/@import\b/iu.test(css)) throw new Error('styles.css: external imports are not allowed');
  for (const match of css.matchAll(/url\(\s*["']?([^\s"')]+)["']?\s*\)/giu)) {
    if (!PUBLIC_FILES.includes(match[1].replace(/^\//u, ''))) throw new Error(`styles.css: unsupported resource ${match[1]}`);
  }
  for (const [filename, content] of files) {
    if (filename.endsWith('.svg') && /<(?:script|foreignObject)\b|\son[a-z]+\s*=|(?:href|src)\s*=\s*["'](?!#)/iu.test(content.toString('utf8'))) {
      throw new Error(`${filename}: SVG must not contain active or external content`);
    }
  }
}

async function readPublicFile(sourceDir, filename) {
  let current = sourceDir;
  for (const part of filename.split('/')) {
    current = path.join(current, part);
    if ((await lstat(current)).isSymbolicLink()) throw new Error(`Public source must not contain symlinks: ${filename}`);
  }
  const stat = await lstat(current);
  if (!stat.isFile() || stat.size > 10 * 1024 * 1024) throw new Error(`Invalid public file: ${filename}`);
  return readFile(current);
}

export async function build({
  sourceDir = path.join(APP_DIR, 'src'),
  outputDir = path.join(path.dirname(sourceDir), 'dist'),
  siteUrl = process.env.PUBLIC_SITE_URL,
  videoUrl = process.env.PUBLIC_VIDEO_URL,
  videoTitle = process.env.PUBLIC_VIDEO_TITLE,
} = {}) {
  sourceDir = path.resolve(sourceDir);
  outputDir = path.resolve(outputDir);
  // The only recursively replaced directory is the src directory's sibling named dist.
  // Resolve and verify its parent before touching it, including on Windows.
  if (outputDir !== path.join(path.dirname(sourceDir), 'dist') || path.basename(sourceDir) !== 'src' ||
      (await lstat(sourceDir)).isSymbolicLink() ||
      await realpath(path.dirname(outputDir)) !== path.dirname(await realpath(sourceDir))) {
    throw new Error('Output must be the real source directory\'s sibling dist directory');
  }
  const existingOutput = await lstat(outputDir).catch((error) => {
    if (error.code === 'ENOENT') return undefined;
    throw error;
  });
  if (existingOutput?.isSymbolicLink()) throw new Error('Refusing to replace a symlinked dist directory');
  const site = publicHttpsUrl(siteUrl, { rootOnly: true, name: 'PUBLIC_SITE_URL' });
  const files = new Map(await Promise.all(PUBLIC_FILES.map(async (filename) => [filename, await readPublicFile(sourceDir, filename)])));
  validateSources(files);
  files.set('index.html', renderIndex(files.get('index.html').toString('utf8'), { siteUrl, videoUrl, videoTitle }));
  files.set('robots.txt', site
    ? `User-agent: *\nAllow: /\nDisallow: /404.html\nSitemap: ${new URL('sitemap.xml', site).href}\n`
    : 'User-agent: *\nDisallow: /\n');
  if (site) files.set('sitemap.xml', `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>${escapeHtml(site)}</loc></url></urlset>\n`);
  files.set('_headers', `/*\n${Object.entries(SECURITY_HEADERS).map(([name, value]) => `  ${name}: ${value}`).join('\n')}\n${site ? '' : '  X-Robots-Tag: noindex, nofollow\n'}/404.html\n  X-Robots-Tag: noindex, nofollow\n`);
  await rm(outputDir, { recursive: true, force: true });
  for (const [filename, contents] of files) {
    const destination = path.join(outputDir, filename);
    await mkdir(path.dirname(destination), { recursive: true });
    await writeFile(destination, contents);
  }
  return { outputDir, files: [...files.keys()], indexable: Boolean(site), hasConceptVideo: Boolean(videoUrl) };
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  try {
    const result = await build();
    console.log(`Landing built: ${result.files.length} public files in ${result.outputDir} (${result.indexable ? 'approved-domain metadata enabled' : 'preview: noindex'})`);
  } catch (error) {
    console.error(error.message);
    process.exitCode = 1;
  }
}
