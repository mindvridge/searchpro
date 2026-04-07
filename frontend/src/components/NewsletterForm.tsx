"use client";

import { useState } from "react";
import { Mail } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { fetchApi } from "@/lib/api";
import { toast } from "sonner";

export function NewsletterForm({ compact = false }: { compact?: boolean }) {
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.trim()) return;
    setLoading(true);
    try {
      const data = await fetchApi<{ message: string }>("/api/v1/newsletter/subscribe", {
        method: "POST",
        body: JSON.stringify({ email }),
      });
      toast.success(data.message);
      setEmail("");
    } catch {
      toast.error("구독에 실패했습니다. 다시 시도해주세요.");
    }
    setLoading(false);
  };

  if (compact) {
    return (
      <form onSubmit={handleSubmit} className="flex gap-2">
        <Input
          type="email"
          placeholder="이메일"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="h-8 text-xs"
          required
        />
        <Button type="submit" size="sm" disabled={loading} className="text-xs shrink-0">
          {loading ? "..." : "구독"}
        </Button>
      </form>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="flex gap-2 max-w-md mx-auto">
      <div className="relative flex-1">
        <Mail className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          type="email"
          placeholder="이메일 주소를 입력하세요"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="pl-9"
          required
        />
      </div>
      <Button type="submit" disabled={loading}>
        {loading ? "구독 중..." : "무료 구독"}
      </Button>
    </form>
  );
}
