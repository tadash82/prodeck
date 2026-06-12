import { create } from "zustand";

import { captureToken, deviceId, deviceName } from "../lib/identity";
import type { Button, DeckConfig, Position } from "../types/protocol";
import { DeckSocket, type ConnStatus, type ServerMessage } from "../ws/client";

export type ButtonResult = {
  status: "ok" | "error";
  message: string;
  at: number;
};

export type DeckStatus = ConnStatus | "no-token";

export type EditTarget =
  | { kind: "edit"; profileId: string; pageId: string; button: Button }
  | { kind: "new"; profileId: string; pageId: string; position: Position };

export type Toast = { text: string; kind: "ok" | "error" };

type DeckState = {
  status: DeckStatus;
  config: DeckConfig | null;
  activePageIndex: number;
  rttMs: number | null;
  results: Record<string, ButtonResult>;
  buttonStates: Record<string, boolean>;
  editMode: boolean;
  editTarget: EditTarget | null;
  manageOpen: boolean;
  toast: Toast | null;

  start: () => void;
  trigger: (buttonId: string) => void;
  setPage: (index: number) => void;
  setEditMode: (on: boolean) => void;
  openEditor: (target: EditTarget) => void;
  closeEditor: () => void;
  setManageOpen: (open: boolean) => void;
  showToast: (text: string, kind?: Toast["kind"]) => void;
  /** Aplica uma operação do deckOps: save otimista + deck.save no agente. */
  apply: (operation: (config: DeckConfig) => DeckConfig) => boolean;
};

let socket: DeckSocket | null = null;
let toastTimer: number | undefined;

export const useDeck = create<DeckState>((set, get) => ({
  status: "connecting",
  config: null,
  activePageIndex: 0,
  rttMs: null,
  results: {},
  buttonStates: {},
  editMode: false,
  editTarget: null,
  manageOpen: false,
  toast: null,

  start: () => {
    const token = captureToken();
    if (!token) {
      set({ status: "no-token" });
      return;
    }
    socket = new DeckSocket(
      {
        status: (status) => set({ status }),
        rtt: (rttMs) => set({ rttMs }),
        message: (message) => handleMessage(message),
      },
      { token, deviceId: deviceId(), deviceName: deviceName() },
    );
    socket.connect();
    document.addEventListener("visibilitychange", () => {
      if (!document.hidden) socket?.connect();
    });
  },

  trigger: (buttonId) => {
    navigator.vibrate?.(15);
    socket?.trigger(buttonId);
  },

  setPage: (activePageIndex) => set({ activePageIndex }),
  setEditMode: (editMode) =>
    set({ editMode, ...(editMode ? {} : { editTarget: null, manageOpen: false }) }),
  openEditor: (editTarget) => set({ editTarget }),
  closeEditor: () => set({ editTarget: null }),
  setManageOpen: (manageOpen) => set({ manageOpen }),

  showToast: (text, kind = "error") => {
    window.clearTimeout(toastTimer);
    set({ toast: { text, kind } });
    toastTimer = window.setTimeout(() => set({ toast: null }), 3500);
  },

  apply: (operation) => {
    const { config, showToast } = get();
    if (!config) return false;
    try {
      const next = operation(config);
      set({ config: next });
      socket?.deckSave(next);
      return true;
    } catch (error) {
      showToast(error instanceof Error ? error.message : String(error));
      return false;
    }
  },
}));

function handleMessage(message: ServerMessage): void {
  const { setState, getState } = useDeck;
  switch (message.type) {
    case "hello.ok":
      socket?.deckGet();
      break;
    case "deck.layout":
      setState({ config: message.payload });
      break;
    case "action.result":
      setState({
        results: {
          ...getState().results,
          [message.payload.button_id]: {
            status: message.payload.status,
            message: message.payload.message ?? "",
            at: Date.now(),
          },
        },
      });
      break;
    case "state.update":
      setState({
        buttonStates: {
          ...getState().buttonStates,
          [message.payload.button_id]: message.payload.active,
        },
      });
      break;
    case "error":
      // save recusado pelo agente: avisa e ressincroniza com o estado canônico
      getState().showToast(message.payload.message);
      socket?.deckGet();
      break;
  }
}
