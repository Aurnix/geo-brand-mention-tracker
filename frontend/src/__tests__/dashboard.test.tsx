import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";

// Mock recharts to avoid rendering SVG in tests
vi.mock("recharts", () => ({
  ResponsiveContainer: ({ children }: any) => <div data-testid="chart-container">{children}</div>,
  LineChart: ({ children }: any) => <div data-testid="line-chart">{children}</div>,
  BarChart: ({ children }: any) => <div data-testid="bar-chart">{children}</div>,
  PieChart: ({ children }: any) => <div data-testid="pie-chart">{children}</div>,
  Line: () => null,
  Bar: () => null,
  Pie: ({ children }: any) => <div>{children}</div>,
  Cell: () => null,
  XAxis: () => null,
  YAxis: () => null,
  CartesianGrid: () => null,
  Tooltip: () => null,
  Legend: () => null,
}));

// Mock ExportDropdown
vi.mock("@/components/ExportDropdown", () => ({
  default: ({ brandName }: any) => (
    <div data-testid="export-dropdown">Export for {brandName}</div>
  ),
}));

// Mock the useBrand context — the dashboard page imports from "./layout"
const mockBrandContext = {
  brandId: "brand-1" as string | null,
  brands: [{ id: "brand-1", name: "Notion" }],
  setBrandId: vi.fn(),
  refreshBrands: vi.fn(),
};

vi.mock("@/app/dashboard/layout", () => ({
  useBrand: () => mockBrandContext,
}));

// Mock the api
vi.mock("@/lib/api", () => ({
  api: {
    getOverview: vi.fn(),
    triggerRun: vi.fn(),
    setToken: vi.fn(),
  },
}));

import DashboardOverview from "@/app/dashboard/page";
import { api } from "@/lib/api";

const mockOverview = {
  mention_rate: 0.642,
  mention_rate_trend: [
    { date: "2025-01-01", rate: 0.6 },
    { date: "2025-01-15", rate: 0.65 },
    { date: "2025-01-30", rate: 0.64 },
  ],
  top_rec_rate: 0.285,
  total_queries: 47,
  total_runs: 1204,
  engine_breakdown: {
    openai: 0.72,
    anthropic: 0.58,
    perplexity: 0.81,
    gemini: 0.45,
  },
  sentiment_breakdown: {
    positive: 120,
    neutral: 80,
    negative: 15,
    mixed: 25,
  },
};

describe("DashboardOverview", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockBrandContext.brandId = "brand-1";
  });

  it("shows loading skeletons initially", () => {
    (api.getOverview as any).mockImplementation(
      () => new Promise(() => {}) // never resolves
    );

    render(<DashboardOverview />);

    const pulseElements = document.querySelectorAll(".animate-pulse");
    expect(pulseElements.length).toBeGreaterThan(0);
  });

  it("renders overview data when loaded", async () => {
    (api.getOverview as any).mockResolvedValue(mockOverview);

    render(<DashboardOverview />);

    await waitFor(() => {
      expect(screen.getByText("Overview")).toBeInTheDocument();
    });

    expect(screen.getByText("64.2%")).toBeInTheDocument();
    expect(screen.getByText("28.5%")).toBeInTheDocument();
    expect(screen.getByText("47")).toBeInTheDocument();
    expect(screen.getByText("1,204")).toBeInTheDocument();
  });

  it("shows empty state when no runs", async () => {
    (api.getOverview as any).mockResolvedValue({
      ...mockOverview,
      total_runs: 0,
    });

    render(<DashboardOverview />);

    await waitFor(() => {
      expect(screen.getByText("No data yet")).toBeInTheDocument();
    });
  });

  it("shows error state on API failure", async () => {
    (api.getOverview as any).mockRejectedValue(new Error("Server error"));

    render(<DashboardOverview />);

    await waitFor(() => {
      expect(screen.getByText("Failed to load dashboard")).toBeInTheDocument();
      expect(screen.getByText("Server error")).toBeInTheDocument();
    });
  });

  it("shows no brand selected when brandId is null", () => {
    mockBrandContext.brandId = null;

    render(<DashboardOverview />);

    expect(screen.getByText("No brand selected")).toBeInTheDocument();
  });

  it("shows export dropdown when data is loaded", async () => {
    (api.getOverview as any).mockResolvedValue(mockOverview);

    render(<DashboardOverview />);

    await waitFor(() => {
      expect(screen.getByTestId("export-dropdown")).toBeInTheDocument();
      expect(screen.getByText("Export for Notion")).toBeInTheDocument();
    });
  });

  it("renders chart section headers", async () => {
    (api.getOverview as any).mockResolvedValue(mockOverview);

    render(<DashboardOverview />);

    await waitFor(() => {
      expect(screen.getByText("Mention Rate Trend")).toBeInTheDocument();
      expect(screen.getByText("Sentiment Breakdown")).toBeInTheDocument();
      expect(screen.getByText("Mention Rate by Engine")).toBeInTheDocument();
    });
  });

  it("triggers scan on button click", async () => {
    (api.getOverview as any).mockResolvedValue(mockOverview);
    (api.triggerRun as any).mockResolvedValue({
      message: "Scan started successfully!",
    });

    render(<DashboardOverview />);

    await waitFor(() => {
      expect(screen.getByText("Run Scan Now")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText("Run Scan Now"));

    await waitFor(() => {
      expect(api.triggerRun).toHaveBeenCalledWith("brand-1");
    });
  });

  it("has retry button on error", async () => {
    (api.getOverview as any)
      .mockRejectedValueOnce(new Error("Fail"))
      .mockResolvedValueOnce(mockOverview);

    render(<DashboardOverview />);

    await waitFor(() => {
      expect(screen.getByText("Try again")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText("Try again"));

    await waitFor(() => {
      expect(api.getOverview).toHaveBeenCalledTimes(2);
    });
  });
});
