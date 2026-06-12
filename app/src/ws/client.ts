import type { Protocol } from "../types/protocol";

export type ClientMessage = Protocol["client"];
export type ServerMessage = Protocol["server"];
export type ConnStatus = "connecting" | "online" | "offline" | "denied";

export type DeckSocketEvents = {
  status: (status: ConnStatus) => void;
  message: (message: ServerMessage) => void;
  rtt: (ms: number) => void;
};

export type DeckAuth = {
  token: string;
  deviceId: string;
  deviceName: string;
};

const PING_INTERVAL_MS = 5000;
const MAX_BACKOFF_MS = 8000;

export class DeckSocket {
  private ws: WebSocket | null = null;
  private retry = 0;
  private seq = 0;
  private denied = false;
  private pending = new Map<string, number>();
  private pingTimer: number | undefined;

  constructor(
    private events: DeckSocketEvents,
    private auth: DeckAuth,
  ) {}

  connect(): void {
    if (this.denied) return;
    if (
      this.ws &&
      (this.ws.readyState === WebSocket.OPEN ||
        this.ws.readyState === WebSocket.CONNECTING)
    ) {
      return;
    }
    this.events.status(this.retry === 0 ? "connecting" : "offline");

    const scheme = location.protocol === "https:" ? "wss" : "ws";
    const ws = new WebSocket(`${scheme}://${location.host}/ws`);
    this.ws = ws;

    ws.onopen = () => {
      this.retry = 0;
      this.dispatch({
        v: 1,
        type: "hello",
        id: this.nextId(),
        payload: {
          token: this.auth.token,
          device_id: this.auth.deviceId,
          device_name: this.auth.deviceName,
        },
      });
    };

    ws.onmessage = (event) => {
      const message = JSON.parse(event.data) as ServerMessage;
      if (message.id) {
        const t0 = this.pending.get(message.id);
        this.pending.delete(message.id);
        if (t0 !== undefined) this.events.rtt(Math.round(performance.now() - t0));
      }
      if (message.type === "hello.ok") {
        this.events.status("online");
        this.startPing();
      } else if (message.type === "hello.denied") {
        this.denied = true;
        this.events.status("denied");
      }
      this.events.message(message);
    };

    ws.onclose = () => {
      this.stopPing();
      this.ws = null;
      if (this.denied) return;
      this.events.status("offline");
      const delay = Math.min(1000 * 2 ** this.retry++, MAX_BACKOFF_MS);
      window.setTimeout(() => this.connect(), delay);
    };
  }

  deckGet(): void {
    this.dispatch({ v: 1, type: "deck.get", id: this.nextId() });
  }

  trigger(buttonId: string): void {
    this.dispatch({
      v: 1,
      type: "action.trigger",
      id: this.nextId(),
      payload: { button_id: buttonId },
    });
  }

  private ping(): void {
    this.dispatch({ v: 1, type: "ping", id: this.nextId() });
  }

  private dispatch(message: ClientMessage): void {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) return;
    this.pending.set(message.id, performance.now());
    this.ws.send(JSON.stringify(message));
  }

  private nextId(): string {
    return String(++this.seq);
  }

  private startPing(): void {
    this.stopPing();
    this.pingTimer = window.setInterval(() => this.ping(), PING_INTERVAL_MS);
  }

  private stopPing(): void {
    if (this.pingTimer !== undefined) {
      window.clearInterval(this.pingTimer);
      this.pingTimer = undefined;
    }
  }
}
