"use client";

import { use } from "react";
import Link from "next/link";
import {
  ArrowLeft,
  Bookmark,
  Building2,
  CalendarDays,
  ExternalLink,
  MapPin,
  Share2,
  Tag,
  Users,
  Banknote,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useProgram } from "@/hooks/useProgram";
import { useAddBookmark, useRemoveBookmark } from "@/hooks/useBookmarks";
import { formatDate, getDday, getDdayVariant } from "@/lib/date";
import { toast } from "sonner";

export default function ProgramDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const { data: program, isLoading, error } = useProgram(id);
  const addBookmark = useAddBookmark();
  const removeBookmark = useRemoveBookmark();

  const handleBookmark = () => {
    addBookmark.mutate({ program_id: id }, {
      onSuccess: () => toast.success("북마크에 추가했습니다"),
      onError: () => toast.error("북마크 추가에 실패했습니다"),
    });
  };

  const handleShare = () => {
    navigator.clipboard.writeText(window.location.href);
    toast.success("URL이 복사되었습니다");
  };

  if (isLoading) return <DetailSkeleton />;
  if (error || !program) {
    return (
      <div className="container mx-auto px-4 py-16 text-center">
        <p className="text-muted-foreground">지원사업을 찾을 수 없습니다.</p>
        <Link href="/programs" className="inline-flex items-center rounded-lg border px-3 py-1.5 text-sm hover:bg-secondary mt-4">
          목록으로
        </Link>
      </div>
    );
  }

  const dday = getDday(program.application_end);
  const ddayVariant = getDdayVariant(program.application_end);

  return (
    <div className="container mx-auto px-4 py-6 max-w-4xl">
      {/* Back */}
      <Link href="/programs" className="inline-flex items-center text-sm text-muted-foreground hover:text-foreground mb-4 -ml-2 px-2 py-1 rounded-md hover:bg-secondary">
        <ArrowLeft className="mr-1 h-4 w-4" /> 목록
      </Link>

      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center gap-2 flex-wrap mb-2">
          <Badge
            variant={
              program.status === "OPEN" ? "default" :
              program.status === "UPCOMING" ? "secondary" : "outline"
            }
          >
            {program.status === "OPEN" ? "진행중" : program.status === "UPCOMING" ? "예정" : "마감"}
          </Badge>
          {dday && <Badge variant={ddayVariant}>{dday}</Badge>}
          {program.category && <Badge variant="outline">{program.category}</Badge>}
        </div>
        <h1 className="text-2xl md:text-3xl font-bold mb-3">{program.title}</h1>
        <div className="flex items-center gap-3 flex-wrap">
          <Button size="sm" variant="outline" onClick={handleBookmark}>
            <Bookmark className="mr-1 h-4 w-4" /> 북마크
          </Button>
          <Button size="sm" variant="outline" onClick={handleShare}>
            <Share2 className="mr-1 h-4 w-4" /> 공유
          </Button>
          {program.detail_url && (
            <a
              href={program.detail_url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1 rounded-lg bg-[var(--color-teal)] hover:bg-[var(--color-teal-light)] text-white text-sm font-medium px-3 py-1.5 transition-colors"
            >
              <ExternalLink className="h-4 w-4" /> 원문 바로가기
            </a>
          )}
        </div>
      </div>

      {/* Info cards */}
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 mb-8">
        <InfoItem icon={Building2} label="주관기관" value={program.organization} />
        <InfoItem icon={MapPin} label="지역" value={program.region} />
        <InfoItem icon={Tag} label="카테고리" value={program.category} />
        <InfoItem icon={Banknote} label="지원금액" value={program.support_amount} />
        <InfoItem
          icon={CalendarDays}
          label="접수기간"
          value={
            program.application_start || program.application_end
              ? `${formatDate(program.application_start)} ~ ${formatDate(program.application_end)}`
              : null
          }
        />
        <InfoItem icon={Users} label="지원대상" value={program.target_type} />
      </div>

      {/* Description */}
      {program.description && (
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="text-base">상세 설명</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm leading-relaxed whitespace-pre-wrap">{program.description}</p>
          </CardContent>
        </Card>
      )}

      {/* Eligibility */}
      {program.eligibility && (
        <Card className="mb-6 border-[var(--color-teal)]/20 bg-[var(--color-teal)]/5">
          <CardHeader>
            <CardTitle className="text-base text-[var(--color-teal)]">자격요건</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm leading-relaxed whitespace-pre-wrap">{program.eligibility}</p>
          </CardContent>
        </Card>
      )}

      {/* Tags */}
      {program.tags && program.tags.length > 0 && (
        <div className="flex flex-wrap gap-1.5 mb-8">
          {program.tags.map((tag) => (
            <Badge key={tag} variant="secondary">{tag}</Badge>
          ))}
        </div>
      )}

      {/* Related */}
      {program.related && program.related.length > 0 && (
        <section>
          <h2 className="text-lg font-bold mb-4">관련 지원사업</h2>
          <div className="grid gap-3 sm:grid-cols-3">
            {program.related.map((r) => (
              <Link key={r.id} href={`/programs/${r.id}`}>
                <Card className="hover:shadow-md transition-shadow h-full">
                  <CardContent className="p-4">
                    <p className="text-sm font-medium line-clamp-2 mb-2">{r.title}</p>
                    {r.organization && (
                      <p className="text-xs text-muted-foreground">{r.organization}</p>
                    )}
                    {r.application_end && (
                      <Badge variant={getDdayVariant(r.application_end)} className="mt-2 text-xs">
                        {getDday(r.application_end)}
                      </Badge>
                    )}
                  </CardContent>
                </Card>
              </Link>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}

function InfoItem({
  icon: Icon,
  label,
  value,
}: {
  icon: React.ElementType;
  label: string;
  value: string | null | undefined;
}) {
  return (
    <div className="flex items-start gap-3 rounded-lg border p-3">
      <Icon className="h-4 w-4 mt-0.5 text-muted-foreground shrink-0" />
      <div className="min-w-0">
        <p className="text-xs text-muted-foreground">{label}</p>
        <p className="text-sm font-medium truncate">{value || "-"}</p>
      </div>
    </div>
  );
}

function DetailSkeleton() {
  return (
    <div className="container mx-auto px-4 py-6 max-w-4xl">
      <div className="h-5 w-16 bg-muted rounded animate-pulse mb-4" />
      <div className="space-y-3 mb-6">
        <div className="flex gap-2">
          <div className="h-6 w-16 bg-muted rounded animate-pulse" />
          <div className="h-6 w-12 bg-muted rounded animate-pulse" />
        </div>
        <div className="h-8 w-3/4 bg-muted rounded animate-pulse" />
        <div className="h-8 w-1/2 bg-muted rounded animate-pulse" />
      </div>
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 mb-8">
        {Array.from({ length: 6 }).map((_, i) => (
          <div key={i} className="h-16 rounded-lg border bg-muted/30 animate-pulse" />
        ))}
      </div>
      <div className="h-40 rounded-lg border bg-muted/30 animate-pulse" />
    </div>
  );
}
