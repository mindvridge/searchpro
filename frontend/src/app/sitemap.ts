import type { MetadataRoute } from "next";

const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL || "https://searchpro.kr";
const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const revalidate = 86400; // 24h

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const staticPages: MetadataRoute.Sitemap = [
    { url: SITE_URL, lastModified: new Date(), changeFrequency: "daily", priority: 1.0 },
    { url: `${SITE_URL}/programs`, lastModified: new Date(), changeFrequency: "daily", priority: 0.9 },
    { url: `${SITE_URL}/calendar`, lastModified: new Date(), changeFrequency: "daily", priority: 0.7 },
    { url: `${SITE_URL}/login`, changeFrequency: "monthly", priority: 0.3 },
    { url: `${SITE_URL}/register`, changeFrequency: "monthly", priority: 0.3 },
  ];

  // Fetch open program IDs for dynamic pages
  let programPages: MetadataRoute.Sitemap = [];
  try {
    const res = await fetch(`${API_URL}/api/v1/programs?status=OPEN&limit=100&sort=created_desc`);
    if (res.ok) {
      const data = await res.json();
      programPages = (data.items || []).map((p: { id: string; created_at: string }) => ({
        url: `${SITE_URL}/programs/${p.id}`,
        lastModified: new Date(p.created_at),
        changeFrequency: "weekly" as const,
        priority: 0.8,
      }));
    }
  } catch {
    // silently fail — static pages still served
  }

  return [...staticPages, ...programPages];
}
