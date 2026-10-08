"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { token, useLoggedIn } from "@/lib/api";

const LINKS = [
  { href: "/", label: "Inbox" },
  { href: "/stats", label: "Stats" },
  { href: "/new", label: "New message" },
];

export function Nav() {
  const pathname = usePathname();
  const router = useRouter();
  const loggedIn = useLoggedIn();

  function logout() {
    token.clear();
    router.push("/login");
  }

  return (
    <header className="border-b border-slate-200 bg-white">
      <nav className="mx-auto flex max-w-6xl flex-wrap items-center gap-x-6 gap-y-2 px-4 py-3">
        <Link href="/" className="text-lg font-semibold text-slate-900">
          ReplyDesk
        </Link>
        {LINKS.map((link) => (
          <Link
            key={link.href}
            href={link.href}
            className={
              pathname === link.href
                ? "font-medium text-slate-900"
                : "text-slate-500 hover:text-slate-900"
            }
          >
            {link.label}
          </Link>
        ))}
        <span className="ml-auto">
          {loggedIn ? (
            <button onClick={logout} className="text-slate-500 hover:text-slate-900">
              Log out
            </button>
          ) : (
            <Link href="/login" className="text-slate-500 hover:text-slate-900">
              Staff login
            </Link>
          )}
        </span>
      </nav>
    </header>
  );
}
