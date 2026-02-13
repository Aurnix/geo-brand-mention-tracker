import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";

// Mock the DemoLoginButton since it uses client-side features
vi.mock("@/components/DemoLoginButton", () => ({
  default: () => <button data-testid="demo-btn">Try live demo</button>,
}));

import LandingPage from "@/app/page";

describe("LandingPage", () => {
  it("renders the hero section", () => {
    render(<LandingPage />);

    expect(screen.getByText("The future of brand visibility tracking")).toBeInTheDocument();
    expect(screen.getByText(/The Rank Tracker for/)).toBeInTheDocument();
    expect(screen.getByText("the AI Era")).toBeInTheDocument();
  });

  it("renders the demo login button", () => {
    render(<LandingPage />);
    expect(screen.getByTestId("demo-btn")).toBeInTheDocument();
  });

  it("renders the signup CTA", () => {
    render(<LandingPage />);
    expect(screen.getByText("Start tracking free")).toBeInTheDocument();
  });

  it("renders navigation links", () => {
    render(<LandingPage />);
    // "Log in" appears multiple times (nav + footer), use getAllByText
    const loginLinks = screen.getAllByText("Log in");
    expect(loginLinks.length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText("Sign up free")).toBeInTheDocument();
  });

  it("renders the how it works section", () => {
    render(<LandingPage />);

    // "How it works" appears in both heading and footer nav link
    const howItWorks = screen.getAllByText("How it works");
    expect(howItWorks.length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText("Set up your brand")).toBeInTheDocument();
    expect(screen.getByText("Add your queries")).toBeInTheDocument();
    expect(screen.getByText("Daily tracking runs")).toBeInTheDocument();
    expect(screen.getByText("Dashboard insights")).toBeInTheDocument();
  });

  it("renders feature grid", () => {
    render(<LandingPage />);

    expect(screen.getByText("Multi-engine tracking")).toBeInTheDocument();
    expect(screen.getByText("Mention detection")).toBeInTheDocument();
    expect(screen.getByText("Sentiment analysis")).toBeInTheDocument();
    expect(screen.getByText("Position tracking")).toBeInTheDocument();
    expect(screen.getByText("Competitor monitoring")).toBeInTheDocument();
    expect(screen.getByText("Trend analysis")).toBeInTheDocument();
  });

  it("renders all engine badges", () => {
    render(<LandingPage />);

    // Engine names appear multiple times (badges + mock dashboard + pricing),
    // so use getAllByText
    expect(screen.getAllByText("ChatGPT").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("Claude").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("Perplexity").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("Gemini").length).toBeGreaterThanOrEqual(1);
  });

  it("renders pricing tiers", () => {
    render(<LandingPage />);

    expect(screen.getByText("Free")).toBeInTheDocument();
    expect(screen.getByText("Pro")).toBeInTheDocument();
    expect(screen.getByText("Agency")).toBeInTheDocument();
    expect(screen.getByText("$0")).toBeInTheDocument();
    expect(screen.getByText("$49")).toBeInTheDocument();
    expect(screen.getByText("$149")).toBeInTheDocument();
  });

  it("renders the footer", () => {
    render(<LandingPage />);

    expect(
      screen.getByText(/2026 GeoTrack. All rights reserved./)
    ).toBeInTheDocument();
  });

  it("renders the final CTA section", () => {
    render(<LandingPage />);

    expect(
      screen.getByText("Start tracking your brand's AI visibility")
    ).toBeInTheDocument();
    expect(screen.getByText("Get started for free")).toBeInTheDocument();
  });

  it("renders the problem section", () => {
    render(<LandingPage />);

    expect(screen.getByText("AI usage is exploding")).toBeInTheDocument();
    expect(screen.getByText("No visibility into AI results")).toBeInTheDocument();
    expect(screen.getByText("GEO is the new SEO")).toBeInTheDocument();
  });
});
