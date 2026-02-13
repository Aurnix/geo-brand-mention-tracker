"use client";

import { useState } from "react";
import { signIn } from "next-auth/react";
import { useRouter } from "next/navigation";
import { Loader2, Play } from "lucide-react";

const DEMO_EMAIL = "demo@geotrack.ai";
const DEMO_PASSWORD = "demo1234";

export default function DemoLoginButton() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleDemoLogin() {
    setLoading(true);
    setError("");

    try {
      const result = await signIn("credentials", {
        email: DEMO_EMAIL,
        password: DEMO_PASSWORD,
        redirect: false,
      });

      if (result?.error) {
        setError("Demo account unavailable. Run the seed script first.");
        setLoading(false);
        return;
      }

      router.push("/dashboard");
    } catch {
      setError("Something went wrong. Please try again.");
      setLoading(false);
    }
  }

  return (
    <div className="flex flex-col items-center gap-2">
      <button
        onClick={handleDemoLogin}
        disabled={loading}
        className="btn-secondary inline-flex items-center gap-2 px-6 py-3 text-base"
      >
        {loading ? (
          <Loader2 className="h-4 w-4 animate-spin" />
        ) : (
          <Play className="h-4 w-4" />
        )}
        {loading ? "Loading demo..." : "Try live demo"}
      </button>
      {error && (
        <p className="text-sm text-red-600">{error}</p>
      )}
    </div>
  );
}
