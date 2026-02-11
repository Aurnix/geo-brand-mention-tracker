"use client";

import { useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import {
  BarChart3,
  Loader2,
  AlertCircle,
  ArrowRight,
  ArrowLeft,
  Plus,
  X,
  CheckCircle2,
  Sparkles,
  Zap,
  Target,
  Users,
  Search,
} from "lucide-react";

const QUERY_TEMPLATES = [
  "Best [category] for [use case]",
  "[Brand] vs [Competitor]",
  "Top [category] tools in 2026",
  "What [category] do you recommend?",
];

interface CompetitorEntry {
  id?: string;
  name: string;
}

export default function OnboardingPage() {
  const router = useRouter();
  const { isLoading: authLoading } = useAuth();

  const [step, setStep] = useState(1);
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Step 1: Brand
  const [brandName, setBrandName] = useState("");
  const [aliasesInput, setAliasesInput] = useState("");
  const [brandId, setBrandId] = useState<string | null>(null);

  // Step 2: Competitors
  const [competitorInput, setCompetitorInput] = useState("");
  const [competitors, setCompetitors] = useState<CompetitorEntry[]>([]);

  // Step 3: Queries
  const [queryInput, setQueryInput] = useState("");
  const [queries, setQueries] = useState<string[]>([]);

  // Step 4: Run
  const [isRunning, setIsRunning] = useState(false);
  const [runComplete, setRunComplete] = useState(false);

  const parseAliases = (input: string): string[] => {
    return input
      .split(",")
      .map((s) => s.trim())
      .filter(Boolean);
  };

  const handleStep1Next = useCallback(async () => {
    if (!brandName.trim()) {
      setError("Please enter a brand name.");
      return;
    }
    setError("");
    setIsSubmitting(true);

    try {
      const aliases = parseAliases(aliasesInput);
      const brand = await api.createBrand({ name: brandName.trim(), aliases });
      setBrandId(brand.id);
      setStep(2);
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Failed to create brand";
      setError(message);
    } finally {
      setIsSubmitting(false);
    }
  }, [brandName, aliasesInput]);

  const handleAddCompetitor = useCallback(() => {
    const name = competitorInput.trim();
    if (!name) return;
    if (competitors.some((c) => c.name.toLowerCase() === name.toLowerCase())) {
      setError("Competitor already added.");
      return;
    }
    setError("");
    setCompetitors((prev) => [...prev, { name }]);
    setCompetitorInput("");
  }, [competitorInput, competitors]);

  const handleRemoveCompetitor = useCallback((name: string) => {
    setCompetitors((prev) => prev.filter((c) => c.name !== name));
  }, []);

  const handleStep2Next = useCallback(async () => {
    if (competitors.length === 0) {
      setError("Please add at least one competitor.");
      return;
    }
    if (!brandId) {
      setError("Brand not created yet. Please go back and try again.");
      return;
    }
    setError("");
    setIsSubmitting(true);

    try {
      const results = await Promise.all(
        competitors
          .filter((c) => !c.id)
          .map((c) => api.addCompetitor(brandId, { name: c.name }))
      );
      setCompetitors((prev) =>
        prev.map((c) => {
          const created = results.find((r) => r.name === c.name);
          return created ? { ...c, id: created.id } : c;
        })
      );
      setStep(3);
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Failed to add competitors";
      setError(message);
    } finally {
      setIsSubmitting(false);
    }
  }, [competitors, brandId]);

  const handleAddQueriesFromInput = useCallback(() => {
    const newQueries = queryInput
      .split("\n")
      .map((q) => q.trim())
      .filter(Boolean)
      .filter((q) => !queries.includes(q));
    if (newQueries.length > 0) {
      setQueries((prev) => [...prev, ...newQueries]);
      setQueryInput("");
    }
  }, [queryInput, queries]);

  const handleAddTemplate = useCallback(
    (template: string) => {
      if (!queries.includes(template)) {
        setQueries((prev) => [...prev, template]);
      }
    },
    [queries]
  );

  const handleRemoveQuery = useCallback((query: string) => {
    setQueries((prev) => prev.filter((q) => q !== query));
  }, []);

  const handleStep3Next = useCallback(async () => {
    if (queries.length === 0) {
      setError("Please add at least one query.");
      return;
    }
    if (!brandId) {
      setError("Brand not created yet. Please go back and try again.");
      return;
    }
    setError("");
    setIsSubmitting(true);

    try {
      await Promise.all(
        queries.map((q) => api.addQuery(brandId, { query_text: q }))
      );
      setStep(4);
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Failed to add queries";
      setError(message);
    } finally {
      setIsSubmitting(false);
    }
  }, [queries, brandId]);

  const handleRunScan = useCallback(async () => {
    if (!brandId) return;
    setIsRunning(true);
    setError("");

    try {
      await api.triggerRun(brandId);
      setRunComplete(true);
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Failed to start scan";
      setError(message);
    } finally {
      setIsRunning(false);
    }
  }, [brandId]);

  if (authLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-brand-600" />
      </div>
    );
  }

  const stepIcons = [Target, Users, Search, Sparkles];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="border-b border-gray-200 bg-white">
        <div className="mx-auto flex max-w-3xl items-center justify-between px-6 py-4">
          <Link href="/" className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand-600">
              <BarChart3 className="h-5 w-5 text-white" />
            </div>
            <span className="text-xl font-bold text-gray-900">GeoTrack</span>
          </Link>
          <span className="text-sm text-gray-500">Step {step} of 4</span>
        </div>
      </div>

      {/* Progress bar */}
      <div className="mx-auto max-w-3xl px-6 pt-8">
        <div className="flex items-center justify-between">
          {[1, 2, 3, 4].map((s) => {
            const Icon = stepIcons[s - 1];
            return (
              <div key={s} className="flex flex-1 items-center">
                <div
                  className={`flex h-10 w-10 items-center justify-center rounded-full text-sm font-semibold transition-colors ${
                    s < step
                      ? "bg-brand-600 text-white"
                      : s === step
                        ? "bg-brand-600 text-white ring-4 ring-brand-100"
                        : "bg-gray-200 text-gray-500"
                  }`}
                >
                  {s < step ? (
                    <CheckCircle2 className="h-5 w-5" />
                  ) : (
                    <Icon className="h-5 w-5" />
                  )}
                </div>
                {s < 4 && (
                  <div
                    className={`mx-2 h-0.5 flex-1 rounded transition-colors ${
                      s < step ? "bg-brand-600" : "bg-gray-200"
                    }`}
                  />
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Content */}
      <div className="mx-auto max-w-3xl px-6 py-10">
        {error && (
          <div className="mb-6 flex items-start gap-3 rounded-lg border border-red-200 bg-red-50 p-3">
            <AlertCircle className="mt-0.5 h-4 w-4 flex-shrink-0 text-red-600" />
            <p className="text-sm text-red-700">{error}</p>
          </div>
        )}

        {/* ── Step 1: Brand ────────────────────────────── */}
        {step === 1 && (
          <div className="card">
            <h2 className="text-2xl font-bold text-gray-900">
              What brand do you want to track?
            </h2>
            <p className="mt-2 text-sm text-gray-600">
              Enter your brand name and any common variations or aliases.
            </p>

            <div className="mt-8 space-y-5">
              <div>
                <label
                  htmlFor="brandName"
                  className="block text-sm font-medium text-gray-700"
                >
                  Brand name
                </label>
                <input
                  id="brandName"
                  type="text"
                  required
                  value={brandName}
                  onChange={(e) => setBrandName(e.target.value)}
                  className="input-field mt-1.5"
                  placeholder="e.g. HubSpot"
                  disabled={isSubmitting}
                />
              </div>

              <div>
                <label
                  htmlFor="aliases"
                  className="block text-sm font-medium text-gray-700"
                >
                  Aliases{" "}
                  <span className="font-normal text-gray-400">(optional)</span>
                </label>
                <input
                  id="aliases"
                  type="text"
                  value={aliasesInput}
                  onChange={(e) => setAliasesInput(e.target.value)}
                  className="input-field mt-1.5"
                  placeholder="e.g. Hub Spot, hubspot.com (comma-separated)"
                  disabled={isSubmitting}
                />
                <p className="mt-1.5 text-xs text-gray-500">
                  Aliases help catch variations of your brand name in AI
                  responses. Separate with commas.
                </p>
              </div>
            </div>

            <div className="mt-8 flex justify-end">
              <button
                onClick={handleStep1Next}
                disabled={isSubmitting || !brandName.trim()}
                className="btn-primary inline-flex items-center gap-2"
              >
                {isSubmitting ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Creating...
                  </>
                ) : (
                  <>
                    Next
                    <ArrowRight className="h-4 w-4" />
                  </>
                )}
              </button>
            </div>
          </div>
        )}

        {/* ── Step 2: Competitors ──────────────────────── */}
        {step === 2 && (
          <div className="card">
            <h2 className="text-2xl font-bold text-gray-900">
              Who are your competitors?
            </h2>
            <p className="mt-2 text-sm text-gray-600">
              Add competitors to compare their AI visibility against yours. We
              recommend 2-5 competitors.
            </p>

            <div className="mt-8">
              <div className="flex gap-2">
                <input
                  type="text"
                  value={competitorInput}
                  onChange={(e) => setCompetitorInput(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") {
                      e.preventDefault();
                      handleAddCompetitor();
                    }
                  }}
                  className="input-field flex-1"
                  placeholder="e.g. Salesforce"
                  disabled={isSubmitting}
                />
                <button
                  onClick={handleAddCompetitor}
                  disabled={!competitorInput.trim() || isSubmitting}
                  className="btn-primary inline-flex items-center gap-1.5"
                >
                  <Plus className="h-4 w-4" />
                  Add
                </button>
              </div>

              {competitors.length > 0 && (
                <ul className="mt-4 space-y-2">
                  {competitors.map((c) => (
                    <li
                      key={c.name}
                      className="flex items-center justify-between rounded-lg border border-gray-200 bg-gray-50 px-4 py-2.5"
                    >
                      <div className="flex items-center gap-2">
                        <Users className="h-4 w-4 text-gray-400" />
                        <span className="text-sm font-medium text-gray-900">
                          {c.name}
                        </span>
                      </div>
                      <button
                        onClick={() => handleRemoveCompetitor(c.name)}
                        className="rounded p-1 text-gray-400 hover:bg-gray-200 hover:text-gray-600"
                      >
                        <X className="h-4 w-4" />
                      </button>
                    </li>
                  ))}
                </ul>
              )}

              {competitors.length === 0 && (
                <p className="mt-4 text-center text-sm text-gray-400">
                  No competitors added yet. Add at least one to continue.
                </p>
              )}
            </div>

            <div className="mt-8 flex justify-between">
              <button
                onClick={() => {
                  setError("");
                  setStep(1);
                }}
                className="btn-secondary inline-flex items-center gap-2"
              >
                <ArrowLeft className="h-4 w-4" />
                Back
              </button>
              <button
                onClick={handleStep2Next}
                disabled={isSubmitting || competitors.length === 0}
                className="btn-primary inline-flex items-center gap-2"
              >
                {isSubmitting ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Saving...
                  </>
                ) : (
                  <>
                    Next
                    <ArrowRight className="h-4 w-4" />
                  </>
                )}
              </button>
            </div>
          </div>
        )}

        {/* ── Step 3: Queries ──────────────────────────── */}
        {step === 3 && (
          <div className="card">
            <h2 className="text-2xl font-bold text-gray-900">
              What queries matter to you?
            </h2>
            <p className="mt-2 text-sm text-gray-600">
              These are the questions people ask AI engines about your space.
              We'll track how each engine responds.
            </p>

            {/* Template chips */}
            <div className="mt-6">
              <p className="mb-2 text-xs font-medium uppercase tracking-wider text-gray-500">
                Quick-add templates
              </p>
              <div className="flex flex-wrap gap-2">
                {QUERY_TEMPLATES.map((template) => (
                  <button
                    key={template}
                    onClick={() => handleAddTemplate(template)}
                    disabled={queries.includes(template)}
                    className={`rounded-full border px-3 py-1.5 text-sm transition-colors ${
                      queries.includes(template)
                        ? "border-brand-200 bg-brand-50 text-brand-600"
                        : "border-gray-200 text-gray-600 hover:border-brand-300 hover:bg-brand-50 hover:text-brand-600"
                    }`}
                  >
                    {queries.includes(template) ? (
                      <span className="flex items-center gap-1">
                        <CheckCircle2 className="h-3.5 w-3.5" />
                        {template}
                      </span>
                    ) : (
                      <span className="flex items-center gap-1">
                        <Plus className="h-3.5 w-3.5" />
                        {template}
                      </span>
                    )}
                  </button>
                ))}
              </div>
            </div>

            {/* Text area for custom queries */}
            <div className="mt-6">
              <label
                htmlFor="queries"
                className="block text-sm font-medium text-gray-700"
              >
                Add custom queries{" "}
                <span className="font-normal text-gray-400">
                  (one per line)
                </span>
              </label>
              <textarea
                id="queries"
                rows={4}
                value={queryInput}
                onChange={(e) => setQueryInput(e.target.value)}
                className="input-field mt-1.5 resize-none"
                placeholder={`What's the best CRM for small businesses?\nCompare HubSpot vs Salesforce\nTop marketing automation tools`}
                disabled={isSubmitting}
              />
              <button
                onClick={handleAddQueriesFromInput}
                disabled={!queryInput.trim() || isSubmitting}
                className="btn-secondary mt-2 inline-flex items-center gap-1.5 text-sm"
              >
                <Plus className="h-4 w-4" />
                Add queries
              </button>
            </div>

            {/* Query list */}
            {queries.length > 0 && (
              <div className="mt-6">
                <p className="mb-2 text-xs font-medium uppercase tracking-wider text-gray-500">
                  Added queries ({queries.length})
                </p>
                <ul className="max-h-48 space-y-1.5 overflow-y-auto">
                  {queries.map((q) => (
                    <li
                      key={q}
                      className="flex items-center justify-between rounded-lg border border-gray-200 bg-gray-50 px-3 py-2"
                    >
                      <span className="text-sm text-gray-800">{q}</span>
                      <button
                        onClick={() => handleRemoveQuery(q)}
                        className="ml-2 rounded p-1 text-gray-400 hover:bg-gray-200 hover:text-gray-600"
                      >
                        <X className="h-3.5 w-3.5" />
                      </button>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            <div className="mt-8 flex justify-between">
              <button
                onClick={() => {
                  setError("");
                  setStep(2);
                }}
                className="btn-secondary inline-flex items-center gap-2"
              >
                <ArrowLeft className="h-4 w-4" />
                Back
              </button>
              <button
                onClick={handleStep3Next}
                disabled={isSubmitting || queries.length === 0}
                className="btn-primary inline-flex items-center gap-2"
              >
                {isSubmitting ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Saving...
                  </>
                ) : (
                  <>
                    Next
                    <ArrowRight className="h-4 w-4" />
                  </>
                )}
              </button>
            </div>
          </div>
        )}

        {/* ── Step 4: All set ──────────────────────────── */}
        {step === 4 && (
          <div className="card text-center">
            <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-green-100">
              <CheckCircle2 className="h-8 w-8 text-green-600" />
            </div>

            <h2 className="mt-6 text-2xl font-bold text-gray-900">
              You&apos;re all set!
            </h2>
            <p className="mt-2 text-sm text-gray-600">
              Here's a summary of what you've configured.
            </p>

            {/* Summary */}
            <div className="mx-auto mt-8 max-w-md space-y-4 text-left">
              <div className="rounded-lg border border-gray-200 bg-gray-50 p-4">
                <div className="flex items-center gap-2 text-sm font-medium text-gray-900">
                  <Target className="h-4 w-4 text-brand-600" />
                  Brand
                </div>
                <p className="mt-1 text-sm text-gray-600">
                  {brandName}
                  {aliasesInput && (
                    <span className="text-gray-400">
                      {" "}
                      (aliases: {aliasesInput})
                    </span>
                  )}
                </p>
              </div>

              <div className="rounded-lg border border-gray-200 bg-gray-50 p-4">
                <div className="flex items-center gap-2 text-sm font-medium text-gray-900">
                  <Users className="h-4 w-4 text-brand-600" />
                  Competitors ({competitors.length})
                </div>
                <p className="mt-1 text-sm text-gray-600">
                  {competitors.map((c) => c.name).join(", ")}
                </p>
              </div>

              <div className="rounded-lg border border-gray-200 bg-gray-50 p-4">
                <div className="flex items-center gap-2 text-sm font-medium text-gray-900">
                  <Search className="h-4 w-4 text-brand-600" />
                  Queries ({queries.length})
                </div>
                <ul className="mt-1 space-y-0.5">
                  {queries.slice(0, 5).map((q) => (
                    <li key={q} className="text-sm text-gray-600">
                      {q}
                    </li>
                  ))}
                  {queries.length > 5 && (
                    <li className="text-sm text-gray-400">
                      ...and {queries.length - 5} more
                    </li>
                  )}
                </ul>
              </div>
            </div>

            {/* Actions */}
            <div className="mt-8 flex flex-col items-center gap-3">
              {!runComplete ? (
                <button
                  onClick={handleRunScan}
                  disabled={isRunning}
                  className="btn-primary inline-flex items-center gap-2 px-6 py-3 text-base"
                >
                  {isRunning ? (
                    <>
                      <Loader2 className="h-5 w-5 animate-spin" />
                      Running first scan...
                    </>
                  ) : (
                    <>
                      <Zap className="h-5 w-5" />
                      Run your first scan
                    </>
                  )}
                </button>
              ) : (
                <div className="rounded-lg border border-green-200 bg-green-50 px-4 py-3 text-sm text-green-700">
                  <CheckCircle2 className="mr-1.5 inline h-4 w-4" />
                  Scan started! Results will appear on your dashboard shortly.
                </div>
              )}

              <button
                onClick={() => router.push("/dashboard")}
                className="btn-secondary inline-flex items-center gap-2"
              >
                Go to dashboard
                <ArrowRight className="h-4 w-4" />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
