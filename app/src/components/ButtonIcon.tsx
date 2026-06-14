import { Icon } from "@iconify/react";

/**
 * Renderiza o ícone de um botão: uma imagem (quando `icon` é uma data URL ou
 * http — ex.: o ícone de um app escolhido do PC) ou um ícone Iconify (nome
 * "prefixo:nome"). Mantém a mesma assinatura nos dois casos.
 */
export function ButtonIcon({ icon, size }: { icon: string; size: string }) {
  if (icon.startsWith("data:") || icon.startsWith("http")) {
    return (
      <img
        src={icon}
        alt=""
        draggable={false}
        style={{ width: size, height: size, objectFit: "contain" }}
      />
    );
  }
  return <Icon icon={icon} style={{ fontSize: size }} />;
}
