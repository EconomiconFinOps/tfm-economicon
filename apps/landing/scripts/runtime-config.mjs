import {localMediaPath} from './public-media.mjs';
import { isIP } from 'node:net';

// These destinations are intentionally public. Never pass signed or secret URLs.
export function publicDestination(value) {
  if (typeof value !== 'string' || !value || value.length > 4096 || /[\u0000-\u0020\u007f\\]/u.test(value)) return null;
  let url;
  try { url = new URL(value); } catch { return null; }
  const host = url.hostname;
  if (url.protocol !== 'https:' || url.username || url.password || url.port ||
      isIP(host) || host.startsWith('[') || !host.includes('.') ||
      /(?:^|\.)(?:localhost|local|internal|lan|home|test|invalid)$/i.test(host) || host.endsWith('.')) return null;
  if ([...url.searchParams.keys()].some(key => /(?:token|secret|password|credential|signature|api[-_]?key|authorization|x-amz-|x-goog-)/i.test(key))) return null;
  return url.href;
}
export function readPublicConfig(environment = {}) {
  return Object.freeze({videoUrl: localMediaPath(environment.LANDING_VIDEO_URL) || publicDestination(environment.LANDING_VIDEO_URL), appUrl: publicDestination(environment.LANDING_APP_URL)});
}
export function serializePublicConfig(config) {
  // Rebuild the closed schema even when a caller supplies additional properties.
  const publicConfig = readPublicConfig({LANDING_VIDEO_URL:config?.videoUrl, LANDING_APP_URL:config?.appUrl});
  const json = JSON.stringify(publicConfig).replace(/</g, '\\u003c').replace(/\u2028/g, '\\u2028').replace(/\u2029/g, '\\u2029');
  return `globalThis.__LANDING_PUBLIC_CONFIG__ = Object.freeze(${json});\n`;
}


export function serializeLlmsDescription(description, config) {
  const appUrl = publicDestination(config?.appUrl);
  const overview = description.trimEnd() + '\n';
  return appUrl ? overview + '\n## Aplicación\n\n- [Abrir la aplicación](<' + appUrl + '>): Puede requerir autorización.\n' : overview;
}
