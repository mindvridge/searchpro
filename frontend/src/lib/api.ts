const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
  }
}

export async function fetchApi<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  const res = await fetch(`${API_URL}${endpoint}`, {
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    ...options,
  });
  if (!res.ok) {
    throw new ApiError(res.status, `API Error: ${res.status}`);
  }
  return res.json();
}

// --- Type definitions for API responses ---

export interface ProgramListItem {
  id: string;
  title: string;
  source: string;
  organization: string | null;
  category: string | null;
  region: string | null;
  target_type: string | null;
  support_amount: string | null;
  support_amount_max: number | null;
  application_start: string | null;
  application_end: string | null;
  status: "UPCOMING" | "OPEN" | "CLOSED";
  tags: string[] | null;
  view_count: number;
  created_at: string;
}

export interface FacetItem {
  name: string;
  count: number;
}

export interface FilterFacets {
  categories: FacetItem[];
  regions: FacetItem[];
  sources: FacetItem[];
}

export interface ProgramListResponse {
  items: ProgramListItem[];
  total: number;
  page: number;
  limit: number;
  total_pages: number;
  filters: FilterFacets | null;
}

export interface ProgramDetail extends ProgramListItem {
  source_id: string;
  sub_category: string | null;
  description: string | null;
  eligibility: string | null;
  detail_url: string | null;
  raw_data: Record<string, unknown> | null;
  summary: string | null;
  updated_at: string;
  related: {
    id: string;
    title: string;
    organization: string | null;
    application_end: string | null;
    status: string;
  }[];
}

export interface CalendarEntry {
  date: string;
  count: number;
  programs: { id: string; title: string; organization: string | null }[];
}

export interface ProgramStats {
  total: number;
  open_count: number;
  closing_this_week: number;
  by_category: { category: string; count: number }[];
  by_source: { source: string; count: number }[];
}

export interface BookmarkItem {
  id: string;
  user_id: string;
  program_id: string;
  memo: string | null;
  created_at: string;
  program: ProgramListItem | null;
}
