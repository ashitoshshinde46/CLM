import { useState } from "react";
import { apiRequest } from "../api/client";
import DataTable from "./DataTable";
import PaginationControls from "./PaginationControls";
import { paginate } from "../utils/pagination";
import { positiveInteger, required } from "../utils/validation";

export default function ObligationsPanel({ token, notify }) {
  const [editingId, setEditingId] = useState(null);
  const [form, setForm] = useState({ contract_id: "", description: "", due_date: "", status: "pending" });
  const [items, setItems] = useState([]);
  const [page, setPage] = useState(1);
  const [formError, setFormError] = useState("");

  const validate = () => {
    const descriptionError = required(form.description, "Description");
    if (descriptionError) return descriptionError;
    if (!editingId) {
      return positiveInteger(form.contract_id, "Contract ID");
    }
    return null;
  };

  const saveObligation = async () => {
    const validationError = validate();
    if (validationError) {
      setFormError(validationError);
      notify(validationError, true);
      return;
    }

    try {
      setFormError("");
      if (editingId) {
        await apiRequest(`/api/obligations/${editingId}`, {
          method: "PUT",
          token,
          body: {
            description: form.description,
            due_date: form.due_date || null,
            status: form.status,
          },
        });
        notify("Obligation updated");
      } else {
        await apiRequest("/api/obligations", {
          method: "POST",
          token,
          body: {
            contract_id: Number(form.contract_id),
            description: form.description,
            due_date: form.due_date || null,
          },
        });
        notify("Obligation created");
      }
      resetForm();
      loadObligations();
    } catch (e) {
      notify(e.message, true);
    }
  };

  const loadObligations = async () => {
    try {
      const data = await apiRequest("/api/obligations", { token });
      setItems(data || []);
      setPage(1);
    } catch (e) {
      notify(e.message, true);
    }
  };

  const complete = async (id) => {
    try {
      await apiRequest(`/api/obligations/${id}/complete`, { method: "PUT", token });
      notify("Marked complete");
      loadObligations();
    } catch (e) {
      notify(e.message, true);
    }
  };

  const startEdit = (item) => {
    setEditingId(item.id);
    setForm({
      contract_id: String(item.contract_id),
      description: item.description || "",
      due_date: item.due_date || "",
      status: item.status || "pending",
    });
  };

  const remove = async (id) => {
    try {
      await apiRequest(`/api/obligations/${id}`, { method: "DELETE", token });
      notify("Obligation deleted");
      if (editingId === id) {
        resetForm();
      }
      loadObligations();
    } catch (e) {
      notify(e.message, true);
    }
  };

  const resetForm = () => {
    setEditingId(null);
    setFormError("");
    setForm({ contract_id: "", description: "", due_date: "", status: "pending" });
  };

  const columns = [
    { key: "id", header: "ID" },
    { key: "contract_id", header: "Contract" },
    { key: "description", header: "Description" },
    { key: "status", header: "Status" },
    {
      key: "due_date",
      header: "Due Date",
      render: (o) => o.due_date || "-",
    },
    {
      key: "actions",
      header: "Actions",
      render: (o) => (
        <div className="flex flex-wrap gap-2">
          {o.status !== "completed" && (
            <button className="btn-secondary" onClick={() => complete(o.id)}>Mark Complete</button>
          )}
          <button className="btn-secondary" onClick={() => startEdit(o)}>Edit</button>
          <button className="btn-secondary" onClick={() => remove(o.id)}>Delete</button>
        </div>
      ),
    },
  ];

  const paged = paginate(items, page, 8);

  return (
    <div className="grid gap-4 lg:grid-cols-2">
      <div className="card space-y-2">
        <h3 className="font-semibold">{editingId ? `Edit Obligation #${editingId}` : "Create Obligation"}</h3>
        <input className="input" placeholder="Contract ID" value={form.contract_id} onChange={(e) => setForm({ ...form, contract_id: e.target.value })} disabled={Boolean(editingId)} />
        <textarea className="input" placeholder="Description" value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
        <input className="input" type="date" value={form.due_date} onChange={(e) => setForm({ ...form, due_date: e.target.value })} />
        {editingId && (
          <select className="input" value={form.status} onChange={(e) => setForm({ ...form, status: e.target.value })}>
            <option value="pending">Pending</option>
            <option value="overdue">Overdue</option>
            <option value="completed">Completed</option>
          </select>
        )}
        {formError && <p className="text-xs text-rose-600">{formError}</p>}
        <div className="flex gap-2">
          <button className="btn" onClick={saveObligation}>{editingId ? "Update" : "Create"}</button>
          {editingId && <button className="btn-secondary" onClick={resetForm}>Cancel</button>}
        </div>
      </div>

      <div className="card">
        <div className="mb-2 flex items-center justify-between">
          <h3 className="font-semibold">Obligation Dashboard</h3>
          <button className="btn-secondary" onClick={loadObligations}>Refresh</button>
        </div>
        <DataTable columns={columns} rows={paged.rows} emptyMessage="No obligations available." />
        <PaginationControls page={paged.page} totalPages={paged.totalPages} onPageChange={setPage} />
      </div>
    </div>
  );
}
