"use client";

import { useState } from "react";
import Link from "next/link";
import { FileText, Search, Trash2, Bot, ExternalLink } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useAdminPrograms, useDeleteProgram, useRegenerateSummary } from "@/hooks/useAdmin";
import { toast } from "sonner";

export default function AdminProgramsPage() {
  const [search, setSearch] = useState("");
  const [q, setQ] = useState("");
  const { data: programs, isLoading } = useAdminPrograms(q || undefined);
  const deleteProgram = useDeleteProgram();
  const regenSummary = useRegenerateSummary();

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setQ(search);
  };

  const handleDelete = (id: string, title: string) => {
    if (!confirm(`"${title}" 공고를 삭제하시겠습니까?`)) return;
    deleteProgram.mutate(id, {
      onSuccess: () => toast.success("공고가 삭제되었습니다"),
    });
  };

  const handleRegenSummary = (id: string) => {
    regenSummary.mutate(id, {
      onSuccess: (data) => {
        if (data.summary) toast.success("AI 요약이 재생성되었습니다");
        else toast.error("AI 요약 생성에 실패했습니다");
      },
    });
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <FileText className="h-6 w-6 text-primary" />
          <h1 className="text-2xl font-bold">공고 관리</h1>
        </div>
      </div>

      <form onSubmit={handleSearch} className="flex gap-2 max-w-md">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="공고명 검색..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9"
          />
        </div>
        <Button type="submit" variant="outline">검색</Button>
      </form>

      <Card>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="p-4 space-y-2">
              {Array.from({ length: 5 }).map((_, i) => (
                <div key={i} className="h-12 bg-muted/30 rounded animate-pulse" />
              ))}
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b text-left text-xs text-muted-foreground">
                    <th className="p-3">제목</th>
                    <th className="p-3">소스</th>
                    <th className="p-3">카테고리</th>
                    <th className="p-3">상태</th>
                    <th className="p-3">요약</th>
                    <th className="p-3">등록일</th>
                    <th className="p-3"></th>
                  </tr>
                </thead>
                <tbody>
                  {programs?.map((p) => (
                    <tr key={p.id} className="border-b last:border-0 hover:bg-secondary/30">
                      <td className="p-3 max-w-[300px]">
                        <Link href={`/programs/${p.id}`} className="hover:text-primary font-medium line-clamp-1">
                          {p.title}
                        </Link>
                      </td>
                      <td className="p-3">
                        <Badge variant="outline" className="text-xs">{p.source}</Badge>
                      </td>
                      <td className="p-3 text-xs">{p.category || "-"}</td>
                      <td className="p-3">
                        <Badge
                          variant={p.status === "OPEN" ? "default" : p.status === "UPCOMING" ? "secondary" : "outline"}
                          className="text-xs"
                        >
                          {p.status}
                        </Badge>
                      </td>
                      <td className="p-3">
                        {p.summary ? (
                          <Badge variant="secondary" className="text-xs">있음</Badge>
                        ) : (
                          <span className="text-xs text-muted-foreground">없음</span>
                        )}
                      </td>
                      <td className="p-3 text-xs">{new Date(p.created_at).toLocaleDateString("ko")}</td>
                      <td className="p-3">
                        <div className="flex gap-1">
                          <Button
                            size="sm"
                            variant="ghost"
                            className="h-7 w-7 p-0"
                            title="AI 요약 재생성"
                            onClick={() => handleRegenSummary(p.id)}
                            disabled={regenSummary.isPending}
                          >
                            <Bot className="h-3.5 w-3.5" />
                          </Button>
                          <Button
                            size="sm"
                            variant="ghost"
                            className="h-7 w-7 p-0 text-red-500 hover:text-red-700"
                            title="삭제"
                            onClick={() => handleDelete(p.id, p.title)}
                          >
                            <Trash2 className="h-3.5 w-3.5" />
                          </Button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          {!isLoading && programs?.length === 0 && (
            <p className="p-8 text-center text-muted-foreground">검색 결과가 없습니다.</p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
