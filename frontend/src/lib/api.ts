const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function fetchApi<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  const res = await fetch(`${API_URL}${endpoint}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    throw new Error(`API Error: ${res.status}`);
  }
  return res.json();
}
