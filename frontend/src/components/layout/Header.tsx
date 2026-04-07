"use client";

import Link from "next/link";
import { Search, Menu, User } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet";
import { Sidebar } from "./Sidebar";

export function Header() {
  return (
    <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container mx-auto flex h-16 items-center gap-4 px-4">
        <Sheet>
          <SheetTrigger className="md:hidden inline-flex items-center justify-center rounded-md p-2 text-sm font-medium hover:bg-accent hover:text-accent-foreground">
            <Menu className="h-5 w-5" />
          </SheetTrigger>
          <SheetContent side="left" className="w-72 p-0">
            <Sidebar />
          </SheetContent>
        </Sheet>

        <Link href="/" className="flex items-center gap-2 font-bold text-lg">
          SearchPro
        </Link>

        <div className="flex flex-1 items-center gap-2 md:max-w-md ml-auto">
          <div className="relative w-full">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              placeholder="지원사업 검색..."
              className="pl-9"
            />
          </div>
        </div>

        <Button variant="ghost" size="icon">
          <User className="h-5 w-5" />
        </Button>
      </div>
    </header>
  );
}
