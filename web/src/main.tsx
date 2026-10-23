import "@fontsource-variable/inter";
import "@fontsource-variable/jetbrains-mono";
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { App } from "./App";
import { applyCssVars } from "./design/cssVars";
import { registerTheme } from "./design/echartsTheme";
import "./design/global.css";

applyCssVars();
registerTheme();
createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
