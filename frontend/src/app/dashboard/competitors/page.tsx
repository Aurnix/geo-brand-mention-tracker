"use client";

import { useState, useEffect, useCallback } from "react";
import { api } from "@/lib/api";
import { useBrand } from "../layout";
import {
  Users,
  Plus,
  Trash2,
  Loader2,
  AlertCircle,
  Inbox,
  X,
  Trophy,
  Minus,
} from "lucide-react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";

// ── Types ───────────────────────────────────────────────────

interface Competitor {
  id: string;
  brand_id: string;
  name: string;
  aliases: string[];
}

interface CompetitorComparison {
  brand: { name: string; mention_rate: number };
  competitors: { name: string; mention_rate: number }[];
  query_winners: {
    query_text: string;
    winners: Record<string, string | null>;
  }[];
}

const ENGINE_DISPLAY: Record<string, string> = {
  openai: "ChatGPT",
  anthropic: "Claude",
  perplexity: "Perplexity",
  gemini: "Gemini",
};

const ENGINES = ["openai", "anthropic", "perplexity", "gemini"] as const;

const BAR_COLORS = [
  "#2563eb", // brand — blue
  "#f59e0b", // competitor 1 — amber
  "#ef4444", // competitor 2 — red
  "#22c55e", // competitor 3 — green
  "#8b5cf6", // competitor 4 — purple
  "#ec4899", // competitor 5 — pink
  "#14b8a6", // competitor 6 — teal
  "#f97316", // competitor 7 — orange
];

// ── Skeleton ────────────────────────────────────────────────

function ChartSkeleton() {
  return (
    <div className="card animate-pulse">
      <div className="h-4 w-48 rounded bg-gray-200" />
      <div className="mt-6 flex h-64 items-end gap-4">
        {Array.from({ length: 5 }).map((_, i) => (
          <div key={i} className="flex flex-1 items-end gap-1">
            <div
              className="flex-1 rounded-t bg-gray-200"
              style={{ height: `${30 + Math.random() * 50}%` }}
            />
            <div
              className="flex-1 rounded-t bg-gray-100"
              style={{ height: `${20 + Math.random() * 40}%` }}
            />
          </div>
        ))}
      </div>
    </div>
  );
}

function TableSkeleton() {
  return (
    <div className="card animate-pulse">
      <div className="h-4 w-48 rounded bg-gray-200" />
      <div className="mt-6 space-y-3">
        {Array.from({ length: 5 }).map((_, i) => (
          <div key={i} className="flex items-center gap-4">
            <div className="h-4 flex-1 rounded bg-gray-200" />
            <div className="h-4 w-20 rounded bg-gray-200" />
            <div className="h-4 w-20 rounded bg-gray-200" />
            <div className="h-4 w-20 rounded bg-gray-200" />
            <div className="h-4 w-20 rounded bg-gray-200" />
          </div>
        ))}
      </div>
    </div>
  );
}

// ── Winner badge ────────────────────────────────────────────

