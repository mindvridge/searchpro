import { differenceInCalendarDays, format, parseISO } from "date-fns";
import { ko } from "date-fns/locale";

export function formatDate(iso: string | null | undefined): string {
  if (!iso) return "-";
  return format(parseISO(iso), "yyyy.MM.dd", { locale: ko });
}

export function getDday(iso: string | null | undefined): string | null {
  if (!iso) return null;
  const diff = differenceInCalendarDays(parseISO(iso), new Date());
  if (diff < 0) return "마감";
  if (diff === 0) return "D-Day";
  return `D-${diff}`;
}

export function getDdayVariant(iso: string | null | undefined): "default" | "destructive" | "secondary" {
  if (!iso) return "secondary";
  const diff = differenceInCalendarDays(parseISO(iso), new Date());
  if (diff <= 3) return "destructive";
  if (diff <= 7) return "default";
  return "secondary";
}
