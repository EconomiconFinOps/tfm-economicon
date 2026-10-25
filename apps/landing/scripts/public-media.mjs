import {promises as fs, constants} from 'node:fs';
import path from 'node:path';
import {createHash} from 'node:crypto';

export const MAX_MEDIA_BYTES = 50 * 1024 * 1024;
const NAME = /^[A-Za-z0-9][A-Za-z0-9_-]{0,79}\.mp4$/;
export function localMediaPath(value) {
  if (typeof value !== 'string' || !value.startsWith('/media/')) return null;
  const name = value.slice(7);
  return NAME.test(name) ? value : null;
}

async function boundedRegularFile(directory, name, limit) {
  const handle = await fs.open(path.join(directory, name), constants.O_RDONLY | (constants.O_NOFOLLOW || 0));
  try {
    const stat = await handle.stat();
    if (!stat.isFile() || stat.size < 1 || stat.size > limit) throw new Error('Invalid media file');
    const bytes = Buffer.alloc(stat.size + 1);
    let used = 0;
    while (used < bytes.length) {
      const {bytesRead} = await handle.read(bytes, used, bytes.length - used, null);
      if (!bytesRead) break;
      used += bytesRead;
    }
    if (used !== stat.size) throw new Error('Media changed during read');
    return bytes.subarray(0, used);
  } finally { await handle.close(); }
}

// The selected file is hashed once and kept in memory. Later host writes cannot
// change a running response. A read-only bind mount alone is not immutability.
export async function loadMediaSnapshot(directory, videoUrl) {
  const route = localMediaPath(videoUrl);
  if (!route) return null;
  try {
    const root = await fs.lstat(directory);
    if (!root.isDirectory() || root.isSymbolicLink()) return null;
    for (const name of ['manifest.json', route.slice(7)]) {
      const stat = await fs.lstat(path.join(directory, name));
      if (!stat.isFile() || stat.isSymbolicLink()) return null;
    }
    const manifest = JSON.parse((await boundedRegularFile(directory, 'manifest.json', 16384)).toString('utf8'));
    if (!manifest || Object.keys(manifest).sort().join() !== 'files,version' || manifest.version !== 1 ||
        !Array.isArray(manifest.files) || manifest.files.length < 1 || manifest.files.length > 16) return null;
    const names = new Set();
    for (const file of manifest.files) {
      if (!file || Object.keys(file).sort().join() !== 'bytes,mimeType,name,sha256' || file.mimeType !== 'video/mp4' || !NAME.test(file.name) || names.has(file.name) ||
          !Number.isSafeInteger(file.bytes) || file.bytes < 8 || file.bytes > MAX_MEDIA_BYTES ||
          typeof file.sha256 !== 'string' || !/^[a-f0-9]{64}$/.test(file.sha256)) return null;
      names.add(file.name);
    }
    const file = manifest.files.find(file => file.name === route.slice(7));
    if (!file) return null;
    const bytes = await boundedRegularFile(directory, file.name, file.bytes);
    if (bytes.length !== file.bytes || bytes.toString('ascii', 4, 8) !== 'ftyp' ||
        createHash('sha256').update(bytes).digest('hex') !== file.sha256) return null;
    return Object.freeze({route, bytes});
  } catch {
    // Media failures disable only the media route; app/configuration stay usable.
    return null;
  }
}

// null: ignore unsupported unit/multipart; false: invalid/unsatisfiable bytes.
// RFC9110: Range applies only to GET; callers handle HEAD and If-Range separately.
export function singleByteRange(value, length) {
  if (typeof value !== 'string' || !value.startsWith('bytes=') || value.includes(',')) return null;
  if (value.length > 256) return false;
  const match = /^bytes=(\d*)-(\d*)$/.exec(value);
  if (!match || (!match[1] && !match[2])) return false;
  const size = BigInt(length);
  if (!match[1]) {
    const suffix = BigInt(match[2]);
    return suffix > 0n ? {start:Number(suffix >= size ? 0n : size - suffix), end:length - 1} : false;
  }
  const start = BigInt(match[1]);
  const end = match[2] ? BigInt(match[2]) : size - 1n;
  if (start >= size || start > end) return false;
  return {start:Number(start), end:Number(end >= size ? size - 1n : end)};
}
