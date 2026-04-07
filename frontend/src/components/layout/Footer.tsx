export function Footer() {
  return (
    <footer className="border-t py-6 md:py-8">
      <div className="container mx-auto flex flex-col items-center gap-4 px-4 md:flex-row md:justify-between">
        <p className="text-sm text-muted-foreground">
          &copy; {new Date().getFullYear()} SearchPro. All rights reserved.
        </p>
        <div className="flex gap-4 text-sm text-muted-foreground">
          <a href="/terms" className="hover:underline">이용약관</a>
          <a href="/privacy" className="hover:underline">개인정보처리방침</a>
          <a href="/contact" className="hover:underline">문의하기</a>
        </div>
      </div>
    </footer>
  );
}
