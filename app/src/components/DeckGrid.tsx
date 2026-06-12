import type { Page } from "../types/protocol";
import { DeckButton } from "./DeckButton";

export function DeckGrid({ page }: { page: Page }) {
  const cols = page.grid?.cols ?? 3;
  return (
    <div
      className="mx-auto grid w-full max-w-md gap-3"
      style={{ gridTemplateColumns: `repeat(${cols}, minmax(0, 1fr))` }}
    >
      {(page.buttons ?? []).map((button) => (
        <DeckButton key={button.id} button={button} />
      ))}
    </div>
  );
}
