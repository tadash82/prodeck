/**
 * Operações imutáveis sobre a DeckConfig — cada uma devolve uma config nova,
 * pronta para o save otimista + deck.save. Regras de UX (ex.: não excluir a
 * última página) vivem aqui e viram Error com mensagem amigável.
 */

import type { Button, DeckConfig, Page, Position, Profile } from "../types/protocol";

export function newId(prefix: string): string {
  return `${prefix}-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 6)}`;
}

function clone(config: DeckConfig): DeckConfig {
  return structuredClone(config);
}

function profileAt(config: DeckConfig, profileId: string): Profile {
  const profile = (config.profiles ?? []).find((p) => p.id === profileId);
  if (!profile) throw new Error("perfil não encontrado");
  return profile;
}

function pageAt(config: DeckConfig, profileId: string, pageId: string): Page {
  const page = (profileAt(config, profileId).pages ?? []).find((p) => p.id === pageId);
  if (!page) throw new Error("página não encontrada");
  return page;
}

// ---------------------------------------------------------------- botões

export function upsertButton(
  config: DeckConfig,
  profileId: string,
  pageId: string,
  button: Button,
): DeckConfig {
  const next = clone(config);
  const page = pageAt(next, profileId, pageId);
  page.buttons = page.buttons ?? [];
  const index = page.buttons.findIndex((b) => b.id === button.id);
  if (index >= 0) page.buttons[index] = button;
  else page.buttons.push(button);
  return next;
}

export function removeButton(
  config: DeckConfig,
  profileId: string,
  pageId: string,
  buttonId: string,
): DeckConfig {
  const next = clone(config);
  const page = pageAt(next, profileId, pageId);
  page.buttons = (page.buttons ?? []).filter((b) => b.id !== buttonId);
  return next;
}

/** Move para a célula destino; se ela estiver ocupada, troca as posições. */
export function moveButton(
  config: DeckConfig,
  profileId: string,
  pageId: string,
  buttonId: string,
  to: Position,
): DeckConfig {
  const next = clone(config);
  const buttons = pageAt(next, profileId, pageId).buttons ?? [];
  const moving = buttons.find((b) => b.id === buttonId);
  if (!moving) return next;
  const occupant = buttons.find(
    (b) => b.id !== buttonId && b.position.col === to.col && b.position.row === to.row,
  );
  if (occupant) occupant.position = { ...moving.position };
  moving.position = { ...to };
  return next;
}

// ---------------------------------------------------------------- páginas

export function addPage(config: DeckConfig, profileId: string, name: string): DeckConfig {
  const next = clone(config);
  const profile = profileAt(next, profileId);
  profile.pages = profile.pages ?? [];
  profile.pages.push({
    id: newId("page"),
    name: name.trim() || `Página ${profile.pages.length + 1}`,
    grid: { cols: 3, rows: 4 },
    buttons: [],
  });
  return next;
}

export function renamePage(
  config: DeckConfig,
  profileId: string,
  pageId: string,
  name: string,
): DeckConfig {
  const next = clone(config);
  pageAt(next, profileId, pageId).name = name.trim() || "Página";
  return next;
}

export function removePage(config: DeckConfig, profileId: string, pageId: string): DeckConfig {
  const next = clone(config);
  const profile = profileAt(next, profileId);
  const pages = profile.pages ?? [];
  if (pages.length <= 1) throw new Error("não dá para excluir a última página do perfil");
  profile.pages = pages.filter((p) => p.id !== pageId);
  return next;
}

// ---------------------------------------------------------------- perfis

export function addProfile(config: DeckConfig, name: string): DeckConfig {
  const next = clone(config);
  const profile: Profile = {
    id: newId("prof"),
    name: name.trim() || "Novo perfil",
    pages: [{ id: newId("page"), name: "Página 1", grid: { cols: 3, rows: 4 }, buttons: [] }],
  };
  next.profiles = [...(next.profiles ?? []), profile];
  next.active_profile = profile.id;
  return next;
}

export function renameProfile(config: DeckConfig, profileId: string, name: string): DeckConfig {
  const next = clone(config);
  profileAt(next, profileId).name = name.trim() || "Perfil";
  return next;
}

export function removeProfile(config: DeckConfig, profileId: string): DeckConfig {
  const next = clone(config);
  const profiles = next.profiles ?? [];
  if (profiles.length <= 1) throw new Error("não dá para excluir o último perfil");
  next.profiles = profiles.filter((p) => p.id !== profileId);
  if (next.active_profile === profileId) next.active_profile = next.profiles[0].id;
  return next;
}

export function setActiveProfile(config: DeckConfig, profileId: string): DeckConfig {
  const next = clone(config);
  profileAt(next, profileId);
  next.active_profile = profileId;
  return next;
}
