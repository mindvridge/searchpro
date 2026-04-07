"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useSession } from "next-auth/react";
import {
  BarChart3,
  Database,
  FileText,
  Shield,
  Users,
} from "lucide-react";
import { cn } from "@/lib/utils";

const ADMIN_EMAILS = (process.env.NEXT_PUBLIC_ADMIN_EMAILS || "").split(",").map(e => e.trim()).filter(Boolean);

const navItems = [
  { href: "/admin", label: "대시보드", icon: BarChart3 },
  { href: "/admin/programs", label: "공고 관리", icon: FileText },
  { href: "/admin/crawlers", label: "크롤러", icon: Database },
  { href: "/admin/users", label: "사용자", icon: Users },
];

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const { data: session, status } = useSession();
  const pathname = usePathname();

  if (status === "loading") {
    return <div className="flex items-center justify-center min-h-[60vh] text-muted-foreground">로딩 중...</div>;
  }

  // Check admin access
  const userEmail = session?.user?.email;
  const isAdmin = userEmail && (ADMIN_EMAILS.length === 0 || ADMIN_EMAILS.includes(userEmail));

  if (!session?.user || !isAdmin) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center">
          <Shield className="h-12 w-12 text-muted-foreground/40 mx-auto mb-4" />
          <p className="text-lg font-semibold mb-2">접근 권한이 없습니다</p>
          <p className="text-sm text-muted-foreground">관리자 계정으로 로그인해주세요.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-6">
      <div className="flex gap-6">
        <aside className="hidden md:block w-48 shrink-0">
          <nav className="sticky top-20 space-y-1">
            <p className="text-xs font-semibold uppercase text-muted-foreground mb-3 px-2">관리자</p>
            {navItems.map((item) => {
              const isActive = pathname === item.href;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={cn(
                    "flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                    isActive ? "bg-primary/10 text-primary" : "text-muted-foreground hover:bg-secondary"
                  )}
                >
                  <item.icon className="h-4 w-4" />
                  {item.label}
                </Link>
              );
            })}
          </nav>
        </aside>
        <main className="flex-1 min-w-0">{children}</main>
      </div>
    </div>
  );
}
