import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { signIn } from "next-auth/react";

// Mock next/navigation locally so we can control push
const mockPush = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({
    push: mockPush,
    replace: vi.fn(),
    refresh: vi.fn(),
    back: vi.fn(),
    forward: vi.fn(),
    prefetch: vi.fn(),
  }),
  usePathname: () => "/",
  useSearchParams: () => new URLSearchParams(),
}));

import DemoLoginButton from "@/components/DemoLoginButton";

describe("DemoLoginButton", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders the demo button", () => {
    render(<DemoLoginButton />);
    expect(screen.getByText("Try live demo")).toBeInTheDocument();
  });

  it("calls signIn with demo credentials on click", async () => {
    (signIn as any).mockResolvedValue({ error: null });

    render(<DemoLoginButton />);
    fireEvent.click(screen.getByText("Try live demo"));

    await waitFor(() => {
      expect(signIn).toHaveBeenCalledWith("credentials", {
        email: "demo@geotrack.ai",
        password: "demo1234",
        redirect: false,
      });
    });
  });

  it("shows loading state while authenticating", async () => {
    (signIn as any).mockImplementation(
      () => new Promise(() => {}) // never resolves
    );

    render(<DemoLoginButton />);
    fireEvent.click(screen.getByText("Try live demo"));

    await waitFor(() => {
      expect(screen.getByText("Loading demo...")).toBeInTheDocument();
    });
  });

  it("shows error when signIn fails", async () => {
    (signIn as any).mockResolvedValue({ error: "Invalid credentials" });

    render(<DemoLoginButton />);
    fireEvent.click(screen.getByText("Try live demo"));

    await waitFor(() => {
      expect(
        screen.getByText("Demo account unavailable. Run the seed script first.")
      ).toBeInTheDocument();
    });
  });

  it("shows generic error on exception", async () => {
    (signIn as any).mockRejectedValue(new Error("Network error"));

    render(<DemoLoginButton />);
    fireEvent.click(screen.getByText("Try live demo"));

    await waitFor(() => {
      expect(
        screen.getByText("Something went wrong. Please try again.")
      ).toBeInTheDocument();
    });
  });

  it("redirects to dashboard on success", async () => {
    (signIn as any).mockResolvedValue({ error: null });

    render(<DemoLoginButton />);
    fireEvent.click(screen.getByText("Try live demo"));

    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith("/dashboard");
    });
  });
});
