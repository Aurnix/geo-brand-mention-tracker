"use client";

import { useState, useRef, useEffect } from "react";
import { Download, FileText, FileSpreadsheet } from "lucide-react";
import { exportOverviewCSV, exportOverviewPDF } from "@/lib/export";

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

interface ExportDropdownProps {
  data: OverviewData;
  brandName: string;
}

export default function ExportDropdown({ data, brandName }: ExportDropdownProps) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (ref.current && !ref.current.contains(event.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  return (
    <div className="relative" ref={ref}>
      <button
        onClick={() => setOpen(!open)}
        className="btn-secondary inline-flex items-center gap-2"
      >
        <Download className="h-4 w-4" />
        Export
      </button>

      {open && (
        <div className="absolute right-0 top-full z-10 mt-2 w-48 rounded-lg border border-gray-200 bg-white py-1 shadow-lg">
          <button
            onClick={() => {
              exportOverviewCSV(data, brandName);
              setOpen(false);
            }}
            className="flex w-full items-center gap-3 px-4 py-2 text-left text-sm text-gray-700 transition-colors hover:bg-gray-50"
          >
            <FileSpreadsheet className="h-4 w-4 text-green-600" />
            Export as CSV
          </button>
          <button
            onClick={() => {
              exportOverviewPDF(data, brandName);
              setOpen(false);
            }}
            className="flex w-full items-center gap-3 px-4 py-2 text-left text-sm text-gray-700 transition-colors hover:bg-gray-50"
          >
            <FileText className="h-4 w-4 text-red-600" />
            Export as PDF
          </button>
        </div>
      )}
    </div>
  );
}
