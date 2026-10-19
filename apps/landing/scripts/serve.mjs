import { promises as fs } from 'node:fs';
import path from 'node:path';
import http from 'node:http';
import { fileURLToPath } from 'node:url';
import { appRoot, buildLanding, digest } from './build.mjs';
import { SECURITY_HEADERS } from './security.mjs';
export { SECURITY_HEADERS } from './security.mjs';
const TYPES = {'.html':'text/html; charset=utf-8','.css':'text/css; charset=utf-8','.js':'text/javascript; charset=utf-8','.json':'application/json; charset=utf-8','.txt':'text/plain; charset=utf-8','.xml':'application/xml; charset=utf-8','.png':'image/png','.woff2':'font/woff2'};
export async function createLandingServer({directory = path.join(appRoot, 'dist')} = {}) {
  const manifest = JSON.parse(await fs.readFile(path.join(directory, 'build-manifest.json'), 'utf8'));
  const files = new Map();
  if (manifest.version !== 1 || !Array.isArray(manifest.files)) throw new Error('Invalid public manifest');
  for (const item of manifest.files) {
    if (!/^(?:index\.html|404\.html|style\.css|app\.js|robots\.txt|sitemap\.xml|_headers|assets\/[A-Za-z0-9.-]+)$/.test(item.file)) throw new Error('Invalid public manifest path');
    const filename = path.join(directory, item.file);
    const stat = await fs.lstat(filename);
    if (!stat.isFile() || stat.isSymbolicLink()) throw new Error('Invalid public artifact file');
    const bytes = await fs.readFile(filename);
    if (digest(bytes) !== item.sha256 || bytes.length !== item.bytes) throw new Error('Public artifact integrity mismatch: ' + item.file);
    if (item.file === '_headers') continue;
    files.set('/' + item.file, {bytes, type:TYPES[path.extname(item.file)] || 'application/octet-stream', etag:'"'+item.sha256+'"'});
  }
  if (!files.has('/index.html') || !files.has('/404.html')) throw new Error('Public index/404 missing');
  return http.createServer((request, response) => {
    const send = (status, item) => { response.writeHead(status, {...SECURITY_HEADERS, 'Content-Type':item.type, 'Content-Length':item.bytes.length, ...(item.etag ? {ETag:item.etag} : {})}); response.end(request.method === 'HEAD' ? undefined : item.bytes); };
    if (!['GET','HEAD'].includes(request.method)) { response.writeHead(405,{...SECURITY_HEADERS,Allow:'GET, HEAD','Content-Type':'text/plain; charset=utf-8'}); response.end('Method not allowed'); return; }
    let pathname;
    try { pathname = decodeURIComponent(new URL(request.url, 'http://127.0.0.1').pathname); } catch { send(400,{bytes:Buffer.from('Bad request'),type:'text/plain; charset=utf-8'}); return; }
    if (pathname.includes('\\') || pathname.includes('\0') || pathname.split('/').includes('..')) { send(404,files.get('/404.html')); return; }
    const item = files.get(pathname === '/' ? '/index.html' : pathname);
    if (!item) { send(404,files.get('/404.html')); return; }
    if (request.headers['if-none-match'] === item.etag) { response.writeHead(304,{...SECURITY_HEADERS,ETag:item.etag}); response.end(); return; }
    send(200,item);
  });
}
if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const port = Number(process.env.PORT || 41790);
  if (!Number.isInteger(port) || port < 1024 || port > 65535) { console.error('PORT must be an unprivileged TCP port'); process.exitCode=1; }
  else { (async()=>{ const directory=process.env.LANDING_OUT_DIR || path.join(appRoot,'dist'); if (process.argv.includes('--build')) await buildLanding({outDir:directory}); const server = await createLandingServer({directory}); server.on('error',error=>{ console.error(error.message); process.exitCode=1; }); server.listen(port,'127.0.0.1',()=>console.log('Economicon landing http://127.0.0.1:'+port+'/')); for (const signal of ['SIGINT','SIGTERM']) process.on(signal,()=>server.close()); })().catch(error=>{console.error(error.message);process.exitCode=1;}); }
}
