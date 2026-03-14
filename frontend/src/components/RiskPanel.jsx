import { useState } from "react";
import { apiRequest } from "../api/client";
import DataTable from "./DataTable";
import PaginationControls from "./PaginationControls";
import { paginate } from "../utils/pagination";
import { positiveInteger } from "../utils/validation";

export default function RiskPanel({ token, notify }) {
  const [contractId, setContractId] = useState("");
  const [report, setReport] = useState(null);
  const [dashboard, setDashboard] = useState({ by_vendor: [], by_type: [] });
  const [vendorPage, setVendorPage] = useState(1);
  const [typePage, setTypePage] = useState(1);
  const [error, setError] = useState("");

  const assess = async () => {
    const validationError = positiveInteger(contractId, "Contract ID");
    if (validationError) {
      setError(validationError);
      notify(validationError, true);
      return;
    }

    try {
      setError("");
      const data = await apiRequest(`/api/risk/assess/${contractId}`, { method: "POST", token });
      setReport(data);
      notify("Risk assessed");
    } catch (e) {
      notify(e.message, true);
    }
  };

  const loadReport = async () => {
    const validationError = positiveInteger(contractId, "Contract ID");
    if (validationError) {
      setError(validationError);
      notify(validationError, true);
      return;
    }

    try {
      setError("");
      const data = await apiRequest(`/api/risk/${contractId}`, { token });
      setReport(data);
    } catch (e) {
      notify(e.message, true);
    }
  };

  const loadDashboard = async () => {
    try {
      const data = await apiRequest("/api/risk/dashboard", { token });
      setDashboard(data);
      setVendorPage(1);
      setTypePage(1);
    } catch (e) {
      notify(e.message, true);
    }
  };

  const riskColumns = [
    { key: "grouping_key", header: "Group" },
    { key: "total_contracts", header: "Contracts" },
    { key: "average_risk_score", header: "Avg Risk Score" },
  ];

  const vendorsPaged = paginate(dashboard.by_vendor || [], vendorPage, 6);
  const typesPaged = paginate(dashboard.by_type || [], typePage, 6);

  return (
    <div className="grid gap-4 lg:grid-cols-2">
      <div className="card space-y-2">
        <h3 className="font-semibold">Risk Assessment</h3>
        <input className="input" placeholder="Contract ID" value={contractId} onChange={(e) => setContractId(e.target.value)} />
        <div className="flex gap-2">
          <button className="btn" onClick={assess}>Assess</button>
          <button className="btn-secondary" onClick={loadReport}>Load Latest</button>
        </div>
        {error && <p className="text-xs text-rose-600">{error}</p>}
        {report && (
          <div className="rounded border border-slate-200 p-2 text-sm">
            <div>Score: {report.risk_score}</div>
            <div>Status: {report.compliance_status}</div>
            <div>Findings: {report.high_risk_clauses?.length || 0}</div>
          </div>
        )}
      </div>

      <div className="card">
        <div className="mb-2 flex items-center justify-between">
          <h3 className="font-semibold">Risk Dashboard</h3>
          <button className="btn-secondary" onClick={loadDashboard}>Refresh</button>
        </div>
        <div className="space-y-4 text-sm">
          <div>
            <p className="mb-2 font-medium">By Vendor</p>
            <DataTable columns={riskColumns} rows={vendorsPaged.rows} emptyMessage="No vendor data." />
            <PaginationControls page={vendorsPaged.page} totalPages={vendorsPaged.totalPages} onPageChange={setVendorPage} />
          </div>
          <div>
            <p className="mb-2 font-medium">By Type</p>
            <DataTable columns={riskColumns} rows={typesPaged.rows} emptyMessage="No type data." />
            <PaginationControls page={typesPaged.page} totalPages={typesPaged.totalPages} onPageChange={setTypePage} />
          </div>
        </div>
      </div>
    </div>
  );
}
