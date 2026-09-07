/**
 * Extended API client — Stage 2 additions.
 * Adds auth (register, login) and events (list, detail) endpoints.
 */

import type {
  ApiResult,
  Event,
  HealthResponse,
  LoginResponse,
  PaginatedEvents,
  UserResponse,
} from "@/types";

// ---------------------------------------------------------------------------
// Configuration
// ---------------------------------------------------------------------------

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

// ---------------------------------------------------------------------------
// Core fetch wrapper
// ---------------------------------------------------------------------------

async function apiFetch<T>(
  path: string,
  options?: RequestInit
): Promise<ApiResult<T>> {
  const url = `${API_BASE_URL}${path}`;
  try {
    const response = await fetch(url, {
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
        ...options?.headers,
      },
      ...options,
    });

    if (!response.ok) {
      const text = await response.text().catch(() => "Unknown error");
      return {
        data: null,
        error: {
          message: text || `HTTP ${response.status}`,
          status: response.status,
        },
      };
    }

    const data = (await response.json()) as T;
    return { data, error: null };
  } catch (err) {
    const message =
      err instanceof Error ? err.message : "Network request failed";
    return { data: null, error: { message } };
  }
}

// ---------------------------------------------------------------------------
// Health
// ---------------------------------------------------------------------------

export async function fetchHealth(): Promise<ApiResult<HealthResponse>> {
  return apiFetch<HealthResponse>("/api/v1/health");
}

// ---------------------------------------------------------------------------
// Auth
// ---------------------------------------------------------------------------

export interface RegisterRequest {
  name: string;
  email: string;
  password: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export async function register(
  data: RegisterRequest
): Promise<ApiResult<LoginResponse>> {
  return apiFetch<LoginResponse>("/api/v1/auth/register", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function login(
  data: LoginRequest
): Promise<ApiResult<LoginResponse>> {
  return apiFetch<LoginResponse>("/api/v1/auth/login", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function getMe(token: string): Promise<ApiResult<UserResponse>> {
  return apiFetch<UserResponse>("/api/v1/users/me", {
    headers: { Authorization: `Bearer ${token}` },
  });
}

// ---------------------------------------------------------------------------
// Events
// ---------------------------------------------------------------------------

export interface EventsQuery {
  page?: number;
  page_size?: number;
  opportunity_type?: string;
  category?: string;
  is_online?: boolean;
  price_type?: "free" | "paid" | "unknown";
  difficulty?: string;
  country?: string;
  source?: string;
  q?: string;
}

export async function fetchEvents(
  query: EventsQuery = {}
): Promise<ApiResult<PaginatedEvents>> {
  const params = new URLSearchParams();
  if (query.page) params.set("page", String(query.page));
  if (query.page_size) params.set("page_size", String(query.page_size));
  if (query.opportunity_type) params.set("opportunity_type", query.opportunity_type);
  if (query.category) params.set("category", query.category);
  if (query.is_online !== undefined) params.set("is_online", String(query.is_online));
  if (query.price_type) params.set("price_type", query.price_type);
  if (query.difficulty) params.set("difficulty", query.difficulty);
  if (query.country) params.set("country", query.country);
  if (query.source) params.set("source", query.source);
  if (query.q) params.set("q", query.q);

  const qs = params.toString();
  return apiFetch<PaginatedEvents>(`/api/v1/events${qs ? `?${qs}` : ""}`);
}

export async function fetchEvent(
  idOrSlug: string
): Promise<ApiResult<Event>> {
  return apiFetch<Event>(`/api/v1/events/${encodeURIComponent(idOrSlug)}`);
}