function WinnerBadge({
  winner,
  brandName,
}: {
  winner: string | null;
  brandName: string;
}) {
  if (!winner) {
    return (
      <span className="inline-flex items-center gap-1 text-xs text-gray-400">
        <Minus className="h-3 w-3" />
        None
      </span>
    );
  }

  const isYourBrand = winner.toLowerCase() === brandName.toLowerCase();

  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium ${
        isYourBrand
          ? "bg-green-100 text-green-700"
          : "bg-gray-100 text-gray-700"
      }`}
    >
      {isYourBrand && <Trophy className="h-3 w-3" />}
      {winner}
    </span>
  );
}

// ── Main page ───────────────────────────────────────────────

export default function CompetitorsPage() {
  const { brandId } = useBrand();

  const [competitors, setCompetitors] = useState<Competitor[]>([]);
  const [comparison, setComparison] = useState<CompetitorComparison | null>(
    null
  );
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // Add competitor
  const [showAddForm, setShowAddForm] = useState(false);
  const [newName, setNewName] = useState("");
  const [addLoading, setAddLoading] = useState(false);

  // Delete
  const [deleteLoading, setDeleteLoading] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    if (!brandId) return;
    setLoading(true);
    setError("");

    try {
      const [competitorsData, comparisonData] = await Promise.all([
        api.getCompetitors(brandId),
        api.getCompetitorComparison(brandId).catch(() => null),
      ]);
      setCompetitors(competitorsData as Competitor[]);
      setComparison(comparisonData as CompetitorComparison | null);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to load competitors"
      );
    } finally {
      setLoading(false);
    }
  }, [brandId]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleAddCompetitor = async () => {
    if (!brandId || !newName.trim()) return;
    setAddLoading(true);
    setError("");

    try {
      await api.addCompetitor(brandId, { name: newName.trim() });
      setNewName("");
      setShowAddForm(false);
      await fetchData();
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to add competitor"
      );
    } finally {
      setAddLoading(false);
    }
  };

  const handleDeleteCompetitor = async (competitorId: string) => {
    setDeleteLoading(competitorId);
    setError("");

    try {
      await api.deleteCompetitor(competitorId);
      setCompetitors((prev) => prev.filter((c) => c.id !== competitorId));
      // Refresh comparison data
      if (brandId) {
        const comparisonData = await api
          .getCompetitorComparison(brandId)
          .catch(() => null);
        setComparison(comparisonData as CompetitorComparison | null);
      }
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to remove competitor"
      );
    } finally {
      setDeleteLoading(null);
    }
  };

  // ── No brand ───────────────────────────────────
  if (!brandId) {
    return (
      <div className="flex flex-col items-center justify-center py-24 text-center">
        <Inbox className="h-12 w-12 text-gray-300" />
        <h3 className="mt-4 text-lg font-semibold text-gray-900">
          No brand selected
        </h3>
        <p className="mt-1 text-sm text-gray-500">
          Create a brand to start tracking competitors.
        </p>
      </div>
    );
  }

  // ── Loading ────────────────────────────────────
  if (loading) {
    return (
      <div>
        <div className="mb-6 flex items-center justify-between">
          <div>
            <div className="h-7 w-40 animate-pulse rounded bg-gray-200" />
            <div className="mt-1 h-4 w-64 animate-pulse rounded bg-gray-200" />
          </div>
        </div>
        <ChartSkeleton />
        <div className="mt-6">
          <TableSkeleton />
        </div>
      </div>
    );
  }

  // ── Error state ────────────────────────────────
  if (error && competitors.length === 0 && !comparison) {
    return (
      <div className="flex flex-col items-center justify-center py-24 text-center">
        <AlertCircle className="h-12 w-12 text-red-400" />
        <h3 className="mt-4 text-lg font-semibold text-gray-900">
          Failed to load competitors
        </h3>
        <p className="mt-1 text-sm text-gray-500">{error}</p>
        <button onClick={fetchData} className="btn-primary mt-4">
          Try again
        </button>
      </div>
    );
  }

  // ── Build chart data ───────────────────────────
  const chartData =
    comparison
      ? [
          {
            name: comparison.brand.name,
            mention_rate: Math.round(comparison.brand.mention_rate * 100) / 100,
          },
          ...comparison.competitors.map((c) => ({
            name: c.name,
            mention_rate: Math.round(c.mention_rate * 100) / 100,
          })),
        ]
      : [];

  const brandName = comparison?.brand.name || "";

  return (
    <div>
      {/* ── Header ───────────────────────────────── */}
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Competitors</h1>
          <p className="mt-1 text-sm text-gray-500">
            Compare your AI visibility against competitors
          </p>
        </div>
        <button
          onClick={() => setShowAddForm(true)}
          className="btn-primary inline-flex items-center gap-1.5"
        >
          <Plus className="h-4 w-4" />
          Add Competitor
        </button>
      </div>

      {/* Error banner */}
      {error && (
        <div className="mb-4 flex items-start gap-3 rounded-lg border border-red-200 bg-red-50 p-3">
          <AlertCircle className="mt-0.5 h-4 w-4 flex-shrink-0 text-red-600" />
          <p className="text-sm text-red-700">{error}</p>
          <button onClick={() => setError("")} className="ml-auto">
            <X className="h-4 w-4 text-red-400" />
          </button>
        </div>
      )}

      {/* ── Add competitor form (inline) ─────────── */}
      {showAddForm && (
        <div className="mb-6 rounded-lg border border-gray-200 bg-white p-4">
          <div className="flex items-end gap-3">
            <div className="flex-1">
              <label className="block text-sm font-medium text-gray-700">
                Competitor name
              </label>
              <input
                type="text"
                value={newName}
                onChange={(e) => setNewName(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") handleAddCompetitor();
                }}
                className="input-field mt-1.5"
                placeholder="e.g. Salesforce"
                autoFocus
              />
            </div>
            <button
              onClick={handleAddCompetitor}
              disabled={addLoading || !newName.trim()}
              className="btn-primary inline-flex items-center gap-1.5"
            >
              {addLoading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Plus className="h-4 w-4" />
              )}
              Add
            </button>
            <button
              onClick={() => {
                setShowAddForm(false);
                setNewName("");
              }}
              className="btn-secondary"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* ── Empty state ──────────────────────────── */}
      {competitors.length === 0 ? (
        <div className="flex flex-col items-center justify-center rounded-xl border-2 border-dashed border-gray-200 py-24 text-center">
          <Users className="h-12 w-12 text-gray-300" />
          <h3 className="mt-4 text-lg font-semibold text-gray-900">
            No competitors tracked
          </h3>
          <p className="mx-auto mt-1 max-w-sm text-sm text-gray-500">
            Add competitors to see how your brand stacks up in AI engine
            recommendations.
          </p>
          <button
            onClick={() => setShowAddForm(true)}
            className="btn-primary mt-6 inline-flex items-center gap-2"
          >
            <Plus className="h-4 w-4" />
            Add your first competitor
          </button>
        </div>
      ) : (
        <>
          {/* ── Competitor list ───────────────────────── */}
          <div className="mb-6">
            <div className="card">
              <h3 className="text-sm font-semibold text-gray-900">
                Tracked Competitors ({competitors.length})
              </h3>
              <div className="mt-3 flex flex-wrap gap-2">
                {competitors.map((c) => (
                  <div
                    key={c.id}
                    className="inline-flex items-center gap-2 rounded-full border border-gray-200 bg-gray-50 py-1.5 pl-3 pr-1.5"
                  >
                    <span className="text-sm font-medium text-gray-700">
                      {c.name}
                    </span>
                    {c.aliases && c.aliases.length > 0 && (
                      <span className="text-xs text-gray-400">
                        ({c.aliases.join(", ")})
                      </span>
                    )}
                    <button
                      onClick={() => handleDeleteCompetitor(c.id)}
                      disabled={deleteLoading === c.id}
                      className="rounded-full p-1 text-gray-400 transition-colors hover:bg-red-50 hover:text-red-600"
                      title="Remove competitor"
                    >
                      {deleteLoading === c.id ? (
                        <Loader2 className="h-3.5 w-3.5 animate-spin" />
                      ) : (
                        <X className="h-3.5 w-3.5" />
                      )}
                    </button>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* ── Mention rate comparison chart ─────────── */}
          {comparison && chartData.length > 0 ? (
            <>
              <div className="card">
                <h3 className="text-sm font-semibold text-gray-900">
                  Mention Rate Comparison
                </h3>
                <p className="mt-0.5 text-xs text-gray-500">
                  How often each brand is mentioned across all AI engines
                </p>
                <div className="mt-4 h-80">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={chartData} barSize={52}>
                      <CartesianGrid
                        strokeDasharray="3 3"
                        stroke="#f1f5f9"
                      />
                      <XAxis
                        dataKey="name"
                        tick={{ fontSize: 12, fill: "#64748b" }}
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
                        formatter={(value: number) => [
                          `${value}%`,
                          "Mention Rate",
                        ]}
                      />
                      <Bar dataKey="mention_rate" radius={[6, 6, 0, 0]}>
                        {chartData.map((_, index) => (
                          <Cell
                            key={`cell-${index}`}
                            fill={BAR_COLORS[index % BAR_COLORS.length]}
                          />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>

              {/* ── Query winners table ─────────────────── */}
              {comparison.query_winners &&
                comparison.query_winners.length > 0 && (
                  <div className="mt-6">
                    <div className="card overflow-hidden p-0">
                      <div className="px-6 py-4">
                        <h3 className="text-sm font-semibold text-gray-900">
                          Top Recommendation Winners
                        </h3>
                        <p className="mt-0.5 text-xs text-gray-500">
                          Which brand gets the top recommendation for each query
                          per engine
                        </p>
                      </div>

                      <div className="overflow-x-auto">
                        <table className="w-full">
                          <thead>
                            <tr className="border-t border-b border-gray-200 bg-gray-50">
                              <th className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500">
                                Query
                              </th>
                              {ENGINES.map((e) => (
                                <th
                                  key={e}
                                  className="px-4 py-3 text-center text-xs font-semibold uppercase tracking-wider text-gray-500"
                                >
                                  {ENGINE_DISPLAY[e]}
                                </th>
                              ))}
                            </tr>
                          </thead>
                          <tbody>
                            {comparison.query_winners.map((qw, index) => (
                              <tr
                                key={index}
                                className={`border-b border-gray-100 ${
                                  index % 2 === 1
                                    ? "bg-gray-50/50"
                                    : "bg-white"
                                }`}
                              >
                                <td className="px-6 py-3">
                                  <span className="text-sm text-gray-900">
                                    {qw.query_text}
                                  </span>
                                </td>
                                {ENGINES.map((engine) => (
                                  <td
                                    key={engine}
                                    className="px-4 py-3 text-center"
                                  >
                                    <WinnerBadge
                                      winner={qw.winners[engine]}
                                      brandName={brandName}
                                    />
                                  </td>
                                ))}
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  </div>
                )}
            </>
          ) : (
            <div className="card text-center">
              <div className="py-12">
                <Users className="mx-auto h-12 w-12 text-gray-300" />
                <h3 className="mt-4 text-base font-semibold text-gray-900">
                  No comparison data yet
                </h3>
                <p className="mx-auto mt-1 max-w-sm text-sm text-gray-500">
                  Run a scan to generate comparison data between your brand and
                  competitors.
                </p>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
