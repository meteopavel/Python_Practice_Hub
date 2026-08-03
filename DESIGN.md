---
name: Python Practice Hub
description: Тёмная тема код-редактора — координатная сетка, моноширинные метки, акцент teal.
colors:
  signal: "#2DD4EF"
  signal-hover: "#54DEF5"
  signal-dim: "#16788A"
  signal-soft: "rgba(45, 212, 239, 0.12)"
  bench-dark: "#222436"
  panel: "#262B41"
  panel-raised: "#2F334D"
  panel-active: "#363C5C"
  hairline: "#2B2F47"
  hairline-strong: "#444A73"
  ink: "#C8D3F5"
  ink-muted: "#828BB8"
  ink-faint: "#6A7396"
  code-screen: "#1A1C2C"
  code-gutter: "#7E8EDA"
  code-keyword: "#baacff"
  code-var: "#70b0ff"
  code-string: "#7af8ca"
  code-class: "#ffdb8e"
  pass: "#6ACC63"
  pass-bg: "rgba(106, 204, 99, 0.10)"
  fail: "#FF757F"
  fail-bg: "rgba(255, 117, 127, 0.10)"
  warn: "#FF9668"
  warn-bg: "rgba(255, 150, 104, 0.10)"
typography:
  display:
    fontFamily: '"JetBrains Mono", ui-monospace, "SF Mono", "Cascadia Code", Menlo, Consolas, monospace'
    fontWeight: 700
    letterSpacing: "-0.01em"
    lineHeight: 1.2
  title:
    fontFamily: '"JetBrains Mono", ui-monospace, "SF Mono", "Cascadia Code", Menlo, Consolas, monospace'
    fontWeight: 600
    lineHeight: 1.2
  body:
    fontFamily: '"Inter Tight", system-ui, -apple-system, "Segoe UI", Roboto, Arial, sans-serif'
    fontWeight: 400
    fontSize: "0.9375rem"
    lineHeight: 1.55
  label:
    fontFamily: '"JetBrains Mono", ui-monospace, monospace'
    fontWeight: 700
    fontSize: "0.6875rem"
    letterSpacing: "0.06em"
    lineHeight: 1
  code:
    fontFamily: '"JetBrains Mono", ui-monospace, "SF Mono", monospace'
    fontWeight: 400
    fontSize: "13px"
    lineHeight: 1.7
rounded:
  default: "2px"
spacing:
  "1": "4px"
  "2": "8px"
  "3": "12px"
  "4": "16px"
  "5": "24px"
  "6": "32px"
  "7": "48px"
  "8": "64px"
components:
  button-primary:
    backgroundColor: "{colors.signal}"
    textColor: "#05181C"
    typography: '"JetBrains Mono", monospace 600 0.8125rem uppercase'
    rounded: "{rounded.default}"
    padding: "9px 16px"
  button-primary-hover:
    backgroundColor: "{colors.signal-hover}"
    textColor: "#05181C"
  button-secondary:
    backgroundColor: "{colors.panel-raised}"
    textColor: "{colors.ink}"
    typography: '"JetBrains Mono", monospace 600 0.8125rem uppercase'
    rounded: "{rounded.default}"
    padding: "9px 16px"
  button-secondary-hover:
    backgroundColor: "{colors.panel-active}"
  button-ghost:
    backgroundColor: "transparent"
    textColor: "{colors.ink-muted}"
    typography: '"JetBrains Mono", monospace 600 0.8125rem uppercase'
    rounded: "{rounded.default}"
    padding: "9px 16px"
  button-danger:
    backgroundColor: "{colors.fail}"
    textColor: "#FFFFFF"
    typography: '"JetBrains Mono", monospace 600 0.8125rem uppercase'
    rounded: "{rounded.default}"
    padding: "9px 16px"
  input-field:
    backgroundColor: "{colors.bench-dark}"
    textColor: "{colors.ink}"
    typography: '"Inter Tight", 0.9375rem'
    rounded: "{rounded.default}"
    padding: "10px 12px"
  chip:
    backgroundColor: "{colors.panel-raised}"
    textColor: "{colors.ink-muted}"
    typography: '"JetBrains Mono", 700 0.6875rem'
    rounded: "{rounded.default}"
    height: "25px"
  badge-pass:
    backgroundColor: "{colors.pass-bg}"
    textColor: "{colors.pass}"
    typography: '"JetBrains Mono", 700 0.6875rem uppercase'
    rounded: "{rounded.default}"
    padding: "3px 8px"
  card:
    backgroundColor: "{colors.panel}"
    textColor: "{colors.ink}"
    rounded: "{rounded.default}"
    padding: "16px"
