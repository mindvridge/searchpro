"use client";

import { useState } from "react";
import Link from "next/link";
import {
  ChevronLeft,
  ChevronRight,
  CalendarDays as CalendarIcon,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { useCalendar } from "@/hooks/useProgram";
import type { CalendarEntry } from "@/lib/api";

const WEEKDAYS = ["일", "월", "화", "수", "목", "금", "토"];

export default function CalendarPage() {
  const now = new Date();
  const [year, setYear] = useState(now.getFullYear());
  const [month, setMonth] = useState(now.getMonth() + 1);
  const [selectedDate, setSelectedDate] = useState<string | null>(null);

  const { data: entries, isLoading } = useCalendar(year, month);

  const entryMap = new Map<string, CalendarEntry>();
  entries?.forEach((e) => entryMap.set(e.date, e));

  const daysInMonth = new Date(year, month, 0).getDate();
  const firstDayOfWeek = new Date(year, month - 1, 1).getDay();

  const prevMonth = () => {
    if (month === 1) { setYear(year - 1); setMonth(12); }
    else setMonth(month - 1);
    setSelectedDate(null);
  };

  const nextMonth = () => {
    if (month === 12) { setYear(year + 1); setMonth(1); }
    else setMonth(month + 1);
    setSelectedDate(null);
  };

  const selectedEntry = selectedDate ? entryMap.get(selectedDate) : null;

  return (
    <div className="container mx-auto px-4 py-6 max-w-4xl">
      <div className="flex items-center gap-3 mb-6">
        <CalendarIcon className="h-6 w-6 text-primary" />
        <h1 className="text-2xl font-bold">마감 캘린더</h1>
      </div>

      <Card>
        <CardContent className="p-4 md:p-6">
          {/* Month navigation */}
          <div className="flex items-center justify-between mb-6">
            <Button variant="ghost" size="icon" onClick={prevMonth}>
              <ChevronLeft className="h-5 w-5" />
            </Button>
            <h2 className="text-lg font-bold">
              {year}년 {month}월
            </h2>
            <Button variant="ghost" size="icon" onClick={nextMonth}>
              <ChevronRight className="h-5 w-5" />
            </Button>
          </div>

          {/* Weekday headers */}
          <div className="grid grid-cols-7 mb-2">
            {WEEKDAYS.map((d, i) => (
              <div
                key={d}
                className={`text-center text-xs font-medium py-1 ${
                  i === 0 ? "text-red-400" : i === 6 ? "text-blue-400" : "text-muted-foreground"
                }`}
              >
                {d}
              </div>
            ))}
          </div>

          {/* Calendar grid */}
          <div className="grid grid-cols-7 gap-px bg-border rounded-lg overflow-hidden">
            {/* Empty cells before first day */}
            {Array.from({ length: firstDayOfWeek }).map((_, i) => (
              <div key={`empty-${i}`} className="bg-background p-1 min-h-[60px] md:min-h-[80px]" />
            ))}

            {/* Day cells */}
            {Array.from({ length: daysInMonth }).map((_, i) => {
              const day = i + 1;
              const dateStr = `${year}-${String(month).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
              const entry = entryMap.get(dateStr);
              const isToday =
                day === now.getDate() && month === now.getMonth() + 1 && year === now.getFullYear();
              const isSelected = dateStr === selectedDate;
              const dayOfWeek = (firstDayOfWeek + i) % 7;

              return (
                <button
                  key={day}
                  onClick={() => setSelectedDate(dateStr === selectedDate ? null : dateStr)}
                  className={`bg-background p-1 min-h-[60px] md:min-h-[80px] text-left transition-colors hover:bg-secondary/50 ${
                    isSelected ? "ring-2 ring-primary ring-inset" : ""
                  }`}
                >
                  <span
                    className={`text-xs font-medium ${
                      isToday
                        ? "inline-flex h-5 w-5 items-center justify-center rounded-full bg-primary text-primary-foreground"
                        : dayOfWeek === 0
                        ? "text-red-400"
                        : dayOfWeek === 6
                        ? "text-blue-400"
                        : ""
                    }`}
                  >
                    {day}
                  </span>
                  {entry && (
                    <Badge variant="default" className="mt-1 text-[10px] px-1.5 py-0 block w-fit bg-[var(--color-teal)]">
                      {entry.count}건
                    </Badge>
                  )}
                </button>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* Selected date programs */}
      {selectedEntry && (
        <Card className="mt-4">
          <CardContent className="p-4">
            <h3 className="font-semibold text-sm mb-3">
              {selectedDate} 마감 ({selectedEntry.count}건)
            </h3>
            <div className="space-y-2">
              {selectedEntry.programs.map((p) => (
                <Link
                  key={p.id}
                  href={`/programs/${p.id}`}
                  className="block rounded-lg border p-3 hover:bg-secondary/50 transition-colors"
                >
                  <p className="text-sm font-medium">{p.title}</p>
                  {p.organization && (
                    <p className="text-xs text-muted-foreground mt-0.5">{p.organization}</p>
                  )}
                </Link>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {selectedDate && !selectedEntry && (
        <Card className="mt-4">
          <CardContent className="p-4 text-center text-sm text-muted-foreground">
            해당 날짜에 마감되는 공고가 없습니다.
          </CardContent>
        </Card>
      )}

      {isLoading && (
        <div className="mt-4 text-center text-sm text-muted-foreground">로딩 중...</div>
      )}
    </div>
  );
}
