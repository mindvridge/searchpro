"use client";

import { useQuery } from "@tanstack/react-query";
import { fetchApi } from "@/lib/api";

interface SummaryResponse {
  summary: string | null;
  cached: boolean;
  message?: string;
}

interface RecommendationItem {
  id: string;
  title: string;
  source: string;
  organization: string | null;
  category: string | null;
  region: string | null;
  support_amount: string | null;
  application_end: string | null;
  status: string;
  tags: string[] | null;
  view_count: number;
  created_at: string;
  reason: string;
}

interface RecommendationResponse {
  items: RecommendationItem[];
  personalized: boolean;
}

export function useProgramSummary(programId: string) {
  return useQuery<SummaryResponse>({
    queryKey: ["program-summary", programId],
    queryFn: () => fetchApi(`/api/v1/programs/${programId}/summary`),
    enabled: !!programId,
    staleTime: 10 * 60 * 1000, // 10 min cache
    retry: 1,
  });
}

export function useRecommendations(limit: number = 6) {
  return useQuery<RecommendationResponse>({
    queryKey: ["recommendations", limit],
    queryFn: () => fetchApi(`/api/v1/recommendations?limit=${limit}`),
    staleTime: 5 * 60 * 1000,
  });
}

export type { RecommendationItem, RecommendationResponse };
