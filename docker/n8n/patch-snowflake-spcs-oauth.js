const fs = require('fs');
const path = require('path');

const pnpmRoot = '/usr/local/lib/node_modules/n8n/node_modules/.pnpm';
const packageDirectory = fs
  .readdirSync(pnpmRoot)
  .find((name) => name.startsWith('n8n-nodes-base@'));

if (!packageDirectory) {
  throw new Error('n8n-nodes-base package not found');
}

const target = path.join(
  pnpmRoot,
  packageDirectory,
  'node_modules/n8n-nodes-base/dist/nodes/Snowflake/GenericFunctions.js',
);

let source = fs.readFileSync(target, 'utf8');
const marker = "const SPCS_TOKEN_PATH = '/snowflake/session/token';";

if (source.includes(marker)) {
  process.exit(0);
}

const importAnchor = 'const binary_1 = require("../../utils/binary");';
if (!source.includes(importAnchor)) {
  throw new Error('Snowflake GenericFunctions import anchor not found');
}

source = source.replace(
  importAnchor,
  `${importAnchor}\nconst fs_1 = require("fs");\n${marker}`,
);

const functionAnchor = 'const getConnectionOptions = (credential, nodeVersion) => {';
if (!source.includes(functionAnchor)) {
  throw new Error('Snowflake getConnectionOptions anchor not found');
}

source = source.replace(
  functionAnchor,
  `${functionAnchor}
    if ((0, fs_1.existsSync)(SPCS_TOKEN_PATH)) {
        const token = (0, fs_1.readFileSync)(SPCS_TOKEN_PATH, 'utf8').trim();
        if (!token)
            throw new Error('SPCS OAuth token file is empty');
        const host = process.env.SNOWFLAKE_HOST;
        const account = process.env.SNOWFLAKE_ACCOUNT || credential.account;
        if (!host || !account)
            throw new Error('SPCS Snowflake host or account is missing');
        const connectionOptions = (0, pick_1.default)(credential, commonConnectionFields);
        connectionOptions.authenticator = 'OAUTH';
        connectionOptions.token = token;
        connectionOptions.host = host;
        connectionOptions.account = account;
        if (typeof nodeVersion === 'number' && nodeVersion >= 1.1)
            connectionOptions.fetchAsString = ['Date'];
        return connectionOptions;
    }`,
);

fs.writeFileSync(target, source);
console.log(`Patched native Snowflake node for SPCS OAuth: ${target}`);

