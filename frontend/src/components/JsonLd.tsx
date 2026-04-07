export function WebsiteJsonLd({ stats }: { stats?: { total: number } }) {
  const data = {
    "@context": "https://schema.org",
    "@type": "WebSite",
    name: "SearchPro",
    url: "https://searchpro.kr",
    description: "정부지원사업, 공모전, 보조금 정보를 한곳에서 검색하고 관리하세요.",
    potentialAction: {
      "@type": "SearchAction",
      target: "https://searchpro.kr/programs?q={search_term_string}",
      "query-input": "required name=search_term_string",
    },
  };

  return (
    <script
      type="application/ld+json"
      dangerouslySetInnerHTML={{ __html: JSON.stringify(data) }}
    />
  );
}

export function ProgramJsonLd({
  title,
  organization,
  description,
  datePublished,
  url,
}: {
  title: string;
  organization?: string | null;
  description?: string | null;
  datePublished?: string | null;
  url: string;
}) {
  const data = {
    "@context": "https://schema.org",
    "@type": "Article",
    headline: title,
    author: organization ? { "@type": "Organization", name: organization } : undefined,
    description: description?.slice(0, 200) || title,
    datePublished: datePublished || undefined,
    url,
    publisher: {
      "@type": "Organization",
      name: "SearchPro",
      url: "https://searchpro.kr",
    },
  };

  return (
    <script
      type="application/ld+json"
      dangerouslySetInnerHTML={{ __html: JSON.stringify(data) }}
    />
  );
}
