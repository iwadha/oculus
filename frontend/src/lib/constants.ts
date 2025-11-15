// frontend/src/lib/constants.ts

export const APP_NAME = process.env.NEXT_PUBLIC_APP_NAME || "Oculus";

// Base URL for the FastAPI backend
export const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

/**
 * SSE endpoint:
 * - Backend exposes /v1/stream (not /v1/events/stream).
 * - You can still override via NEXT_PUBLIC_SSE_URL if needed.
 */
export const SSE_URL =
  process.env.NEXT_PUBLIC_SSE_URL ?? `${API_BASE}/v1/stream`;
