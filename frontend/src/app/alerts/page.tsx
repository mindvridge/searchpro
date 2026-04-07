"use client";

import { useState } from "react";
import {
  Bell,
  BellOff,
  Plus,
  Trash2,
  Search,
  Tag,
  CalendarClock,
  Mail,
  X,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogClose,
} from "@/components/ui/dialog";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  useAlerts,
  useCreateAlert,
  useDeleteAlert,
  useToggleAlert,
  type AlertItem,
} from "@/hooks/useAlerts";
import { toast } from "sonner";

const CATEGORIES = ["창업", "R&D", "수출", "마케팅", "인력", "시설/공간", "금융/투자", "컨설팅"];
const REGIONS = ["전국", "서울", "경기", "인천", "부산", "대구", "광주", "대전", "울산", "세종", "강원", "충북", "충남", "전북", "전남", "경북", "경남", "제주"];

export default function AlertsPage() {
  const { data: alerts, isLoading } = useAlerts();
  const toggleAlert = useToggleAlert();
  const deleteAlert = useDeleteAlert();
  const [dialogOpen, setDialogOpen] = useState(false);

  const handleToggle = (id: string) => {
    toggleAlert.mutate(id, {
      onSuccess: () => toast.success("알림 상태가 변경되었습니다"),
    });
  };

  const handleDelete = (id: string) => {
    deleteAlert.mutate(id, {
      onSuccess: () => toast.success("알림이 삭제되었습니다"),
    });
  };

  const typeInfo: Record<string, { icon: React.ElementType; label: string; color: string }> = {
    KEYWORD: { icon: Search, label: "키워드", color: "text-blue-500" },
    CATEGORY: { icon: Tag, label: "카테고리", color: "text-green-500" },
    DEADLINE: { icon: CalendarClock, label: "마감 알림", color: "text-orange-500" },
  };

  return (
    <div className="container mx-auto px-4 py-6 max-w-3xl">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <Bell className="h-6 w-6 text-primary" />
          <h1 className="text-2xl font-bold">알림 설정</h1>
        </div>
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogTrigger className="inline-flex items-center gap-1.5 rounded-lg bg-primary text-primary-foreground px-3 py-1.5 text-sm font-medium hover:bg-primary/90 transition-colors">
            <Plus className="h-4 w-4" />
            새 알림
          </DialogTrigger>
          <DialogContent className="max-w-lg max-h-[80vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>새 알림 만들기</DialogTitle>
            </DialogHeader>
            <CreateAlertForm onSuccess={() => setDialogOpen(false)} />
          </DialogContent>
        </Dialog>
      </div>

      {isLoading && (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-24 rounded-lg border bg-muted/30 animate-pulse" />
          ))}
        </div>
      )}

      {!isLoading && (!alerts || alerts.length === 0) && (
        <Card>
          <CardContent className="py-16 text-center">
            <BellOff className="h-12 w-12 text-muted-foreground/40 mx-auto mb-4" />
            <p className="text-muted-foreground mb-2">설정된 알림이 없습니다</p>
            <p className="text-sm text-muted-foreground">
              키워드나 관심 분야를 등록하면 새 공고를 알려드립니다
            </p>
          </CardContent>
        </Card>
      )}

      <div className="space-y-3">
        {alerts?.map((alert) => {
          const info = typeInfo[alert.type] || typeInfo.KEYWORD;
          const Icon = info.icon;
          return (
            <Card key={alert.id} className={!alert.is_active ? "opacity-60" : ""}>
              <CardContent className="p-4">
                <div className="flex items-start justify-between gap-3">
                  <div className="flex items-start gap-3 flex-1 min-w-0">
                    <Icon className={`h-5 w-5 mt-0.5 shrink-0 ${info.color}`} />
                    <div className="min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <Badge variant="outline" className="text-xs">{info.label}</Badge>
                        <Badge variant="secondary" className="text-xs gap-1">
                          <Mail className="h-3 w-3" />
                          {alert.channel}
                        </Badge>
                        {!alert.is_active && (
                          <Badge variant="outline" className="text-xs text-muted-foreground">비활성</Badge>
                        )}
                      </div>
                      <AlertConditionSummary alert={alert} />
                    </div>
                  </div>
                  <div className="flex items-center gap-1 shrink-0">
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-8 w-8"
                      onClick={() => handleToggle(alert.id)}
                      title={alert.is_active ? "비활성화" : "활성화"}
                    >
                      {alert.is_active ? (
                        <Bell className="h-4 w-4 text-primary" />
                      ) : (
                        <BellOff className="h-4 w-4 text-muted-foreground" />
                      )}
                    </Button>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-8 w-8 text-muted-foreground hover:text-destructive"
                      onClick={() => handleDelete(alert.id)}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
}

function AlertConditionSummary({ alert }: { alert: AlertItem }) {
  const cond = alert.condition;

  if (alert.type === "KEYWORD") {
    const keywords = (cond.keywords as string[]) || [];
    return (
      <p className="text-sm text-muted-foreground">
        키워드: {keywords.length > 0 ? keywords.join(", ") : "-"}
      </p>
    );
  }
  if (alert.type === "CATEGORY") {
    const cats = (cond.categories as string[]) || [];
    const regions = (cond.regions as string[]) || [];
    return (
      <p className="text-sm text-muted-foreground">
        {cats.length > 0 && <>분야: {cats.join(", ")}</>}
        {cats.length > 0 && regions.length > 0 && " · "}
        {regions.length > 0 && <>지역: {regions.join(", ")}</>}
      </p>
    );
  }
  if (alert.type === "DEADLINE") {
    const days = (cond.days_before as number[]) || [7, 3, 1];
    return (
      <p className="text-sm text-muted-foreground">
        마감 D-{days.join(", D-")} 전 알림
      </p>
    );
  }
  return null;
}

function CreateAlertForm({ onSuccess }: { onSuccess: () => void }) {
  const createAlert = useCreateAlert();
  const [type, setType] = useState<"KEYWORD" | "CATEGORY" | "DEADLINE">("KEYWORD");

  // Keyword state
  const [keywords, setKeywords] = useState<string[]>([]);
  const [keywordInput, setKeywordInput] = useState("");

  // Category state
  const [selCategories, setSelCategories] = useState<string[]>([]);
  const [selRegions, setSelRegions] = useState<string[]>([]);

  // Deadline state
  const [daysBefore, setDaysBefore] = useState<number[]>([7, 3, 1]);

  const addKeyword = () => {
    const kw = keywordInput.trim();
    if (kw && !keywords.includes(kw)) {
      setKeywords([...keywords, kw]);
      setKeywordInput("");
    }
  };

  const toggleItem = (list: string[], item: string, setter: (v: string[]) => void) => {
    setter(list.includes(item) ? list.filter((x) => x !== item) : [...list, item]);
  };

  const toggleDay = (day: number) => {
    setDaysBefore((prev) =>
      prev.includes(day) ? prev.filter((d) => d !== day) : [...prev, day].sort((a, b) => b - a)
    );
  };

  const handleSubmit = () => {
    let condition: Record<string, unknown> = {};
    if (type === "KEYWORD") {
      if (keywords.length === 0) { toast.error("키워드를 1개 이상 입력하세요"); return; }
      condition = { keywords };
    } else if (type === "CATEGORY") {
      if (selCategories.length === 0) { toast.error("카테고리를 1개 이상 선택하세요"); return; }
      condition = { categories: selCategories, regions: selRegions };
    } else {
      condition = { days_before: daysBefore };
    }

    createAlert.mutate(
      { type, condition, channel: "EMAIL" },
      {
        onSuccess: () => {
          toast.success("알림이 생성되었습니다");
          onSuccess();
        },
        onError: () => toast.error("알림 생성에 실패했습니다"),
      }
    );
  };

  return (
    <div className="space-y-5">
      <Tabs value={type} onValueChange={(v) => setType(v as typeof type)}>
        <TabsList className="w-full">
          <TabsTrigger value="KEYWORD" className="flex-1">키워드</TabsTrigger>
          <TabsTrigger value="CATEGORY" className="flex-1">카테고리</TabsTrigger>
          <TabsTrigger value="DEADLINE" className="flex-1">마감 알림</TabsTrigger>
        </TabsList>

        <TabsContent value="KEYWORD" className="space-y-3 pt-3">
          <p className="text-sm text-muted-foreground">
            키워드가 포함된 새 공고가 등록되면 알려드립니다.
          </p>
          <div className="flex gap-2">
            <Input
              placeholder="키워드 입력"
              value={keywordInput}
              onChange={(e) => setKeywordInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && (e.preventDefault(), addKeyword())}
            />
            <Button variant="outline" onClick={addKeyword}>추가</Button>
          </div>
          <div className="flex flex-wrap gap-1.5">
            {keywords.map((kw) => (
              <Badge key={kw} variant="secondary" className="gap-1">
                {kw}
                <X className="h-3 w-3 cursor-pointer" onClick={() => setKeywords(keywords.filter((k) => k !== kw))} />
              </Badge>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="CATEGORY" className="space-y-4 pt-3">
          <div>
            <p className="text-sm font-medium mb-2">분야 선택</p>
            <div className="flex flex-wrap gap-1.5">
              {CATEGORIES.map((cat) => (
                <Badge
                  key={cat}
                  variant={selCategories.includes(cat) ? "default" : "outline"}
                  className="cursor-pointer"
                  onClick={() => toggleItem(selCategories, cat, setSelCategories)}
                >
                  {cat}
                </Badge>
              ))}
            </div>
          </div>
          <div>
            <p className="text-sm font-medium mb-2">지역 선택 (선택사항)</p>
            <div className="flex flex-wrap gap-1.5">
              {REGIONS.map((r) => (
                <Badge
                  key={r}
                  variant={selRegions.includes(r) ? "default" : "outline"}
                  className="cursor-pointer"
                  onClick={() => toggleItem(selRegions, r, setSelRegions)}
                >
                  {r}
                </Badge>
              ))}
            </div>
          </div>
        </TabsContent>

        <TabsContent value="DEADLINE" className="space-y-3 pt-3">
          <p className="text-sm text-muted-foreground">
            북마크한 사업의 마감일이 다가오면 알려드립니다.
          </p>
          <div className="flex flex-wrap gap-2">
            {[14, 7, 3, 1].map((day) => (
              <Badge
                key={day}
                variant={daysBefore.includes(day) ? "default" : "outline"}
                className="cursor-pointer px-3 py-1.5"
                onClick={() => toggleDay(day)}
              >
                D-{day}
              </Badge>
            ))}
          </div>
        </TabsContent>
      </Tabs>

      <div className="flex items-center gap-2 pt-2">
        <Badge variant="secondary" className="gap-1">
          <Mail className="h-3 w-3" /> 이메일 알림
        </Badge>
      </div>

      <div className="flex justify-end gap-2 pt-2">
        <DialogClose className="inline-flex items-center rounded-lg border px-3 py-1.5 text-sm hover:bg-secondary">
          취소
        </DialogClose>
        <Button onClick={handleSubmit} disabled={createAlert.isPending}>
          {createAlert.isPending ? "생성 중..." : "알림 만들기"}
        </Button>
      </div>
    </div>
  );
}
