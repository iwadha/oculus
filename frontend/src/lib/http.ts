export async function fetchJson<T>(path: string, init?: RequestInit & { signal?: AbortSignal }) {
const url = path.startsWith("http") ? path : `${process.env.NEXT_PUBLIC_API_BASE_URL}${path}`;
const res = await fetch(url, { ...init, headers: { "Content-Type": "application/json", ...(init?.headers || {}) }, cache: "no-store" });
if (!res.ok) {
const text = await res.text().catch(() => "");
throw new Error(`${res.status} ${res.statusText}: ${text}`);
}
return res.json() as Promise<T>;
}
