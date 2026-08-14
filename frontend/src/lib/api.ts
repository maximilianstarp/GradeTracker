import type { KombiModul, Modul, Overview, Studiengang } from "./types";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:5000";

export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    ...options,
    headers: { "Content-Type": "application/json", ...options?.headers },
    cache: "no-store",
  });

  if (res.status === 204) return undefined as T;

  const body = await res.json().catch(() => null);
  if (!res.ok) {
    throw new ApiError(body?.error ?? `Request fehlgeschlagen (${res.status})`, res.status);
  }
  return body as T;
}

// Studiengänge
export const listStudiengaenge = () => request<Studiengang[]>("/api/studiengaenge");
export const createStudiengang = (name: string) =>
  request<Studiengang>("/api/studiengaenge", { method: "POST", body: JSON.stringify({ name }) });
export const updateStudiengang = (id: number, name: string) =>
  request<Studiengang>(`/api/studiengaenge/${id}`, { method: "PATCH", body: JSON.stringify({ name }) });
export const deleteStudiengang = (id: number) =>
  request<void>(`/api/studiengaenge/${id}`, { method: "DELETE" });

// Module
export const listModule = (studiengangId?: number | null) => {
  const qs =
    studiengangId === undefined
      ? ""
      : `?studiengang_id=${studiengangId === null ? "null" : studiengangId}`;
  return request<Modul[]>(`/api/module${qs}`);
};
export const getModul = (id: number) => request<Modul>(`/api/module/${id}`);
export const createModul = (data: { name: string; credits: number; studiengang_id: number | null }) =>
  request<Modul>("/api/module", { method: "POST", body: JSON.stringify(data) });
export const updateModul = (
  id: number,
  data: Partial<{ name: string; credits: number; studiengang_id: number | null }>
) => request<Modul>(`/api/module/${id}`, { method: "PATCH", body: JSON.stringify(data) });
export const deleteModul = (id: number) => request<void>(`/api/module/${id}`, { method: "DELETE" });

// Grades
export const upsertGrade = (
  modulId: number,
  data: { slot: number; kind: "numeric" | "pass" | "fail"; value?: number }
) => request<Modul>(`/api/module/${modulId}/grades`, { method: "POST", body: JSON.stringify(data) });
export const deleteGrade = (gradeId: number) => request<Modul>(`/api/grades/${gradeId}`, { method: "DELETE" });

// Submission series
export const createSeries = (
  modulId: number,
  data: { name: string; threshold_percent?: number; total_weeks?: number }
) => request<Modul>(`/api/module/${modulId}/series`, { method: "POST", body: JSON.stringify(data) });
export const updateSeries = (
  seriesId: number,
  data: Partial<{ name: string; threshold_percent: number; total_weeks: number | null }>
) => request<Modul>(`/api/series/${seriesId}`, { method: "PATCH", body: JSON.stringify(data) });
export const deleteSeries = (seriesId: number) =>
  request<Modul>(`/api/series/${seriesId}`, { method: "DELETE" });

// Submissions
export const createSubmission = (
  seriesId: number,
  data: { week_number: number; points_achieved: number; points_max: number }
) => request<Modul>(`/api/series/${seriesId}/submissions`, { method: "POST", body: JSON.stringify(data) });
export const updateSubmission = (
  submissionId: number,
  data: Partial<{ points_achieved: number; points_max: number; week_number: number }>
) => request<Modul>(`/api/submissions/${submissionId}`, { method: "PATCH", body: JSON.stringify(data) });
export const deleteSubmission = (submissionId: number) =>
  request<Modul>(`/api/submissions/${submissionId}`, { method: "DELETE" });

// Kombi-Module
export const listKombimodule = () => request<KombiModul[]>("/api/kombimodule");
export const createKombimodul = (data: {
  name: string;
  credits: number;
  studiengang_id: number;
  source_module_ids: number[];
}) => request<KombiModul>("/api/kombimodule", { method: "POST", body: JSON.stringify(data) });
export const updateKombimodul = (
  id: number,
  data: Partial<{ name: string; credits: number; studiengang_id: number; source_module_ids: number[] }>
) => request<KombiModul>(`/api/kombimodule/${id}`, { method: "PATCH", body: JSON.stringify(data) });
export const deleteKombimodul = (id: number) =>
  request<void>(`/api/kombimodule/${id}`, { method: "DELETE" });

// Stats
export const getOverview = () => request<Overview>("/api/stats/overview");
