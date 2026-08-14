import type { Studiengang } from "@/lib/types";

export function StudiengangMultiSelect({
  studiengaenge,
  selectedIds,
  onChange,
}: {
  studiengaenge: Studiengang[];
  selectedIds: number[];
  onChange: (ids: number[]) => void;
}) {
  function toggle(id: number) {
    onChange(selectedIds.includes(id) ? selectedIds.filter((x) => x !== id) : [...selectedIds, id]);
  }

  return (
    <div className="flex flex-wrap gap-2">
      {studiengaenge.map((sg) => (
        <label
          key={sg.id}
          className={`flex cursor-pointer items-center gap-1.5 rounded-full border px-3 py-1 text-sm ${
            selectedIds.includes(sg.id)
              ? "border-series-1 bg-series-1/10 text-series-1"
              : "border-border text-text-secondary hover:bg-text-muted/10"
          }`}
        >
          <input
            type="checkbox"
            checked={selectedIds.includes(sg.id)}
            onChange={() => toggle(sg.id)}
            className="hidden"
          />
          {sg.name}
        </label>
      ))}
      {studiengaenge.length === 0 && (
        <span className="text-sm text-text-muted">Keine Studiengänge angelegt.</span>
      )}
      {selectedIds.length === 0 && studiengaenge.length > 0 && (
        <span className="self-center text-sm text-text-muted">→ Sonstiges</span>
      )}
    </div>
  );
}
