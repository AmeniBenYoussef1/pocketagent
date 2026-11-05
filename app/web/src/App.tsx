import { useEffect, useState } from "react";
import { NavLink, Route, Routes } from "react-router-dom";
import { ErrorBoundary } from "./components/ErrorBoundary";
import { cx } from "./components/ui";
import Assistant from "./pages/Assistant";
import HowItWorks from "./pages/HowItWorks";
import Results from "./pages/Results";

function ThemeToggle() {
  const [dark, setDark] = useState(() => document.documentElement.classList.contains("dark"));
  useEffect(() => {
    document.documentElement.classList.toggle("dark", dark);
    localStorage.setItem("theme", dark ? "dark" : "light");
  }, [dark]);
  return (
    <button
      onClick={() => setDark((d) => !d)}
      aria-label={dark ? "Switch to light mode" : "Switch to dark mode"}
      className="ease label rounded-full border border-line px-3 py-1.5 hover:border-terracotta hover:text-ink"
    >
      {dark ? "Light" : "Dark"}
    </button>
  );
}

const LINKS = [
  { to: "/", label: "Assistant" },
  { to: "/results", label: "Results" },
  { to: "/how-it-works", label: "How it works" },
];

export default function App() {
  return (
    <div className="min-h-screen">
      <header className="sticky top-0 z-20 border-b border-line bg-page/85 backdrop-blur">
        <div className="mx-auto flex max-w-[1280px] flex-wrap items-center justify-between gap-4 px-5 py-4 sm:px-8">
          <NavLink to="/" className="font-display text-2xl leading-none">
            Pocket<em>Agent</em>
          </NavLink>
          <nav className="flex items-center gap-1" aria-label="Pages">
            {LINKS.map((l) => (
              <NavLink
                key={l.to}
                to={l.to}
                end
                className={({ isActive }) =>
                  cx("ease rounded-full px-3 py-1.5 text-sm", isActive ? "bg-card text-fn font-medium" : "text-ink-2 hover:text-ink")
                }
              >
                {l.label}
              </NavLink>
            ))}
          </nav>
          <ThemeToggle />
        </div>
      </header>
      <main className="mx-auto max-w-[1280px] px-5 py-8 sm:px-8 sm:py-12">
        <ErrorBoundary>
        <Routes>
          <Route path="/" element={<Assistant />} />
          <Route path="/results" element={<Results />} />
          <Route path="/how-it-works" element={<HowItWorks />} />
          <Route path="*" element={<p className="text-ink-2">This page doesn't exist.</p>} />
        </Routes>
        </ErrorBoundary>
      </main>
      
    </div>
  );
}
