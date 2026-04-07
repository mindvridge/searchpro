"use client";

import { useQuery } from "@tanstack/react-query";
import { fetchApi, type ProgramDetail, type CalendarEntry } from "@/lib/api";

export function useProgram(id: string) {
  return useQuery<ProgramDetail>({
    queryKey: ["program", id],
    queryFn: () => fetchApi(`/api/v1/programs/${id}`),
    enabled: !!id,
  });
}

export function useCalendar(year: number, month: number) {
  return useQuery<CalendarEntry[]>({
    queryKey: ["calendar", year, month],
    queryFn: () => fetchApi(`/api/v1/programs/calendar?year=${year}&month=${month}`),
  });
}
