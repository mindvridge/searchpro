import { Search } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

export default function HomePage() {
  return (
    <div className="space-y-8">
      <section className="text-center space-y-4 py-8">
        <h1 className="text-3xl font-bold tracking-tight sm:text-4xl">
          정부지원사업 통합 검색
        </h1>
        <p className="text-muted-foreground max-w-2xl mx-auto">
          정부지원사업, 공모전, 보조금 정보를 한곳에서 검색하고 관리하세요.
        </p>
        <div className="flex max-w-lg mx-auto gap-2">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input placeholder="키워드로 검색..." className="pl-9" />
          </div>
          <Button>검색</Button>
        </div>
        <div className="flex flex-wrap justify-center gap-2">
          <Badge variant="secondary">청년</Badge>
          <Badge variant="secondary">창업</Badge>
          <Badge variant="secondary">중소기업</Badge>
          <Badge variant="secondary">R&D</Badge>
          <Badge variant="secondary">고용</Badge>
        </div>
      </section>

      <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {[1, 2, 3].map((i) => (
          <Card key={i}>
            <CardHeader>
              <div className="flex items-center gap-2">
                <Badge>모집중</Badge>
                <span className="text-xs text-muted-foreground">D-14</span>
              </div>
              <CardTitle className="text-base">
                샘플 지원사업 {i}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">
                지원사업 상세 내용이 이곳에 표시됩니다.
              </p>
            </CardContent>
          </Card>
        ))}
      </section>
    </div>
  );
}
