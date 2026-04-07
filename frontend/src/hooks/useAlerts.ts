"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { fetchApi } from "@/lib/api";

export interface AlertItem {
  id: string;
  user_id: string;
  type: "KEYWORD" | "CATEGORY" | "DEADLINE";
  condition: Record<string, unknown>;
  channel: "EMAIL" | "PUSH";
  is_active: boolean;
  created_at: string;
}

export function useAlerts() {
  return useQuery<AlertItem[]>({
    queryKey: ["alerts"],
    queryFn: () => fetchApi("/api/v1/alerts"),
  });
}

export function useCreateAlert() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: { type: string; condition: Record<string, unknown>; channel: string }) =>
      fetchApi("/api/v1/alerts", { method: "POST", body: JSON.stringify(body) }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["alerts"] }),
  });
}

export function useDeleteAlert() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => fetchApi(`/api/v1/alerts/${id}`, { method: "DELETE" }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["alerts"] }),
  });
}

export function useToggleAlert() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => fetchApi(`/api/v1/alerts/${id}/toggle`, { method: "PUT" }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["alerts"] }),
  });
}

export function useUpdateAlert() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, ...body }: { id: string; condition?: Record<string, unknown>; channel?: string; is_active?: boolean }) =>
      fetchApi(`/api/v1/alerts/${id}`, { method: "PUT", body: JSON.stringify(body) }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["alerts"] }),
  });
}
