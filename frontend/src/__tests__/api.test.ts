import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";

// Import the api client fresh for each test
let api: any;

beforeEach(async () => {
  // Reset modules to get a fresh ApiClient
  vi.resetModules();
  const mod = await import("@/lib/api");
  api = mod.api;
});

afterEach(() => {
  vi.restoreAllMocks();
});

// Helper to mock fetch
function mockFetch(data: any, status = 200) {
  return vi.spyOn(globalThis, "fetch").mockResolvedValue({
    ok: status >= 200 && status < 300,
    status,
    json: () => Promise.resolve(data),
  } as Response);
}

describe("ApiClient", () => {
  describe("setToken", () => {
    it("includes Authorization header after setToken", async () => {
      const fetchSpy = mockFetch({ id: "1", email: "test@test.com" });
      api.setToken("my-jwt-token");

      await api.getMe();

      expect(fetchSpy).toHaveBeenCalledWith(
        expect.stringContaining("/api/auth/me"),
        expect.objectContaining({
          headers: expect.objectContaining({
            Authorization: "Bearer my-jwt-token",
          }),
        })
      );
    });
  });

  describe("signup", () => {
    it("sends POST with email and password", async () => {
      const fetchSpy = mockFetch({ access_token: "tok", token_type: "bearer" });

      const result = await api.signup("user@test.com", "password123");

      expect(fetchSpy).toHaveBeenCalledWith(
        expect.stringContaining("/api/auth/signup"),
        expect.objectContaining({
          method: "POST",
          body: JSON.stringify({ email: "user@test.com", password: "password123" }),
        })
      );
      expect(result.access_token).toBe("tok");
    });
  });

  describe("login", () => {
    it("sends POST with email and password", async () => {
      const fetchSpy = mockFetch({ access_token: "tok", token_type: "bearer" });

      const result = await api.login("user@test.com", "pass");

      expect(fetchSpy).toHaveBeenCalledWith(
        expect.stringContaining("/api/auth/login"),
        expect.objectContaining({
          method: "POST",
          body: JSON.stringify({ email: "user@test.com", password: "pass" }),
        })
      );
      expect(result.access_token).toBe("tok");
    });
  });

  describe("getBrands", () => {
    it("fetches brands list", async () => {
      const brands = [
        { id: "1", name: "Notion" },
        { id: "2", name: "Airtable" },
      ];
      mockFetch(brands);

      const result = await api.getBrands();

      expect(result).toEqual(brands);
    });
  });

  describe("createBrand", () => {
    it("sends POST with brand data", async () => {
      const brand = { id: "1", name: "Notion", aliases: ["notion.so"] };
      const fetchSpy = mockFetch(brand);

      const result = await api.createBrand({
        name: "Notion",
        aliases: ["notion.so"],
      });

      expect(fetchSpy).toHaveBeenCalledWith(
        expect.stringContaining("/api/brands"),
        expect.objectContaining({
          method: "POST",
          body: JSON.stringify({ name: "Notion", aliases: ["notion.so"] }),
        })
      );
      expect(result.name).toBe("Notion");
    });
  });

  describe("deleteBrand", () => {
    it("sends DELETE request", async () => {
      const fetchSpy = mockFetch(undefined, 204);

      await api.deleteBrand("brand-1");

      expect(fetchSpy).toHaveBeenCalledWith(
        expect.stringContaining("/api/brands/brand-1"),
        expect.objectContaining({ method: "DELETE" })
      );
    });
  });

  describe("triggerRun", () => {
    it("sends POST to run endpoint", async () => {
      const fetchSpy = mockFetch({ message: "Scan started" });

      const result = await api.triggerRun("brand-1");

      expect(fetchSpy).toHaveBeenCalledWith(
        expect.stringContaining("/api/brands/brand-1/run"),
        expect.objectContaining({ method: "POST" })
      );
      expect(result.message).toBe("Scan started");
    });
  });

  describe("getOverview", () => {
    it("fetches overview data", async () => {
      const overview = {
        mention_rate: 0.65,
        top_rec_rate: 0.3,
        total_queries: 20,
        total_runs: 100,
      };
      mockFetch(overview);

      const result = await api.getOverview("brand-1");

      expect(result.mention_rate).toBe(0.65);
    });
  });

  describe("getResults", () => {
    it("includes query params", async () => {
      const fetchSpy = mockFetch({
        items: [],
        total: 0,
        page: 1,
        page_size: 20,
        pages: 0,
      });

      await api.getResults("brand-1", { engine: "openai", page: "2" });

      expect(fetchSpy).toHaveBeenCalledWith(
        expect.stringMatching(/\/api\/brands\/brand-1\/results\?engine=openai&page=2/),
        expect.anything()
      );
    });
  });

  describe("competitors", () => {
    it("addCompetitor sends POST", async () => {
      const fetchSpy = mockFetch({ id: "c1", name: "Slack" });

      await api.addCompetitor("brand-1", { name: "Slack" });

      expect(fetchSpy).toHaveBeenCalledWith(
        expect.stringContaining("/api/brands/brand-1/competitors"),
        expect.objectContaining({ method: "POST" })
      );
    });

    it("deleteCompetitor with brandId uses nested path", async () => {
      const fetchSpy = mockFetch(undefined, 204);

      await api.deleteCompetitor("comp-1", "brand-1");

      expect(fetchSpy).toHaveBeenCalledWith(
        expect.stringContaining("/api/brands/brand-1/competitors/comp-1"),
        expect.objectContaining({ method: "DELETE" })
      );
    });
  });

  describe("queries", () => {
    it("addQuery sends POST with query data", async () => {
      const fetchSpy = mockFetch({ id: "q1", query_text: "best tool?" });

      await api.addQuery("brand-1", {
        query_text: "best tool?",
        category: "general",
      });

      expect(fetchSpy).toHaveBeenCalledWith(
        expect.stringContaining("/api/brands/brand-1/queries"),
        expect.objectContaining({
          method: "POST",
          body: JSON.stringify({
            query_text: "best tool?",
            category: "general",
          }),
        })
      );
    });

    it("updateQuery sends PATCH", async () => {
      const fetchSpy = mockFetch({ id: "q1", is_active: false });

      await api.updateQuery("q1", { is_active: false });

      expect(fetchSpy).toHaveBeenCalledWith(
        expect.stringContaining("/api/queries/q1"),
        expect.objectContaining({
          method: "PATCH",
          body: JSON.stringify({ is_active: false }),
        })
      );
    });

    it("deleteQuery sends DELETE", async () => {
      const fetchSpy = mockFetch(undefined, 204);

      await api.deleteQuery("q1");

      expect(fetchSpy).toHaveBeenCalledWith(
        expect.stringContaining("/api/queries/q1"),
        expect.objectContaining({ method: "DELETE" })
      );
    });
  });

  describe("error handling", () => {
    it("throws on non-ok response with detail", async () => {
      vi.spyOn(globalThis, "fetch").mockResolvedValue({
        ok: false,
        status: 403,
        json: () => Promise.resolve({ detail: "Forbidden" }),
      } as Response);

      await expect(api.getBrands()).rejects.toThrow("Forbidden");
    });

    it("throws generic error when no detail in response", async () => {
      vi.spyOn(globalThis, "fetch").mockResolvedValue({
        ok: false,
        status: 500,
        json: () => Promise.reject(new Error("parse error")),
      } as Response);

      await expect(api.getBrands()).rejects.toThrow("Request failed");
    });
  });
});
