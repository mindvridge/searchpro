"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { fetchApi, type BookmarkItem } from "@/lib/api";

export function useBookmarks() {
  return useQuery<BookmarkItem[]>({
    queryKey: ["bookmarks"],
    queryFn: () => fetchApi("/api/v1/bookmarks"),
  });
}

export function useAddBookmark() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (params: { program_id: string; memo?: string }) =>
      fetchApi("/api/v1/bookmarks", {
        method: "POST",
        body: JSON.stringify(params),
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["bookmarks"] }),
  });
}

export function useRemoveBookmark() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (programId: string) =>
      fetchApi(`/api/v1/bookmarks/${programId}`, { method: "DELETE" }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["bookmarks"] }),
  });
}

export function useUpdateBookmarkMemo() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ programId, memo }: { programId: string; memo: string }) =>
      fetchApi(`/api/v1/bookmarks/${programId}/memo`, {
        method: "PUT",
        body: JSON.stringify({ memo }),
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["bookmarks"] }),
  });
}
