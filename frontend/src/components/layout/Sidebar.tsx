"use client";

import Link from "next/link";
import {
  Home,
  Search,
  Bookmark,
  Bell,
  Settings,
  FileText,
} from "lucide-react";

const navItems = [
  { href: "/", label: "홈", icon: Home },
  { href: "/search", label: "검색", icon: Search },
  { href: "/programs", label: "지원사업 목록", icon: FileText },
  { href: "/bookmarks", label: "관심 사업", icon: Bookmark },
  { href: "/alerts", label: "알림", icon: Bell },
  { href: "/settings", label: "설정", icon: Settings },
];

export function Sidebar() {
  return (
    <nav className="flex flex-col gap-1 p-4">
      <h2 className="mb-4 px-2 text-lg font-semibold">메뉴</h2>
      {navItems.map((item) => (
        <Link
          key={item.href}
          href={item.href}
          className="flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium text-muted-foreground transition-colors hover:bg-accent hover:text-accent-foreground"
        >
          <item.icon className="h-4 w-4" />
          {item.label}
        </Link>
      ))}
    </nav>
  );
}