---

# Design System: Python Practice Hub

## Overview

Тёмная тема в стиле код-редактора. Грунт — тёмно-синий (`#222436`, палитра Moonlight), один акцент (`#2DD4EF`, teal) для действий и фокуса, моноширинный шрифт (JetBrains Mono) для меток, кода и чисел. Чтение результата проверки кода (pass/fail) — первичная задача интерфейса; всё остальное подчинено ясности этого результата.

Глубина передаётся тональными слоями поверхности, а не мягкими тенями. Координатная сетка — **не фоновый паттерн всего body**, а фон рабочих зон (результаты тестов, редактор кода).

**Key Characteristics:**
- Тёмно-синий фон как primary; координатная сетка — только на рабочих зонах, не весь body.
- Один акцент (Signal Cyan `#2DD4EF`); цвет несёт функцию (pass/fail/working), не настроение.
- Моноширинный шрифт для меток, цифр и кода; метки — uppercase, с акцентным маркером.
- Глубина через тональные слои (`bench-dark → panel → panel-raised → panel-active`), не тени; края — hairline-линии полного периметра.
- Острые углы и технические радиусы; градиентов, стекла и декоративных теней нет.

## Colors

Палитра — тёмно-синий грунт, один акцент и функциональные семантические цвета.

### Primary (акцент)
- **Signal Cyan** (`#2DD4EF`): единственный акцент — primary action, фокус, выделение текущего элемента, индикатор состояния. Точечно, ≤10% поверхности. Hover поднимается до `#54DEF5`; приглушённый `#16788A` (`signal-dim`) — для контуров активного состояния, мягче сплошной заливки.

### Neutral (грунт и поверхности)
- **Bench Dark** (`#222436`): фон страницы, базовый слой и фон полей ввода.
- **Panel** (`#262B41`): поверхность панели/карточки — первый тональный подъём над грунтом.
- **Panel Raised** (`#2F334D`): поднятая поверхность — кнопки-secondary, чипы, hover-состояния ячеек.
- **Panel Active** (`#363C5C`): вершина тональной лестницы — sticky-заголовки таблиц, active-press кнопок.
- **Hairline** (`#2B2F47`): тихие разделители и контуры покоящихся поверхностей.
- **Hairline Strong** (`#444A73`): контуры контролов и поднятых границ (кнопок, чипов, полей).
- **Ink** (`#C8D3F5`): основной текст.
- **Ink Muted** (`#828BB8`): вторичный текст, лейблы, мета.
- **Ink Faint** (`#6A7396`): placeholder, мета нижнего уровня, подписи полей I/O.

### Code screen (глубже грунта)
- **Code Screen** (`#1A1C2C`): фон редактора кода и блоков `<pre>` — тон ниже грунта для зрительного отделения кода.
- **Code Gutter** (`#7E8EDA`): placeholder и gutter редактора, прохладно-сиреневый.

### Semantic
- **Pass** (`#6ACC63`, фон `rgba(106,204,99,0.10)`): тест прошёл.
- **Fail** (`#FF757F`, фон `rgba(255,117,127,0.10)`): тест упал. Диагональная риска в мини-индикаторах — fail отличается формой, не только цветом (для дальтоников).
- **Warn** (`#FF9668`, фон `rgba(255,150,104,0.10)`): вычисляется / в процессе / частичный прогресс.

### Named Rules
**The Function-Only Color Rule.** Цвет несёт функцию (pass/fail/working/active), никогда — настроение или декорацию.
**The One Signal Rule.** Акцент (`#2DD4EF`) — ≤10% любой поверхности; его редкость и есть техно-характер.

## Typography

