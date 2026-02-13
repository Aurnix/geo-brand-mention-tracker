"use client";

import { useState, useEffect, useCallback } from "react";
import { api } from "@/lib/api";
import { useBrand } from "./layout";
import {
  TrendingUp,
  TrendingDown,
  BarChart3,
  Star,
  Search,
  Activity,
  Zap,
  Loader2,
  AlertCircle,
  Inbox,
} from "lucide-react";
import ExportDropdown from "@/components/ExportDropdown";
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";

// ── Types ───────────────────────────────────────────────────

interface OverviewData {
  mention_rate: number;
  mention_rate_trend: { date: string; rate: number }[];
  top_rec_rate: number;
  total_queries: number;
  total_runs: number;
  engine_breakdown: Record<string, number>;
  sentiment_breakdown: { positive: number; neutral: number; negative: number; mixed: number };
}

// ── Skeleton components ─────────────────────────────────────

function CardSkeleton() {
  return (
    <div className="card animate-pulse">
      <div className="h-3 w-20 rounded bg-gray-200" />
      <div className="mt-3 h-8 w-24 rounded bg-gray-200" />
      <div className="mt-2 h-3 w-16 rounded bg-gray-200" />
    </div>
  );
}

function ChartSkeleton({ height = 300 }: { height?: number }) {
  return (
    <div className="card animate-pulse" style={{ height }}>
      <div className="h-4 w-32 rounded bg-gray-200" />
      <div className="mt-6 flex h-48 items-end gap-2">
        {Array.from({ length: 12 }).map((_, i) => (
          <div
            key={i}
            className="flex-1 rounded-t bg-gray-200"
            style={{ height: `${20 + Math.random() * 60}%` }}
          />
        ))}
      </div>
    </div>
  );
}

// ── Color constants ─────────────────────────────────────────

const SENTIMENT_COLORS: Record<string, string> = {
  positive: "#22c55e",
  neutral: "#94a3b8",
  negative: "#ef4444",
  mixed: "#f59e0b",
};

const ENGINE_DISPLAY_NAMES: Record<string, string> = {
  openai: "ChatGPT",
  anthropic: "Claude",
  perplexity: "Perplexity",
  gemini: "Gemini",
};

// ── Main page ───────────────────────────────────────────────

