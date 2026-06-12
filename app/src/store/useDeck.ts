import { create } from "zustand";

import { captureToken, deviceId, deviceName } from "../lib/identity";
import type { DeckConfig } from "../types/protocol";
import { DeckSocket, type ConnStatus, type ServerMessage } from "../ws/client";

export type ButtonResult = {
  status: "ok" | "error";
  message: string;
  at: number;
};

export type DeckStatus = ConnStatus | "no-token";

type DeckState = {
  status: DeckStatus;
  config: DeckConfig | null;
  activePageIndex: number;
  rttMs: number | null;
  results: Record<string, ButtonResult>;
  start: () => void;
  trigger: (buttonId: string) => void;
  setPage: (index: number) => void;
};

let socket: DeckSocket | null = null;

export const useDeck = create<DeckState>((set) => ({
  status: "connecting",
  config: null,
  activePageIndex: 0,
  rttMs: null,
  results: {},

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
}));

function handleMessage(message: ServerMessage): void {
  const { setState, getState } = useDeck;
  switch (message.type) {
    case "hello.ok":
      socket?.deckGet();
      break;
    case "deck.layout":
      setState({ config: message.payload, activePageIndex: 0 });
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
  }
}
