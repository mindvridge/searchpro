"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function adminFetch<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const adminKey = typeof window !== "undefined" ? localStorage.getItem("admin_key") || "" : "";
  const res = await fetch(`${API_URL}${endpoint}`, {
    headers: { "Content-Type": "application/json", "X-Admin-Key": adminKey },
    ...options,
  });
  if (!res.ok) throw new Error(`Admin API Error: ${res.status}`);
  if (res.status === 204) return {} as T;
  return res.json();
}

// --- Types ---

export interface AdminStats {
  total_programs: number;
  programs_by_status: Record<string, number>;
  programs_by_source: { source: string; count: number }[];
  programs_by_category: { category: string; count: number }[];
  today_new: number;
  today_updated: number;
  total_users: number;
  today_new_users: number;
  total_subscribers: number;
  recent_crawl_logs: CrawlLog[];
}

export interface CrawlLog {
  id: string;
  source: string;
  started_at: string;
  finished_at: string | null;
  total_fetched: number;
  new_count: number;
  updated_count: number;
  error_count: number;
  error_detail: string | null;
  status: string;
}

export interface AdminUser {
  id: string;
  email: string;
  name: string | null;
  provider: string;
  is_premium: boolean;
  profile: Record<string, unknown> | null;
  created_at: string;
}

export interface AdminProgram {
  id: string;
  title: string;
  source: string;
  source_id: string;
  organization: string | null;
  category: string | null;
  region: string | null;
  status: string;
  application_end: string | null;
  summary: string | null;
  created_at: string;
  updated_at: string;
}

// --- Hooks ---

export function useAdminStats() {
  return useQuery<AdminStats>({
    queryKey: ["admin-stats"],
    queryFn: () => adminFetch("/api/v1/admin/stats"),
    staleTime: 30_000,
  });
}

export function useAdminCrawlLogs(limit = 20) {
  return useQuery<CrawlLog[]>({
    queryKey: ["admin-crawl-logs", limit],
    queryFn: () => adminFetch(`/api/v1/admin/crawl/logs?limit=${limit}`),
  });
}

export function useTriggerCrawl() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (source: string) =>
      adminFetch(`/api/v1/admin/crawl/${source}`, { method: "POST" }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["admin-stats"] });
      qc.invalidateQueries({ queryKey: ["admin-crawl-logs"] });
    },
  });
}

export function useAdminUsers(limit = 50) {
  return useQuery<AdminUser[]>({
    queryKey: ["admin-users", limit],
    queryFn: () => adminFetch(`/api/v1/admin/users?limit=${limit}`),
  });
}

export function usePatchUser() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, ...body }: { id: string; is_premium?: boolean; name?: string }) =>
      adminFetch(`/api/v1/admin/users/${id}`, { method: "PATCH", body: JSON.stringify(body) }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["admin-users"] }),
  });
}

export function useAdminPrograms(q?: string, limit = 20) {
  return useQuery<AdminProgram[]>({
    queryKey: ["admin-programs", q, limit],
    queryFn: () => adminFetch(`/api/v1/admin/programs?limit=${limit}${q ? `&q=${q}` : ""}`),
  });
}

export function useDeleteProgram() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) =>
      adminFetch(`/api/v1/admin/programs/${id}`, { method: "DELETE" }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["admin-programs"] }),
  });
}

export function useRegenerateSummary() {
  return useMutation({
    mutationFn: (id: string) =>
      adminFetch<{ summary: string | null }>(`/api/v1/admin/programs/${id}/regenerate-summary`, { method: "POST" }),
  });
}