export default function DashboardOverview() {
  const { brandId, brands } = useBrand();
  const brandName = brands.find((b) => b.id === brandId)?.name || "Brand";
  const [data, setData] = useState<OverviewData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [runLoading, setRunLoading] = useState(false);
  const [runMessage, setRunMessage] = useState("");

  const fetchOverview = useCallback(async () => {
    if (!brandId) return;
    setLoading(true);
    setError("");

    try {
      const result = await api.getOverview(brandId);
      setData(result as OverviewData);
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Failed to load overview";
      setError(message);
    } finally {
      setLoading(false);
    }
  }, [brandId]);

  useEffect(() => {
    fetchOverview();
  }, [fetchOverview]);

  const handleRunScan = async () => {
    if (!brandId) return;
    setRunLoading(true);
    setRunMessage("");
    try {
      const result = await api.triggerRun(brandId);
      setRunMessage(result.message || "Scan started successfully!");
      // Refresh data after a short delay
      setTimeout(fetchOverview, 3000);
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Failed to trigger scan";
      setRunMessage(message);
    } finally {
      setRunLoading(false);
    }
  };

  // ── Loading state ───────────────────────────────
  if (!brandId) {
    return (
      <div className="flex flex-col items-center justify-center py-24 text-center">
        <Inbox className="h-12 w-12 text-gray-300" />
        <h3 className="mt-4 text-lg font-semibold text-gray-900">
          No brand selected
        </h3>
        <p className="mt-1 text-sm text-gray-500">
          Create a brand in the onboarding flow to get started.
        </p>
      </div>
    );
  }

  if (loading) {
    return (
      <div>
        <div className="mb-6 flex items-center justify-between">
          <div>
            <div className="h-7 w-40 animate-pulse rounded bg-gray-200" />
            <div className="mt-1 h-4 w-64 animate-pulse rounded bg-gray-200" />
          </div>
        </div>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <CardSkeleton />
          <CardSkeleton />
          <CardSkeleton />
          <CardSkeleton />
        </div>
        <div className="mt-6 grid grid-cols-1 gap-6 lg:grid-cols-3">
          <div className="lg:col-span-2">
            <ChartSkeleton />
          </div>
          <ChartSkeleton />
        </div>
      </div>
    );
  }

  // ── Error state ─────────────────────────────────
  if (error) {
    return (
      <div className="flex flex-col items-center justify-center py-24 text-center">
        <AlertCircle className="h-12 w-12 text-red-400" />
        <h3 className="mt-4 text-lg font-semibold text-gray-900">
          Failed to load dashboard
        </h3>
        <p className="mt-1 text-sm text-gray-500">{error}</p>
        <button onClick={fetchOverview} className="btn-primary mt-4">
          Try again
        </button>
      </div>
    );
  }

  // ── Empty state ─────────────────────────────────
  if (!data || data.total_runs === 0) {
    return (
      <div>
        <div className="mb-6 flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Overview</h1>
            <p className="mt-1 text-sm text-gray-500">
              Your brand visibility dashboard
            </p>
          </div>
          <button
            onClick={handleRunScan}
            disabled={runLoading}
            className="btn-primary inline-flex items-center gap-2"
          >
            {runLoading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Zap className="h-4 w-4" />
            )}
            Run Scan Now
          </button>
        </div>
        <div className="flex flex-col items-center justify-center rounded-xl border-2 border-dashed border-gray-200 py-24 text-center">
          <Activity className="h-12 w-12 text-gray-300" />
          <h3 className="mt-4 text-lg font-semibold text-gray-900">
            No data yet
          </h3>
          <p className="mx-auto mt-1 max-w-sm text-sm text-gray-500">
            Run your first scan to start tracking your brand's AI visibility.
            Results will appear here within a few minutes.
          </p>
          <button
            onClick={handleRunScan}
            disabled={runLoading}
            className="btn-primary mt-6 inline-flex items-center gap-2"
          >
            {runLoading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Zap className="h-4 w-4" />
            )}
            Run your first scan
          </button>
        </div>
      </div>
    );
  }

  // ── Format chart data ───────────────────────────
  const trendData = data.mention_rate_trend.map((d) => ({
    date: new Date(d.date).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
    }),
    mention_rate: Math.round(d.rate * 10000) / 100,
  }));

  const engineData = Object.entries(data.engine_breakdown).map(([engine, rate]) => ({
    engine: ENGINE_DISPLAY_NAMES[engine] || engine,
    mention_rate: Math.round(rate * 10000) / 100,
  }));

  const sentimentData = Object.entries(data.sentiment_breakdown).map(([sentiment, count]) => ({
    name: sentiment.charAt(0).toUpperCase() + sentiment.slice(1),
    value: count,
    color: SENTIMENT_COLORS[sentiment] || "#94a3b8",
  }));

  // Compute trend: compare second-half average vs first-half average
  const trendPoints = data.mention_rate_trend;
  const mid = Math.floor(trendPoints.length / 2);
  const recentAvg =
    trendPoints.length > 0
      ? trendPoints.slice(mid).reduce((s, d) => s + d.rate, 0) /
        (trendPoints.length - mid)
      : 0;
  const olderAvg =
    mid > 0
      ? trendPoints.slice(0, mid).reduce((s, d) => s + d.rate, 0) / mid
      : recentAvg;
  const trendDelta = (recentAvg - olderAvg) * 100;
  const trendDirection = trendDelta >= 0;

  return (
    <div>
      {/* ── Header ───────────────────────────────────── */}
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Overview</h1>
          <p className="mt-1 text-sm text-gray-500">
            Your brand visibility across AI engines
          </p>
        </div>
        <div className="flex items-center gap-3">
          {runMessage && (
            <span className="text-sm text-gray-500">{runMessage}</span>
          )}
          {data && <ExportDropdown data={data} brandName={brandName} />}
          <button
            onClick={handleRunScan}
            disabled={runLoading}
            className="btn-primary inline-flex items-center gap-2"
          >
            {runLoading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Zap className="h-4 w-4" />
            )}
            Run Scan Now
          </button>
        </div>
      </div>

      {/* ── Scorecard row ────────────────────────────── */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {/* Mention Rate */}
        <div className="card">
          <div className="flex items-center gap-2 text-sm font-medium text-gray-500">
            <BarChart3 className="h-4 w-4" />
            Mention Rate
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-3xl font-bold text-gray-900">
              {(data.mention_rate * 100).toFixed(1)}%
            </span>
            <span
              className={`inline-flex items-center gap-0.5 text-sm font-medium ${
                trendDirection ? "text-green-600" : "text-red-600"
              }`}
            >
              {trendDirection ? (
                <TrendingUp className="h-4 w-4" />
              ) : (
                <TrendingDown className="h-4 w-4" />
              )}
              {Math.abs(trendDelta).toFixed(1)}%
            </span>
          </div>
          <p className="mt-1 text-xs text-gray-400">vs previous period</p>
        </div>

        {/* Top Recommendation Rate */}
        <div className="card">
          <div className="flex items-center gap-2 text-sm font-medium text-gray-500">
            <Star className="h-4 w-4" />
            Top Recommendation
          </div>
          <div className="mt-2">
            <span className="text-3xl font-bold text-gray-900">
              {(data.top_rec_rate * 100).toFixed(1)}%
            </span>
          </div>
          <p className="mt-1 text-xs text-gray-400">
            of queries where you are #1 pick
          </p>
        </div>

        {/* Total Queries */}
        <div className="card">
          <div className="flex items-center gap-2 text-sm font-medium text-gray-500">
            <Search className="h-4 w-4" />
            Total Queries
          </div>
          <div className="mt-2">
            <span className="text-3xl font-bold text-gray-900">
              {data.total_queries}
            </span>
          </div>
          <p className="mt-1 text-xs text-gray-400">active monitored queries</p>
        </div>

        {/* Total Runs */}
        <div className="card">
          <div className="flex items-center gap-2 text-sm font-medium text-gray-500">
            <Activity className="h-4 w-4" />
            Total Runs
          </div>
          <div className="mt-2">
            <span className="text-3xl font-bold text-gray-900">
              {data.total_runs.toLocaleString()}
            </span>
          </div>
          <p className="mt-1 text-xs text-gray-400">query results collected</p>
        </div>
      </div>

      {/* ── Charts row ───────────────────────────────── */}
      <div className="mt-6 grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Trend line chart */}
        <div className="card lg:col-span-2">
          <h3 className="text-sm font-semibold text-gray-900">
            Mention Rate Trend
          </h3>
          <p className="mt-0.5 text-xs text-gray-500">Last 30 days</p>
          <div className="mt-4 h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={trendData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis
                  dataKey="date"
                  tick={{ fontSize: 12, fill: "#94a3b8" }}
                  axisLine={{ stroke: "#e2e8f0" }}
                  tickLine={false}
                />
                <YAxis
                  tick={{ fontSize: 12, fill: "#94a3b8" }}
                  axisLine={{ stroke: "#e2e8f0" }}
                  tickLine={false}
                  tickFormatter={(value) => `${value}%`}
                />
                <Tooltip
                  contentStyle={{
                    borderRadius: "8px",
                    border: "1px solid #e2e8f0",
                    boxShadow: "0 4px 6px -1px rgb(0 0 0 / 0.1)",
                  }}
                  formatter={(value: number) => [`${value}%`, "Mention Rate"]}
                />
                <Line
                  type="monotone"
                  dataKey="mention_rate"
                  stroke="#2563eb"
                  strokeWidth={2.5}
                  dot={false}
                  activeDot={{ r: 5, fill: "#2563eb" }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Sentiment donut */}
        <div className="card">
          <h3 className="text-sm font-semibold text-gray-900">
            Sentiment Breakdown
          </h3>
          <p className="mt-0.5 text-xs text-gray-500">
            How AI engines describe your brand
          </p>
          <div className="mt-4 h-64">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={sentimentData}
                  cx="50%"
                  cy="45%"
                  innerRadius={55}
                  outerRadius={80}
                  paddingAngle={3}
                  dataKey="value"
                >
                  {sentimentData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    borderRadius: "8px",
                    border: "1px solid #e2e8f0",
                    boxShadow: "0 4px 6px -1px rgb(0 0 0 / 0.1)",
                  }}
                />
                <Legend
                  verticalAlign="bottom"
                  height={36}
                  iconType="circle"
                  iconSize={8}
                  formatter={(value) => (
                    <span className="text-xs text-gray-600">{value}</span>
                  )}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* ── Engine breakdown ─────────────────────────── */}
      <div className="mt-6">
        <div className="card">
          <h3 className="text-sm font-semibold text-gray-900">
            Mention Rate by Engine
          </h3>
          <p className="mt-0.5 text-xs text-gray-500">
            How often each AI engine mentions your brand
          </p>
          <div className="mt-4 h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={engineData} barSize={48}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis
                  dataKey="engine"
                  tick={{ fontSize: 12, fill: "#94a3b8" }}
                  axisLine={{ stroke: "#e2e8f0" }}
                  tickLine={false}
                />
                <YAxis
                  tick={{ fontSize: 12, fill: "#94a3b8" }}
                  axisLine={{ stroke: "#e2e8f0" }}
                  tickLine={false}
                  tickFormatter={(value) => `${value}%`}
                />
                <Tooltip
                  contentStyle={{
                    borderRadius: "8px",
                    border: "1px solid #e2e8f0",
                    boxShadow: "0 4px 6px -1px rgb(0 0 0 / 0.1)",
                  }}
                  formatter={(value: number) => [`${value}%`, "Mention Rate"]}
                />
                <Bar
                  dataKey="mention_rate"
                  fill="#2563eb"
                  radius={[6, 6, 0, 0]}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
}