Шрифты хостятся локально в `webapp/static/fonts/` (woff2, subset под Latin + кириллицу), подключаются через `webapp/static/css/fonts.css` (`@font-face`, `font-display: swap`). Никаких внешних запросов: лучше приватность, быстрее, работает офлайн. Лицензии: Inter Tight и JetBrains Mono — обе SIL OFL 1.1 (тексты лицензий лежат рядом со шрифтами).

**Display/Label Font:** JetBrains Mono (с fallback на системный моно) — лейблы, метки, цифры, названия, код.
**Body Font:** Inter Tight (с system-ui fallback) — беглое чтение описаний и подсказок.

**Character:** Моноширинный шрифт доминирует. Лейблы uppercase, единый трекинг `--tracking-label: 0.06em`, набраны жирно. Sans включается только для беглого чтения связного текста.

### Hierarchy
- **Display** (JetBrains Mono 700, `1.75rem`, `1.2`, `letter-spacing: -0.01em`): заголовки страниц (`h1`).
- **Headline** (JetBrains Mono 700, `1.375rem`, `1.2`): заголовки секций (`h2`).
- **Title** (JetBrains Mono 600, `1.0625rem`, `1.2`): заголовки панелей (`h3`).
- **Body** (Inter Tight 400, `0.9375rem`, `1.55`): описания задач, подсказки, связный текст — max ~70ch.
- **Label/Mark** (JetBrains Mono 700, `0.6875rem`, `letter-spacing: 0.06em`, uppercase): заголовки панелей (`panel-title`), имена полей, подписи I/O.
- **Data/Mono** (JetBrains Mono 400–500, `13px` / `tabular-nums`): тестовые I/O, таймеры, счётчики, номера заданий, табличные числа, блоки кода в подсказках (`--fs-code`).

### Named Rules
**The No-SaaS-Label Rule.** Серые инертные uppercase-микролейблы запрещены; метки — моноширинные, с акцентным маркером перед текстом (`panel-title::before` — квадрат `#2DD4EF`), набранные жирно.
**The Mono-For-Numbers Rule.** Все цифры, код, идентификаторы и табличные данные — моноширинно с `font-variant-numeric: tabular-nums`. Sans — только для беглого чтения связного текста.

## Layout

- **Контейнер:** `max-width: 1320px`, `padding-inline: 24px`, центрирование по горизонтали.
- **Wide-режим:** полноэкранные рабочие страницы (практика ученика, работа тьютора) снимают потолок ширины — трём колонкам + редактору кода нужно больше места, чем базовому контейнеру.
- **Рабочее место:** трёхколоночная сетка `300px / 1fr / 320px` (список заданий / редактор / панель подсказок) — идентичная для практики ученика (`.student-layout`) и работы тьютора (`.session-layout`). `gap: 16px`, `align-items: start`. Сайдбары sticky.
- **Материалы:** узкая читательская колонка `max-width: 860px`.
- **Spacing-ритм:** шаг 4px (`4 / 8 / 12 / 16 / 24 / 32 / 48 / 64`).

**Responsive (desktop-first):** Десктоп — основная сцена. Брейкпоинты по убыванию:
- `≤1100px`: трёхколоночные сетки схлопываются в одну колонку; sticky-сайдбары становятся статичными.
- `≤760px`: админка подсказок (редактор + превью) — в одну колонку.
- `≤720px`: хедер переносится (`flex-wrap`), `padding` сжимается, подписи полей I/O встают поверх значений, brand уменьшается.
- `prefers-reduced-motion: reduce`: все переходы и анимации гасятся до `0.01ms`.

## Elevation & Depth

Глубина — через тональные слои поверхности (`bench-dark → panel → panel-raised → panel-active`), а не мягкие тени. Hairline-линии (1px полного периметра) отделяют зоны. Приподнятое состояние (hover/active/selected) — подъём тона поверхности, опционально hairline-контур `signal-dim`.

Теневые токены (`--shadow-*`) оставлены, но **только для всплывающих меню** (account-dropdown, attempt-preview) — покоящиеся поверхности теней не носят. Каждый `--shadow-*` включает `0 0 0 1px` hairline-контур, чтобы край оставался прочитываемым даже там, где есть тень.

**The Flat-By-Default Rule.** Поверхности плоские в покое; «глубина» появляется как тональный подъём по состоянию, а не как декоративная тень. Тень — исключение для floating overlays, и даже там она несёт hairline-край.

