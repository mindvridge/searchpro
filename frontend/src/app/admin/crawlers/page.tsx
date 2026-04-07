"use client";

import {
  Play,
  CheckCircle,
  AlertCircle,
  Clock,
  Database,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useAdminCrawlLogs, useTriggerCrawl } from "@/hooks/useAdmin";
import { toast } from "sonner";

const SOURCES = [
  { key: "bizinfo", label: "기업마당", schedule: "매일 06:00, 18:00" },
  { key: "kstartup", label: "K-Startup", schedule: "매일 07:00, 19:00" },
  { key: "thinkcontest", label: "씽굿", schedule: "매일 12:00" },
  { key: "wevity", label: "위비티", schedule: "매일 12:30" },
];

export default function CrawlersPage() {
  const { data: logs, isLoading } = useAdminCrawlLogs(30);
  const trigger = useTriggerCrawl();

  const handleTrigger = (source: string) => {
    trigger.mutate(source, {
      onSuccess: () => toast.success(`${source} 크롤링 시작됨`),
      onError: () => toast.error("크롤링 실행에 실패했습니다"),
    });
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2">
        <Database className="h-6 w-6 text-primary" />
        <h1 className="text-2xl font-bold">크롤러 관리</h1>
      </div>

      {/* Source cards */}
      <div className="grid gap-3 sm:grid-cols-2">
        {SOURCES.map((src) => (
          <Card key={src.key}>
            <CardContent className="p-4 flex items-center justify-between">
              <div>
                <p className="font-semibold text-sm">{src.label}</p>
                <p className="text-xs text-muted-foreground">{src.schedule}</p>
              </div>
              <Button
                size="sm"
                onClick={() => handleTrigger(src.key)}
                disabled={trigger.isPending}
              >
                <Play className="h-3 w-3 mr-1" />
                실행
              </Button>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Log table */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm">크롤링 로그</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="space-y-2">
              {Array.from({ length: 5 }).map((_, i) => (
                <div key={i} className="h-10 bg-muted/30 rounded animate-pulse" />
              ))}
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b text-left text-xs text-muted-foreground">
                    <th className="py-2 pr-3">상태</th>
                    <th className="py-2 pr-3">소스</th>
                    <th className="py-2 pr-3">시작</th>
                    <th className="py-2 pr-3">종료</th>
                    <th className="py-2 pr-3 text-right">수집</th>
                    <th className="py-2 pr-3 text-right">신규</th>
                    <th className="py-2 pr-3 text-right">갱신</th>
                    <th className="py-2 text-right">에러</th>
                  </tr>
                </thead>
                <tbody>
                  {logs?.map((log) => (
                    <tr key={log.id} className="border-b last:border-0 hover:bg-secondary/30">
                      <td className="py-2 pr-3">
                        {log.status === "SUCCESS" ? (
                          <CheckCircle className="h-4 w-4 text-green-500" />
                        ) : log.status === "FAILED" ? (
                          <AlertCircle className="h-4 w-4 text-red-500" />
                        ) : (
                          <Clock className="h-4 w-4 text-yellow-500" />
                        )}
                      </td>
                      <td className="py-2 pr-3">
                        <Badge variant="outline" className="text-xs">{log.source}</Badge>
                      </td>
                      <td className="py-2 pr-3 text-xs">{new Date(log.started_at).toLocaleString("ko")}</td>
                      <td className="py-2 pr-3 text-xs">
                        {log.finished_at ? new Date(log.finished_at).toLocaleString("ko") : "-"}
                      </td>
                      <td className="py-2 pr-3 text-right">{log.total_fetched}</td>
                      <td className="py-2 pr-3 text-right font-medium text-green-600">+{log.new_count}</td>
                      <td className="py-2 pr-3 text-right">{log.updated_count}</td>
                      <td className="py-2 text-right">
                        {log.error_count > 0 ? (
                          <span className="text-red-500 font-medium">{log.error_count}</span>
                        ) : (
                          <span className="text-muted-foreground">0</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
