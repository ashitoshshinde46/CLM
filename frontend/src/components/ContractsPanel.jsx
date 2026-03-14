import { useEffect, useState } from "react";
import { apiRequest } from "../api/client";
import DataTable from "./DataTable";
import PaginationControls from "./PaginationControls";
import { paginate } from "../utils/pagination";
import { nonNegativeNumber, required } from "../utils/validation";

export default function ContractsPanel({ token, notify }) {
  const [contracts, setContracts] = useState([]);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [formError, setFormError] = useState("");
  const [editingId, setEditingId] = useState(null);
  const [form, setForm] = useState({
    title: "",
    contract_type: "service",
    vendor_name: "",
    amount: "",
    status: "draft",
  });

  const loadContracts = async () => {
    try {
      const data = await apiRequest("/api/contracts", { token });
      setContracts(data.items || []);
    } catch (e) {
      notify(e.message, true);
    }
  };

  useEffect(() => {
    loadContracts();
  }, [token]);

  const validate = () => {
    const titleError = required(form.title, "Title");
    if (titleError) return titleError;
    return nonNegativeNumber(form.amount, "Amount");
  };

  const saveContract = async (e) => {
    e.preventDefault();
    const validationError = validate();
    if (validationError) {
      setFormError(validationError);
      notify(validationError, true);
      return;
    }

    try {
      setFormError("");
      const payload = {
        ...form,
        amount: form.amount ? Number(form.amount) : null,
      };

      if (editingId) {
        await apiRequest(`/api/contracts/${editingId}`, {
          method: "PUT",
          token,
          body: payload,
        });
        notify("Contract updated");
      } else {
        await apiRequest("/api/contracts", {
          method: "POST",
          token,
          body: payload,
        });
        notify("Contract created");
      }

      resetForm();
      loadContracts();
    } catch (err) {
      notify(err.message, true);
    }
  };

  const startEdit = (contract) => {
    setEditingId(contract.id);
    setForm({
      title: contract.title || "",
      contract_type: contract.contract_type || "service",
      vendor_name: contract.vendor_name || "",
      amount: contract.amount ?? "",
      status: contract.status || "draft",
    });
  };

  const removeContract = async (id) => {
    try {
      await apiRequest(`/api/contracts/${id}`, { method: "DELETE", token });
      notify("Contract deleted");
      if (editingId === id) {
        resetForm();
      }
      loadContracts();
    } catch (err) {
      notify(err.message, true);
    }
  };

  const resetForm = () => {
    setEditingId(null);
    setFormError("");
    setForm({ title: "", contract_type: "service", vendor_name: "", amount: "", status: "draft" });
  };

  const doSearch = async () => {
    try {
      if (!search) return loadContracts();
      const data = await apiRequest("/api/contracts/search", {
        method: "POST",
        token,
        body: { query: search },
      });
      setContracts(data.items || []);
      setPage(1);
    } catch (err) {
      notify(err.message, true);
    }
  };

  const tableColumns = [
    {
      key: "title",
      header: "Contract",
      render: (c) => (
        <div>
          <div className="font-medium">{c.title}</div>
          <div className="text-xs text-slate-500">{c.contract_number}</div>
        </div>
      ),
    },
    { key: "contract_type", header: "Type" },
    { key: "status", header: "Status" },
    {
      key: "vendor_name",
      header: "Vendor",
      render: (c) => c.vendor_name || "-",
    },
    {
      key: "amount",
      header: "Amount",
      render: (c) => (c.amount ?? "-"),
    },
    {
      key: "actions",
      header: "Actions",
      render: (c) => (
        <div className="flex gap-2">
          <button className="btn-secondary" onClick={() => startEdit(c)}>Edit</button>
          <button className="btn-secondary" onClick={() => removeContract(c.id)}>Delete</button>
        </div>
      ),
    },
  ];

  const paged = paginate(contracts, page, 8);

  return (
    <div className="grid gap-4 lg:grid-cols-2">
      <div className="card">
        <h3 className="mb-3 font-semibold">{editingId ? `Edit Contract #${editingId}` : "Create Contract"}</h3>
        <form className="space-y-2" onSubmit={saveContract}>
          <input className="input" placeholder="Title" value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} required />
          <select className="input" value={form.contract_type} onChange={(e) => setForm({ ...form, contract_type: e.target.value })}>
            <option value="service">Service</option>
            <option value="vendor">Vendor</option>
            <option value="employee">Employee</option>
            <option value="lease">Lease</option>
            <option value="nda">NDA</option>
          </select>
          {editingId && (
            <select className="input" value={form.status} onChange={(e) => setForm({ ...form, status: e.target.value })}>
              <option value="draft">Draft</option>
              <option value="sent">Sent</option>
              <option value="negotiating">Negotiating</option>
              <option value="signed">Signed</option>
              <option value="active">Active</option>
              <option value="expired">Expired</option>
              <option value="terminated">Terminated</option>
            </select>
          )}
          <input className="input" placeholder="Vendor Name" value={form.vendor_name} onChange={(e) => setForm({ ...form, vendor_name: e.target.value })} />
          <input className="input" placeholder="Amount" type="number" value={form.amount} onChange={(e) => setForm({ ...form, amount: e.target.value })} />
          {formError && <p className="text-xs text-rose-600">{formError}</p>}
          <div className="flex gap-2">
            <button className="btn" type="submit">{editingId ? "Update" : "Create"}</button>
            {editingId && (
              <button className="btn-secondary" type="button" onClick={resetForm}>Cancel</button>
            )}
          </div>
        </form>
      </div>

      <div className="card">
        <div className="mb-3 flex gap-2">
          <input className="input" placeholder="Search by title/vendor/number" value={search} onChange={(e) => setSearch(e.target.value)} />
          <button className="btn-secondary" onClick={doSearch}>Search</button>
        </div>
        <DataTable columns={tableColumns} rows={paged.rows} emptyMessage="No contracts found." />
        <PaginationControls page={paged.page} totalPages={paged.totalPages} onPageChange={setPage} />
      </div>
    </div>
  );
}
