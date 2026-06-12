import { labelClass } from "./Sheet";

const PALETTE = [
  "#3b82f6",
  "#2dd4bf",
  "#22c55e",
  "#eab308",
  "#f59e0b",
  "#ef4444",
  "#ec4899",
  "#8b5cf6",
  "#06b6d4",
  "#64748b",
];

export function ColorPicker({
  value,
  onChange,
}: {
  value: string;
  onChange: (color: string) => void;
}) {
  return (
    <div>
      <label className={labelClass}>Cor</label>
      <div className="flex flex-wrap gap-2">
        {PALETTE.map((color) => (
          <button
            key={color}
            type="button"
            onClick={() => onChange(color)}
            aria-label={color}
            className={`h-9 w-9 rounded-full transition-transform ${
              color === value ? "scale-110 ring-2 ring-white" : "active:scale-95"
            }`}
            style={{ background: color }}
          />
        ))}
      </div>
    </div>
  );
}
