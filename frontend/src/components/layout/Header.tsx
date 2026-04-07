"use client";

import Link from "next/link";
import { useSession, signOut } from "next-auth/react";
import { Search, Menu, Bookmark, CalendarDays, LogIn, LogOut, User } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet";
import { Sidebar } from "./Sidebar";
import { useRouter } from "next/navigation";
import { useState } from "react";

export function Header() {
  const { data: session } = useSession();
  const router = useRouter();
  const [query, setQuery] = useState("");

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim().length >= 2) {
      router.push(`/programs?q=${encodeURIComponent(query.trim())}`);
    }
  };

  return (
    <header className="sticky top-0 z-50 w-full border-b bg-white/80 backdrop-blur-md">
      <div className="container mx-auto flex h-14 items-center gap-4 px-4">
        {/* Mobile menu */}
        <Sheet>
          <SheetTrigger className="md:hidden inline-flex items-center justify-center rounded-md p-2 hover:bg-secondary">
            <Menu className="h-5 w-5" />
          </SheetTrigger>
          <SheetContent side="left" className="w-72 p-0">
            <Sidebar />
          </SheetContent>
        </Sheet>

        {/* Logo */}
        <Link href="/" className="flex items-center gap-2 font-bold text-lg shrink-0">
          <span className="text-[var(--color-navy)]">Search</span>
          <span className="text-[var(--color-teal)]">Pro</span>
        </Link>

        {/* Desktop nav */}
        <nav className="hidden md:flex items-center gap-1 ml-6">
          <Link href="/programs" className="px-3 py-1.5 text-sm font-medium text-muted-foreground hover:text-foreground rounded-md hover:bg-secondary transition-colors">
            지원사업
          </Link>
          <Link href="/calendar" className="px-3 py-1.5 text-sm font-medium text-muted-foreground hover:text-foreground rounded-md hover:bg-secondary transition-colors">
            캘린더
          </Link>
          {session && (
            <Link href="/bookmarks" className="px-3 py-1.5 text-sm font-medium text-muted-foreground hover:text-foreground rounded-md hover:bg-secondary transition-colors">
              북마크
            </Link>
          )}
        </nav>

        {/* Search bar - desktop */}
        <form onSubmit={handleSearch} className="hidden md:flex flex-1 max-w-md mx-auto">
          <div className="relative w-full">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              placeholder="지원사업 검색..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              className="pl-9 h-9 bg-secondary/50 border-0 focus-visible:bg-white focus-visible:ring-1"
            />
          </div>
        </form>

        {/* Auth */}
        <div className="flex items-center gap-2 ml-auto">
          {session ? (
            <div className="flex items-center gap-2">
              <span className="hidden sm:inline text-sm text-muted-foreground">
                {session.user?.name || session.user?.email}
              </span>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => signOut()}
                className="text-muted-foreground"
              >
                <LogOut className="h-4 w-4" />
              </Button>
            </div>
          ) : (
            <Link href="/login" className="inline-flex items-center gap-1 rounded-lg bg-[var(--color-navy)] hover:bg-[var(--color-navy-light)] text-white text-sm font-medium px-3 py-1.5 transition-colors">
              <LogIn className="h-4 w-4" />
              로그인
            </Link>
          )}
        </div>
      </div>
    </header>
  );
}
