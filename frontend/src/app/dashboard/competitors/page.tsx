"use client";

import { useState, useEffect, useCallback } from "react";
import { useAuth } from "@/lib/auth";
import { api } from "@/lib/api";
import { useBrand } from "../layout";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Legend,
  Cell,
} from "recharts";
import { Plus, Trash2, Loader2, Users, AlertCircle } from "lucide-react";

interface Competitor {
  id: string;
  brand_id: string;
  name: string;
  aliases: string[];
  created_at: string;
}

interface SentimentBreakdown {
  positive: number;
  neutral: number;
  negative: number;
  mixed: number;
}

interface ComparisonEntry {
  name: string;
  mention_rate: number;
  sentiment_breakdown: SentimentBreakdown;
}

interface ComparisonData {
  brand: ComparisonEntry;
  competitors: ComparisonEntry[];
}

const COLORS = [
  "#3b82f6",
  "#ef4444",
  "#f59e0b",
  "#10b981",
  "#8b5cf6",
  "#ec4899",
  "#06b6d4",
  "#f97316",
];

export default function CompetitorsPage() {
  const { brandId } = useBrand();
  const { isAuthenticated } = useAuth();

  const [competitors, setCompetitors] = useState<Competitor[]>([]);
  const [comparison, setComparison] = useState<ComparisonData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Add competitor form
  const [showAddForm, setShowAddForm] = useState(false);
  const [newName, setNewName] = useState("");
  const [newAliases, setNewAliases] = useState("");
  const [adding, setAdding] = useState(false);

  const fetchData = useCallback(async () => {
    if (!brandId) return;
    try {
      setLoading(true);
      setError(null);
      const [comps, comp] = await Promise.all([
        api.getCompetitors(brandId),
        api.getCompetitorComparison(brandId).catch(() => null),
      ]);
      setCompetitors(comps);
      setComparison(comp);
    } catch (err: any) {
      setError(err.message || "Failed to load data");
    } finally {
      setLoading(false);
    }
  }, [brandId]);

  useEffect(() => {
    if (isAuthenticated && brandId) {
      fetchData();
    }
  }, [isAuthenticated, brandId, fetchData]);

  const handleAddCompetitor = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!brandId || !newName.trim()) return;
    try {
      setAdding(true);
      const aliases = newAliases
        .split(",")
        .map((a) => a.trim())
        .filter(Boolean);
      await api.addCompetitor(brandId, { name: newName.trim(), aliases });
      setNewName("");
      setNewAliases("");
      setShowAddForm(false);
      await fetchData();
    } catch (err: any) {
      setError(err.message || "Failed to add competitor");
    } finally {
      setAdding(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Remove this competitor?")) return;
    try {
      await api.deleteCompetitor(id, brandId || undefined);
      await fetchData();
    } catch (err: any) {
      setError(err.message || "Failed to delete competitor");
    }
  };

  if (!brandId) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-gray-500">
        <Users className="mb-4 h-12 w-12 text-gray-300" />
        <p className="text-lg font-medium">No brand selected</p>
        <p className="text-sm">Create a brand first to track competitors.</p>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div className="h-8 w-48 animate-pulse rounded bg-gray-200" />
          <div className="h-10 w-40 animate-pulse rounded bg-gray-200" />
        </div>
        <div className="card h-80 animate-pulse bg-gray-100" />
        <div className="card h-64 animate-pulse bg-gray-100" />
      </div>
    );
  }

  // Build chart data
  const chartData =
    comparison
      ? [
          {
            name: comparison.brand.name,
            "Mention Rate": Math.round(comparison.brand.mention_rate * 100),
          },
          ...comparison.competitors.map((c) => ({
            name: c.name,
            "Mention Rate": Math.round(c.mention_rate * 100),
          })),
        ]
      : [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Competitors</h1>
          <p className="mt-1 text-sm text-gray-500">
            Compare your brand visibility against competitors across AI engines.
          </p>
        </div>
        <button
          onClick={() => setShowAddForm(!showAddForm)}
          className="btn-primary"
        >
          <Plus className="mr-2 h-4 w-4" />
          Add Competitor
        </button>
      </div>

      {error && (
        <div className="flex items-center gap-2 rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700">
          <AlertCircle className="h-4 w-4" />
          {error}
        </div>
      )}

      {/* Add competitor form */}
      {showAddForm && (
        <div className="card">
          <form onSubmit={handleAddCompetitor} className="flex items-end gap-4">
            <div className="flex-1">
              <label className="block text-sm font-medium text-gray-700">
                Competitor Name
              </label>
              <input
                type="text"
                value={newName}
                onChange={(e) => setNewName(e.target.value)}
                placeholder="e.g. Salesforce"
                className="input-field mt-1"
                required
              />
            </div>
            <div className="flex-1">
              <label className="block text-sm font-medium text-gray-700">
                Aliases (comma-separated)
              </label>
              <input
                type="text"
                value={newAliases}
                onChange={(e) => setNewAliases(e.target.value)}
                placeholder="e.g. salesforce.com, SFDC"
                className="input-field mt-1"
              />
            </div>
            <button
              type="submit"
              disabled={adding || !newName.trim()}
              className="btn-primary"
            >
              {adding ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                "Add"
              )}
            </button>
          </form>
        </div>
      )}

      {/* Comparison chart */}
      {comparison && chartData.length > 0 && (
        <div className="card">
          <h2 className="mb-4 text-lg font-semibold text-gray-900">
            Mention Rate Comparison
          </h2>
          <ResponsiveContainer width="100%" height={350}>
            <BarChart data={chartData} layout="vertical" margin={{ left: 20 }}>
              <XAxis
                type="number"
                domain={[0, 100]}
                tickFormatter={(v) => `${v}%`}
              />
              <YAxis type="category" dataKey="name" width={120} />
              <Tooltip formatter={(value: number) => `${value}%`} />
              <Bar dataKey="Mention Rate" radius={[0, 6, 6, 0]}>
                {chartData.map((_, index) => (
                  <Cell
                    key={`cell-${index}`}
                    fill={index === 0 ? "#3b82f6" : COLORS[index % COLORS.length]}
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Sentiment breakdown */}
      {comparison && (
        <div className="card">
          <h2 className="mb-4 text-lg font-semibold text-gray-900">
            Sentiment Breakdown
          </h2>
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="py-3 pr-4 text-left font-medium text-gray-500">
                    Brand / Competitor
                  </th>
                  <th className="px-4 py-3 text-center font-medium text-gray-500">
                    Mention Rate
                  </th>
                  <th className="px-4 py-3 text-center font-medium text-green-600">
                    Positive
                  </th>
                  <th className="px-4 py-3 text-center font-medium text-gray-500">
                    Neutral
                  </th>
                  <th className="px-4 py-3 text-center font-medium text-red-600">
                    Negative
                  </th>
                  <th className="px-4 py-3 text-center font-medium text-yellow-600">
                    Mixed
                  </th>
                </tr>
              </thead>
              <tbody>
                {[comparison.brand, ...comparison.competitors].map(
                  (entry, i) => (
                    <tr
                      key={entry.name}
                      className={`border-b border-gray-100 ${
                        i === 0 ? "bg-blue-50/50 font-medium" : ""
                      }`}
                    >
                      <td className="py-3 pr-4">
                        <span className="flex items-center gap-2">
                          {i === 0 && (
                            <span className="inline-block h-2 w-2 rounded-full bg-brand-500" />
                          )}
                          {entry.name}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-center">
                        {Math.round(entry.mention_rate * 100)}%
                      </td>
                      <td className="px-4 py-3 text-center text-green-700">
                        {entry.sentiment_breakdown.positive}
                      </td>
                      <td className="px-4 py-3 text-center text-gray-600">
                        {entry.sentiment_breakdown.neutral}
                      </td>
                      <td className="px-4 py-3 text-center text-red-700">
                        {entry.sentiment_breakdown.negative}
                      </td>
                      <td className="px-4 py-3 text-center text-yellow-700">
                        {entry.sentiment_breakdown.mixed}
                      </td>
                    </tr>
                  )
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Competitor list */}
      <div className="card">
        <h2 className="mb-4 text-lg font-semibold text-gray-900">
          Tracked Competitors ({competitors.length})
        </h2>
        {competitors.length === 0 ? (
          <div className="py-8 text-center text-gray-500">
            <Users className="mx-auto mb-3 h-10 w-10 text-gray-300" />
            <p>No competitors added yet.</p>
            <p className="text-sm">
              Add competitors to see how your brand compares.
            </p>
          </div>
        ) : (
          <div className="space-y-2">
            {competitors.map((comp) => (
              <div
                key={comp.id}
                className="flex items-center justify-between rounded-lg border border-gray-100 px-4 py-3 transition-colors hover:bg-gray-50"
              >
                <div>
                  <span className="font-medium text-gray-900">
                    {comp.name}
                  </span>
                  {comp.aliases.length > 0 && (
                    <span className="ml-2 text-sm text-gray-500">
                      ({comp.aliases.join(", ")})
                    </span>
                  )}
                </div>
                <button
                  onClick={() => handleDelete(comp.id)}
                  className="rounded p-1.5 text-gray-400 transition-colors hover:bg-red-50 hover:text-red-600"
                  title="Remove competitor"
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
