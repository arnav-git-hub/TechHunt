/**
 * Tests for the HealthBadge component.
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { HealthBadge } from "@/components/HealthBadge";
import * as api from "@/lib/api";

describe("HealthBadge", () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  it("shows loading state initially", async () => {
    vi.spyOn(api, "fetchHealth").mockImplementation(
      () => new Promise(() => {}) // never resolves — keeps loading state
    );

    render(<HealthBadge />);
    expect(screen.getByRole("status")).toBeInTheDocument();
    expect(screen.getByText(/checking api/i)).toBeInTheDocument();
  });

  it("shows connected state when health is ok", async () => {
    vi.spyOn(api, "fetchHealth").mockResolvedValue({
      data: {
        status: "ok",
        version: "0.1.0",
        environment: "test",
        uptime_seconds: 5,
        database: "ok",
      },
      error: null,
    });

    render(<HealthBadge />);
    await waitFor(() => {
      expect(screen.getByText(/api connected/i)).toBeInTheDocument();
    });
  });

  it("shows unreachable state on error", async () => {
    vi.spyOn(api, "fetchHealth").mockResolvedValue({
      data: null,
      error: { message: "Network request failed" },
    });

    render(<HealthBadge />);
    await waitFor(() => {
      expect(screen.getByText(/api unreachable/i)).toBeInTheDocument();
    });
  });
});
