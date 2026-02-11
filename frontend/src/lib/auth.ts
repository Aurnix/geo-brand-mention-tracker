"use client";

import { useSession } from "next-auth/react";
import { useEffect } from "react";
import { api } from "./api";

export function useAuth() {
  const { data: session, status } = useSession();

  useEffect(() => {
    if ((session as any)?.accessToken) {
      api.setToken((session as any).accessToken);
    }
  }, [session]);

  return {
    session,
    status,
    isLoading: status === "loading",
    isAuthenticated: status === "authenticated",
    token: (session as any)?.accessToken as string | undefined,
    userId: (session as any)?.userId as string | undefined,
    planTier: (session as any)?.planTier as string | undefined,
  };
}
