export type GradeKind = "numeric" | "pass" | "fail";

export type FinalGradeStatus = "numeric" | "passed" | "failed" | "none";

export interface FinalGrade {
  status: FinalGradeStatus;
  value: number | null;
}

export interface GradeAttempt {
  id: number;
  slot: number;
  kind: GradeKind;
  value: number | null;
}

export interface SeriesProgress {
  points_achieved: number;
  points_max: number;
  percent: number | null;
  passed: boolean;
  points_needed: number;
}

export interface Submission {
  id: number;
  series_id: number;
  week_number: number;
  points_achieved: number;
  points_max: number;
}

export interface SubmissionSeries {
  id: number;
  modul_id: number;
  name: string;
  threshold_percent: number;
  total_weeks: number | null;
  submissions: Submission[];
  progress: SeriesProgress;
}

export interface Modul {
  id: number;
  name: string;
  credits: number;
  studiengang_ids: number[];
  studiengaenge: { id: number; name: string }[];
  grade_attempts: GradeAttempt[];
  final_grade: FinalGrade;
  series: SubmissionSeries[];
  zulassung: boolean;
}

export interface Studiengang {
  id: number;
  name: string;
}

export interface User {
  id: number;
  name: string;
  email: string;
}

export interface KombiModul {
  id: number;
  name: string;
  credits: number;
  studiengang_id: number;
  source_module_ids: number[];
  source_module: { id: number; name: string }[];
  final_grade: FinalGrade;
}

export interface StudiengangStats {
  id: number | null;
  name: string;
  average: number | null;
  graded_credits: number;
  ungraded_pass_credits: number;
  total_credits: number;
  module_count: number;
  open_zulassung: { modul_id: number; modul_name: string }[];
}

export interface Overview {
  studiengaenge: StudiengangStats[];
  sonstiges: StudiengangStats;
  overall: StudiengangStats;
}
