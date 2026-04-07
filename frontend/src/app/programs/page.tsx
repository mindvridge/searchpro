"use client";

import { Suspense, useCallback, useMemo, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import {
  Filter,
  LayoutGrid,
  List,
  X,
  ChevronLeft,
  ChevronRight,
  SlidersHorizontal,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet";
import { ProgramCard, ProgramCardSkeleton } from "@/components/ProgramCard";
import { usePrograms, type ProgramFilters } from "@/hooks/usePrograms";
import type { FacetItem } from "@/lib/api";

export default function ProgramsPage() {
  return (
    <Suspense>
      <ProgramsContent />
    </Suspense>
  );
}

function ProgramsContent() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const filtersFromUrl = useMemo<ProgramFilters>(() => ({
    q: searchParams.get("q") || undefined,
    category: searchParams.getAll("category").length ? searchParams.getAll("category") : undefined,
    region: searchParams.getAll("region").length ? searchParams.getAll("region") : undefined,
    status: searchParams.get("status") || "OPEN",
    sort: searchParams.get("sort") || "created_desc",
    page: Number(searchParams.get("page")) || 1,
    limit: 20,
  }), [searchParams]);

  const { data, isLoading } = usePrograms(filtersFromUrl);
  const facets = data?.filters;

  const updateParams = useCallback(
    (updates: Record<string, string | string[] | null>) => {
      const params = new URLSearchParams(searchParams.toString());
      // Reset page on filter change
      params.delete("page");
      Object.entries(updates).forEach(([key, value]) => {
        params.delete(key);
        if (value === null) return;
        if (Array.isArray(value)) {
          value.forEach((v) => params.append(key, v));
        } else {
          params.set(key, value);
        }
      });
      router.push(`/programs?${params.toString()}`);
    },
    [searchParams, router]
  );

  const toggleArrayParam = useCallback(
    (key: string, value: string) => {
      const current = searchParams.getAll(key);
      const next = current.includes(value)
        ? current.filter((v) => v !== value)
        : [...current, value];
      updateParams({ [key]: next.length ? next : null });
    },
    [searchParams, updateParams]
  );

  const resetFilters = () => {
    router.push("/programs");
  };

  const goToPage = (page: number) => {
    const params = new URLSearchParams(searchParams.toString());
    params.set("page", String(page));
    router.push(`/programs?${params.toString()}`);
  };

  const hasActiveFilters =
    (filtersFromUrl.category?.length ?? 0) > 0 ||
    (filtersFromUrl.region?.length ?? 0) > 0 ||
    filtersFromUrl.q;

  const filterSidebar = (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="font-semibold text-sm">필터</h3>
        {hasActiveFilters && (
          <button onClick={resetFilters} className="text-xs text-muted-foreground hover:text-foreground">
            초기화
          </button>
        )}
      </div>

      {/* Status */}
      <div>
        <p className="text-xs font-medium text-muted-foreground mb-2">상태</p>
        <div className="flex flex-wrap gap-1.5">
          {[
            { value: "OPEN", label: "진행중" },
            { value: "UPCOMING", label: "예정" },
            { value: "CLOSED", label: "마감" },
          ].map((s) => (
            <Badge
              key={s.value}
              variant={filtersFromUrl.status === s.value ? "default" : "outline"}
              className="cursor-pointer"
              onClick={() => updateParams({ status: s.value })}
            >
              {s.label}
            </Badge>
          ))}
        </div>
      </div>

      {/* Categories */}
      <FilterCheckboxGroup
        title="카테고리"
        items={facets?.categories ?? []}
        selected={filtersFromUrl.category ?? []}
        onToggle={(v) => toggleArrayParam("category", v)}
      />

      {/* Regions */}
      <FilterCheckboxGroup
        title="지역"
        items={facets?.regions ?? []}
        selected={filtersFromUrl.region ?? []}
        onToggle={(v) => toggleArrayParam("region", v)}
      />

      {/* Sources */}
      <FilterCheckboxGroup
        title="데이터 소스"
        items={facets?.sources ?? []}
        selected={searchParams.getAll("source")}
        onToggle={(v) => toggleArrayParam("source", v)}
      />
    </div>
  );

  return (
    <div className="container mx-auto px-4 py-6">
      <div className="flex gap-6">
        {/* Desktop filter sidebar */}
        <aside className="hidden lg:block w-56 shrink-0">
          <div className="sticky top-20">{filterSidebar}</div>
        </aside>

        {/* Main content */}
        <div className="flex-1 min-w-0">
          {/* Top bar */}
          <div className="flex items-center justify-between mb-4 gap-3 flex-wrap">
            <div className="flex items-center gap-2">
              {/* Mobile filter button */}
              <Sheet>
                <SheetTrigger className="lg:hidden inline-flex items-center gap-1.5 rounded-lg border px-3 py-1.5 text-sm hover:bg-secondary">
                  <SlidersHorizontal className="h-4 w-4" />
                  필터
                </SheetTrigger>
                <SheetContent side="left" className="w-72 overflow-y-auto pt-8">
                  {filterSidebar}
                </SheetContent>
              </Sheet>

              <p className="text-sm text-muted-foreground">
                {data ? (
                  <>
                    <span className="font-semibold text-foreground">{data.total.toLocaleString()}</span>건
                  </>
                ) : (
                  "검색 중..."
                )}
              </p>
            </div>

            <Select
              value={filtersFromUrl.sort}
              onValueChange={(v) => updateParams({ sort: v })}
            >
              <SelectTrigger className="w-36 h-8 text-xs">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="created_desc">최신순</SelectItem>
                <SelectItem value="deadline_asc">마감임박순</SelectItem>
                <SelectItem value="amount_desc">금액순</SelectItem>
                <SelectItem value="popular">인기순</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Active filter chips */}
          {hasActiveFilters && (
            <div className="flex flex-wrap gap-1.5 mb-4">
              {filtersFromUrl.q && (
                <Badge variant="secondary" className="gap-1">
                  검색: {filtersFromUrl.q}
                  <X className="h-3 w-3 cursor-pointer" onClick={() => updateParams({ q: null })} />
                </Badge>
              )}
              {filtersFromUrl.category?.map((c) => (
                <Badge key={c} variant="secondary" className="gap-1">
                  {c}
                  <X className="h-3 w-3 cursor-pointer" onClick={() => toggleArrayParam("category", c)} />
                </Badge>
              ))}
              {filtersFromUrl.region?.map((r) => (
                <Badge key={r} variant="secondary" className="gap-1">
                  {r}
                  <X className="h-3 w-3 cursor-pointer" onClick={() => toggleArrayParam("region", r)} />
                </Badge>
              ))}
            </div>
          )}

          {/* Results grid */}
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
            {isLoading
              ? Array.from({ length: 6 }).map((_, i) => <ProgramCardSkeleton key={i} />)
              : data?.items.map((p) => <ProgramCard key={p.id} program={p} />)}
          </div>

          {/* Empty state */}
          {!isLoading && data?.items.length === 0 && (
            <div className="text-center py-16">
              <p className="text-muted-foreground mb-2">조건에 맞는 지원사업이 없습니다.</p>
              <p className="text-sm text-muted-foreground mb-4">
                필터 조건을 완화하거나 다른 키워드로 검색해보세요.
              </p>
              <Button variant="outline" onClick={resetFilters}>
                필터 초기화
              </Button>
            </div>
          )}

          {/* Pagination */}
          {data && data.total_pages > 1 && (
            <div className="flex items-center justify-center gap-2 mt-8">
              <Button
                variant="outline"
                size="icon"
                className="h-8 w-8"
                disabled={data.page <= 1}
                onClick={() => goToPage(data.page - 1)}
              >
                <ChevronLeft className="h-4 w-4" />
              </Button>
              <span className="text-sm text-muted-foreground px-3">
                {data.page} / {data.total_pages}
              </span>
              <Button
                variant="outline"
                size="icon"
                className="h-8 w-8"
                disabled={data.page >= data.total_pages}
                onClick={() => goToPage(data.page + 1)}
              >
                <ChevronRight className="h-4 w-4" />
              </Button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function FilterCheckboxGroup({
  title,
  items,
  selected,
  onToggle,
}: {
  title: string;
  items: FacetItem[];
  selected: string[];
  onToggle: (value: string) => void;
}) {
  const [expanded, setExpanded] = useState(false);
  const visible = expanded ? items : items.slice(0, 6);

  return (
    <div>
      <p className="text-xs font-medium text-muted-foreground mb-2">{title}</p>
      <div className="space-y-1">
        {visible.map((item) => (
          <label key={item.name} className="flex items-center gap-2 text-sm cursor-pointer hover:bg-secondary/50 rounded px-1 py-0.5">
            <input
              type="checkbox"
              checked={selected.includes(item.name)}
              onChange={() => onToggle(item.name)}
              className="rounded border-muted-foreground/30"
            />
            <span className="flex-1 truncate">{item.name}</span>
            <span className="text-xs text-muted-foreground">{item.count}</span>
          </label>
        ))}
      </div>
      {items.length > 6 && (
        <button
          onClick={() => setExpanded(!expanded)}
          className="text-xs text-primary mt-1 hover:underline"
        >
          {expanded ? "접기" : `+${items.length - 6}개 더보기`}
        </button>
      )}
    </div>
  );
}
