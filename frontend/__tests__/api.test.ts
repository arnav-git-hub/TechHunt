/**
 * Tests for the API client.
 *
 * These tests mock fetch and verify the api client handles
 * success and error responses correctly.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { fetchHealth } from "@/lib/api";
import type { HealthResponse } from "@/types";

const mockHealthResponse: HealthResponse = {
  status: "ok",
  version: "0.1.0",
  environment: "test",
  uptime_seconds: 5.0,
  database: "not_configured",
};

describe("fetchHealth", () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("returns data when the API responds with 200", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => mockHealthResponse,
        headers: { get: () => "application/json" },
      })
    );

    const result = await fetchHealth();
    expect(result.error).toBeNull();
    expect(result.data).toEqual(mockHealthResponse);
  });

  it("returns an error when the API responds with 500", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        status: 500,
        text: async () => "Internal Server Error",
        headers: { get: () => "text/plain" },
      })
    );

    const result = await fetchHealth();
    expect(result.data).toBeNull();
    expect(result.error).not.toBeNull();
    expect(result.error?.status).toBe(500);
  });

  it("returns a network error when fetch throws", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockRejectedValue(new Error("Network request failed"))
    );

    const result = await fetchHealth();
    expect(result.data).toBeNull();
    expect(result.error).not.toBeNull();
    expect(result.error?.message).toBe("Network request failed");
  });
});
