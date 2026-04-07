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
  Bot,
  Bell,
  Building2,
  Sparkles,
  CheckCircle,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { ProgramCard, ProgramCardSkeleton } from "@/components/ProgramCard";
import { usePrograms, useProgramStats } from "@/hooks/usePrograms";
import { useRecommendations, type RecommendationItem } from "@/hooks/useAI";
import { useSession } from "next-auth/react";
import { getDday, getDdayVariant } from "@/lib/date";
import { NewsletterForm } from "@/components/NewsletterForm";
import { WebsiteJsonLd } from "@/components/JsonLd";

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

const FEATURES = [
  {
    icon: Search,
    title: "통합 검색",
    desc: "기업마당, K-Startup 공공데이터를 한 곳에서 검색하세요.",
    color: "bg-blue-50 text-blue-600",
  },
  {
    icon: Bot,
    title: "AI 매칭",
    desc: "내 조건에 맞는 지원사업만 AI가 골라서 추천합니다.",
    color: "bg-teal-50 text-teal-600",
  },
  {
    icon: Bell,
    title: "마감 알림",
    desc: "관심 사업 마감일을 놓치지 않도록 자동으로 알려드립니다.",
    color: "bg-orange-50 text-orange-600",
  },
];

export default function HomePage() {
  const { data: session, status } = useSession();
  const isLoggedIn = !!session?.user;

  // 개발 모드에서는 항상 대시보드 뷰 표시
  const showLanding = !isLoggedIn && status !== "loading" && process.env.NODE_ENV === "production";

  return (
    <>
      <WebsiteJsonLd />
      <HeroSection />
      <CategoryLinks />
      <div className="container mx-auto px-4 py-12 space-y-12">
        {/* Landing features for anonymous users (프로덕션만) */}
        {showLanding && <FeaturesSection />}

        {/* Recommendations */}
        <RecommendationsSection />

        {/* Deadline & Recent */}
        <DeadlineSection />
        <RecentSection />

        {/* Stats bar for anonymous (프로덕션만) */}
        {showLanding && <StatsBar />}

        {/* Newsletter CTA */}
        {showLanding && <NewsletterCTA />}
      </div>
    </>
  );
}

// ---------------------------------------------------------------------------
// Hero
// ---------------------------------------------------------------------------

function HeroSection() {
  const router = useRouter();
  const [query, setQuery] = useState("");
  const { data: stats } = useProgramStats();
  const { data: session } = useSession();

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim().length >= 2) {
      router.push(`/programs?q=${encodeURIComponent(query.trim())}`);
    }
  };

  return (
    <section className="bg-gradient-to-br from-[var(--color-navy)] to-[var(--color-navy-light)] text-white">
      <div className="container mx-auto px-4 py-16 md:py-24 text-center">
        {session?.user ? (
          <h1 className="text-3xl md:text-4xl font-bold tracking-tight mb-4">
            {session.user.name || "회원"}님, 오늘의 지원사업을 확인하세요
          </h1>
        ) : (
          <>
            <h1 className="text-3xl md:text-5xl font-bold tracking-tight mb-4">
              1,000개+ 정부지원사업
              <br />
              <span className="text-[var(--color-teal-light)]">AI가 딱 맞는 것만 골라줍니다</span>
            </h1>
            <p className="text-white/70 mb-8 max-w-xl mx-auto">
              기업마당, K-Startup 공공데이터를 통합 검색하고, 맞춤 추천받으세요.
            </p>
          </>
        )}

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

        {!session?.user && (
          <div className="mt-8">
            <Link
              href="/register"
              className="inline-flex items-center gap-2 rounded-xl bg-white text-[var(--color-navy)] font-semibold px-6 py-3 hover:bg-white/90 transition-colors"
            >
              무료로 시작하기 <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
        )}
      </div>
    </section>
  );
}

// ---------------------------------------------------------------------------
// Category quick links
// ---------------------------------------------------------------------------

function CategoryLinks() {
  return (
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
  );
}

// ---------------------------------------------------------------------------
// Features (landing — anonymous only)
// ---------------------------------------------------------------------------

function FeaturesSection() {
  return (
    <section>
      <div className="grid gap-6 md:grid-cols-3">
        {FEATURES.map((f) => (
          <Card key={f.title} className="text-center border-0 shadow-sm">
            <CardContent className="pt-8 pb-6 space-y-3">
              <div className={`inline-flex p-3 rounded-xl ${f.color}`}>
                <f.icon className="h-6 w-6" />
              </div>
              <h3 className="font-bold">{f.title}</h3>
              <p className="text-sm text-muted-foreground">{f.desc}</p>
            </CardContent>
          </Card>
        ))}
      </div>
    </section>
  );
}

// ---------------------------------------------------------------------------
// Stats bar (landing)
// ---------------------------------------------------------------------------

