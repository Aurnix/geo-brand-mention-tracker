import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { signIn } from "next-auth/react";

// Mock next/navigation locally
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
  usePathname: () => "/login",
  useSearchParams: () => new URLSearchParams(),
}));

// Override the session mock for login page (unauthenticated)
vi.mock("next-auth/react", async () => {
  const actual = await vi.importActual("next-auth/react");
  return {
    ...actual,
    useSession: () => ({
      data: null,
      status: "unauthenticated",
    }),
    signIn: vi.fn(),
    SessionProvider: ({ children }: { children: React.ReactNode }) => children,
  };
});

import LoginPage from "@/app/login/page";

describe("LoginPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders login form with email and password fields", () => {
    render(<LoginPage />);

    expect(screen.getByRole("heading", { name: /sign in/i })).toBeInTheDocument();
    expect(screen.getByLabelText("Email address")).toBeInTheDocument();
    expect(screen.getByLabelText("Password")).toBeInTheDocument();
  });

  it("renders sign up link", () => {
    render(<LoginPage />);
    expect(screen.getByText("Sign up free")).toBeInTheDocument();
  });

  it("submits form with email and password", async () => {
    (signIn as any).mockResolvedValue({ error: null });
    const user = userEvent.setup();

    render(<LoginPage />);

    await user.type(screen.getByLabelText("Email address"), "test@test.com");
    await user.type(screen.getByLabelText("Password"), "password123");

    const submitButton = screen.getByRole("button", { name: /sign in/i });
    await user.click(submitButton);

    await waitFor(() => {
      expect(signIn).toHaveBeenCalledWith("credentials", {
        email: "test@test.com",
        password: "password123",
        redirect: false,
      });
    });
  });

  it("shows error on failed login", async () => {
    (signIn as any).mockResolvedValue({ error: "Invalid credentials" });
    const user = userEvent.setup();

    render(<LoginPage />);

    await user.type(screen.getByLabelText("Email address"), "bad@test.com");
    await user.type(screen.getByLabelText("Password"), "wrong");

    const submitButton = screen.getByRole("button", { name: /sign in/i });
    await user.click(submitButton);

    await waitFor(() => {
      expect(
        screen.getByText("Invalid email or password. Please try again.")
      ).toBeInTheDocument();
    });
  });

  it("redirects to dashboard on successful login", async () => {
    (signIn as any).mockResolvedValue({ error: null });
    const user = userEvent.setup();

    render(<LoginPage />);

    await user.type(screen.getByLabelText("Email address"), "test@test.com");
    await user.type(screen.getByLabelText("Password"), "password123");

    const submitButton = screen.getByRole("button", { name: /sign in/i });
    await user.click(submitButton);

    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith("/dashboard");
    });
  });

  it("shows loading state while submitting", async () => {
    (signIn as any).mockImplementation(
      () => new Promise(() => {}) // never resolves
    );
    const user = userEvent.setup();

    render(<LoginPage />);

    await user.type(screen.getByLabelText("Email address"), "test@test.com");
    await user.type(screen.getByLabelText("Password"), "pass");

    const submitButton = screen.getByRole("button", { name: /sign in/i });
    await user.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText("Signing in...")).toBeInTheDocument();
    });
  });
});
