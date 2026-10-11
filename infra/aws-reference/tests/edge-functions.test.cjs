const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
function invoke(file, uri) {
  const context = vm.createContext({});
  vm.runInContext(fs.readFileSync(path.join(__dirname, '../functions', file), 'utf8'), context);
  return context.handler({ request: { uri, headers: { authorization: { value: 'test-token' } }, querystring: { tenant: { value: 'test' } } } });
}
for (const [input, expected] of [['/api', '/'], ['/api/assistant', '/assistant'], ['/api/billing/summary', '/billing/summary']]) {
  const result = invoke('api.js', input);
  assert.equal(result.uri, expected);
  assert.equal(result.headers.authorization.value, 'test-token');
  assert.equal(result.querystring.tenant.value, 'test');
}
for (const [input, expected] of [['/', '/index.html'], ['/dashboard', '/index.html'], ['/auth/callback', '/index.html'], ['/assets/app.js', '/assets/app.js'], ['/missing.css', '/missing.css']]) {
  assert.equal(invoke('spa.js', input).uri, expected);
}
console.log('8 routing scenarios passed; API headers/query retained, static files not masked.');
