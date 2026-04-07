"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  Search,
  ArrowRight,
  Rocket,
  FlaskConical,
  Globe,
  Banknote,
  Users,
  Building,
  Lightbulb,
  TrendingUp,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { ProgramCard, ProgramCardSkeleton } from "@/components/ProgramCard";
import { usePrograms, useProgramStats } from "@/hooks/usePrograms";

const CATEGORIES = [
  { label: "창업", icon: Rocket, color: "text-orange-500" },
  { label: "R&D", icon: FlaskConical, color: "text-blue-500" },
  { label: "수출", icon: Globe, color: "text-green-500" },
  { label: "금융/투자", icon: Banknote, color: "text-purple-500" },
  { label: "인력", icon: Users, color: "text-pink-500" },
  { label: "시설/공간", icon: Building, color: "text-yellow-600" },
  { label: "컨설팅", icon: Lightbulb, color: "text-cyan-500" },
  { label: "마케팅", icon: TrendingUp, color: "text-red-500" },
];

export default function HomePage() {
  const router = useRouter();
  const [query, setQuery] = useState("");
  const { data: stats } = useProgramStats();

  const { data: deadlineData, isLoading: loadingDeadline } = usePrograms({
    status: "OPEN",
    sort: "deadline_asc",
    limit: 6,
  });

  const { data: recentData, isLoading: loadingRecent } = usePrograms({
    sort: "created_desc",
    limit: 6,
  });

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim().length >= 2) {
      router.push(`/programs?q=${encodeURIComponent(query.trim())}`);
    }
  };

  return (
    <div>
      {/* Hero */}
      <section className="bg-gradient-to-br from-[var(--color-navy)] to-[var(--color-navy-light)] text-white">
        <div className="container mx-auto px-4 py-16 md:py-24 text-center">
          <h1 className="text-3xl md:text-5xl font-bold tracking-tight mb-4">
            당신에게 맞는 지원사업을
            <br />
            <span className="text-[var(--color-teal-light)]">찾아드립니다</span>
          </h1>
          <p className="text-white/70 mb-8 max-w-xl mx-auto">
            정부지원사업, 공모전, 보조금 정보를 한곳에서 검색하고 관리하세요.
          </p>

          <form onSubmit={handleSearch} className="max-w-lg mx-auto flex gap-2">
            <div className="relative flex-1">
              <Search className="absolute left-4 top-1/2 h-5 w-5 -translate-y-1/2 text-muted-foreground" />
              <Input
                placeholder="키워드로 검색 (예: 예비창업자, AI, 수출)"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                className="pl-11 h-12 rounded-xl bg-white text-foreground border-0 shadow-lg"
              />
            </div>
            <Button type="submit" className="h-12 px-6 rounded-xl bg-[var(--color-teal)] hover:bg-[var(--color-teal-light)]">
              검색
            </Button>
          </form>

          {/* Stats */}
          {stats && (
            <div className="flex justify-center gap-8 mt-8 text-sm">
              <div>
                <p className="text-2xl font-bold">{stats.open_count.toLocaleString()}</p>
                <p className="text-white/60">진행중</p>
              </div>
              <div className="h-10 w-px bg-white/20" />
              <div>
                <p className="text-2xl font-bold">{stats.closing_this_week}</p>
                <p className="text-white/60">이번주 마감</p>
              </div>
              <div className="h-10 w-px bg-white/20" />
              <div>
                <p className="text-2xl font-bold">{stats.total.toLocaleString()}</p>
                <p className="text-white/60">전체 공고</p>
              </div>
            </div>
          )}
        </div>
      </section>

      {/* Category quick links */}
      <section className="container mx-auto px-4 -mt-6 relative z-10">
        <div className="grid grid-cols-4 md:grid-cols-8 gap-2">
          {CATEGORIES.map((cat) => (
            <Link
              key={cat.label}
              href={`/programs?category=${encodeURIComponent(cat.label)}`}
              className="flex flex-col items-center gap-1.5 rounded-xl bg-white p-3 shadow-sm border hover:shadow-md transition-shadow"
            >
              <cat.icon className={`h-5 w-5 ${cat.color}`} />
              <span className="text-xs font-medium">{cat.label}</span>
            </Link>
          ))}
        </div>
      </section>

      <div className="container mx-auto px-4 py-12 space-y-12">
        {/* Deadline section */}
        <section>
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-xl font-bold">마감 임박</h2>
              <p className="text-sm text-muted-foreground">7일 이내 마감되는 지원사업</p>
            </div>
            <Link href="/programs?sort=deadline_asc&status=OPEN" className="inline-flex items-center text-sm text-muted-foreground hover:text-foreground">
              전체보기 <ArrowRight className="ml-1 h-4 w-4" />
            </Link>
          </div>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {loadingDeadline
              ? Array.from({ length: 6 }).map((_, i) => <ProgramCardSkeleton key={i} />)
              : deadlineData?.items.map((p) => <ProgramCard key={p.id} program={p} />)}
            {!loadingDeadline && deadlineData?.items.length === 0 && (
              <p className="col-span-full text-center text-muted-foreground py-8">
                마감 임박 공고가 없습니다.
              </p>
            )}
          </div>
        </section>

        {/* Recent section */}
        <section>
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-xl font-bold">신규 등록</h2>
              <p className="text-sm text-muted-foreground">최근 등록된 지원사업</p>
            </div>
            <Link href="/programs?sort=created_desc" className="inline-flex items-center text-sm text-muted-foreground hover:text-foreground">
              전체보기 <ArrowRight className="ml-1 h-4 w-4" />
            </Link>
          </div>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {loadingRecent
              ? Array.from({ length: 6 }).map((_, i) => <ProgramCardSkeleton key={i} />)
              : recentData?.items.map((p) => <ProgramCard key={p.id} program={p} />)}
            {!loadingRecent && recentData?.items.length === 0 && (
              <p className="col-span-full text-center text-muted-foreground py-8">
                등록된 공고가 없습니다.
              </p>
            )}
          </div>
        </section>
      </div>
    </div>
  );
}
