"use client";

import { useState, useEffect, createContext, useContext, useCallback } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { signOut } from "next-auth/react";
import { useAuth } from "@/lib/auth";
import { api } from "@/lib/api";
import {
  BarChart3,
  Search,
  Users,
  LogOut,
  ChevronDown,
  Loader2,
} from "lucide-react";

// ── Brand context ───────────────────────────────────────────

interface Brand {
  id: string;
  name: string;
}

interface BrandContextValue {
  brandId: string | null;
  brands: Brand[];
  setBrandId: (id: string) => void;
  refreshBrands: () => Promise<void>;
}

const BrandContext = createContext<BrandContextValue>({
  brandId: null,
  brands: [],
  setBrandId: () => {},
  refreshBrands: async () => {},
});

export function useBrand() {
  return useContext(BrandContext);
}

// ── Navigation items ────────────────────────────────────────

const navItems = [
  { label: "Overview", href: "/dashboard", icon: BarChart3 },
  { label: "Queries", href: "/dashboard/queries", icon: Search },
  { label: "Competitors", href: "/dashboard/competitors", icon: Users },
];

// ── Plan tier badge ─────────────────────────────────────────

function PlanBadge({ tier }: { tier: string }) {
  const colors: Record<string, string> = {
    free: "bg-gray-600 text-gray-200",
    pro: "bg-brand-600 text-white",
    agency: "bg-purple-600 text-white",
  };
  return (
    <span
      className={`rounded px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide ${colors[tier] || colors.free}`}
    >
      {tier}
    </span>
  );
}

// ── Layout ──────────────────────────────────────────────────

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const router = useRouter();
  const { session, isLoading: authLoading, isAuthenticated, planTier } = useAuth();

  const [brands, setBrands] = useState<Brand[]>([]);
  const [brandId, setBrandId] = useState<string | null>(null);
  const [brandsLoading, setBrandsLoading] = useState(true);
  const [brandDropdownOpen, setBrandDropdownOpen] = useState(false);

  const email = session?.user?.email || "";

  const fetchBrands = useCallback(async () => {
    try {
      setBrandsLoading(true);
      const result = await api.getBrands();
      const mapped = result.map((b: Brand) => ({ id: b.id, name: b.name }));
      setBrands(mapped);
      if (mapped.length > 0 && !brandId) {
        setBrandId(mapped[0].id);
      }
    } catch {
      // Brands may fail if user hasn't created one yet — that's fine
    } finally {
      setBrandsLoading(false);
    }
  }, [brandId]);

  useEffect(() => {
    if (isAuthenticated) {
      fetchBrands();
    }
  }, [isAuthenticated, fetchBrands]);

  if (authLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gray-50">
        <Loader2 className="h-8 w-8 animate-spin text-brand-600" />
      </div>
    );
  }

  if (!isAuthenticated) {
    router.push("/login");
    return null;
  }

  const selectedBrand = brands.find((b) => b.id === brandId);

  return (
    <BrandContext.Provider
      value={{ brandId, brands, setBrandId, refreshBrands: fetchBrands }}
    >
      <div className="flex min-h-screen bg-gray-50">
        {/* ── Sidebar ────────────────────────────────── */}
        <aside className="fixed inset-y-0 left-0 z-30 flex w-64 flex-col bg-sidebar">
          {/* Logo */}
          <div className="flex h-16 items-center gap-2 px-6">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand-600">
              <BarChart3 className="h-5 w-5 text-white" />
            </div>
            <span className="text-lg font-bold text-white">GeoTrack</span>
          </div>

          {/* Brand selector */}
          {brands.length > 0 && (
            <div className="relative px-4 pb-4">
              <button
                onClick={() => setBrandDropdownOpen(!brandDropdownOpen)}
                className="flex w-full items-center justify-between rounded-lg bg-sidebar-hover px-3 py-2 text-sm text-gray-300 transition-colors hover:bg-sidebar-active"
              >
                <span className="truncate">
                  {brandsLoading
                    ? "Loading..."
                    : selectedBrand?.name || "Select brand"}
                </span>
                <ChevronDown className="h-4 w-4 flex-shrink-0 text-gray-500" />
              </button>

              {brandDropdownOpen && (
                <div className="absolute left-4 right-4 top-full z-10 mt-1 rounded-lg border border-gray-700 bg-sidebar-hover shadow-lg">
                  {brands.map((brand) => (
                    <button
                      key={brand.id}
                      onClick={() => {
                        setBrandId(brand.id);
                        setBrandDropdownOpen(false);
                      }}
                      className={`flex w-full items-center px-3 py-2 text-left text-sm transition-colors ${
                        brand.id === brandId
                          ? "bg-sidebar-active text-white"
                          : "text-gray-400 hover:bg-sidebar-active hover:text-white"
                      }`}
                    >
                      {brand.name}
                    </button>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Nav links */}
          <nav className="flex-1 space-y-1 px-4">
            {navItems.map((item) => {
              const isActive =
                item.href === "/dashboard"
                  ? pathname === "/dashboard"
                  : pathname.startsWith(item.href);
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors ${
                    isActive
                      ? "bg-sidebar-active text-white"
                      : "text-gray-400 hover:bg-sidebar-hover hover:text-white"
                  }`}
                >
                  <item.icon className="h-5 w-5" />
                  {item.label}
                </Link>
              );
            })}
          </nav>

          {/* User info + sign out */}
          <div className="border-t border-gray-700 px-4 py-4">
            <div className="flex items-center gap-3">
              <div className="flex h-8 w-8 items-center justify-center rounded-full bg-sidebar-active text-sm font-semibold text-white">
                {email ? email[0].toUpperCase() : "?"}
              </div>
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-medium text-gray-200">
                  {email}
                </p>
                <PlanBadge tier={planTier || "free"} />
              </div>
            </div>
            <button
              onClick={() => signOut({ callbackUrl: "/" })}
              className="mt-3 flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm text-gray-400 transition-colors hover:bg-sidebar-hover hover:text-white"
            >
              <LogOut className="h-4 w-4" />
              Sign out
            </button>
          </div>
        </aside>

        {/* ── Main content ───────────────────────────── */}
        <main className="ml-64 flex-1 p-8">{children}</main>
      </div>
    </BrandContext.Provider>
  );
}
