import Link from "next/link";
import { NewsletterForm } from "@/components/NewsletterForm";

export function Footer() {
  return (
    <footer className="border-t bg-secondary/30">
      <div className="container mx-auto px-4 py-8">
        <div className="grid gap-8 sm:grid-cols-2 lg:grid-cols-4">
          <div>
            <p className="font-bold text-sm mb-2">
              <span className="text-[var(--color-navy)]">Search</span>
              <span className="text-[var(--color-teal)]">Pro</span>
            </p>
            <p className="text-xs text-muted-foreground leading-relaxed">
              정부지원사업, 공모전, 보조금 정보를
              <br />한곳에서 검색하고 관리하세요.
            </p>
          </div>
          <div>
            <p className="font-semibold text-xs mb-2">서비스</p>
            <div className="flex flex-col gap-1.5 text-xs text-muted-foreground">
              <Link href="/programs" className="hover:text-foreground transition-colors">지원사업 검색</Link>
              <Link href="/calendar" className="hover:text-foreground transition-colors">마감 캘린더</Link>
              <Link href="/alerts" className="hover:text-foreground transition-colors">알림 설정</Link>
            </div>
          </div>
          <div>
            <p className="font-semibold text-xs mb-2">법적 고지</p>
            <div className="flex flex-col gap-1.5 text-xs text-muted-foreground">
              <Link href="/terms" className="hover:text-foreground transition-colors">이용약관</Link>
              <Link href="/privacy" className="hover:text-foreground transition-colors">개인정보처리방침</Link>
              <Link href="/contact" className="hover:text-foreground transition-colors">문의하기</Link>
            </div>
          </div>
          <div>
            <p className="font-semibold text-xs mb-2">주간 뉴스레터</p>
            <p className="text-xs text-muted-foreground mb-2">매주 맞춤 지원사업을 보내드립니다.</p>
            <NewsletterForm compact />
          </div>
        </div>
        <div className="mt-8 pt-4 border-t text-center">
          <p className="text-xs text-muted-foreground">
            본 서비스는 기업마당, K-Startup 공공데이터를 활용합니다.
          </p>
          <p className="text-xs text-muted-foreground mt-1">
            &copy; {new Date().getFullYear()} SearchPro. All rights reserved.
          </p>
        </div>
      </div>
    </footer>
  );
}
