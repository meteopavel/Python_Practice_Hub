/* ==========================================================================
   codemirror-entry.js — исходник для webapp/static/vendor/codemirror.bundle.js.
   Раньше бандл коммитился готовым (esbuild-минифицированным), без исходников
   и без package.json — воспроизвести его было невозможно. Правь цвета/keymap
   здесь и в tokens.css, не в самом бандле, и пересобери:
     npm install && npm run build:codemirror
   ========================================================================== */
import {EditorState} from '@codemirror/state';
import {
  EditorView, keymap, lineNumbers, highlightActiveLineGutter,
  drawSelection, dropCursor,
} from '@codemirror/view';
import {
  bracketMatching, syntaxHighlighting, HighlightStyle, indentUnit,
} from '@codemirror/language';
import {defaultKeymap, historyKeymap, history, indentWithTab} from '@codemirror/commands';
import {python} from '@codemirror/lang-python';
import {tags} from '@lezer/highlight';

// Тема — на дизайн-токенах проекта (webapp/static/css/tokens.css). Раньше
// часть значений (фон/текст редактора) ссылалась на --c-code-bg/--c-code-text,
// которых давно нет в токенах (переименованы в --c-code-screen/--c-ink) —
// var() с несуществующим токеном молча схлопывался, и цвет фактически
// брался от родительского .code-editor/наследования, а не от самого CM6.
const theme = EditorView.theme({
  '&': {
    color: 'var(--c-ink)',
    backgroundColor: 'var(--c-code-screen)',
    fontSize: 'var(--fs-code)',
  },
  '.cm-content': {
    fontFamily: 'var(--font-mono)',
    caretColor: 'var(--c-focus)',
    padding: '16px',
  },
  '.cm-line': {
    lineHeight: 'var(--lh-base)',
  },
  '.cm-gutters': {
    backgroundColor: 'var(--c-code-screen)',
    color: 'var(--c-code-gutter)',
    border: 'none',
  },
  '.cm-activeLine': {backgroundColor: 'rgba(255, 255, 255, 0.04)'},
  '.cm-activeLineGutter': {backgroundColor: 'rgba(255, 255, 255, 0.06)'},
  '&.cm-focused': {outline: 'none'},
  '.cm-matchingBracket': {
    backgroundColor: 'transparent',
    borderBottom: '2px solid var(--c-focus)',
  },
  '.cm-nonmatchingBracket': {
    backgroundColor: 'transparent',
    borderBottom: '2px solid var(--c-fail)',
  },
  '.cm-scroller': {overflow: 'auto'},
}, {dark: true});

// Подсветка синтаксиса — тоже на токенах (--c-code-keyword/var/string/class
// в tokens.css); числа/bool/null используют уже существующий --c-warn
// (то же значение, что раньше было захардкожено отдельно).
const highlightStyle = HighlightStyle.define([
  {tag: tags.keyword, color: 'var(--c-code-keyword)'},
  {tag: tags.controlKeyword, color: 'var(--c-code-keyword)'},
  {tag: [tags.name, tags.propertyName], color: 'var(--c-ink)'},
  {tag: tags.definition(tags.variableName), color: 'var(--c-code-var)'},
  {tag: tags.function(tags.variableName), color: 'var(--c-code-var)'},
  {tag: [tags.number, tags.bool, tags.null], color: 'var(--c-warn)'},
  {tag: [tags.string, tags.special(tags.string)], color: 'var(--c-code-string)'},
  {tag: tags.comment, color: 'var(--c-code-gutter)', fontStyle: 'italic'},
  {tag: tags.operator, color: 'var(--c-code-keyword)'},
  {tag: tags.punctuation, color: 'var(--c-code-gutter)'},
  {tag: tags.className, color: 'var(--c-code-class)'},
]);

// API: create(mount, code, onChange, options) → {getValue, setValue, focus}.
// onChange(code) зовётся на каждое изменение документа (debounce — забота
// страницы, не редактора). options.readOnly — для live-зеркала кода ученика
// и превью попыток.
function create(mount, code, onChange, options) {
  const opts = options || {};
  const state = EditorState.create({
    doc: code || '',
    extensions: [
      lineNumbers(),
      highlightActiveLineGutter(),
      history(),
      drawSelection(),
      dropCursor(),
      indentUnit.of('    '),
      syntaxHighlighting(highlightStyle),
      bracketMatching(),
      keymap.of([...defaultKeymap, ...historyKeymap, indentWithTab]),
      python(),
      theme,
      EditorView.lineWrapping,
      opts.readOnly ? [EditorState.readOnly.of(true), EditorView.editable.of(false)] : [],
      EditorView.updateListener.of((update) => {
        if (update.docChanged && onChange) onChange(update.state.doc.toString());
      }),
    ],
  });
  const view = new EditorView({state, parent: mount});
  return {
    getValue: () => view.state.doc.toString(),
    setValue: (value) => {
      const next = value || '';
      view.dispatch({
        changes: {from: 0, to: view.state.doc.length, insert: next},
        selection: {anchor: next.length},
      });
    },
    focus: () => view.focus(),
  };
}

window.PracticeHubEditor = {create};
