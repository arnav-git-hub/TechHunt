/**
 * Extended shared TypeScript types — Stage 2.
 */

// ---------------------------------------------------------------------------
// API utilities
// ---------------------------------------------------------------------------

export interface HealthResponse {
  status: "ok" | string;
  version: string;
  environment: string;
  uptime_seconds: number;
  database: "ok" | "unavailable" | "not_configured" | string;
}

export interface ApiError {
  message: string;
  status?: number;
}

export type ApiResult<T> =
  | { data: T; error: null }
  | { data: null; error: ApiError };

// ---------------------------------------------------------------------------
// Opportunity types
// ---------------------------------------------------------------------------

export type OpportunityType =
  | "hackathon"
  | "coding_competition"
  | "technical_competition"
  | "meetup"
  | "workshop"
  | "conference"
  | "ai_ml_event"
  | "open_source_program"
  | "fellowship"
  | "scholarship"
  | "startup_event"
  | "startup_competition"
  | "accelerator"
  | "grant"
  | "student_opportunity"
  | "other";

export type PriceType = "free" | "paid" | "unknown";
export type EventStatus =
  | "draft"
  | "pending"
  | "published"
  | "rejected"
  | "archived"
  | "cancelled";

// ---------------------------------------------------------------------------
// Event
// ---------------------------------------------------------------------------

export interface Event {
  id: string;
  title: string;
  slug: string;
  description: string | null;
  source: string;
  event_url: string | null;
  image_url: string | null;
  organizer: string | null;
  opportunity_type: OpportunityType;
  category: string | null;
  start_at_utc: string | null;
  end_at_utc: string | null;
  original_timezone: string | null;
  registration_deadline_utc: string | null;
  location: string | null;
  city: string | null;
  state: string | null;
  country: string | null;
  latitude: number | null;
  longitude: number | null;
  is_online: boolean;
  eligibility: string | null;
  difficulty: string | null;
  price_type: PriceType;
  event_status: EventStatus;
  ai_summary: string | null;
  tags: string[];
  skills: string[];
  technologies: string[];
  published_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface PaginatedEvents {
  items: Event[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

// ---------------------------------------------------------------------------
// Auth
// ---------------------------------------------------------------------------

export interface UserResponse {
  id: string;
  name: string;
  email: string;
  role: string;
  bio: string | null;
  location: string | null;
  experience_level: string | null;
  email_verified_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: UserResponse;
}
