import type { Metadata } from "next";
import "./globals.css";
import { Header } from "@/components/layout/Header";
import { Footer } from "@/components/layout/Footer";
import { Sidebar } from "@/components/layout/Sidebar";
import { QueryProvider } from "@/lib/queryClient";
import { Toaster } from "@/components/ui/sonner";

export const metadata: Metadata = {
  title: "SearchPro — 정부지원사업 통합 검색",
  description:
    "정부지원사업, 공모전, 보조금 정보를 한곳에서 검색하고 관리하세요.",
  openGraph: {
    title: "SearchPro — 정부지원사업 통합 검색",
    description:
      "정부지원사업, 공모전, 보조금 정보를 한곳에서 검색하고 관리하세요.",
    locale: "ko_KR",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="ko"
      className="h-full antialiased"
    >
      <body className="min-h-full flex flex-col">
        <QueryProvider>
          <Header />
          <div className="container mx-auto flex flex-1 gap-6 px-4 py-6">
            <aside className="hidden w-64 shrink-0 md:block">
              <Sidebar />
            </aside>
            <main className="flex-1 min-w-0">{children}</main>
          </div>
          <Footer />
          <Toaster />
        </QueryProvider>
      </body>
    </html>
  );
}