## Shapes

Форм-язык — угловатый: **одно значение радиуса** (`--radius: 2px`). Квадратные маркеры состояния (`--mark: 8px` для меток панелей/тестов, `--mark-sm: 6px` для бейджей/баров) — перед лейблами и в строках тестов. Иконки звонка квадратные, наравне с остальными controls (круглые пробовались и отвергнуты).

**The Sharp Edge Rule.** Один радиус `2px` на все поверхности; скругление — минимальная техническая необходимость (чтобы браузерный дефолт `0` не выглядел сломанным), не дизайн-высказывание. Pill-формы и крупные скругления — другой мир.

## Components

### Buttons
Моноширинно-uppercase. Один размер по умолчанию (`9px 16px`), модификаторы `btn-sm` (`height: 25px`) и `btn-lg`. Переходы `120ms cubic-bezier(0.4,0,0.2,1)` по `background/border-color/color`.
- **Shape:** `border-radius: var(--radius)`, `border: 1px solid`, uppercase mono `600`.
- **Primary** (`btn-primary`): Signal Cyan заливка (`#2DD4EF`), тёмный текст (`#05181C`). Hover → `#54DEF5`. Primary action («Запустить/Проверить»).
- **Secondary** (`btn`): Panel Raised фон (`#2F334D`), Ink текст, `border: hairline-strong`. Hover → `panel-active` + `signal-dim` контур. Базовый control.
- **Ghost** (`btn-ghost`): transparent, Ink Muted текст. Hover → фон Panel Raised, текст Ink, появляется контур.
- **Danger** (`btn-danger`): Fail-цвет заливка (`#FF757F`), тёмный текст (`signal-text`, для контраста WCAG AA). Отмена созвона/ошибка отправки. Hover через `brightness(1.12)`.
- **Icon button** (`icon-btn`, `26×26px`): квадратная, второстепенные действия рядом с заголовками. SVG-иконки `14×14px`.

### Call icons — состояние-зависимые квадраты (`call-icon-btn`, `44×44px`)
Состояния-модификаторы: `is-accept` (Pass-заливка), `is-hangup` (Fail-заливка, иконка повёрнута на 135°), `is-mute` (surface + переключаемый `is-active` в Fail-цветах), `is-pulsing` (зелёная пульсация `call-pulse-green 1.6s` — входящий звонок). Хедерные иконки — `is-sm` (`25×25px`).

### Chips
- **Style:** Panel Raised фон, Ink Muted текст, mono `700`, `height: 25px`, `border-radius: var(--radius)`, контур `hairline-strong`. Тэги и метки-не-статус.

### Badges
- **Style:** mono `700` uppercase, `border-radius: var(--radius)`, `padding: 3px 8px`, цветной контур + тонкий тонированный фон. Перед текстом — `6×6px` маркер `currentColor`.
- **Variants:** `badge-pass` / `badge-fail` / `badge-warn` / `badge-neutral`. Нейтральный — серый surface с маркером `ink-faint`.

### Cards / Panels
- **Corner:** `border-radius: var(--radius)`.
- **Background:** Panel (`#262B41`).
- **Border:** `1px solid hairline` (`#2B2F47`).
- **Shadow:** нет (`box-shadow: none`) — глубина через hairline-контур, не тень.
- **Internal padding:** `16px` (`.card-pad`).
- **Panel title** (`panel-title`): заголовок панели с акцентным маркером перед текстом (см. No-SaaS-Label Rule).

### Inputs / Fields
- **Style:** Bench Dark фон (`#222436`), Ink текст, `border: 1px solid hairline-strong`, `border-radius: var(--radius)`, `padding: 10px 12px`, Inter Tight `0.9375rem`.
- **Focus:** `border-color: signal`, `box-shadow: 0 0 0 3px signal-soft`.
- **Placeholder:** Ink Faint.
- **Field label:** mono `700` uppercase `0.6875rem`, `letter-spacing: 0.06em`, Ink Muted.

### Task list item
Прозрачен в покое; hover → фон Panel Raised. Активный (`is-active`) — `signal-soft` фон + `signal-dim` контур. Номер задания — моно-квадрат (`task-item-num`), в активном состоянии инвертируется: Signal фон, тёмный текст. Статус — `8×8px` маркер справа (`dot-pass` / `dot-fail` / `dot-none`).

