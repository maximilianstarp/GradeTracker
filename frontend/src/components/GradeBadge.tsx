import type { FinalGrade } from "@/lib/types";
import { formatFinalGrade, gradeStatusColor } from "@/lib/format";

const STYLES: Record<string, string> = {
  good: "bg-status-good/10 text-status-good",
  warning: "bg-status-warning/15 text-[#a5690a] dark:text-status-warning",
  critical: "bg-status-critical/10 text-status-critical",
  muted: "bg-text-muted/10 text-text-muted",
};

export function GradeBadge({ grade }: { grade: FinalGrade }) {
  const color = gradeStatusColor(grade);
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-1 text-sm font-medium tabular-nums ${STYLES[color]}`}
    >
      {formatFinalGrade(grade)}
    </span>
  );
}
