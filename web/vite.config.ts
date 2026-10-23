/// <reference types="vitest/config" />
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// GitHub Pages project path: https://parbproject.github.io/energy-sector-deep-dive/
export default defineConfig({
  base: "/energy-sector-deep-dive/",
  plugins: [react()],
  build: { chunkSizeWarningLimit: 1200 },
  test: { environment: "node", include: ["tests/**/*.test.ts"] },
});
