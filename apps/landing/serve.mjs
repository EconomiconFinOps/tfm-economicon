import { createServer } from 'node:http';
import { lstat, readFile, realpath } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { PUBLIC_FILES, SECURITY_HEADERS } from './build.mjs';

const APP_DIR = path.dirname(fileURLToPath(import.meta.url));
const SERVED_FILES = new Set([...PUBLIC_FILES, 'robots.txt', 'sitemap.xml']);
const MIME_TYPES = {
  '.html': 'text/html; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.svg': 'image/svg+xml',
  '.png': 'image/png',
  '.webp': 'image/webp',
  '.woff2': 'font/woff2',
  '.ttf': 'font/ttf',
  '.txt': 'text/plain; charset=utf-8',
  '.xml': 'application/xml; charset=utf-8',
};

export function requestFilename(requestTarget) {
  if (!requestTarget?.startsWith('/') || requestTarget.startsWith('//')) return undefined;
  let pathname;
  try { pathname = decodeURIComponent(requestTarget.split('?')[0]); } catch { return undefined; }
  if (/[\\%:#\u0000-\u0020\u007f]/u.test(pathname) || pathname.includes('//') ||
      pathname.split('/').some((part) => part === '.' || part === '..')) return undefined;
  const filename = pathname === '/' ? 'index.html' : pathname.slice(1);
  return SERVED_FILES.has(filename) ? filename : undefined;
}

export async function createPreviewServer({ rootDir = path.join(APP_DIR, 'dist') } = {}) {
  rootDir = path.resolve(rootDir);
  if (path.basename(rootDir) !== 'dist' || (await lstat(rootDir)).isSymbolicLink()) {
    throw new Error('Preview serves only a real dist directory');
  }
  const realRoot = await realpath(rootDir);

  async function publicFile(filename) {
    if (!SERVED_FILES.has(filename)) return undefined;
    let target = rootDir;
    try {
      for (const segment of filename.split('/')) {
        target = path.join(target, segment);
        if ((await lstat(target)).isSymbolicLink()) return undefined;
      }
      const resolved = await realpath(target);
      if (!resolved.startsWith(`${realRoot}${path.sep}`) || !(await lstat(resolved)).isFile()) return undefined;
      return await readFile(resolved);
    } catch (error) {
      if (['ENOENT', 'ENOTDIR', 'EACCES', 'EPERM'].includes(error.code)) return undefined;
      throw error;
    }
  }

  return createServer(async (request, response) => {
    const headers = {
      ...SECURITY_HEADERS,
      'Cache-Control': 'no-store',
      'X-Robots-Tag': 'noindex, nofollow',
    };
    const send = (status, contents, mime = 'text/plain; charset=utf-8', extra = {}) => {
      response.writeHead(status, { ...headers, ...extra, 'Content-Type': mime, 'Content-Length': Buffer.byteLength(contents) });
      response.end(request.method === 'HEAD' ? undefined : contents);
    };
    if (!['GET', 'HEAD'].includes(request.method)) return send(405, 'Method not allowed\n', undefined, { Allow: 'GET, HEAD' });
    try {
      const filename = requestFilename(request.url);
      const contents = filename ? await publicFile(filename) : undefined;
      if (contents !== undefined && filename !== '404.html') {
        return send(200, contents, MIME_TYPES[path.extname(filename)]);
      }
      const notFound = await publicFile('404.html');
      return send(404, notFound ?? 'Not found\n', notFound ? MIME_TYPES['.html'] : undefined);
    } catch {
      return send(500, 'Unable to serve the public page\n');
    }
  });
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  try {
    const value = process.env.PORT || '4179';
    if (!/^\d+$/u.test(value) || Number(value) < 1 || Number(value) > 65535) throw new Error('PORT must be an integer from 1 to 65535');
    const server = await createPreviewServer();
    server.on('error', (error) => { console.error(error.message); process.exitCode = 1; });
    server.listen(Number(value), '127.0.0.1', () => console.log(`Landing preview: http://127.0.0.1:${value} (local only; noindex)`));
  } catch (error) {
    console.error(error.code === 'ENOENT' ? 'No dist directory. Run the landing build first.' : error.message);
    process.exitCode = 1;
  }
}
