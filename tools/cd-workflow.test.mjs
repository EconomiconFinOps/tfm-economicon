import assert from 'node:assert/strict';
import fs from 'node:fs';
import test from 'node:test';
import { parse } from 'yaml';

const cd = parse(fs.readFileSync(new URL('../.github/workflows/cd.yml', import.meta.url), 'utf8'));
const ci = parse(fs.readFileSync(new URL('../.github/workflows/ci.yml', import.meta.url), 'utf8'));

test('CD only gates trusted develop and reuses all CI jobs without inherited secrets', () => {
  assert.deepEqual(cd.on.push.branches, ['develop']);
  assert.equal(cd.on.pull_request, undefined);
  assert.equal(cd.on.pull_request_target, undefined);
  assert.equal(cd.jobs.validate.if, "github.ref == 'refs/heads/develop'");
  assert.equal(cd.jobs.validate.uses, './.github/workflows/ci.yml');
  assert.ok(Object.hasOwn(ci.on, 'workflow_call'));
  assert.equal(cd.jobs.validate.secrets, undefined);
  assert.deepEqual(cd.permissions, { contents: 'read' });
});

test('eligibility waits for CI and never claims server runtime success', () => {
  assert.equal(cd.jobs.eligible.needs, 'validate');
  assert.equal(cd.jobs.eligible.if, undefined);
  const script = cd.jobs.eligible.steps[0].run;
  assert.match(script, /does not claim runtime success/);
  assert.doesNotMatch(script, /ssh |curl |docker /);
});

test('runtime tests run in reused CI and the timer never executes a pull request', () => {
  assert.match(ci.jobs.governance.steps.map(x => x.run ?? '').join('\n'), /pnpm cd:test/);
  const unit = fs.readFileSync(new URL('../infra/cd/economicon-cd.service', import.meta.url), 'utf8');
  assert.match(unit, /deploy\.py .* poll/);
  assert.doesNotMatch(unit, /validate-source|sudo|User=root/);
});