function StatsBar() {
  const { data: stats } = useProgramStats();
  if (!stats) return null;

  const items = [
    { label: "수집된 공고", value: `${stats.total.toLocaleString()}건` },
    { label: "데이터 소스", value: `${stats.by_source.length}개 기관` },
    { label: "갱신 주기", value: "매일 자동 갱신" },
  ];

  return (
    <section className="bg-secondary/50 -mx-4 px-4 py-8 rounded-xl">
      <h2 className="text-lg font-bold text-center mb-6">숫자로 보는 SearchPro</h2>
      <div className="grid grid-cols-3 gap-4 text-center">
        {items.map((item) => (
          <div key={item.label}>
            <p className="text-xl md:text-2xl font-bold text-primary">{item.value}</p>
            <p className="text-xs text-muted-foreground mt-1">{item.label}</p>
          </div>
        ))}
      </div>
    </section>
  );
}

// ---------------------------------------------------------------------------
// Newsletter CTA (landing)
// ---------------------------------------------------------------------------

function NewsletterCTA() {
  return (
    <section className="bg-gradient-to-r from-[var(--color-navy)] to-[var(--color-navy-light)] text-white rounded-xl p-8 text-center">
      <h2 className="text-xl font-bold mb-2">매주 맞춤 지원사업을 받아보세요</h2>
      <p className="text-white/70 text-sm mb-6">
        이메일만 입력하면 매주 월요일, 나에게 맞는 지원사업을 보내드립니다.
      </p>
      <NewsletterForm />
    </section>
  );
}

// ---------------------------------------------------------------------------
// Recommendations
// ---------------------------------------------------------------------------

function RecommendationsSection() {
  const { data: session } = useSession();
  const { data, isLoading } = useRecommendations(6);

  if (isLoading) {
    return (
      <section>
        <div className="flex items-center gap-2 mb-6">
          <Sparkles className="h-5 w-5 text-[var(--color-teal)]" />
          <h2 className="text-xl font-bold">추천 지원사업</h2>
        </div>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => <ProgramCardSkeleton key={i} />)}
        </div>
      </section>
    );
  }

  if (!data?.items.length) return null;

  return (
    <section>
      <div className="mb-6">
        <div className="flex items-center gap-2">
          <Sparkles className="h-5 w-5 text-[var(--color-teal)]" />
          <h2 className="text-xl font-bold">
            {data.personalized && session?.user?.name
              ? `${session.user.name}님을 위한 추천`
              : "인기 지원사업"}
          </h2>
        </div>
        {data.personalized && (
          <p className="text-sm text-muted-foreground mt-1">프로필 기반 맞춤 추천</p>
        )}
      </div>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {data.items.map((item) => (
          <Link key={item.id} href={`/programs/${item.id}`}>
            <Card className="group h-full transition-all hover:shadow-md hover:border-primary/20">
              <CardHeader className="pb-3">
                <div className="flex items-center gap-2 flex-wrap">
                  {item.application_end && (
                    <Badge variant={getDdayVariant(item.application_end)} className="text-xs font-semibold">
                      {getDday(item.application_end)}
                    </Badge>
                  )}
                  {item.category && <Badge variant="outline" className="text-xs">{item.category}</Badge>}
                </div>
                <h3 className="text-sm font-semibold leading-snug line-clamp-2 mt-1 group-hover:text-primary transition-colors">
                  {item.title}
                </h3>
              </CardHeader>
              <CardContent className="pt-0 space-y-2">
                {item.organization && (
                  <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
                    <Building2 className="h-3 w-3 shrink-0" />
                    <span className="truncate">{item.organization}</span>
                  </div>
                )}
                {item.support_amount && (
                  <p className="text-xs font-medium text-[var(--color-teal)]">{item.support_amount}</p>
                )}
                <p className="text-xs text-primary/70 font-medium">{item.reason}</p>
              </CardContent>
            </Card>
          </Link>
        ))}
      </div>
    </section>
  );
}

// ---------------------------------------------------------------------------
// Deadline section
// ---------------------------------------------------------------------------

function DeadlineSection() {
  const { data, isLoading } = usePrograms({ status: "OPEN", sort: "deadline_asc", limit: 6 });

  return (
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
        {isLoading
          ? Array.from({ length: 6 }).map((_, i) => <ProgramCardSkeleton key={i} />)
          : data?.items.map((p) => <ProgramCard key={p.id} program={p} />)}
        {!isLoading && data?.items.length === 0 && (
          <p className="col-span-full text-center text-muted-foreground py-8">마감 임박 공고가 없습니다.</p>
        )}
      </div>
    </section>
  );
}

// ---------------------------------------------------------------------------
// Recent section
// ---------------------------------------------------------------------------

function RecentSection() {
  const { data, isLoading } = usePrograms({ sort: "created_desc", limit: 6 });

  return (
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
        {isLoading
          ? Array.from({ length: 6 }).map((_, i) => <ProgramCardSkeleton key={i} />)
          : data?.items.map((p) => <ProgramCard key={p.id} program={p} />)}
        {!isLoading && data?.items.length === 0 && (
          <p className="col-span-full text-center text-muted-foreground py-8">등록된 공고가 없습니다.</p>
        )}
      </div>
    </section>
  );
}
