"use client";

import Link from "next/link";
import { Bookmark, Building2, MapPin } from "lucide-react";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { getDday, getDdayVariant } from "@/lib/date";
import type { ProgramListItem } from "@/lib/api";

interface Props {
  program: ProgramListItem;
  onBookmark?: (id: string) => void;
  isBookmarked?: boolean;
}

export function ProgramCard({ program, onBookmark, isBookmarked }: Props) {
  const dday = getDday(program.application_end);
  const ddayVariant = getDdayVariant(program.application_end);

  return (
    <Link href={`/programs/${program.id}`}>
      <Card className="group h-full transition-all hover:shadow-md hover:border-primary/20 relative">
        <CardHeader className="pb-3">
          <div className="flex items-center gap-2 flex-wrap">
            {dday && (
              <Badge variant={ddayVariant} className="text-xs font-semibold">
                {dday}
              </Badge>
            )}
            {program.category && (
              <Badge variant="outline" className="text-xs">
                {program.category}
              </Badge>
            )}
            {program.status === "UPCOMING" && (
              <Badge variant="secondary" className="text-xs">예정</Badge>
            )}
          </div>
          <h3 className="text-sm font-semibold leading-snug line-clamp-2 mt-1 group-hover:text-primary transition-colors">
            {program.title}
          </h3>
        </CardHeader>
        <CardContent className="pt-0 space-y-2">
          {program.organization && (
            <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
              <Building2 className="h-3 w-3 shrink-0" />
              <span className="truncate">{program.organization}</span>
            </div>
          )}
          {program.region && (
            <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
              <MapPin className="h-3 w-3 shrink-0" />
              <span>{program.region}</span>
            </div>
          )}
          {program.support_amount && (
            <p className="text-xs font-medium text-[var(--color-teal)]">
              {program.support_amount}
            </p>
          )}
        </CardContent>
        {onBookmark && (
          <Button
            variant="ghost"
            size="icon"
            className="absolute top-2 right-2 h-7 w-7 opacity-0 group-hover:opacity-100 transition-opacity"
            onClick={(e) => {
              e.preventDefault();
              onBookmark(program.id);
            }}
          >
            <Bookmark className={`h-4 w-4 ${isBookmarked ? "fill-current text-[var(--color-teal)]" : ""}`} />
          </Button>
        )}
      </Card>
    </Link>
  );
}

export function ProgramCardSkeleton() {
  return (
    <Card className="h-full">
      <CardHeader className="pb-3">
        <div className="flex gap-2">
          <div className="h-5 w-12 rounded bg-muted animate-pulse" />
          <div className="h-5 w-16 rounded bg-muted animate-pulse" />
        </div>
        <div className="h-4 w-full rounded bg-muted animate-pulse mt-2" />
        <div className="h-4 w-3/4 rounded bg-muted animate-pulse" />
      </CardHeader>
      <CardContent className="pt-0 space-y-2">
        <div className="h-3 w-32 rounded bg-muted animate-pulse" />
        <div className="h-3 w-20 rounded bg-muted animate-pulse" />
        <div className="h-3 w-24 rounded bg-muted animate-pulse" />
      </CardContent>
    </Card>
  );
}
