import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import App from "./App";
import "./index.css";
import { keepAwakeOnFirstTouch } from "./lib/keepAwake";
import { useDeck } from "./store/useDeck";
import { initPrefs } from "./store/usePrefs";

initPrefs();
useDeck.getState().start();
keepAwakeOnFirstTouch();

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
