"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Home,
  Search,
  Bookmark,
  CalendarDays,
  Settings,
  FileText,
  Bell,
} from "lucide-react";
import { cn } from "@/lib/utils";

const navItems = [
  { href: "/", label: "홈", icon: Home },
  { href: "/programs", label: "지원사업", icon: FileText },
  { href: "/calendar", label: "캘린더", icon: CalendarDays },
  { href: "/bookmarks", label: "북마크", icon: Bookmark },
  { href: "/alerts", label: "알림 설정", icon: Bell },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <nav className="flex flex-col gap-1 p-4">
      <div className="px-2 mb-4">
        <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
          메뉴
        </p>
      </div>
      {navItems.map((item) => {
        const isActive = pathname === item.href || (item.href !== "/" && pathname.startsWith(item.href));
        return (
          <Link
            key={item.href}
            href={item.href}
            className={cn(
              "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
              isActive
                ? "bg-primary/10 text-primary"
                : "text-muted-foreground hover:bg-secondary hover:text-foreground"
            )}
          >
            <item.icon className="h-4 w-4" />
            {item.label}
          </Link>
        );
      })}
    </nav>
  );
}
