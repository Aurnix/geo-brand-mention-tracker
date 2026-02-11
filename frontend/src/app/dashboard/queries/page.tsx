"use client";

import { useState, useEffect, useCallback } from "react";
import { api } from "@/lib/api";
import { useBrand } from "../layout";
import {
  Search,
  Plus,
  Trash2,
  ChevronDown,
  ChevronRight,
  Loader2,
  AlertCircle,
  Inbox,
  X,
  Filter,
} from "lucide-react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

// ── Types ───────────────────────────────────────────────────

interface MonitoredQuery {
  id: string;
  brand_id: string;
  query_text: string;
  category: string | null;
  is_active: boolean;
  created_at: string;
}

interface QueryResult {
  id: string;
  query_id: string;
  engine: string;
  raw_response: string;
  brand_mentioned: boolean;
  mention_position: string;
  is_top_recommendation: boolean;
  sentiment: string;
  run_date: string;
}

interface QueryHistoryData {
  query: MonitoredQuery;
  results: QueryResult[];
  trend: { date: string; mentioned: boolean; engine: string }[];
}

const ENGINES = ["openai", "anthropic", "perplexity", "gemini"] as const;

const ENGINE_DISPLAY: Record<string, string> = {
  openai: "ChatGPT",
  anthropic: "Claude",
  perplexity: "Perplexity",
  gemini: "Gemini",
};

const SENTIMENTS = ["positive", "neutral", "negative", "mixed"] as const;

// ── Helper: get latest result per engine for a query ────────

function getLatestByEngine(
  results: QueryResult[],
  queryId: string
): Record<string, QueryResult | undefined> {
  const map: Record<string, QueryResult | undefined> = {};
  const queryResults = results.filter((r) => r.query_id === queryId);

  for (const engine of ENGINES) {
    const engineResults = queryResults
      .filter((r) => r.engine === engine)
      .sort(
        (a, b) =>
          new Date(b.run_date).getTime() - new Date(a.run_date).getTime()
      );
    map[engine] = engineResults[0];
  }
  return map;
}

// ── Status icon ─────────────────────────────────────────────

function StatusIcon({
  result,
}: {
  result: QueryResult | undefined;
}) {
  if (!result) {
    return <span className="text-gray-300">--</span>;
  }
  if (result.is_top_recommendation) {
    return (
      <span className="text-lg" title="Top recommendation">
        &#11088;
      </span>
    );
  }
  if (result.brand_mentioned) {
    return (
      <span className="text-lg text-green-600" title="Mentioned">
        &#10003;
      </span>
    );
  }
  return (
    <span className="text-lg text-red-500" title="Not mentioned">
      &#10007;
    </span>
  );
}

// ── Skeleton ────────────────────────────────────────────────

function TableSkeleton() {
  return (
    <div className="card animate-pulse">
      <div className="h-4 w-48 rounded bg-gray-200" />
      <div className="mt-6 space-y-3">
        {Array.from({ length: 6 }).map((_, i) => (
          <div key={i} className="flex items-center gap-4">
            <div className="h-4 flex-1 rounded bg-gray-200" />
            <div className="h-4 w-12 rounded bg-gray-200" />
            <div className="h-4 w-12 rounded bg-gray-200" />
            <div className="h-4 w-12 rounded bg-gray-200" />
            <div className="h-4 w-12 rounded bg-gray-200" />
          </div>
        ))}
      </div>
    </div>
  );
}

// ── Expanded row ────────────────────────────────────────────

