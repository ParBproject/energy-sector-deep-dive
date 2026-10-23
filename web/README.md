# web/ — Energy Sector Explorer

Vite + React + TypeScript, ECharts, Framer Motion and Zustand, with pinned exact versions in `package.json`.

The app reads only the precomputed JSON in `public/data/`. Refresh it from the repo root with `make export`, which copies `results/*.json` and writes `index.json`. The app never calls a data API.

```bash
npm ci
npm run dev        # local dev server
npm test           # vitest: tokens, WCAG contrast, export JSON shape
npm run build      # writes src/design/tokens.json, type-checks, builds to dist/
```

## Design system
- `src/design/tokens.ts` is the **single source** for colour, type, spacing, layout and motion. `npm run tokens` writes `src/design/tokens.json`, and the Python README charts (`src/analysis/charts.py`) read that file, so the app and the charts match.
- **Colour:** a near-black base with two raised surfaces. The emerald `#10B981` accent is used for selection, the primary line and focus rings. Segment colours are a muted Okabe-Ito palette, which is colour-blind safe. Every text pair passes WCAG AA, and `tests/contrast.test.ts` checks this.
- **Type:** Inter for UI and JetBrains Mono with tabular figures for numbers. Both are self-hosted through fontsource, with no CDN. The scale is 12/14/16/20/28/40.
- **Layout:** a 12-column grid with 8 px spacing. Touch targets are at least 44 px. The mobile layout targets 390 px, with a filter bottom sheet and swipeable chart tabs.
- **Theme:** the ECharts theme is registered from the tokens in `src/design/echartsTheme.ts`. Motion respects `prefers-reduced-motion`.
- **Styleguide:** at `#/styleguide`.
