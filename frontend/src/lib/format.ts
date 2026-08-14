import type { FinalGrade } from "./types";

export function formatGradeValue(value: number): string {
  return value.toFixed(1).replace(".", ",");
}

export function formatFinalGrade(grade: FinalGrade): string {
  switch (grade.status) {
    case "numeric":
      return grade.value !== null ? formatGradeValue(grade.value) : "–";
    case "passed":
      return "bestanden";
    case "failed":
      return "nicht bestanden";
    default:
      return "offen";
  }
}

/** Status color role for a final grade, following the fixed status palette. */
export function gradeStatusColor(grade: FinalGrade): "good" | "warning" | "critical" | "muted" {
  if (grade.status === "numeric" && grade.value !== null) {
    if (grade.value <= 1.5) return "good";
    if (grade.value <= 2.5) return "good";
    if (grade.value <= 3.5) return "warning";
    if (grade.value <= 4.0) return "warning";
    return "critical";
  }
  if (grade.status === "passed") return "good";
  if (grade.status === "failed") return "critical";
  return "muted";
}

export function formatCredits(value: number): string {
  const rounded = Math.round(value * 10) / 10;
  return `${rounded % 1 === 0 ? rounded.toFixed(0) : rounded.toFixed(1)} CP`;
}

export function formatPercent(value: number | null): string {
  if (value === null) return "–";
  return `${Math.round(value)}%`;
}
