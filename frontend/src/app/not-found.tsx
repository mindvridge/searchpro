import Link from "next/link";
import { FileQuestion } from "lucide-react";

export default function NotFound() {
  return (
    <div className="flex min-h-[60vh] items-center justify-center">
      <div className="text-center space-y-4">
        <FileQuestion className="h-16 w-16 text-muted-foreground/40 mx-auto" />
        <h1 className="text-4xl font-bold">404</h1>
        <p className="text-muted-foreground">페이지를 찾을 수 없습니다.</p>
        <Link
          href="/"
          className="inline-flex items-center rounded-lg bg-primary text-primary-foreground px-4 py-2 text-sm font-medium hover:bg-primary/90"
        >
          홈으로 돌아가기
        </Link>
      </div>
    </div>
  );
}
