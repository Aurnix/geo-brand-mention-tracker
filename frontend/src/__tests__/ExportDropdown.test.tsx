import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import ExportDropdown from "@/components/ExportDropdown";
import * as exportUtils from "@/lib/export";

vi.mock("@/lib/export", () => ({
  exportOverviewCSV: vi.fn(),
  exportOverviewPDF: vi.fn(),
}));

const mockData = {
  mention_rate: 0.642,
  mention_rate_trend: [{ date: "2025-01-01", rate: 0.6 }],
  top_rec_rate: 0.285,
  total_queries: 47,
  total_runs: 1204,
  engine_breakdown: { openai: 0.72 },
  sentiment_breakdown: { positive: 120, neutral: 80, negative: 15, mixed: 25 },
};

describe("ExportDropdown", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders the export button", () => {
    render(<ExportDropdown data={mockData} brandName="Notion" />);
    expect(screen.getByText("Export")).toBeInTheDocument();
  });

  it("shows dropdown menu on click", () => {
    render(<ExportDropdown data={mockData} brandName="Notion" />);
    fireEvent.click(screen.getByText("Export"));

    expect(screen.getByText("Export as CSV")).toBeInTheDocument();
    expect(screen.getByText("Export as PDF")).toBeInTheDocument();
  });

  it("calls exportOverviewCSV when CSV option clicked", () => {
    render(<ExportDropdown data={mockData} brandName="Notion" />);
    fireEvent.click(screen.getByText("Export"));
    fireEvent.click(screen.getByText("Export as CSV"));

    expect(exportUtils.exportOverviewCSV).toHaveBeenCalledWith(
      mockData,
      "Notion"
    );
  });

  it("calls exportOverviewPDF when PDF option clicked", () => {
    render(<ExportDropdown data={mockData} brandName="Notion" />);
    fireEvent.click(screen.getByText("Export"));
    fireEvent.click(screen.getByText("Export as PDF"));

    expect(exportUtils.exportOverviewPDF).toHaveBeenCalledWith(
      mockData,
      "Notion"
    );
  });

  it("closes dropdown after selecting an option", () => {
    render(<ExportDropdown data={mockData} brandName="Notion" />);
    fireEvent.click(screen.getByText("Export"));
    fireEvent.click(screen.getByText("Export as CSV"));

    expect(screen.queryByText("Export as PDF")).not.toBeInTheDocument();
  });

  it("closes dropdown on outside click", () => {
    render(
      <div>
        <span data-testid="outside">Outside</span>
        <ExportDropdown data={mockData} brandName="Notion" />
      </div>
    );

    fireEvent.click(screen.getByText("Export"));
    expect(screen.getByText("Export as CSV")).toBeInTheDocument();

    fireEvent.mouseDown(screen.getByTestId("outside"));
    expect(screen.queryByText("Export as CSV")).not.toBeInTheDocument();
  });
});
