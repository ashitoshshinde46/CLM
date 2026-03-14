import { useState } from "react";
import { apiRequest } from "../api/client";
import DataTable from "./DataTable";
import PaginationControls from "./PaginationControls";
import { paginate } from "../utils/pagination";
import { positiveInteger } from "../utils/validation";

export default function WorkflowsPanel({ token, notify }) {
  const [contractId, setContractId] = useState("");
  const [approverId, setApproverId] = useState("");
  const [workflowId, setWorkflowId] = useState("");
  const [tasks, setTasks] = useState([]);
  const [page, setPage] = useState(1);
  const [error, setError] = useState("");

  const startWorkflow = async () => {
    const contractError = positiveInteger(contractId, "Contract ID");
    if (contractError) {
      setError(contractError);
      notify(contractError, true);
      return;
    }
    const approverError = positiveInteger(approverId, "Approver User ID");
    if (approverError) {
      setError(approverError);
      notify(approverError, true);
      return;
    }

    try {
      setError("");
      await apiRequest(`/api/workflows/${contractId}/start`, {
        method: "POST",
        token,
        body: {
          workflow_type: "standard",
          initial_stage: "legal_review",
          approvers: [{ user_id: Number(approverId), stage: "legal_review", status: "pending" }],
        },
      });
      notify("Workflow started");
    } catch (e) {
      notify(e.message, true);
    }
  };

  const approve = async (action) => {
    const workflowError = positiveInteger(workflowId, "Workflow ID");
    if (workflowError) {
      setError(workflowError);
      notify(workflowError, true);
      return;
    }

    try {
      setError("");
      await apiRequest(`/api/workflows/${workflowId}/${action}`, {
        method: "POST",
        token,
        body: { comments: `${action} via UI` },
      });
      notify(`Workflow ${action} done`);
    } catch (e) {
      notify(e.message, true);
    }
  };

  const loadTasks = async () => {
    try {
      const data = await apiRequest("/api/workflows/my-tasks/list", { token });
      setTasks(data || []);
      setPage(1);
    } catch (e) {
      notify(e.message, true);
    }
  };

  const columns = [
    { key: "id", header: "Workflow ID" },
    { key: "contract_id", header: "Contract ID" },
    { key: "current_stage", header: "Current Stage" },
    {
      key: "workflow_type",
      header: "Type",
      render: (t) => t.workflow_type || "standard",
    },
  ];

  const paged = paginate(tasks, page, 8);

  return (
    <div className="grid gap-4 lg:grid-cols-2">
      <div className="card space-y-3">
        <h3 className="font-semibold">Workflow Actions</h3>
        <input className="input" placeholder="Contract ID" value={contractId} onChange={(e) => setContractId(e.target.value)} />
        <input className="input" placeholder="Approver User ID" value={approverId} onChange={(e) => setApproverId(e.target.value)} />
        <button className="btn" onClick={startWorkflow}>Start Workflow</button>
        <hr />
        <input className="input" placeholder="Workflow ID" value={workflowId} onChange={(e) => setWorkflowId(e.target.value)} />
        <div className="flex gap-2">
          <button className="btn-secondary" onClick={() => approve("approve")}>Approve</button>
          <button className="btn-secondary" onClick={() => approve("reject")}>Reject</button>
        </div>
        {error && <p className="text-xs text-rose-600">{error}</p>}
      </div>

      <div className="card">
        <div className="mb-2 flex items-center justify-between">
          <h3 className="font-semibold">My Tasks</h3>
          <button className="btn-secondary" onClick={loadTasks}>Refresh</button>
        </div>
        <DataTable columns={columns} rows={paged.rows} emptyMessage="No pending tasks loaded." />
        <PaginationControls page={paged.page} totalPages={paged.totalPages} onPageChange={setPage} />
      </div>
    </div>
  );
}
