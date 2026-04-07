"use client";

import {
  BarChart3,
  FileText,
  Users,
  Mail,
  TrendingUp,
  AlertCircle,
  CheckCircle,
  Clock,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { useAdminStats } from "@/hooks/useAdmin";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from "recharts";

const COLORS = ["#1e3a5f", "#0d9488", "#f59e0b", "#ef4444", "#8b5cf6", "#ec4899", "#06b6d4", "#84cc16"];

export default function AdminDashboard() {
  const { data: stats, isLoading } = useAdminStats();

  if (isLoading) {
    return (
      <div className="space-y-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="h-24 rounded-lg bg-muted/30 animate-pulse" />
        ))}
      </div>
    );
  }

  if (!stats) return <p className="text-muted-foreground">통계를 불러올 수 없습니다.</p>;

  const statCards = [
    { label: "전체 공고", value: stats.total_programs, icon: FileText, color: "text-primary" },
    { label: "오늘 신규", value: stats.today_new, icon: TrendingUp, color: "text-[var(--color-teal)]" },
    { label: "오늘 갱신", value: stats.today_updated, icon: Clock, color: "text-orange-500" },
    { label: "사용자", value: stats.total_users, icon: Users, color: "text-blue-500" },
    { label: "오늘 가입", value: stats.today_new_users, icon: Users, color: "text-purple-500" },
    { label: "구독자", value: stats.total_subscribers, icon: Mail, color: "text-pink-500" },
  ];

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">관리자 대시보드</h1>

      {/* Stat cards */}
      <div className="grid gap-3 grid-cols-2 md:grid-cols-3 lg:grid-cols-6">
        {statCards.map((s) => (
          <Card key={s.label}>
            <CardContent className="p-4">
              <div className="flex items-center gap-2 mb-1">
                <s.icon className={`h-4 w-4 ${s.color}`} />
                <p className="text-xs text-muted-foreground">{s.label}</p>
              </div>
              <p className="text-xl font-bold">{s.value.toLocaleString()}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Charts row */}
      <div className="grid gap-4 md:grid-cols-2">
        {/* Source distribution */}
        <Card>
          <CardHeader><CardTitle className="text-sm">소스별 공고</CardTitle></CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={stats.programs_by_source}>
                <XAxis dataKey="source" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip />
                <Bar dataKey="count" fill="#1e3a5f" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Category distribution */}
        <Card>
          <CardHeader><CardTitle className="text-sm">카테고리별 분포</CardTitle></CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={200}>
              <PieChart>
                <Pie
                  data={stats.programs_by_category}
                  dataKey="count"
                  nameKey="category"
                  cx="50%"
                  cy="50%"
                  outerRadius={80}
                  label={(props: any) => `${props.name || ""} ${((props.percent || 0) * 100).toFixed(0)}%`}
                  labelLine={false}
                  fontSize={10}
                >
                  {stats.programs_by_category.map((_, i) => (
                    <Cell key={i} fill={COLORS[i % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Status breakdown */}
      <Card>
        <CardHeader><CardTitle className="text-sm">상태별 현황</CardTitle></CardHeader>
        <CardContent>
          <div className="flex gap-4">
            {Object.entries(stats.programs_by_status).map(([status, count]) => (
              <div key={status} className="flex items-center gap-2">
                <Badge variant={status === "OPEN" ? "default" : status === "UPCOMING" ? "secondary" : "outline"}>
                  {status}
                </Badge>
                <span className="font-semibold">{count.toLocaleString()}</span>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Recent crawl logs */}
      <Card>
        <CardHeader><CardTitle className="text-sm">최근 크롤링 로그</CardTitle></CardHeader>
        <CardContent>
          <div className="space-y-2">
            {stats.recent_crawl_logs.map((log) => (
              <div key={log.id} className="flex items-center justify-between text-sm border-b pb-2 last:border-0">
                <div className="flex items-center gap-2">
                  {log.status === "SUCCESS" ? (
                    <CheckCircle className="h-4 w-4 text-green-500" />
                  ) : log.status === "FAILED" ? (
                    <AlertCircle className="h-4 w-4 text-red-500" />
                  ) : (
                    <Clock className="h-4 w-4 text-yellow-500 animate-spin" />
                  )}
                  <Badge variant="outline" className="text-xs">{log.source}</Badge>
                </div>
                <div className="flex items-center gap-4 text-xs text-muted-foreground">
                  <span>+{log.new_count} 신규</span>
                  <span>{log.updated_count} 갱신</span>
                  {log.error_count > 0 && <span className="text-red-500">{log.error_count} 에러</span>}
                  <span>{new Date(log.started_at).toLocaleString("ko")}</span>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
