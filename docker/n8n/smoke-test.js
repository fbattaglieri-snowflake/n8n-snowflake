const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const expected = process.argv[2];
assert.match(expected, /^\d+\.\d+\.\d+$/);
const installation = '/usr/local/lib/node_modules/n8n';
assert.equal(require(path.join(installation, 'package.json')).version, expected);
const packages = path.join(installation, 'node_modules/.pnpm');
const base = fs.readdirSync(packages).find(name => name.startsWith('n8n-nodes-base@'));
assert.ok(base, 'Native node package must be present');
const source = fs.readFileSync(path.join(packages, base,
  'node_modules/n8n-nodes-base/dist/nodes/Snowflake/GenericFunctions.js'), 'utf8');
assert.ok(source.includes("const SPCS_TOKEN_PATH = '/snowflake/session/token';"));
assert.ok(source.includes("connectionOptions.authenticator = 'OAUTH';"));
assert.ok(source.includes('connectionOptions.token = token;'));
assert.ok(source.includes("readFileSync)(SPCS_TOKEN_PATH, 'utf8').trim()"));
new vm.Script(source);
console.log(`n8n ${expected}: native Snowflake OAuth patch present and JavaScript parses`);