### Code editor
Code Screen фон (`#1A1C2C`), глубже грунта. Бар редактора — mono uppercase signal-цвет с маркером перед подписью (как `panel-title`). Сам редактор — CodeMirror 6 (собирается из исходников в `build/codemirror-entry.js` через esbuild, `npm run build:codemirror`; см. `webapp/static/vendor/codemirror.bundle.js`), JetBrains Mono `13px`/`1.7`, `caret-color: signal`, отступ 4 пробела. Инлайновый `code.inline` — Signal текст на Panel Raised с hairline-контуром.

**Подсветка синтаксиса:** keyword/operator — Code Keyword (`#baacff`); имя переменной/функции — Code Var (`#70b0ff`); число/bool/null — Warn (`#FF9668`, тот же токен, что и статус «в процессе»); строка — Code String (`#7af8ca`); имя класса — Code Class (`#ffdb8e`); комментарий и пунктуация — Code Gutter, обычный текст — Ink.

### Verdict Readout (сигнатурный компонент)
Таблица тестов. Каждый `.test-case` — ячейка с цветным контуром полного периметра по состоянию (pass/fail), **не бордюр с одной стороны**. Перед именем теста — `8×8px` маркер состояния. I/O — двухколоночная сетка `96px / 1fr`: слева моно-uppercase подпись (`dt`, Ink Faint), справа значение (`dd`, моно на Bench Dark фоне, hairline-контур). `diff-got` (полученный ответ при провале) — Fail-цвета.

Итоговый счётчик (`result-summary`): крупная моно-цифра (`fs-2xl`, `tabular-nums`) в тонированном фоне по состоянию (`.is-pass` / `.is-fail`).

### Attempt strip
Полоса квадратов `22×22px` — каждая попытка. Pass: зелёный маркер + `pass-bg`. Fail: красный маркер + диагональная риска `background-image` (для дальтоников, не только цвет). Последняя попытка — усиленный контур. Hover → превью-модалка; клик → инлайн-раскрытие кода. На тач-устройствах (`hover: none`) превью отключается, остаётся клик.

### Navigation
Sticky хедер (`min-height: 56px`), Bench Dark фон, hairline снизу, без blur-стекла. Brand — mono-bold с `</>`-знаком в акцентной плитке (`30×30px`, `signal-soft` фон, `signal-dim` контур). Account-меню — `<details>`-выпадашка (без JS на открытие), Panel фон, `shadow-lg` + hairline-strong контур. Аватар — `30×30px` акцентная плитка с инициалами.

### Table (экран репетитора)
Panel фон, `border-radius: var(--radius)`, hairline-контур. Sticky thead в Panel Active (`#363C5C`), mono uppercase заголовки. Hover-строки → Panel Raised. Числа — моно `tabular-nums`.

## Do's and Don'ts

### Do:
- **Do** использовать координатную сетку (`--grid-cell: 24px`) точечно на рабочих зонах, видимо (через `.bench-grid`) или подразумеваемо.
- **Do** использовать цвет только как функцию (pass/fail/working/active); семантические цвета — только для статуса.
- **Do** набирать метки, цифры, код моноширинно (JetBrains Mono), жирно, uppercase-tracked.
- **Do** передавать глубину тональными слоями (`bench-dark → panel → panel-raised → panel-active`), а не тенями.
- **Do** различать fail не только цветом: диагональная риска в мини-индикаторах (дальтоники).
- **Do** ставить акцентный маркер перед заголовками панелей (`panel-title`, `code-editor-bar`, `badge`).

### Don't:
- **Don't** использовать мягкие декоративные тени, градиенты, glassmorphism, blur-стекло.
- **Don't** использовать серые инертные uppercase-микролейблы без акцентного маркера.
- **Don't** жертвовать читаемостью результата ради атмосферы; pass/fail — первичны.
- **Don't** использовать радиус больше `2px`, pill-формы или крупные скругления.
- **Don't** делать бордюр с одной стороны для статуса — только контур полного периметра.
- **Don't** вешать координатную сетку на весь body — она живёт только на рабочих зонах.
