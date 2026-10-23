import { useEffect, useState } from "react";
import { loadAll } from "./data/load";
import { Shell } from "./routes/Shell";
import { Styleguide } from "./routes/Styleguide";
import { useStore } from "./state/store";

function useHashRoute(): string {
  const [hash, setHash] = useState(() => window.location.hash);
  useEffect(() => {
    const on = () => setHash(window.location.hash);
    window.addEventListener("hashchange", on);
    return () => window.removeEventListener("hashchange", on);
  }, []);
  return hash;
}

export function App() {
  const route = useHashRoute();
  const { setData, setError } = useStore();
  useEffect(() => {
    loadAll().then(setData).catch((e: Error) => setError(e.message));
  }, [setData, setError]);
  return route.startsWith("#/styleguide") ? <Styleguide /> : <Shell />;
}
