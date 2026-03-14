import { NavLink } from "react-router-dom";

const NAV_ITEMS = [
  { label: "Contracts", path: "/contracts" },
  { label: "Workflows", path: "/workflows" },
  { label: "Documents", path: "/documents" },
  { label: "Obligations", path: "/obligations" },
  { label: "Risk", path: "/risk" },
  { label: "Reports", path: "/reports" },
];

export default function AppShell({ children, onLogout }) {
  return (
    <div className="min-h-screen bg-slate-100 p-4 md:p-6">
      <div className="mx-auto max-w-7xl space-y-4">
        <header className="flex flex-wrap items-center justify-between gap-2 rounded-xl bg-white p-4 shadow-sm">
          <div>
            <h1 className="text-lg font-semibold">GCC Lightweight CLM</h1>
            <p className="text-sm text-slate-500">Single-entity deployment | Phases 1-3 UI</p>
          </div>
          <button className="btn-secondary" onClick={onLogout}>Logout</button>
        </header>

        <nav className="flex flex-wrap gap-2">
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                `rounded px-3 py-2 text-sm ${isActive ? "bg-indigo-600 text-white" : "bg-white text-slate-700"}`
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>

        {children}
      </div>
    </div>
  );
}
