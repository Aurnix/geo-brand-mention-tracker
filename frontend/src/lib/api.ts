const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

class ApiClient {
  private token: string | null = null;

  setToken(token: string) {
    this.token = token;
  }

  private async request<T>(path: string, options?: RequestInit): Promise<T> {
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
      ...(options?.headers as Record<string, string>),
    };

    if (this.token) {
      headers["Authorization"] = `Bearer ${this.token}`;
    }

    const res = await fetch(`${API_URL}${path}`, {
      ...options,
      headers,
    });

    if (!res.ok) {
      const error = await res
        .json()
        .catch(() => ({ detail: "Request failed" }));
      throw new Error(error.detail || `HTTP ${res.status}`);
    }

    if (res.status === 204) return undefined as T;

    return res.json();
  }

  // Auth
  async signup(email: string, password: string) {
    return this.request<{ access_token: string; token_type: string }>(
      "/api/auth/signup",
      {
        method: "POST",
        body: JSON.stringify({ email, password }),
      }
    );
  }

  async login(email: string, password: string) {
    return this.request<{ access_token: string; token_type: string }>(
      "/api/auth/login",
      {
        method: "POST",
        body: JSON.stringify({ email, password }),
      }
    );
  }

  async getMe() {
    return this.request<any>("/api/auth/me");
  }

  // Brands
  async getBrands() {
    return this.request<any[]>("/api/brands");
  }

  async createBrand(data: { name: string; aliases?: string[] }) {
    return this.request<any>("/api/brands", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async getBrand(id: string) {
    return this.request<any>(`/api/brands/${id}`);
  }

  async updateBrand(id: string, data: { name?: string; aliases?: string[] }) {
    return this.request<any>(`/api/brands/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    });
  }

  async deleteBrand(id: string) {
    return this.request<void>(`/api/brands/${id}`, {
      method: "DELETE",
    });
  }

  async triggerRun(brandId: string) {
    return this.request<any>(`/api/brands/${brandId}/run`, {
      method: "POST",
    });
  }

  // Competitors
  async getCompetitors(brandId: string) {
    return this.request<any[]>(`/api/brands/${brandId}/competitors`);
  }

  async addCompetitor(
    brandId: string,
    data: { name: string; aliases?: string[] }
  ) {
    return this.request<any>(`/api/brands/${brandId}/competitors`, {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async deleteCompetitor(id: string, brandId?: string) {
    // If brandId provided, use the nested path; otherwise try the flat path
    const path = brandId
      ? `/api/brands/${brandId}/competitors/${id}`
      : `/api/competitors/${id}`;
    return this.request<void>(path, {
      method: "DELETE",
    });
  }

  // Queries
  async getQueries(brandId: string) {
    return this.request<any[]>(`/api/brands/${brandId}/queries`);
  }

  async addQuery(
    brandId: string,
    data: { query_text: string; category?: string }
  ) {
    return this.request<any>(`/api/brands/${brandId}/queries`, {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async updateQuery(
    id: string,
    data: { query_text?: string; category?: string; is_active?: boolean }
  ) {
    return this.request<any>(`/api/queries/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    });
  }

  async deleteQuery(id: string) {
    return this.request<void>(`/api/queries/${id}`, {
      method: "DELETE",
    });
  }

  // Results
  async getOverview(brandId: string) {
    return this.request<any>(`/api/brands/${brandId}/overview`);
  }

  async getResults(brandId: string, params?: Record<string, string>) {
    const qs = params ? "?" + new URLSearchParams(params).toString() : "";
    return this.request<any>(`/api/brands/${brandId}/results${qs}`);
  }

  async getQueryHistory(queryId: string) {
    return this.request<any[]>(`/api/queries/${queryId}/history`);
  }

  async getCompetitorComparison(brandId: string) {
    return this.request<any>(`/api/brands/${brandId}/competitors/comparison`);
  }
}

export const api = new ApiClient();
