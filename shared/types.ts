// 공유 타입 정의

export interface Program {
  id: string;
  title: string;
  description: string;
  category: string;
  organization: string;
  startDate: string;
  endDate: string;
  eligibility: string[];
  benefits: string;
  applicationUrl: string;
  source: string;
  createdAt: string;
  updatedAt: string;
}

export interface SearchParams {
  query?: string;
  category?: string;
  region?: string;
  targetAge?: number;
  page?: number;
  limit?: number;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  limit: number;
  totalPages: number;
}
