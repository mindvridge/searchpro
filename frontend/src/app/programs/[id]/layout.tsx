import type { Metadata } from "next";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function generateMetadata({
  params,
}: {
  params: Promise<{ id: string }>;
}): Promise<Metadata> {
  const { id } = await params;

  try {
    const res = await fetch(`${API_URL}/api/v1/programs/${id}`, {
      next: { revalidate: 3600 },
    });
    if (!res.ok) throw new Error("Not found");
    const program = await res.json();

    const title = `${program.title}${program.organization ? ` - ${program.organization}` : ""} | SearchPro`;
    const description =
      program.description?.slice(0, 160) ||
      `${program.title} - 지원사업 상세 정보를 확인하세요.`;

    return {
      title,
      description,
      openGraph: {
        title,
        description,
        type: "article",
        locale: "ko_KR",
      },
      twitter: {
        card: "summary_large_image",
        title,
        description,
      },
    };
  } catch {
    return {
      title: "지원사업 상세 | SearchPro",
    };
  }
}

export default function ProgramDetailLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <>{children}</>;
}
