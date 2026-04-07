"use client";

import { AlertTriangle } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function ErrorPage({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div className="flex min-h-[60vh] items-center justify-center">
      <div className="text-center space-y-4">
        <AlertTriangle className="h-16 w-16 text-destructive/60 mx-auto" />
        <h1 className="text-2xl font-bold">오류가 발생했습니다</h1>
        <p className="text-muted-foreground text-sm max-w-md mx-auto">
          일시적인 문제가 발생했습니다. 잠시 후 다시 시도해주세요.
        </p>
        <Button onClick={reset}>다시 시도</Button>
      </div>
    </div>
  );
}
