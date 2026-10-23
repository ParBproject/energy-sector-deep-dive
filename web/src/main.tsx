import "@fontsource-variable/inter";
import "@fontsource-variable/jetbrains-mono";
import { LazyMotion } from "framer-motion";
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { App } from "./App";
import { applyCssVars } from "./design/cssVars";
import "./design/global.css";

applyCssVars();
createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <LazyMotion features={() => import("./motionFeatures").then((r) => r.default)} strict>
      <App />
    </LazyMotion>
  </StrictMode>,
);
