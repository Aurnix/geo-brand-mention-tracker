"use client";

import { useState, useEffect, useCallback, useMemo, Fragment } from "react";
import { useBrand } from "../layout";
import { useAuth } from "@/lib/auth";
import { api } from "@/lib/api";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import {
  Plus,
  Trash2,
  Check,
  X,
  Star,
  ChevronDown,
  ChevronRight,
  Loader2,
  AlertCircle,
  Inbox,
  Search,
  Filter,
  Minus,
} from "lucide-react";

// ── Types ───────────────────────────────────────────────────

interface Query {
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
  model_version: string;
  raw_response: string;
  brand_mentioned: boolean;
  mention_position: number | null;
  is_top_recommendation: boolean;
  sentiment: string | null;
  competitor_mentions: string[];
  citations: string[];
  run_date: string;
  created_at: string;
}

interface ResultPage {
  items: QueryResult[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

type EngineKey = "openai" | "anthropic" | "perplexity" | "gemini";

// ── Constants ───────────────────────────────────────────────

const ENGINES: EngineKey[] = ["openai", "anthropic", "perplexity", "gemini"];

const ENGINE_DISPLAY: Record<EngineKey, string> = {
  openai: "ChatGPT",
  anthropic: "Claude",
  perplexity: "Perplexity",
  gemini: "Gemini",
};

const ENGINE_COLORS: Record<EngineKey, string> = {
  openai: "#10a37f",
  anthropic: "#d97706",
  perplexity: "#2563eb",
  gemini: "#7c3aed",
};

const CATEGORY_OPTIONS = [
  "general",
  "product",
  "comparison",
  "recommendation",
  "review",
  "how-to",
  "pricing",
  "alternative",
];

// ── Helpers ─────────────────────────────────────────────────

function formatDate(dateStr: string): string {
  const d = new Date(dateStr);
  return d.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

function formatShortDate(dateStr: string): string {
  const d = new Date(dateStr);
  return d.toLocaleDateString("en-US", { month: "short", day: "numeric" });
}

// ── Skeleton components ─────────────────────────────────────

function TableSkeleton() {
  return (
    <div className="card overflow-hidden p-0">
      <div className="animate-pulse">
        <div className="flex items-center gap-4 border-b border-gray-100 px-6 py-4">
          <div className="h-4 w-48 rounded bg-gray-200" />
          <div className="h-4 w-20 rounded bg-gray-200" />
          {ENGINES.map((e) => (
            <div key={e} className="h-4 w-16 rounded bg-gray-200" />
          ))}
        </div>
        {Array.from({ length: 5 }).map((_, i) => (
          <div
            key={i}
            className="flex items-center gap-4 border-b border-gray-50 px-6 py-4"
          >
            <div className="h-4 w-64 rounded bg-gray-100" />
            <div className="h-5 w-20 rounded-full bg-gray-100" />
            {ENGINES.map((e) => (
              <div key={e} className="mx-auto h-5 w-5 rounded-full bg-gray-100" />
            ))}
            <div className="ml-auto h-4 w-8 rounded bg-gray-100" />
          </div>
        ))}
      </div>
    </div>
  );
}

// ── Engine status icon ──────────────────────────────────────

function EngineStatusIcon({
  mentioned,
  topRec,
}: {
  mentioned: boolean | null;
  topRec: boolean;
}) {
  if (mentioned === null) {
    return (
      <span title="No data">
        <Minus className="h-4 w-4 text-gray-300" />
      </span>
    );
  }
  if (topRec) {
    return (
      <span title="Top recommendation">
        <Star className="h-4 w-4 fill-amber-400 text-amber-400" />
      </span>
    );
  }
  if (mentioned) {
    return (
      <span title="Mentioned">
        <Check className="h-4 w-4 text-green-500" />
      </span>
    );
  }
  return (
    <span title="Not mentioned">
      <X className="h-4 w-4 text-red-400" />
    </span>
  );
}

// ── Expanded row: history chart + response accordions ───────

function QueryExpandedRow({ queryId }: { queryId: string }) {
  const [history, setHistory] = useState<QueryResult[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [openEngine, setOpenEngine] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function fetchHistory() {
      setLoading(true);
      setError("");
      try {
        const results = await api.getQueryHistory(queryId);
        if (!cancelled) {
          setHistory(results as QueryResult[]);
        }
      } catch (err) {
        if (!cancelled) {
          setError(
            err instanceof Error ? err.message : "Failed to load history"
          );
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    fetchHistory();
    return () => {
      cancelled = true;
    };
  }, [queryId]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-8">
        <Loader2 className="h-5 w-5 animate-spin text-gray-400" />
        <span className="ml-2 text-sm text-gray-500">Loading history...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center py-8 text-sm text-red-500">
        <AlertCircle className="mr-2 h-4 w-4" />
        {error}
      </div>
    );
  }

  if (history.length === 0) {
    return (
      <div className="py-8 text-center text-sm text-gray-400">
        No historical results yet. Run a scan to collect data.
      </div>
    );
  }

  // Build chart data: group by run_date, compute mention rate per date
  const dateMap = new Map<string, { total: number; mentioned: number }>();
  history.forEach((r) => {
    const dateKey = r.run_date || r.created_at.split("T")[0];
    const existing = dateMap.get(dateKey) || { total: 0, mentioned: 0 };
    existing.total += 1;
    if (r.brand_mentioned) existing.mentioned += 1;
    dateMap.set(dateKey, existing);
  });

  const chartData = Array.from(dateMap.entries())
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([date, counts]) => ({
      date: formatShortDate(date),
      mention_rate:
        counts.total > 0
          ? Math.round((counts.mentioned / counts.total) * 100)
          : 0,
    }));

  // Get latest result per engine for response text
  const latestByEngine = new Map<string, QueryResult>();
  const sortedHistory = [...history].sort(
    (a, b) =>
      new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
  );
  sortedHistory.forEach((r) => {
    if (!latestByEngine.has(r.engine)) {
      latestByEngine.set(r.engine, r);
    }
  });

  return (
    <div className="space-y-6 px-2 py-4">
      {/* Mini trend chart */}
      {chartData.length > 1 && (
        <div>
          <h4 className="mb-3 text-xs font-semibold uppercase tracking-wide text-gray-500">
            Mention Rate Over Time
          </h4>
          <div className="h-40">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis
                  dataKey="date"
                  tick={{ fontSize: 11, fill: "#94a3b8" }}
                  axisLine={{ stroke: "#e2e8f0" }}
                  tickLine={false}
                />
                <YAxis
                  tick={{ fontSize: 11, fill: "#94a3b8" }}
                  axisLine={{ stroke: "#e2e8f0" }}
                  tickLine={false}
                  tickFormatter={(v) => `${v}%`}
                  domain={[0, 100]}
                />
                <Tooltip
                  contentStyle={{
                    borderRadius: "8px",
                    border: "1px solid #e2e8f0",
                    fontSize: "12px",
                    boxShadow: "0 4px 6px -1px rgb(0 0 0 / 0.1)",
                  }}
                  formatter={(value: number) => [`${value}%`, "Mention Rate"]}
                />
                <Line
                  type="monotone"
                  dataKey="mention_rate"
                  stroke="#2563eb"
                  strokeWidth={2}
                  dot={{ r: 3, fill: "#2563eb" }}
                  activeDot={{ r: 5 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Engine response accordions */}
      <div>
        <h4 className="mb-3 text-xs font-semibold uppercase tracking-wide text-gray-500">
          Latest Responses by Engine
        </h4>
        <div className="space-y-2">
          {ENGINES.map((engine) => {
            const result = latestByEngine.get(engine);
            const isOpen = openEngine === engine;

            return (
              <div
                key={engine}
                className="overflow-hidden rounded-lg border border-gray-200"
              >
                <button
                  onClick={() => setOpenEngine(isOpen ? null : engine)}
                  className="flex w-full items-center justify-between px-4 py-3 text-left text-sm font-medium text-gray-700 transition-colors hover:bg-gray-50"
                >
                  <div className="flex items-center gap-3">
                    <div
                      className="h-2 w-2 rounded-full"
                      style={{ backgroundColor: ENGINE_COLORS[engine] }}
                    />
                    <span>{ENGINE_DISPLAY[engine]}</span>
                    {result && (
                      <EngineStatusIcon
                        mentioned={result.brand_mentioned}
                        topRec={result.is_top_recommendation}
                      />
                    )}
                    {result?.sentiment && (
                      <span
                        className={`rounded-full px-2 py-0.5 text-[10px] font-medium ${
                          result.sentiment === "positive"
                            ? "bg-green-50 text-green-700"
                            : result.sentiment === "negative"
                              ? "bg-red-50 text-red-700"
                              : result.sentiment === "mixed"
                                ? "bg-amber-50 text-amber-700"
                                : "bg-gray-50 text-gray-600"
                        }`}
                      >
                        {result.sentiment}
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-2">
                    {!result && (
                      <span className="text-xs text-gray-400">No data</span>
                    )}
                    {isOpen ? (
                      <ChevronDown className="h-4 w-4 text-gray-400" />
                    ) : (
                      <ChevronRight className="h-4 w-4 text-gray-400" />
                    )}
                  </div>
                </button>
                <div
                  className={`overflow-hidden transition-all duration-200 ease-in-out ${
                    isOpen ? "max-h-[600px]" : "max-h-0"
                  }`}
                >
                  {result ? (
                    <div className="border-t border-gray-100 px-4 py-3">
                      <div className="mb-2 flex flex-wrap items-center gap-3 text-xs text-gray-400">
                        {result.model_version && (
                          <span>Model: {result.model_version}</span>
                        )}
                        <span>
                          Run: {formatDate(result.run_date || result.created_at)}
                        </span>
                        {result.mention_position !== null && (
                          <span>Position: #{result.mention_position}</span>
                        )}
                      </div>
                      <div className="max-h-80 overflow-y-auto rounded-lg bg-gray-50 p-3 text-sm leading-relaxed text-gray-700">
                        {result.raw_response || "No response text available."}
                      </div>
                      {result.citations && result.citations.length > 0 && (
                        <div className="mt-2">
                          <span className="text-xs font-medium text-gray-500">
                            Citations:
                          </span>
                          <ul className="mt-1 space-y-0.5">
                            {result.citations.map((cite, i) => (
                              <li
                                key={i}
                                className="text-xs text-blue-600 hover:underline"
                              >
                                <a
                                  href={cite}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                >
                                  {cite}
                                </a>
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                      {result.competitor_mentions &&
                        result.competitor_mentions.length > 0 && (
                          <div className="mt-2 flex flex-wrap items-center gap-1">
                            <span className="text-xs font-medium text-gray-500">
                              Competitors mentioned:
                            </span>
                            {result.competitor_mentions.map((comp, i) => (
                              <span
                                key={i}
                                className="rounded-full bg-orange-50 px-2 py-0.5 text-[10px] font-medium text-orange-700"
                              >
                                {comp}
                              </span>
                            ))}
                          </div>
                        )}
                    </div>
                  ) : (
                    <div className="border-t border-gray-100 px-4 py-4 text-sm text-gray-400">
                      No results from this engine yet.
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

// ── Filter types ────────────────────────────────────────────

type MentionFilter = "all" | "mentioned" | "not_mentioned" | "top_rec";

interface Filters {
  engine: EngineKey | "all";
  mention: MentionFilter;
  category: string;
  search: string;
}

// ── Main page component ─────────────────────────────────────

export default function QueriesPage() {
  const { brandId } = useBrand();
  useAuth();

  const [queries, setQueries] = useState<Query[]>([]);
  const [results, setResults] = useState<QueryResult[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [confirmDeleteId, setConfirmDeleteId] = useState<string | null>(null);

  // Add query form
  const [showAddForm, setShowAddForm] = useState(false);
  const [newQueryText, setNewQueryText] = useState("");
  const [newQueryCategory, setNewQueryCategory] = useState("");
  const [addLoading, setAddLoading] = useState(false);
  const [addError, setAddError] = useState("");

  // Filters
  const [filters, setFilters] = useState<Filters>({
    engine: "all",
    mention: "all",
    category: "",
    search: "",
  });

  // ── Fetch data ──────────────────────────────────

  const fetchData = useCallback(async () => {
    if (!brandId) return;
    setLoading(true);
    setError("");
    try {
      const [queriesData, resultsData] = await Promise.all([
        api.getQueries(brandId),
        api
          .getResults(brandId, { page_size: "500" })
          .catch(() => ({
            items: [] as QueryResult[],
            total: 0,
            page: 1,
            page_size: 500,
            pages: 0,
          })),
      ]);
      setQueries(queriesData as Query[]);
      const rPage = resultsData as ResultPage;
      setResults(rPage.items || []);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to load queries"
      );
    } finally {
      setLoading(false);
    }
  }, [brandId]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // ── Build latest result map ─────────────────────

  const latestResultMap = useMemo(() => {
    const map = new Map<string, Map<EngineKey, QueryResult>>();

    const sorted = [...results].sort(
      (a, b) =>
        new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
    );

    sorted.forEach((r) => {
      if (!map.has(r.query_id)) {
        map.set(r.query_id, new Map());
      }
      const engineMap = map.get(r.query_id)!;
      const engineKey = r.engine as EngineKey;
      if (ENGINES.includes(engineKey) && !engineMap.has(engineKey)) {
        engineMap.set(engineKey, r);
      }
    });

    return map;
  }, [results]);

  // ── Derive categories from data ─────────────────

  const categories = useMemo(() => {
    const cats = new Set<string>();
    queries.forEach((q) => {
      if (q.category) cats.add(q.category);
    });
    return Array.from(cats).sort();
  }, [queries]);

  // ── Filter queries ──────────────────────────────

  const filteredQueries = useMemo(() => {
    return queries.filter((q) => {
      // Text search
      if (
        filters.search &&
        !q.query_text.toLowerCase().includes(filters.search.toLowerCase())
      ) {
        return false;
      }

      // Category filter
      if (filters.category && q.category !== filters.category) {
        return false;
      }

      // Engine + mention filter
      const engineResults = latestResultMap.get(q.id);
      if (filters.engine !== "all" || filters.mention !== "all") {
        const enginesToCheck: EngineKey[] =
          filters.engine === "all" ? ENGINES : [filters.engine];

        if (filters.mention === "mentioned") {
          const hasMention = enginesToCheck.some((e) => {
            const r = engineResults?.get(e);
            return r?.brand_mentioned === true;
          });
          if (!hasMention) return false;
        } else if (filters.mention === "not_mentioned") {
          const allNotMentioned = enginesToCheck.every((e) => {
            const r = engineResults?.get(e);
            return !r || r.brand_mentioned === false;
          });
          if (!allNotMentioned) return false;
        } else if (filters.mention === "top_rec") {
          const hasTopRec = enginesToCheck.some((e) => {
            const r = engineResults?.get(e);
            return r?.is_top_recommendation === true;
          });
          if (!hasTopRec) return false;
        }
      }

      return true;
    });
  }, [queries, filters, latestResultMap]);

  // ── Add query handler ───────────────────────────

  const handleAddQuery = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!brandId || !newQueryText.trim()) return;

    setAddLoading(true);
    setAddError("");
    try {
      await api.addQuery(brandId, {
        query_text: newQueryText.trim(),
        category: newQueryCategory || undefined,
      });
      setNewQueryText("");
      setNewQueryCategory("");
      setShowAddForm(false);
      await fetchData();
    } catch (err) {
      setAddError(
        err instanceof Error ? err.message : "Failed to add query"
      );
    } finally {
      setAddLoading(false);
    }
  };

  // ── Delete query handler ────────────────────────

  const handleDeleteQuery = async (queryId: string) => {
    setDeletingId(queryId);
    try {
      await api.deleteQuery(queryId);
      setConfirmDeleteId(null);
      if (expandedId === queryId) setExpandedId(null);
      await fetchData();
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to delete query"
      );
    } finally {
      setDeletingId(null);
    }
  };

  // ── Check if any filter is active ───────────────

  const hasActiveFilters =
    filters.engine !== "all" ||
    filters.mention !== "all" ||
    filters.category !== "" ||
    filters.search !== "";

  const clearFilters = () => {
    setFilters({ engine: "all", mention: "all", category: "", search: "" });
  };

  // ── No brand selected ──────────────────────────

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

  // ── Loading state ─────────────────────────────

  if (loading) {
    return (
      <div>
        <div className="mb-6 flex items-center justify-between">
          <div>
            <div className="h-7 w-40 animate-pulse rounded bg-gray-200" />
            <div className="mt-1 h-4 w-64 animate-pulse rounded bg-gray-200" />
          </div>
          <div className="h-10 w-28 animate-pulse rounded-lg bg-gray-200" />
        </div>
        <div className="mb-4 flex gap-3">
          <div className="h-9 w-48 animate-pulse rounded-lg bg-gray-200" />
          <div className="h-9 w-32 animate-pulse rounded-lg bg-gray-200" />
          <div className="h-9 w-32 animate-pulse rounded-lg bg-gray-200" />
          <div className="h-9 w-32 animate-pulse rounded-lg bg-gray-200" />
        </div>
        <TableSkeleton />
      </div>
    );
  }

  // ── Error state ───────────────────────────────

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

  // ── Main render ───────────────────────────────

  return (
    <div>
      {/* ── Header ───────────────────────────────────── */}
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            Monitored Queries
          </h1>
          <p className="mt-1 text-sm text-gray-500">
            Track how AI engines respond to queries about your brand
          </p>
        </div>
        <button
          onClick={() => {
            setShowAddForm(!showAddForm);
            setAddError("");
          }}
          className="btn-primary inline-flex items-center gap-2"
        >
          <Plus className="h-4 w-4" />
          Add Query
        </button>
      </div>

      {/* ── Inline add form ──────────────────────────── */}
      {showAddForm && (
        <div className="card mb-6">
          <form
            onSubmit={handleAddQuery}
            className="flex flex-wrap items-end gap-4"
          >
            <div className="min-w-[300px] flex-1">
              <label
                htmlFor="query-text"
                className="mb-1 block text-sm font-medium text-gray-700"
              >
                Query Text
              </label>
              <input
                id="query-text"
                type="text"
                value={newQueryText}
                onChange={(e) => setNewQueryText(e.target.value)}
                placeholder='e.g. "What is the best project management tool?"'
                className="input-field"
                required
                autoFocus
              />
            </div>
            <div className="w-48">
              <label
                htmlFor="query-category"
                className="mb-1 block text-sm font-medium text-gray-700"
              >
                Category
                <span className="ml-1 font-normal text-gray-400">
                  (optional)
                </span>
              </label>
              <select
                id="query-category"
                value={newQueryCategory}
                onChange={(e) => setNewQueryCategory(e.target.value)}
                className="input-field"
              >
                <option value="">None</option>
                {CATEGORY_OPTIONS.map((cat) => (
                  <option key={cat} value={cat}>
                    {cat.charAt(0).toUpperCase() + cat.slice(1)}
                  </option>
                ))}
              </select>
            </div>
            <div className="flex items-center gap-2">
              <button
                type="submit"
                disabled={addLoading || !newQueryText.trim()}
                className="btn-primary inline-flex items-center gap-2"
              >
                {addLoading ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Plus className="h-4 w-4" />
                )}
                Add
              </button>
              <button
                type="button"
                onClick={() => {
                  setShowAddForm(false);
                  setAddError("");
                  setNewQueryText("");
                  setNewQueryCategory("");
                }}
                className="btn-secondary"
              >
                Cancel
              </button>
            </div>
          </form>
          {addError && (
            <p className="mt-3 text-sm text-red-600">{addError}</p>
          )}
        </div>
      )}

      {/* ── Error banner (non-fatal) ─────────────────── */}
      {error && queries.length > 0 && (
        <div className="mb-4 flex items-center gap-2 rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700">
          <AlertCircle className="h-4 w-4 flex-shrink-0" />
          {error}
          <button
            onClick={() => setError("")}
            className="ml-auto text-red-500 hover:text-red-700"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      )}

      {/* ── Filter bar ───────────────────────────────── */}
      <div className="mb-4 flex flex-wrap items-center gap-3">
        {/* Search */}
        <div className="relative max-w-sm min-w-[200px] flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
          <input
            type="text"
            value={filters.search}
            onChange={(e) =>
              setFilters((f) => ({ ...f, search: e.target.value }))
            }
            placeholder="Search queries..."
            className="input-field pl-9"
          />
        </div>

        {/* Engine filter */}
        <div className="flex items-center gap-1">
          <Filter className="h-4 w-4 text-gray-400" />
          <select
            value={filters.engine}
            onChange={(e) =>
              setFilters((f) => ({
                ...f,
                engine: e.target.value as Filters["engine"],
              }))
            }
            className="rounded-lg border-0 bg-white py-2 pl-3 pr-8 text-sm text-gray-700 shadow-sm ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-brand-600"
          >
            <option value="all">All Engines</option>
            {ENGINES.map((e) => (
              <option key={e} value={e}>
                {ENGINE_DISPLAY[e]}
              </option>
            ))}
          </select>
        </div>

        {/* Mention status filter */}
        <select
          value={filters.mention}
          onChange={(e) =>
            setFilters((f) => ({
              ...f,
              mention: e.target.value as MentionFilter,
            }))
          }
          className="rounded-lg border-0 bg-white py-2 pl-3 pr-8 text-sm text-gray-700 shadow-sm ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-brand-600"
        >
          <option value="all">All Statuses</option>
          <option value="mentioned">Mentioned</option>
          <option value="not_mentioned">Not Mentioned</option>
          <option value="top_rec">Top Recommendation</option>
        </select>

        {/* Category filter */}
        {categories.length > 0 && (
          <select
            value={filters.category}
            onChange={(e) =>
              setFilters((f) => ({ ...f, category: e.target.value }))
            }
            className="rounded-lg border-0 bg-white py-2 pl-3 pr-8 text-sm text-gray-700 shadow-sm ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-brand-600"
          >
            <option value="">All Categories</option>
            {categories.map((cat) => (
              <option key={cat} value={cat}>
                {cat.charAt(0).toUpperCase() + cat.slice(1)}
              </option>
            ))}
          </select>
        )}

        {/* Clear filters */}
        {hasActiveFilters && (
          <button
            onClick={clearFilters}
            className="inline-flex items-center gap-1 rounded-lg px-3 py-2 text-sm font-medium text-gray-500 transition-colors hover:bg-gray-100 hover:text-gray-700"
          >
            <X className="h-3.5 w-3.5" />
            Clear filters
          </button>
        )}

        {/* Result count */}
        <span className="ml-auto text-sm text-gray-400">
          {filteredQueries.length} of {queries.length}{" "}
          {queries.length === 1 ? "query" : "queries"}
        </span>
      </div>

      {/* ── Empty state ──────────────────────────────── */}
      {queries.length === 0 && (
        <div className="flex flex-col items-center justify-center rounded-xl border-2 border-dashed border-gray-200 py-24 text-center">
          <Search className="h-12 w-12 text-gray-300" />
          <h3 className="mt-4 text-lg font-semibold text-gray-900">
            No queries yet
          </h3>
          <p className="mx-auto mt-1 max-w-sm text-sm text-gray-500">
            Add your first query to start monitoring how AI engines mention your
            brand. Try questions your customers might ask, like &quot;What is the
            best tool for...&quot;
          </p>
          <button
            onClick={() => setShowAddForm(true)}
            className="btn-primary mt-6 inline-flex items-center gap-2"
          >
            <Plus className="h-4 w-4" />
            Add your first query
          </button>
        </div>
      )}

      {/* ── Filtered empty state ─────────────────────── */}
      {queries.length > 0 && filteredQueries.length === 0 && (
        <div className="flex flex-col items-center justify-center rounded-xl border-2 border-dashed border-gray-200 py-16 text-center">
          <Filter className="h-10 w-10 text-gray-300" />
          <h3 className="mt-4 text-base font-semibold text-gray-900">
            No matching queries
          </h3>
          <p className="mt-1 text-sm text-gray-500">
            Try adjusting your filters to see more results.
          </p>
          <button
            onClick={clearFilters}
            className="btn-secondary mt-4 inline-flex items-center gap-2"
          >
            <X className="h-4 w-4" />
            Clear filters
          </button>
        </div>
      )}

      {/* ── Data table ───────────────────────────────── */}
      {filteredQueries.length > 0 && (
        <div className="card overflow-hidden p-0">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-100 bg-gray-50/50">
                  <th className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wide text-gray-500">
                    Query
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-gray-500">
                    Category
                  </th>
                  {ENGINES.map((engine) => (
                    <th
                      key={engine}
                      className="px-3 py-3 text-center text-xs font-semibold uppercase tracking-wide text-gray-500"
                    >
                      {ENGINE_DISPLAY[engine]}
                    </th>
                  ))}
                  <th className="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wide text-gray-500">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody>
                {filteredQueries.map((query, index) => {
                  const engineResults = latestResultMap.get(query.id);
                  const isExpanded = expandedId === query.id;
                  const isConfirmingDelete = confirmDeleteId === query.id;
                  const isDeleting = deletingId === query.id;

                  return (
                    <Fragment key={query.id}>
                      <tr
                        onClick={() =>
                          setExpandedId(isExpanded ? null : query.id)
                        }
                        className={`cursor-pointer border-b border-gray-50 transition-colors hover:bg-blue-50/40 ${
                          index % 2 === 1 ? "bg-gray-50/30" : "bg-white"
                        } ${isExpanded ? "bg-blue-50/30" : ""}`}
                      >
                        {/* Query text */}
                        <td className="px-6 py-4">
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

                        {/* Category */}
                        <td className="px-4 py-4">
                          {query.category ? (
                            <span className="inline-flex rounded-full bg-gray-100 px-2.5 py-0.5 text-xs font-medium text-gray-600">
                              {query.category.charAt(0).toUpperCase() +
                                query.category.slice(1)}
                            </span>
                          ) : (
                            <span className="text-xs text-gray-300">
                              &mdash;
                            </span>
                          )}
                        </td>

                        {/* Engine status icons */}
                        {ENGINES.map((engine) => {
                          const r = engineResults?.get(engine);
                          return (
                            <td key={engine} className="px-3 py-4 text-center">
                              <div className="flex items-center justify-center">
                                <EngineStatusIcon
                                  mentioned={r ? r.brand_mentioned : null}
                                  topRec={r?.is_top_recommendation ?? false}
                                />
                              </div>
                            </td>
                          );
                        })}

                        {/* Actions */}
                        <td className="px-4 py-4 text-right">
                          <div
                            className="flex items-center justify-end gap-1"
                            onClick={(e) => e.stopPropagation()}
                          >
                            {isConfirmingDelete ? (
                              <div className="flex items-center gap-2">
                                <span className="text-xs text-red-600">
                                  Delete?
                                </span>
                                <button
                                  onClick={() => handleDeleteQuery(query.id)}
                                  disabled={isDeleting}
                                  className="inline-flex items-center rounded px-2 py-1 text-xs font-medium text-red-600 transition-colors hover:bg-red-50"
                                >
                                  {isDeleting ? (
                                    <Loader2 className="h-3.5 w-3.5 animate-spin" />
                                  ) : (
                                    "Yes"
                                  )}
                                </button>
                                <button
                                  onClick={() => setConfirmDeleteId(null)}
                                  className="inline-flex items-center rounded px-2 py-1 text-xs font-medium text-gray-500 transition-colors hover:bg-gray-100"
                                >
                                  No
                                </button>
                              </div>
                            ) : (
                              <button
                                onClick={() => setConfirmDeleteId(query.id)}
                                className="rounded p-1.5 text-gray-400 transition-colors hover:bg-red-50 hover:text-red-500"
                                title="Delete query"
                              >
                                <Trash2 className="h-4 w-4" />
                              </button>
                            )}
                          </div>
                        </td>
                      </tr>

                      {/* Expanded row */}
                      {isExpanded && (
                        <tr>
                          <td
                            colSpan={3 + ENGINES.length}
                            className="border-b border-gray-100 bg-white px-6 py-2"
                          >
                            <QueryExpandedRow queryId={query.id} />
                          </td>
                        </tr>
                      )}
                    </Fragment>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
