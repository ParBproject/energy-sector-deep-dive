/// <reference types="vitest/config" />
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Relative base so the build works from GitHub Pages project paths.
export default defineConfig({
  base: "./",
  plugins: [react()],
  build: { chunkSizeWarningLimit: 1200 },
  test: { environment: "node", include: ["tests/**/*.test.ts"] },
});
