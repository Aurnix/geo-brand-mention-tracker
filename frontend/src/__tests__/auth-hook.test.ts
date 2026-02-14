import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook } from "@testing-library/react";
import { useSession } from "next-auth/react";

// Override the mock for specific tests
vi.mock("next-auth/react", () => ({
  useSession: vi.fn(),
  signIn: vi.fn(),
  signOut: vi.fn(),
  SessionProvider: ({ children }: { children: React.ReactNode }) => children,
}));

vi.mock("@/lib/api", () => ({
  api: {
    setToken: vi.fn(),
  },
}));

import { useAuth } from "@/lib/auth";
import { api } from "@/lib/api";

describe("useAuth", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("returns loading state when session is loading", () => {
    (useSession as any).mockReturnValue({
      data: null,
      status: "loading",
    });

    const { result } = renderHook(() => useAuth());

    expect(result.current.isLoading).toBe(true);
    expect(result.current.isAuthenticated).toBe(false);
  });

  it("returns authenticated state with session data", () => {
    (useSession as any).mockReturnValue({
      data: {
        user: { email: "test@test.com" },
        accessToken: "jwt-token-123",
        userId: "user-1",
        planTier: "pro",
      },
      status: "authenticated",
    });

    const { result } = renderHook(() => useAuth());

    expect(result.current.isAuthenticated).toBe(true);
    expect(result.current.isLoading).toBe(false);
    expect(result.current.token).toBe("jwt-token-123");
    expect(result.current.userId).toBe("user-1");
    expect(result.current.planTier).toBe("pro");
  });

  it("sets token on API client when session has accessToken", () => {
    (useSession as any).mockReturnValue({
      data: {
        user: { email: "test@test.com" },
        accessToken: "jwt-token-123",
        userId: "user-1",
        planTier: "free",
      },
      status: "authenticated",
    });

    renderHook(() => useAuth());

    expect(api.setToken).toHaveBeenCalledWith("jwt-token-123");
  });

  it("returns unauthenticated state when no session", () => {
    (useSession as any).mockReturnValue({
      data: null,
      status: "unauthenticated",
    });

    const { result } = renderHook(() => useAuth());

    expect(result.current.isAuthenticated).toBe(false);
    expect(result.current.token).toBeUndefined();
    expect(result.current.userId).toBeUndefined();
  });

  it("does not set token when no accessToken", () => {
    (useSession as any).mockReturnValue({
      data: { user: { email: "test@test.com" } },
      status: "authenticated",
    });

    renderHook(() => useAuth());

    expect(api.setToken).not.toHaveBeenCalled();
  });
});
