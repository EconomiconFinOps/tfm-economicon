import test from 'node:test';
import assert from 'node:assert/strict';
import {promises as fs} from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';

const repoRoot = fileURLToPath(new URL('../', import.meta.url));
const launcher = path.join(repoRoot, 'node_modules/turbo/bin/turbo');

async function plans(t) {
  const root = await fs.mkdtemp(path.join(os.tmpdir(), 'economicon-landing-turbo-'));
  t.after(async () => {
    if (path.dirname(root) !== path.resolve(os.tmpdir()) || !path.basename(root).startsWith('economicon-landing-turbo-')) throw new Error('Unsafe fixture cleanup');
    await fs.rm(root, {recursive:true, force:true});
  });
  return (task, overrides = {}) => {
    // Dry runs never execute a workspace task or write its .turbo task log.
    const output = execFileSync(process.execPath, [launcher, 'run', task, '--filter=@finops/landing', '--dry-run=json', '--no-update-notifier', '--cache-dir=' + path.join(root, 'cache')], {
      cwd:repoRoot, encoding:'utf8', maxBuffer:4 * 1024 * 1024,
      env:{...process.env, TURBO_TELEMETRY_DISABLED:'1', SITE_ORIGIN:'https://landing.example.test', LANDING_OUT_DIR:path.join(root, 'first', 'dist'), PORT:'41791', LANDING_VIDEO_URL:'https://video.example.org/one', LANDING_APP_URL:'https://app.example.org/one', ...overrides}
    });
    return JSON.parse(output).tasks.find(item => item.taskId === '@finops/landing#' + task);
  };
}

test('workspace build preserves public origin and external destination without cached artifact replay', async t => {
  const plan = await plans(t);
  const first = plan('build');
  const otherOrigin = plan('build', {SITE_ORIGIN:'https://other.example.test'});
  const otherDestination = plan('build', {LANDING_OUT_DIR:path.join(os.tmpdir(), 'economicon-output-example', 'dist')});
  assert.equal(first.hash, plan('build',{LANDING_VIDEO_URL:'https://other.example.org/video',LANDING_APP_URL:'https://other.example.org/app'}).hash, 'runtime destinations must not alter the build hash');
  assert.equal(first.envMode, 'strict');
  assert.deepEqual([...first.environmentVariables.specified.env].sort(), ['LANDING_OUT_DIR','SITE_ORIGIN']);
  assert.equal(first.environmentVariables.configured.length, 2);
  assert.notEqual(first.hash, otherOrigin.hash, 'origin must affect the resolved task hash');
  assert.notEqual(first.hash, otherDestination.hash, 'destination must affect the resolved task hash');
  assert.equal(first.resolvedTaskDefinition.cache, false, 'external destinations cannot be restored from a workspace-relative artifact cache');
  assert.deepEqual(first.resolvedTaskDefinition.outputs, []);
});

test('workspace development preserves origin, external output and the requested port', async t => {
  const plan = await plans(t);
  const first = plan('dev');
  const otherPort = plan('dev', {PORT:'41792'});
  assert.equal(first.envMode, 'strict');
  assert.deepEqual([...first.environmentVariables.specified.env].sort(), ['LANDING_APP_URL','LANDING_OUT_DIR','LANDING_VIDEO_URL','PORT','SITE_ORIGIN']);
  assert.equal(first.environmentVariables.configured.length, 5);
  assert.notEqual(first.hash, otherPort.hash);
  assert.equal(first.resolvedTaskDefinition.cache, false);
  assert.equal(first.resolvedTaskDefinition.persistent, true);
});
