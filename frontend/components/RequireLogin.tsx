"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { useLoggedIn } from "@/lib/api";

/** Shows its children only to a logged-in user; everyone else is sent to /login. */
export function RequireLogin({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const loggedIn = useLoggedIn();

  useEffect(() => {
    if (loggedIn === false) router.replace("/login");
  }, [loggedIn, router]);

  return loggedIn ? <>{children}</> : <p className="p-8 text-slate-500">Loading…</p>;
}
