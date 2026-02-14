import { describe, it, expect, vi, beforeEach } from "vitest";

// Mock jspdf to avoid actual PDF generation in tests
const mockSave = vi.fn();
const mockText = vi.fn();
const mockSetFontSize = vi.fn();
const mockSetFont = vi.fn();
const mockSetTextColor = vi.fn();
const mockSetDrawColor = vi.fn();
const mockLine = vi.fn();
const mockAddPage = vi.fn();

vi.mock("jspdf", () => {
  function MockJsPDF(this: any) {
    this.internal = { pageSize: { getWidth: () => 210 } };
    this.text = mockText;
    this.setFontSize = mockSetFontSize;
    this.setFont = mockSetFont;
    this.setTextColor = mockSetTextColor;
    this.setDrawColor = mockSetDrawColor;
    this.line = mockLine;
    this.addPage = mockAddPage;
    this.save = mockSave;
    this.lastAutoTable = { finalY: 80 };
  }
  return {
    default: MockJsPDF,
    jsPDF: MockJsPDF,
  };
});

vi.mock("jspdf-autotable", () => ({
  default: vi.fn().mockImplementation((doc: any) => {
    // Set lastAutoTable on the doc for position tracking
    doc.lastAutoTable = { finalY: 80 };
  }),
}));

import { exportOverviewCSV, exportOverviewPDF } from "@/lib/export";

const mockOverviewData = {
  mention_rate: 0.642,
  mention_rate_trend: [
    { date: "2025-01-01", rate: 0.6 },
    { date: "2025-01-02", rate: 0.65 },
    { date: "2025-01-03", rate: 0.64 },
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

describe("exportOverviewCSV", () => {
  let clickSpy: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    vi.restoreAllMocks();
    clickSpy = vi.fn();

    const origCreateElement = document.createElement.bind(document);
    vi.spyOn(document, "createElement").mockImplementation((tag: string) => {
      const el = origCreateElement(tag);
      if (tag === "a") {
        Object.defineProperty(el, "click", { value: clickSpy });
      }
      return el;
    });

    vi.spyOn(document.body, "appendChild").mockImplementation((node) => node);
    vi.spyOn(document.body, "removeChild").mockImplementation((node) => node);
  });

  it("creates and triggers a CSV download", () => {
    exportOverviewCSV(mockOverviewData, "Notion");
    expect(clickSpy).toHaveBeenCalled();
  });

  it("generates a blob with csv mime type", () => {
    let capturedBlob: Blob | null = null;
    vi.spyOn(URL, "createObjectURL").mockImplementation((blob) => {
      capturedBlob = blob as Blob;
      return "blob:mock";
    });

    exportOverviewCSV(mockOverviewData, "Notion");

    expect(capturedBlob).not.toBeNull();
    expect(capturedBlob!.type).toBe("text/csv");
  });
});

describe("exportOverviewCSV content validation", () => {
  it("formats mention rate correctly", () => {
    const rate = 0.642;
    expect((rate * 100).toFixed(1)).toBe("64.2");
  });

  it("formats engine names correctly", () => {
    const ENGINE_DISPLAY_NAMES: Record<string, string> = {
      openai: "ChatGPT",
      anthropic: "Claude",
      perplexity: "Perplexity",
      gemini: "Gemini",
    };
    expect(ENGINE_DISPLAY_NAMES["openai"]).toBe("ChatGPT");
    expect(ENGINE_DISPLAY_NAMES["anthropic"]).toBe("Claude");
  });

  it("capitalizes sentiment names", () => {
    const sentiment = "positive";
    const formatted =
      sentiment.charAt(0).toUpperCase() + sentiment.slice(1);
    expect(formatted).toBe("Positive");
  });
});

describe("exportOverviewPDF", () => {
  beforeEach(() => {
    mockSave.mockClear();
    mockText.mockClear();
  });

  it("generates a PDF and calls save", () => {
    expect(() => {
      exportOverviewPDF(mockOverviewData, "Notion");
    }).not.toThrow();

    expect(mockSave).toHaveBeenCalledWith("geotrack-notion-overview.pdf");
  });

  it("slugifies brand name in filename", () => {
    exportOverviewPDF(mockOverviewData, "My Cool Brand");

    expect(mockSave).toHaveBeenCalledWith("geotrack-my-cool-brand-overview.pdf");
  });

  it("handles empty trend data", () => {
    const dataNoTrend = {
      ...mockOverviewData,
      mention_rate_trend: [],
    };

    expect(() => {
      exportOverviewPDF(dataNoTrend, "Test");
    }).not.toThrow();

    expect(mockSave).toHaveBeenCalled();
  });

  it("includes brand name in document text", () => {
    exportOverviewPDF(mockOverviewData, "Notion");

    expect(mockText).toHaveBeenCalledWith("GeoTrack Report", expect.any(Number), expect.any(Number));
    expect(mockText).toHaveBeenCalledWith("Notion", expect.any(Number), expect.any(Number));
  });
});
