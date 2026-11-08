const fs = require('node:fs');
const crypto = require('node:crypto');
const [input, publicKeyPath, output] = process.argv.slice(2);
const key = crypto.randomBytes(32);
const nonce = crypto.randomBytes(12);
const cipher = crypto.createCipheriv('aes-256-gcm', key, nonce);
const ciphertext = Buffer.concat([cipher.update(fs.readFileSync(input)), cipher.final()]);
const wrapped = crypto.publicEncrypt({key: fs.readFileSync(publicKeyPath), oaepHash:'sha256', padding:crypto.constants.RSA_PKCS1_OAEP_PADDING}, key);
fs.writeFileSync(output, JSON.stringify({key:wrapped.toString('base64'),nonce:nonce.toString('base64'),tag:cipher.getAuthTag().toString('base64'),ciphertext:ciphertext.toString('base64')}));
