import { promises as fs } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createHash, randomUUID } from 'node:crypto';
import { SECURITY_HEADERS } from './security.mjs';

export const appRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
export const PUBLIC_INPUTS = Object.freeze(['index.html', 'style.css', 'app.js', '404.html', 'assets/economicon-primary.png', 'assets/economicon-inverse.png', 'assets/favicon.png', 'assets/Inter.woff2', 'assets/SpaceGrotesk.woff2', 'assets/Inter-OFL.txt', 'assets/SpaceGrotesk-OFL.txt']);
export const digest = bytes => createHash('sha256').update(bytes).digest('hex');
export function parseOrigin(value = '') {
  if (!value) return null;
  let url;
  try { url = new URL(value); } catch { throw new Error('SITE_ORIGIN must be an HTTPS root origin'); }
  if (url.protocol !== 'https:' || url.username || url.password || url.pathname !== '/' || url.search || url.hash || url.port || url.hostname === 'localhost' || url.hostname.endsWith('.localhost') || url.hostname.startsWith('[') || /^\d+(?:\.\d+){3}$/.test(url.hostname)) throw new Error('SITE_ORIGIN must be a public HTTPS root origin without credentials, port, path, query or fragment');
  return url.origin;
}
async function readPublicInput(sourceDir, relative) {
  const components = relative.split('/');
  let current = sourceDir;
  for (const component of ['', ...components]) {
    if (component) current = path.join(current, component);
    const stat = await fs.lstat(current);
    if (stat.isSymbolicLink()) throw new Error('Symbolic public input rejected: ' + relative);
    if (current !== path.join(sourceDir, ...components) && !stat.isDirectory()) throw new Error('Public input parent is not a directory');
  }
  if (!(await fs.lstat(current)).isFile()) throw new Error('Public input is not a regular file: ' + relative);
  return fs.readFile(current);
}
const escapeXml = value => value.replaceAll('&', '&amp;').replaceAll('"', '&quot;').replaceAll('<', '&lt;').replaceAll('>', '&gt;');
export async function buildLanding({sourceDir = path.join(appRoot, 'src'), outDir = path.join(appRoot, 'dist'), origin = process.env.SITE_ORIGIN ?? ''} = {}) {
  sourceDir = path.resolve(sourceDir); outDir = path.resolve(outDir);
  if (path.basename(outDir) !== 'dist' || sourceDir === outDir || sourceDir.startsWith(outDir + path.sep)) throw new Error('Output must be a dedicated dist directory outside source');
  const publicOrigin = parseOrigin(origin);
  const files = new Map();
  for (const relative of PUBLIC_INPUTS) files.set(relative, await readPublicInput(sourceDir, relative));
  const metadata = [
    '<meta name="robots" content="' + (publicOrigin ? 'index,follow' : 'noindex,nofollow') + '">',
    '<meta property="og:type" content="website"><meta property="og:locale" content="es_ES">',
    '<meta property="og:site_name" content="Economicon"><meta property="og:title" content="Economicon — El gasto. Con contexto.">',
    '<meta property="og:description" content="Costes observados, señales candidatas y contexto con fuentes. Recorrido ilustrativo de Economicon.">',
    '<meta property="og:image" content="' + (publicOrigin || '') + '/assets/economicon-primary.png">',
    '<meta property="og:image:alt" content="Logotipo original de Economicon">',
    '<meta name="twitter:card" content="summary">',
    publicOrigin ? '<link rel="canonical" href="' + escapeXml(publicOrigin) + '/"><meta property="og:url" content="' + escapeXml(publicOrigin) + '/">' : ''
  ].join('');
  const inputHtml = files.get('index.html').toString('utf8');
  if (!inputHtml.includes('<!-- PUBLIC_METADATA -->')) throw new Error('Missing public metadata marker');
  files.set('index.html', Buffer.from(inputHtml.replace('<!-- PUBLIC_METADATA -->', metadata)));
  files.set('robots.txt', Buffer.from(publicOrigin ? 'User-agent: *\nAllow: /\nSitemap: ' + publicOrigin + '/sitemap.xml\n' : 'User-agent: *\nDisallow: /\n'));
  files.set('sitemap.xml', Buffer.from('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + (publicOrigin ? '<url><loc>' + escapeXml(publicOrigin) + '/</loc></url>' : '') + '</urlset>\n'));
  const hostHeaders = {...SECURITY_HEADERS, ...(publicOrigin ? {'Strict-Transport-Security':'max-age=31536000'} : {'X-Robots-Tag':'noindex, nofollow'})};
  files.set('_headers', Buffer.from('/*\n' + Object.entries(hostHeaders).map(([name,value])=>'  '+name+': '+value).join('\n')+'\n'));
  const manifest = {version: 1, mode: publicOrigin ? 'public-origin-configured' : 'local-noindex', origin: publicOrigin, files: [...files].map(([file, bytes]) => ({file, bytes: bytes.length, sha256: digest(bytes)}))};
  files.set('build-manifest.json', Buffer.from(JSON.stringify(manifest, null, 2) + '\n'));
  const parent = path.dirname(outDir); await fs.mkdir(parent, {recursive: true});
  const temporary = await fs.mkdtemp(path.join(parent, 'dist.tmp-'));
  const backup = path.join(parent, 'dist.previous-' + randomUUID());
  const removeOwned = async target => { if (path.dirname(target) !== parent || !/^dist\.(?:tmp-|previous-)/.test(path.basename(target))) throw new Error('Unsafe temporary output path'); await fs.rm(target, {recursive: true, force: true}); };
  let backedUp = false; let published = false;
  try {
    for (const [relative, bytes] of files) { const destination = path.join(temporary, relative); await fs.mkdir(path.dirname(destination), {recursive: true}); await fs.writeFile(destination, bytes); }
    try { const stat = await fs.lstat(outDir); if (!stat.isDirectory() || stat.isSymbolicLink()) throw new Error('Output is not an owned directory'); await fs.rename(outDir, backup); backedUp = true; } catch (error) { if (error.code !== 'ENOENT') throw error; }
    try { await fs.rename(temporary, outDir); published = true; } catch (error) { if (backedUp) { await fs.rename(backup, outDir); backedUp = false; } throw error; }
    return manifest;
  } finally { if (!published) await removeOwned(temporary); if (published && backedUp) await removeOwned(backup); }
}
if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  buildLanding({outDir:process.env.LANDING_OUT_DIR || path.join(appRoot, 'dist')}).then(manifest => console.log(JSON.stringify({mode: manifest.mode, files: manifest.files.length, bytes: manifest.files.reduce((sum, item) => sum + item.bytes, 0)}))).catch(error => { console.error(error.message); process.exitCode = 1; });
}
