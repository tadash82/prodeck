const TOKEN_KEY = "prodeck.token";
const DEVICE_KEY = "prodeck.device-id";

/** Captura o token vindo do QR (?token=...) e o tira da barra de endereço. */
export function captureToken(): string | null {
  const url = new URL(window.location.href);
  const fromUrl = url.searchParams.get("token");
  if (fromUrl) {
    localStorage.setItem(TOKEN_KEY, fromUrl);
    url.searchParams.delete("token");
    history.replaceState(null, "", url.pathname + url.search + url.hash);
  }
  return localStorage.getItem(TOKEN_KEY);
}

/** Token salvo deste aparelho (para chamadas HTTP autenticadas, ex.: /apps). */
export function token(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function deviceId(): string {
  let id = localStorage.getItem(DEVICE_KEY);
  if (!id) {
    // crypto.randomUUID exige HTTPS; para identificar o aparelho isto basta
    id =
      "d-" +
      Array.from({ length: 2 }, () => Math.random().toString(36).slice(2, 10)).join("");
    localStorage.setItem(DEVICE_KEY, id);
  }
  return id;
}

export function deviceName(): string {
  const ua = navigator.userAgent;
  if (/iPhone/.test(ua)) return "iPhone";
  if (/iPad/.test(ua)) return "iPad";
  if (/Android/.test(ua)) return "Android";
  if (/Windows/.test(ua)) return "Windows";
  if (/Macintosh/.test(ua)) return "Mac";
  if (/Linux/.test(ua)) return "Linux";
  return "Navegador";
}
