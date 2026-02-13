import jsPDF from "jspdf";
import autoTable from "jspdf-autotable";

// ── Types ───────────────────────────────────────────────────

interface OverviewData {
  mention_rate: number;
  mention_rate_trend: { date: string; rate: number }[];
  top_rec_rate: number;
  total_queries: number;
  total_runs: number;
  engine_breakdown: Record<string, number>;
  sentiment_breakdown: {
    positive: number;
    neutral: number;
    negative: number;
    mixed: number;
  };
}

const ENGINE_DISPLAY_NAMES: Record<string, string> = {
  openai: "ChatGPT",
  anthropic: "Claude",
  perplexity: "Perplexity",
  gemini: "Gemini",
};

// ── CSV Export ──────────────────────────────────────────────

function escapeCSV(value: string | number): string {
  const str = String(value);
  if (str.includes(",") || str.includes('"') || str.includes("\n")) {
    return `"${str.replace(/"/g, '""')}"`;
  }
  return str;
}

export function exportOverviewCSV(data: OverviewData, brandName: string) {
  const lines: string[] = [];

  // Header
  lines.push(`GeoTrack Report - ${brandName}`);
  lines.push(`Generated: ${new Date().toLocaleDateString()}`);
  lines.push("");

  // Scorecard
  lines.push("OVERVIEW");
  lines.push("Metric,Value");
  lines.push(`Mention Rate,${(data.mention_rate * 100).toFixed(1)}%`);
  lines.push(`Top Recommendation Rate,${(data.top_rec_rate * 100).toFixed(1)}%`);
  lines.push(`Total Queries,${data.total_queries}`);
  lines.push(`Total Runs,${data.total_runs}`);
  lines.push("");

  // Engine breakdown
  lines.push("ENGINE BREAKDOWN");
  lines.push("Engine,Mention Rate");
  Object.entries(data.engine_breakdown).forEach(([engine, rate]) => {
    const displayName = ENGINE_DISPLAY_NAMES[engine] || engine;
    lines.push(`${escapeCSV(displayName)},${(rate * 100).toFixed(1)}%`);
  });
  lines.push("");

  // Sentiment breakdown
  lines.push("SENTIMENT BREAKDOWN");
  lines.push("Sentiment,Count");
  Object.entries(data.sentiment_breakdown).forEach(([sentiment, count]) => {
    lines.push(
      `${sentiment.charAt(0).toUpperCase() + sentiment.slice(1)},${count}`
    );
  });
  lines.push("");

  // Mention rate trend
  lines.push("MENTION RATE TREND");
  lines.push("Date,Mention Rate");
  data.mention_rate_trend.forEach((d) => {
    lines.push(`${d.date},${(d.rate * 100).toFixed(1)}%`);
  });

  const csv = lines.join("\n");
  downloadFile(csv, `geotrack-${slugify(brandName)}-overview.csv`, "text/csv");
}

// ── PDF Export ──────────────────────────────────────────────

export function exportOverviewPDF(data: OverviewData, brandName: string) {
  const doc = new jsPDF();
  const pageWidth = doc.internal.pageSize.getWidth();
  let y = 20;

  // Title
  doc.setFontSize(20);
  doc.setFont("helvetica", "bold");
  doc.text("GeoTrack Report", 14, y);
  y += 10;

  doc.setFontSize(12);
  doc.setFont("helvetica", "normal");
  doc.setTextColor(100);
  doc.text(brandName, 14, y);
  y += 7;

  doc.setFontSize(9);
  doc.text(`Generated: ${new Date().toLocaleDateString()}`, 14, y);
  doc.setTextColor(0);
  y += 12;

  // Separator line
  doc.setDrawColor(200);
  doc.line(14, y, pageWidth - 14, y);
  y += 10;

  // Scorecard section
  doc.setFontSize(14);
  doc.setFont("helvetica", "bold");
  doc.text("Overview", 14, y);
  y += 8;

  autoTable(doc, {
    startY: y,
    head: [["Metric", "Value"]],
    body: [
      ["Mention Rate", `${(data.mention_rate * 100).toFixed(1)}%`],
      ["Top Recommendation Rate", `${(data.top_rec_rate * 100).toFixed(1)}%`],
      ["Total Queries", String(data.total_queries)],
      ["Total Runs", String(data.total_runs)],
    ],
    theme: "striped",
    headStyles: { fillColor: [37, 99, 235] },
    margin: { left: 14, right: 14 },
  });

  y = (doc as any).lastAutoTable.finalY + 14;

  // Engine breakdown
  doc.setFontSize(14);
  doc.setFont("helvetica", "bold");
  doc.text("Engine Breakdown", 14, y);
  y += 8;

  const engineRows = Object.entries(data.engine_breakdown).map(
    ([engine, rate]) => [
      ENGINE_DISPLAY_NAMES[engine] || engine,
      `${(rate * 100).toFixed(1)}%`,
    ]
  );

  autoTable(doc, {
    startY: y,
    head: [["Engine", "Mention Rate"]],
    body: engineRows,
    theme: "striped",
    headStyles: { fillColor: [37, 99, 235] },
    margin: { left: 14, right: 14 },
  });

  y = (doc as any).lastAutoTable.finalY + 14;

  // Sentiment breakdown
  doc.setFontSize(14);
  doc.setFont("helvetica", "bold");
  doc.text("Sentiment Breakdown", 14, y);
  y += 8;

  const sentimentRows = Object.entries(data.sentiment_breakdown).map(
    ([sentiment, count]) => [
      sentiment.charAt(0).toUpperCase() + sentiment.slice(1),
      String(count),
    ]
  );

  autoTable(doc, {
    startY: y,
    head: [["Sentiment", "Count"]],
    body: sentimentRows,
    theme: "striped",
    headStyles: { fillColor: [37, 99, 235] },
    margin: { left: 14, right: 14 },
  });

  y = (doc as any).lastAutoTable.finalY + 14;

  // Mention rate trend
  if (data.mention_rate_trend.length > 0) {
    // Check if we need a new page
    if (y > 220) {
      doc.addPage();
      y = 20;
    }

    doc.setFontSize(14);
    doc.setFont("helvetica", "bold");
    doc.text("Mention Rate Trend", 14, y);
    y += 8;

    const trendRows = data.mention_rate_trend.map((d) => [
      d.date,
      `${(d.rate * 100).toFixed(1)}%`,
    ]);

    autoTable(doc, {
      startY: y,
      head: [["Date", "Mention Rate"]],
      body: trendRows,
      theme: "striped",
      headStyles: { fillColor: [37, 99, 235] },
      margin: { left: 14, right: 14 },
    });
  }

  doc.save(`geotrack-${slugify(brandName)}-overview.pdf`);
}

// ── Helpers ─────────────────────────────────────────────────

function slugify(text: string): string {
  return text
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "");
}

function downloadFile(content: string, filename: string, mimeType: string) {
  const blob = new Blob([content], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}
