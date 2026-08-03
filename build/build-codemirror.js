#!/usr/bin/env node
/* Пересобирает webapp/static/vendor/codemirror.bundle.js из
   build/codemirror-entry.js через esbuild. Запуск: npm run build:codemirror
   (требует npm install — devDependencies в package.json). */
const esbuild = require('esbuild');
const path = require('path');

esbuild.build({
  entryPoints: [path.join(__dirname, 'codemirror-entry.js')],
  bundle: true,
  minify: true,
  format: 'iife',
  target: 'es2020',
  outfile: path.join(__dirname, '..', 'webapp', 'static', 'vendor', 'codemirror.bundle.js'),
  banner: {
    js: '/*! CodeMirror 6 bundle (state/view/language/commands/lang-python), MIT License. https://codemirror.net/ */',
  },
}).then(() => {
  console.log('OK: webapp/static/vendor/codemirror.bundle.js');
}).catch((err) => {
  console.error(err);
  process.exit(1);
});
