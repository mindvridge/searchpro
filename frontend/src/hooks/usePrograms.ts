"use client";

import { useQuery, useInfiniteQuery } from "@tanstack/react-query";
import { fetchApi, type ProgramListResponse, type ProgramStats } from "@/lib/api";

export interface ProgramFilters {
  q?: string;
  category?: string[];
  region?: string[];
  status?: string;
  target_type?: string;
  amount_min?: number;
  amount_max?: number;
  source?: string[];
  deadline_from?: string;
  deadline_to?: string;
  sort?: string;
  page?: number;
  limit?: number;
}

function buildQuery(filters: ProgramFilters): string {
  const params = new URLSearchParams();
  if (filters.q) params.set("q", filters.q);
  if (filters.status) params.set("status", filters.status);
  if (filters.target_type) params.set("target_type", filters.target_type);
  if (filters.amount_min != null) params.set("amount_min", String(filters.amount_min));
  if (filters.amount_max != null) params.set("amount_max", String(filters.amount_max));
  if (filters.deadline_from) params.set("deadline_from", filters.deadline_from);
  if (filters.deadline_to) params.set("deadline_to", filters.deadline_to);
  if (filters.sort) params.set("sort", filters.sort);
  if (filters.page) params.set("page", String(filters.page));
  if (filters.limit) params.set("limit", String(filters.limit));
  filters.category?.forEach((c) => params.append("category", c));
  filters.region?.forEach((r) => params.append("region", r));
  filters.source?.forEach((s) => params.append("source", s));
  return params.toString();
}

export function usePrograms(filters: ProgramFilters) {
  return useQuery<ProgramListResponse>({
    queryKey: ["programs", filters],
    queryFn: () => fetchApi(`/api/v1/programs?${buildQuery(filters)}`),
  });
}

export function useProgramsInfinite(filters: Omit<ProgramFilters, "page">) {
  return useInfiniteQuery<ProgramListResponse>({
    queryKey: ["programs-infinite", filters],
    queryFn: ({ pageParam = 1 }) =>
      fetchApi(`/api/v1/programs?${buildQuery({ ...filters, page: pageParam as number })}`),
    getNextPageParam: (last) =>
      last.page < last.total_pages ? last.page + 1 : undefined,
    initialPageParam: 1,
  });
}

export function useProgramStats() {
  return useQuery<ProgramStats>({
    queryKey: ["program-stats"],
    queryFn: () => fetchApi("/api/v1/programs/stats"),
    staleTime: 5 * 60 * 1000,
  });
}
