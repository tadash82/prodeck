import { describe, expect, it } from "vitest";

import {
  addAutoRule,
  addPage,
  addProfile,
  moveButton,
  removeAutoRule,
  removeButton,
  removePage,
  removeProfile,
  repackButtons,
  setActiveProfile,
  setAllowShell,
  setGrid,
  upsertButton,
} from "../src/lib/deckOps";
import type { Button, DeckConfig } from "../src/types/protocol";

function button(id: string, col = 0, row = 0): Button {
  return {
    id,
    position: { col, row },
    label: id,
    action: { type: "open_path", path: "~" },
  };
}

function config(): DeckConfig {
  return {
    version: 1,
    active_profile: "a",
    profiles: [
      {
        id: "a",
        name: "A",
        pages: [
          { id: "p1", name: "P1", grid: { cols: 3, rows: 4 }, buttons: [button("b1")] },
        ],
      },
    ],
  };
}

describe("deckOps", () => {
  it("upsertButton adiciona e substitui sem mutar a original", () => {
    const original = config();
    const added = upsertButton(original, "a", "p1", button("b2", 1, 0));
    expect(added.profiles![0].pages![0].buttons).toHaveLength(2);
    expect(original.profiles![0].pages![0].buttons).toHaveLength(1);

    const replaced = upsertButton(added, "a", "p1", { ...button("b2"), label: "Novo" });
    expect(replaced.profiles![0].pages![0].buttons).toHaveLength(2);
    expect(replaced.profiles![0].pages![0].buttons![1].label).toBe("Novo");
  });

  it("moveButton troca posições quando a célula está ocupada", () => {
    let c = upsertButton(config(), "a", "p1", button("b2", 1, 0));
    c = moveButton(c, "a", "p1", "b1", { col: 1, row: 0 });
    const [b1, b2] = c.profiles![0].pages![0].buttons!;
    expect(b1.position).toEqual({ col: 1, row: 0 });
    expect(b2.position).toEqual({ col: 0, row: 0 });
  });

  it("removeButton remove pelo id", () => {
    const c = removeButton(config(), "a", "p1", "b1");
    expect(c.profiles![0].pages![0].buttons).toHaveLength(0);
  });

  it("removePage impede excluir a última página", () => {
    expect(() => removePage(config(), "a", "p1")).toThrow(/última página/);
    const withTwo = addPage(config(), "a", "Extra");
    const pageId = withTwo.profiles![0].pages![1].id;
    expect(removePage(withTwo, "a", pageId).profiles![0].pages).toHaveLength(1);
  });

  it("addProfile cria com uma página e ativa", () => {
    const c = addProfile(config(), "Trabalho");
    expect(c.profiles).toHaveLength(2);
    expect(c.active_profile).toBe(c.profiles![1].id);
    expect(c.profiles![1].pages).toHaveLength(1);
  });

  it("removeProfile do ativo migra o ativo e impede remover o último", () => {
    const two = addProfile(config(), "B");
    const removed = removeProfile(two, two.active_profile);
    expect(removed.active_profile).toBe("a");
    expect(() => removeProfile(removed, "a")).toThrow(/último perfil/);
  });

  it("setActiveProfile valida existência", () => {
    expect(() => setActiveProfile(config(), "nope")).toThrow(/não encontrado/);
  });

  it("setAllowShell liga e desliga", () => {
    expect(setAllowShell(config(), true).allow_shell).toBe(true);
    expect(setAllowShell(setAllowShell(config(), true), false).allow_shell).toBe(false);
  });

  it("setGrid ajusta a grade e respeita os limites do modelo", () => {
    expect(setGrid(config(), "a", "p1", { cols: 5 }).profiles![0].pages![0].grid).toEqual({
      cols: 5,
      rows: 4,
    });
    expect(setGrid(config(), "a", "p1", { cols: 99, rows: 0 }).profiles![0].pages![0].grid).toEqual({
      cols: 8,
      rows: 1,
    });
  });

  it("repackButtons preenche o grid em ordem de leitura, sem buracos", () => {
    let c = upsertButton(config(), "a", "p1", button("b2", 2, 1));
    c = upsertButton(c, "a", "p1", button("b3", 1, 0));
    const pos = Object.fromEntries(
      repackButtons(c, "a", "p1").profiles![0].pages![0].buttons!.map((b) => [b.id, b.position]),
    );
    expect(pos.b1).toEqual({ col: 0, row: 0 });
    expect(pos.b3).toEqual({ col: 1, row: 0 });
    expect(pos.b2).toEqual({ col: 2, row: 0 });
  });

  it("addAutoRule acrescenta a regra e valida match/perfil", () => {
    const c = addAutoRule(config(), " code ", "a");
    expect(c.auto_profile).toEqual([{ match: "code", profile: "a" }]);
    expect(() => addAutoRule(config(), "  ", "a")).toThrow();
    expect(() => addAutoRule(config(), "code", "naoexiste")).toThrow();
  });

  it("removeAutoRule remove pelo índice", () => {
    let c = addAutoRule(config(), "code", "a");
    c = addAutoRule(c, "firefox", "a");
    expect(removeAutoRule(c, 0).auto_profile).toEqual([{ match: "firefox", profile: "a" }]);
  });
});
