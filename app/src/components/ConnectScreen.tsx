import type { DeckStatus } from "../store/useDeck";

const CONTENT: Record<string, { title: string; body: string }> = {
  connecting: {
    title: "Conectando ao agente…",
    body: "Procurando o ProDeck Agent neste endereço.",
  },
  offline: {
    title: "Agente fora do ar",
    body: "Verifique se o prodeck-agent está rodando no PC. Reconectando automaticamente…",
  },
  denied: {
    title: "Acesso negado",
    body: "O token deste aparelho não vale mais. Abra a página de pareamento e pareie de novo.",
  },
  "no-token": {
    title: "Pareie com o seu PC",
    body: "Escaneie o QR com o celular, ou — neste computador — abra a página de pareamento e clique em “Abrir o deck aqui”.",
  },
};

export function ConnectScreen({ status }: { status: DeckStatus }) {
  const { title, body } = CONTENT[status] ?? CONTENT.connecting;
  const spinning = status === "connecting" || status === "offline";
  return (
    <div className="flex min-h-full flex-col items-center justify-center gap-5 p-8 text-center">
      {spinning ? (
        <div className="h-10 w-10 animate-spin rounded-full border-2 border-slate-700 border-t-blue-500" />
      ) : (
        <div className="text-4xl">🔒</div>
      )}
      <h1 className="text-lg font-semibold text-slate-100">{title}</h1>
      <p className="max-w-xs text-sm leading-relaxed text-slate-400">{body}</p>
      {(status === "no-token" || status === "denied") && (
        <a
          href="/qr"
          className="rounded-xl bg-blue-600 px-5 py-2.5 text-sm font-semibold text-white active:bg-blue-700"
        >
          Abrir página de pareamento
        </a>
      )}
      <p className="font-mono text-xs text-slate-600">{location.host}</p>
    </div>
  );
}
