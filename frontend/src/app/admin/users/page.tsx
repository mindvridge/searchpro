"use client";

import { Users as UsersIcon, Crown } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useAdminUsers, usePatchUser } from "@/hooks/useAdmin";
import { toast } from "sonner";

export default function AdminUsersPage() {
  const { data: users, isLoading } = useAdminUsers();
  const patchUser = usePatchUser();

  const togglePremium = (id: string, current: boolean) => {
    patchUser.mutate(
      { id, is_premium: !current },
      { onSuccess: () => toast.success("프리미엄 상태 변경됨") }
    );
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2">
        <UsersIcon className="h-6 w-6 text-primary" />
        <h1 className="text-2xl font-bold">사용자 관리</h1>
      </div>

      <Card>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="p-4 space-y-2">
              {Array.from({ length: 5 }).map((_, i) => (
                <div key={i} className="h-10 bg-muted/30 rounded animate-pulse" />
              ))}
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b text-left text-xs text-muted-foreground">
                    <th className="p-3">이메일</th>
                    <th className="p-3">이름</th>
                    <th className="p-3">인증</th>
                    <th className="p-3">프리미엄</th>
                    <th className="p-3">프로필</th>
                    <th className="p-3">가입일</th>
                    <th className="p-3"></th>
                  </tr>
                </thead>
                <tbody>
                  {users?.map((u) => (
                    <tr key={u.id} className="border-b last:border-0 hover:bg-secondary/30">
                      <td className="p-3 font-medium">{u.email}</td>
                      <td className="p-3">{u.name || "-"}</td>
                      <td className="p-3">
                        <Badge variant="outline" className="text-xs">{u.provider}</Badge>
                      </td>
                      <td className="p-3">
                        {u.is_premium ? (
                          <Badge className="bg-yellow-100 text-yellow-700 text-xs gap-1">
                            <Crown className="h-3 w-3" /> Premium
                          </Badge>
                        ) : (
                          <span className="text-xs text-muted-foreground">Free</span>
                        )}
                      </td>
                      <td className="p-3 text-xs text-muted-foreground max-w-[200px] truncate">
                        {u.profile ? JSON.stringify(u.profile).slice(0, 50) : "-"}
                      </td>
                      <td className="p-3 text-xs">{new Date(u.created_at).toLocaleDateString("ko")}</td>
                      <td className="p-3">
                        <Button
                          size="sm"
                          variant={u.is_premium ? "outline" : "default"}
                          className="text-xs"
                          onClick={() => togglePremium(u.id, u.is_premium)}
                        >
                          {u.is_premium ? "Free로 변경" : "Premium"}
                        </Button>
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
