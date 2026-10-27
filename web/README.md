# Explorer

Vite, React, and TypeScript. Charts use ECharts. The app reads the JSON in `public/data/` and does not call a data API. From the repo root, `make export` refreshes that JSON from `results/`.

```bash
npm ci
npm run dev
npm test
npm run build
```

Colours, type, and spacing are in `src/design/tokens.ts`. `npm run tokens` writes `src/design/tokens.json`, which the Python charts read as well. `tests/contrast.test.ts` checks the text pairs against WCAG AA. The styleguide is at `#/styleguide`. The sample chart there is not a result.
