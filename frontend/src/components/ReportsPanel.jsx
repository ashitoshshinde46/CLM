import { useState } from "react";
import { apiRequest } from "../api/client";
import DataTable from "./DataTable";
import PaginationControls from "./PaginationControls";
import { paginate } from "../utils/pagination";
import { validYear } from "../utils/validation";

export default function ReportsPanel({ token, notify }) {
  const [spend, setSpend] = useState(null);
  const [custom, setCustom] = useState(null);
  const [vendor, setVendor] = useState("");
  const [year, setYear] = useState("");
  const [groupBy, setGroupBy] = useState("status");
  const [metric, setMetric] = useState("count");
  const [customPage, setCustomPage] = useState(1);
  const [error, setError] = useState("");

  const loadSpend = async () => {
    const yearError = validYear(year);
    if (yearError) {
      setError(yearError);
      notify(yearError, true);
      return;
    }

    try {
      setError("");
      const q = new URLSearchParams();
      if (vendor) q.set("vendor", vendor);
      if (year) q.set("year", year);
      const data = await apiRequest(`/api/analytics/spend${q.toString() ? `?${q}` : ""}`, { token });
      setSpend(data);
    } catch (e) {
      notify(e.message, true);
    }
  };

  const loadCustom = async () => {
    const yearError = validYear(year);
    if (yearError) {
      setError(yearError);
      notify(yearError, true);
      return;
    }

    try {
      setError("");
      const data = await apiRequest("/api/reports/custom", {
        method: "POST",
        token,
        body: { group_by: groupBy, metric, year: year ? Number(year) : null },
      });
      setCustom(data);
      setCustomPage(1);
    } catch (e) {
      notify(e.message, true);
    }
  };

  const openAgingCsv = () => {
    apiRequest("/api/reports/contracts-aging?format=csv", { token })
      .then((csvText) => {
        const blob = new Blob([csvText], { type: "text/csv;charset=utf-8;" });
        const url = URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.href = url;
        link.setAttribute("download", "contracts_aging.csv");
        document.body.appendChild(link);
        link.click();
        link.remove();
        URL.revokeObjectURL(url);
      })
      .catch((e) => notify(e.message, true));
  };

  const customColumns = [
    { key: "key", header: "Group" },
    { key: "value", header: "Value" },
  ];
  const pagedCustom = paginate(custom?.items || [], customPage, 8);

  return (
    <div className="grid gap-4 lg:grid-cols-2">
      <div className="card space-y-2">
        <h3 className="font-semibold">Spend Analytics</h3>
        <input className="input" placeholder="Vendor (optional)" value={vendor} onChange={(e) => setVendor(e.target.value)} />
        <input className="input" placeholder="Year (optional)" value={year} onChange={(e) => setYear(e.target.value)} />
        <div className="grid grid-cols-2 gap-2">
          <select className="input" value={groupBy} onChange={(e) => setGroupBy(e.target.value)}>
            <option value="status">Group by Status</option>
            <option value="vendor">Group by Vendor</option>
            <option value="type">Group by Type</option>
          </select>
          <select className="input" value={metric} onChange={(e) => setMetric(e.target.value)}>
            <option value="count">Count</option>
            <option value="sum_amount">Sum Amount</option>
            <option value="avg_amount">Average Amount</option>
          </select>
        </div>
        <div className="flex gap-2">
          <button className="btn" onClick={loadSpend}>Load Spend</button>
          <button className="btn-secondary" onClick={loadCustom}>Custom Report</button>
          <button className="btn-secondary" onClick={openAgingCsv}>Aging CSV</button>
        </div>
        {error && <p className="text-xs text-rose-600">{error}</p>}
        {spend && <pre className="rounded bg-slate-100 p-2 text-xs">{JSON.stringify(spend, null, 2)}</pre>}
      </div>

      <div className="card">
        <h3 className="mb-2 font-semibold">Custom Report Result</h3>
        {custom ? (
          <>
            <DataTable columns={customColumns} rows={pagedCustom.rows} emptyMessage="No rows." />
            <PaginationControls page={pagedCustom.page} totalPages={pagedCustom.totalPages} onPageChange={setCustomPage} />
          </>
        ) : (
          <p className="text-sm text-slate-500">Run custom report to view grouped metrics.</p>
        )}
      </div>
    </div>
  );
}
