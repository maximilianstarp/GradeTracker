export function StatTile({
  label,
  value,
  sublabel,
}: {
  label: string;
  value: string;
  sublabel?: string;
}) {
  return (
    <div className="rounded-xl border border-border bg-surface p-5">
      <div className="text-sm text-text-secondary">{label}</div>
      <div className="mt-1 text-3xl font-semibold tabular-nums text-text-primary">
        {value}
      </div>
      {sublabel && <div className="mt-1 text-sm text-text-muted">{sublabel}</div>}
    </div>
  );
}