function ExpandedRow({
  queryId,
  onClose,
}: {
  queryId: string;
  onClose: () => void;
}) {
  const [history, setHistory] = useState<QueryHistoryData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [expandedResponse, setExpandedResponse] = useState<string | null>(null);

  useEffect(() => {
    async function fetchHistory() {
      setLoading(true);
      setError("");
      try {
        const data = await api.getQueryHistory(queryId);
        setHistory(data as QueryHistoryData);
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Failed to load history"
        );
      } finally {
        setLoading(false);
      }
    }
    fetchHistory();
  }, [queryId]);

  if (loading) {
    return (
      <tr>
        <td colSpan={7} className="bg-gray-50 px-6 py-8">
          <div className="flex items-center justify-center gap-2 text-sm text-gray-500">
            <Loader2 className="h-4 w-4 animate-spin" />
            Loading history...
          </div>
        </td>
      </tr>
    );
  }

  if (error) {
    return (
      <tr>
        <td colSpan={7} className="bg-gray-50 px-6 py-8">
          <div className="flex items-center justify-center gap-2 text-sm text-red-600">
            <AlertCircle className="h-4 w-4" />
            {error}
          </div>
        </td>
      </tr>
    );
  }

  if (!history || history.results.length === 0) {
    return (
      <tr>
        <td colSpan={7} className="bg-gray-50 px-6 py-8">
          <p className="text-center text-sm text-gray-500">
            No historical data for this query yet.
          </p>
        </td>
      </tr>
    );
  }

  // Build trend chart data — daily mention rate across engines
  const trendMap = new Map<string, { mentioned: number; total: number }>();
  for (const t of history.trend) {
    const existing = trendMap.get(t.date) || { mentioned: 0, total: 0 };
    existing.total += 1;
    if (t.mentioned) existing.mentioned += 1;
    trendMap.set(t.date, existing);
  }
  const trendChartData = Array.from(trendMap.entries())
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([date, vals]) => ({
      date: new Date(date).toLocaleDateString("en-US", {
        month: "short",
        day: "numeric",
      }),
      rate:
        vals.total > 0
          ? Math.round((vals.mentioned / vals.total) * 100)
          : 0,
    }));

  // Group responses by engine (latest first)
  const latestByEngine: Record<string, QueryResult[]> = {};
  for (const r of history.results) {
    if (!latestByEngine[r.engine]) latestByEngine[r.engine] = [];
    latestByEngine[r.engine].push(r);
  }
  for (const engine of Object.keys(latestByEngine)) {
    latestByEngine[engine].sort(
      (a, b) =>
        new Date(b.run_date).getTime() - new Date(a.run_date).getTime()
    );
  }

  return (
    <tr>
      <td colSpan={7} className="bg-gray-50 p-0">
        <div className="border-t border-b border-gray-200 px-6 py-6">
          {/* Mini trend chart */}
          {trendChartData.length > 1 && (
            <div className="mb-6">
              <h4 className="mb-2 text-sm font-semibold text-gray-700">
                Mention rate over time
              </h4>
              <div className="h-32">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={trendChartData}>
                    <XAxis
                      dataKey="date"
                      tick={{ fontSize: 10, fill: "#94a3b8" }}
                      axisLine={false}
                      tickLine={false}
                    />
                    <YAxis
                      tick={{ fontSize: 10, fill: "#94a3b8" }}
                      axisLine={false}
                      tickLine={false}
                      tickFormatter={(v) => `${v}%`}
                    />
                    <Tooltip
                      formatter={(value: number) => [
                        `${value}%`,
                        "Mention Rate",
                      ]}
                      contentStyle={{
                        borderRadius: "6px",
                        border: "1px solid #e2e8f0",
                        fontSize: 12,
                      }}
                    />
                    <Line
                      type="monotone"
                      dataKey="rate"
                      stroke="#2563eb"
                      strokeWidth={2}
                      dot={false}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}

          {/* Per-engine responses */}
          <h4 className="mb-3 text-sm font-semibold text-gray-700">
            Latest responses by engine
          </h4>
          <div className="space-y-2">
            {ENGINES.map((engine) => {
              const latest = latestByEngine[engine]?.[0];
              if (!latest) return null;
              const isExpanded = expandedResponse === `${engine}-${latest.id}`;

              return (
                <div
                  key={engine}
                  className="rounded-lg border border-gray-200 bg-white"
                >
                  <button
                    onClick={() =>
                      setExpandedResponse(
                        isExpanded ? null : `${engine}-${latest.id}`
                      )
                    }
                    className="flex w-full items-center justify-between px-4 py-3 text-left"
                  >
                    <div className="flex items-center gap-3">
                      <span className="text-sm font-medium text-gray-900">
                        {ENGINE_DISPLAY[engine]}
                      </span>
                      <StatusIcon result={latest} />
                      <span
                        className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                          latest.sentiment === "positive"
                            ? "bg-green-100 text-green-700"
                            : latest.sentiment === "negative"
                              ? "bg-red-100 text-red-700"
                              : latest.sentiment === "mixed"
                                ? "bg-amber-100 text-amber-700"
                                : "bg-gray-100 text-gray-700"
                        }`}
                      >
                        {latest.sentiment}
                      </span>
                      <span className="text-xs text-gray-400">
                        {latest.run_date}
                      </span>
                    </div>
                    {isExpanded ? (
                      <ChevronDown className="h-4 w-4 text-gray-400" />
                    ) : (
                      <ChevronRight className="h-4 w-4 text-gray-400" />
                    )}
                  </button>
                  {isExpanded && (
                    <div className="border-t border-gray-100 px-4 py-3">
                      <pre className="max-h-48 overflow-y-auto whitespace-pre-wrap text-xs leading-5 text-gray-700">
                        {latest.raw_response}
                      </pre>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </td>
    </tr>
  );
}

// ── Main page ───────────────────────────────────────────────

export default function QueriesPage() {
  const { brandId } = useBrand();

  const [queries, setQueries] = useState<MonitoredQuery[]>([]);
  const [results, setResults] = useState<QueryResult[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // Expansion
  const [expandedQueryId, setExpandedQueryId] = useState<string | null>(null);

  // Filters
  const [filterEngine, setFilterEngine] = useState<string>("");
  const [filterMentioned, setFilterMentioned] = useState<string>("");
  const [filterSentiment, setFilterSentiment] = useState<string>("");
  const [filterCategory, setFilterCategory] = useState<string>("");
  const [showFilters, setShowFilters] = useState(false);

  // Add query modal
  const [showAddModal, setShowAddModal] = useState(false);
  const [newQueryText, setNewQueryText] = useState("");
  const [newQueryCategory, setNewQueryCategory] = useState("");
  const [addLoading, setAddLoading] = useState(false);

  // Delete
  const [deleteLoading, setDeleteLoading] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    if (!brandId) return;
    setLoading(true);
    setError("");

    try {
      const [queriesData, resultsData] = await Promise.all([
        api.getQueries(brandId),
        api.getResults(brandId),
      ]);
      setQueries(queriesData as MonitoredQuery[]);
      const rData = resultsData as { results: QueryResult[] };
      setResults(rData.results || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load queries");
    } finally {
      setLoading(false);
    }
  }, [brandId]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleAddQuery = async () => {
    if (!brandId || !newQueryText.trim()) return;
    setAddLoading(true);
    try {
      await api.addQuery(brandId, {
        query_text: newQueryText.trim(),
        category: newQueryCategory.trim() || undefined,
      });
      setNewQueryText("");
      setNewQueryCategory("");
      setShowAddModal(false);
      await fetchData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to add query");
    } finally {
      setAddLoading(false);
    }
  };

  const handleDeleteQuery = async (queryId: string) => {
    setDeleteLoading(queryId);
    try {
      await api.deleteQuery(queryId);
      setQueries((prev) => prev.filter((q) => q.id !== queryId));
      if (expandedQueryId === queryId) setExpandedQueryId(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete query");
    } finally {
      setDeleteLoading(null);
    }
  };

  // ── Apply filters ──────────────────────────────
  const filteredQueries = queries.filter((q) => {
    // Category filter
    if (filterCategory && q.category !== filterCategory) return false;

    // Engine / mentioned / sentiment filters need results
    if (filterEngine || filterMentioned || filterSentiment) {
      const latestByEngine = getLatestByEngine(results, q.id);
      const relevantResults = filterEngine
        ? [latestByEngine[filterEngine]].filter(Boolean)
        : Object.values(latestByEngine).filter(Boolean);

      if (relevantResults.length === 0) {
        return filterMentioned === "no";
      }

      if (filterMentioned === "yes") {
        if (!relevantResults.some((r) => r!.brand_mentioned)) return false;
      } else if (filterMentioned === "no") {
        if (!relevantResults.some((r) => !r!.brand_mentioned)) return false;
      }

      if (filterSentiment) {
        if (!relevantResults.some((r) => r!.sentiment === filterSentiment))
          return false;
      }
    }

    return true;
  });

  // Get unique categories
  const categories = Array.from(
    new Set(queries.map((q) => q.category).filter(Boolean))
  ) as string[];

  // ── No brand ───────────────────────────────────
  if (!brandId) {
    return (
      <div className="flex flex-col items-center justify-center py-24 text-center">
        <Inbox className="h-12 w-12 text-gray-300" />
        <h3 className="mt-4 text-lg font-semibold text-gray-900">
          No brand selected
        </h3>
        <p className="mt-1 text-sm text-gray-500">
          Create a brand to start tracking queries.
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
            <div className="h-7 w-32 animate-pulse rounded bg-gray-200" />
            <div className="mt-1 h-4 w-48 animate-pulse rounded bg-gray-200" />
          </div>
        </div>
        <TableSkeleton />
      </div>
    );
  }

  // ── Error ──────────────────────────────────────
  if (error && queries.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-24 text-center">
        <AlertCircle className="h-12 w-12 text-red-400" />
        <h3 className="mt-4 text-lg font-semibold text-gray-900">
          Failed to load queries
        </h3>
        <p className="mt-1 text-sm text-gray-500">{error}</p>
        <button onClick={fetchData} className="btn-primary mt-4">
          Try again
        </button>
      </div>
    );
  }

  return (
    <div>
      {/* ── Header ───────────────────────────────── */}
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Queries</h1>
          <p className="mt-1 text-sm text-gray-500">
            {queries.length} monitored {queries.length === 1 ? "query" : "queries"}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowFilters(!showFilters)}
            className={`btn-secondary inline-flex items-center gap-1.5 ${showFilters ? "ring-2 ring-brand-500" : ""}`}
          >
            <Filter className="h-4 w-4" />
            Filters
          </button>
          <button
            onClick={() => setShowAddModal(true)}
            className="btn-primary inline-flex items-center gap-1.5"
          >
            <Plus className="h-4 w-4" />
            Add Query
          </button>
        </div>
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

      {/* ── Filter bar ───────────────────────────── */}
      {showFilters && (
        <div className="mb-4 flex flex-wrap items-center gap-3 rounded-lg border border-gray-200 bg-white p-4">
          <select
            value={filterEngine}
            onChange={(e) => setFilterEngine(e.target.value)}
            className="input-field w-auto py-2 text-sm"
          >
            <option value="">All engines</option>
            {ENGINES.map((e) => (
              <option key={e} value={e}>
                {ENGINE_DISPLAY[e]}
              </option>
            ))}
          </select>

          <select
            value={filterMentioned}
            onChange={(e) => setFilterMentioned(e.target.value)}
            className="input-field w-auto py-2 text-sm"
          >
            <option value="">Mentioned / Not</option>
            <option value="yes">Mentioned</option>
            <option value="no">Not Mentioned</option>
          </select>

          <select
            value={filterSentiment}
            onChange={(e) => setFilterSentiment(e.target.value)}
            className="input-field w-auto py-2 text-sm"
          >
            <option value="">All sentiments</option>
            {SENTIMENTS.map((s) => (
              <option key={s} value={s}>
                {s.charAt(0).toUpperCase() + s.slice(1)}
              </option>
            ))}
          </select>

          {categories.length > 0 && (
            <select
              value={filterCategory}
              onChange={(e) => setFilterCategory(e.target.value)}
              className="input-field w-auto py-2 text-sm"
            >
              <option value="">All categories</option>
              {categories.map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </select>
          )}

          {(filterEngine ||
            filterMentioned ||
            filterSentiment ||
            filterCategory) && (
            <button
              onClick={() => {
                setFilterEngine("");
                setFilterMentioned("");
                setFilterSentiment("");
                setFilterCategory("");
              }}
              className="text-sm text-brand-600 hover:text-brand-700"
            >
              Clear filters
            </button>
          )}
        </div>
      )}

      {/* ── Empty state ──────────────────────────── */}
      {queries.length === 0 ? (
        <div className="flex flex-col items-center justify-center rounded-xl border-2 border-dashed border-gray-200 py-24 text-center">
          <Search className="h-12 w-12 text-gray-300" />
          <h3 className="mt-4 text-lg font-semibold text-gray-900">
            No queries yet
          </h3>
          <p className="mx-auto mt-1 max-w-sm text-sm text-gray-500">
            Add queries to start monitoring how AI engines respond to questions
            about your industry.
          </p>
          <button
            onClick={() => setShowAddModal(true)}
            className="btn-primary mt-6 inline-flex items-center gap-2"
          >
            <Plus className="h-4 w-4" />
            Add your first query
          </button>
        </div>
      ) : (
        /* ── Table ─────────────────────────────────── */
        <div className="card overflow-hidden p-0">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-200 bg-gray-50">
                  <th className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500">
                    Query
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500">
                    Category
                  </th>
                  {ENGINES.map((e) => (
                    <th
                      key={e}
                      className="px-4 py-3 text-center text-xs font-semibold uppercase tracking-wider text-gray-500"
                    >
                      {ENGINE_DISPLAY[e]}
                    </th>
                  ))}
                  <th className="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wider text-gray-500">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody>
                {filteredQueries.map((query, index) => {
                  const latestByEngine = getLatestByEngine(results, query.id);
                  const isExpanded = expandedQueryId === query.id;

                  return (
                    <>
                      <tr
                        key={query.id}
                        className={`cursor-pointer border-b border-gray-100 transition-colors hover:bg-gray-50 ${
                          index % 2 === 1 ? "bg-gray-50/50" : "bg-white"
                        } ${isExpanded ? "bg-brand-50" : ""}`}
                        onClick={() =>
                          setExpandedQueryId(isExpanded ? null : query.id)
                        }
                      >
                        <td className="px-6 py-3">
                          <div className="flex items-center gap-2">
                            {isExpanded ? (
                              <ChevronDown className="h-4 w-4 flex-shrink-0 text-gray-400" />
                            ) : (
                              <ChevronRight className="h-4 w-4 flex-shrink-0 text-gray-400" />
                            )}
                            <span className="text-sm font-medium text-gray-900">
                              {query.query_text}
                            </span>
                          </div>
                        </td>
                        <td className="px-4 py-3">
                          {query.category ? (
                            <span className="rounded-full bg-gray-100 px-2 py-0.5 text-xs font-medium text-gray-600">
                              {query.category}
                            </span>
                          ) : (
                            <span className="text-xs text-gray-400">--</span>
                          )}
                        </td>
                        {ENGINES.map((engine) => (
                          <td
                            key={engine}
                            className="px-4 py-3 text-center"
                          >
                            <StatusIcon result={latestByEngine[engine]} />
                          </td>
                        ))}
                        <td className="px-4 py-3 text-right">
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              handleDeleteQuery(query.id);
                            }}
                            disabled={deleteLoading === query.id}
                            className="rounded p-1.5 text-gray-400 transition-colors hover:bg-red-50 hover:text-red-600"
                            title="Delete query"
                          >
                            {deleteLoading === query.id ? (
                              <Loader2 className="h-4 w-4 animate-spin" />
                            ) : (
                              <Trash2 className="h-4 w-4" />
                            )}
                          </button>
                        </td>
                      </tr>

                      {isExpanded && (
                        <ExpandedRow
                          key={`expanded-${query.id}`}
                          queryId={query.id}
                          onClose={() => setExpandedQueryId(null)}
                        />
                      )}
                    </>
                  );
                })}

                {filteredQueries.length === 0 && queries.length > 0 && (
                  <tr>
                    <td colSpan={7} className="px-6 py-12 text-center">
                      <p className="text-sm text-gray-500">
                        No queries match the current filters.
                      </p>
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* ── Add query modal ──────────────────────── */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="w-full max-w-md rounded-xl bg-white p-6 shadow-xl">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold text-gray-900">
                Add Query
              </h3>
              <button
                onClick={() => setShowAddModal(false)}
                className="rounded p-1 text-gray-400 hover:bg-gray-100 hover:text-gray-600"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="mt-4 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Query text
                </label>
                <input
                  type="text"
                  value={newQueryText}
                  onChange={(e) => setNewQueryText(e.target.value)}
                  className="input-field mt-1.5"
                  placeholder="e.g. What's the best CRM for startups?"
                  autoFocus
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Category{" "}
                  <span className="font-normal text-gray-400">(optional)</span>
                </label>
                <input
                  type="text"
                  value={newQueryCategory}
                  onChange={(e) => setNewQueryCategory(e.target.value)}
                  className="input-field mt-1.5"
                  placeholder="e.g. purchase_intent, comparison"
                />
              </div>
            </div>

            <div className="mt-6 flex justify-end gap-3">
              <button
                onClick={() => setShowAddModal(false)}
                className="btn-secondary"
              >
                Cancel
              </button>
              <button
                onClick={handleAddQuery}
                disabled={addLoading || !newQueryText.trim()}
                className="btn-primary inline-flex items-center gap-1.5"
              >
                {addLoading ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Plus className="h-4 w-4" />
                )}
                Add query
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
