import {
  DndContext,
  PointerSensor,
  useDroppable,
  useSensor,
  useSensors,
  type DragEndEvent,
} from "@dnd-kit/core";
import { Icon } from "@iconify/react";

import { moveButton } from "../lib/deckOps";
import { useDeck } from "../store/useDeck";
import type { Button, Page } from "../types/protocol";
import { DeckButton, markDragEnd } from "./DeckButton";

type DeckGridProps = {
  page: Page;
  profileId: string;
};

export function DeckGrid({ page, profileId }: DeckGridProps) {
  const editMode = useDeck((s) => s.editMode);
  const openEditor = useDeck((s) => s.openEditor);
  const apply = useDeck((s) => s.apply);

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 8 } }),
  );

  const cols = page.grid?.cols ?? 3;
  const rows = page.grid?.rows ?? 4;
  const buttons = page.buttons ?? [];
  const byCell = new Map<string, Button>();
  for (const button of buttons) {
    byCell.set(`${button.position.col}:${button.position.row}`, button);
  }

  const onDragEnd = (event: DragEndEvent) => {
    markDragEnd();
    const over = event.over?.id;
    if (typeof over !== "string" || !over.startsWith("cell-")) return;
    const [, col, row] = over.split("-");
    apply((config) =>
      moveButton(config, profileId, page.id, String(event.active.id), {
        col: Number(col),
        row: Number(row),
      }),
    );
  };

  const grid = (
    <div
      className="mx-auto grid w-full max-w-md gap-3"
      style={{ gridTemplateColumns: `repeat(${cols}, minmax(0, 1fr))` }}
    >
      {Array.from({ length: rows * cols }, (_, index) => {
        const col = index % cols;
        const row = Math.floor(index / cols);
        const button = byCell.get(`${col}:${row}`);
        if (button) {
          return (
            <DeckButton
              key={button.id}
              button={button}
              profileId={profileId}
              pageId={page.id}
            />
          );
        }
        if (!editMode) return <div key={`empty-${index}`} className="aspect-square" />;
        return (
          <EmptyCell
            key={`cell-${col}-${row}`}
            col={col}
            row={row}
            onAdd={() =>
              openEditor({ kind: "new", profileId, pageId: page.id, position: { col, row } })
            }
          />
        );
      })}
      {/* botões fora dos limites do grid continuam visíveis e editáveis */}
      {buttons
        .filter((b) => b.position.col >= cols || b.position.row >= rows)
        .map((button) => (
          <DeckButton
            key={button.id}
            button={button}
            profileId={profileId}
            pageId={page.id}
          />
        ))}
    </div>
  );

  if (!editMode) return grid;
  return (
    <DndContext sensors={sensors} onDragEnd={onDragEnd}>
      {grid}
    </DndContext>
  );
}

function EmptyCell({ col, row, onAdd }: { col: number; row: number; onAdd: () => void }) {
  const { setNodeRef, isOver } = useDroppable({ id: `cell-${col}-${row}` });
  return (
    <button
      ref={setNodeRef}
      onClick={onAdd}
      style={{ gridColumnStart: col + 1, gridRowStart: row + 1 }}
      className={`flex aspect-square items-center justify-center rounded-2xl border-2 border-dashed transition-colors ${
        isOver ? "border-blue-500 bg-blue-500/10" : "border-slate-700/70 text-slate-600"
      }`}
    >
      <Icon icon="mdi:plus" style={{ fontSize: "1.6rem" }} />
    </button>
  );
}
