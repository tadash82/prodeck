import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import App from "./App";
import "./index.css";
import { keepAwake } from "./lib/keepAwake";
import { useDeck } from "./store/useDeck";
import { initPrefs } from "./store/usePrefs";

initPrefs();
useDeck.getState().start();
keepAwake();

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
