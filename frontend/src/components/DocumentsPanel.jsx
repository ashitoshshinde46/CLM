import { useState } from "react";
import { apiRequest } from "../api/client";
import DataTable from "./DataTable";
import PaginationControls from "./PaginationControls";
import { paginate } from "../utils/pagination";
import { positiveInteger, required } from "../utils/validation";

export default function DocumentsPanel({ token, notify }) {
  const [contractId, setContractId] = useState("");
  const [filePath, setFilePath] = useState("");
  const [versions, setVersions] = useState([]);
  const [versionsPage, setVersionsPage] = useState(1);
  const [clausePage, setClausePage] = useState(1);
  const [clause, setClause] = useState({ name: "", category: "", content: "", tags: "" });
  const [editingClauseId, setEditingClauseId] = useState(null);
  const [selectedClauseIds, setSelectedClauseIds] = useState([]);
  const [template, setTemplate] = useState("Contract Template\n\nScope:\n");
  const [generatedDoc, setGeneratedDoc] = useState("");
  const [clauses, setClauses] = useState([]);
  const [versionError, setVersionError] = useState("");
  const [clauseError, setClauseError] = useState("");

  const uploadVersion = async () => {
    const contractError = positiveInteger(contractId, "Contract ID");
    if (contractError) {
      setVersionError(contractError);
      notify(contractError, true);
      return;
    }
    const fileError = required(filePath, "File path");
    if (fileError) {
      setVersionError(fileError);
      notify(fileError, true);
      return;
    }

    try {
      setVersionError("");
      await apiRequest(`/api/documents/${contractId}/version`, {
        method: "POST",
        token,
        body: { file_path: filePath, changes_summary: "Uploaded from frontend" },
      });
      notify("Version uploaded");
      loadVersions();
    } catch (e) {
      notify(e.message, true);
    }
  };

  const loadVersions = async () => {
    const contractError = positiveInteger(contractId, "Contract ID");
    if (contractError) {
      setVersionError(contractError);
      notify(contractError, true);
      return;
    }

    try {
      setVersionError("");
      const data = await apiRequest(`/api/documents/${contractId}/versions`, { token });
      setVersions(data || []);
      setVersionsPage(1);
    } catch (e) {
      notify(e.message, true);
    }
  };

  const saveClause = async () => {
    const nameError = required(clause.name, "Clause name");
    if (nameError) {
      setClauseError(nameError);
      notify(nameError, true);
      return;
    }
    const contentError = required(clause.content, "Clause content");
    if (contentError) {
      setClauseError(contentError);
      notify(contentError, true);
      return;
    }

    try {
      setClauseError("");
      const payload = {
        ...clause,
        tags: clause.tags ? clause.tags.split(",").map((tag) => tag.trim()).filter(Boolean) : null,
      };
      if (editingClauseId) {
        await apiRequest(`/api/clauses/${editingClauseId}`, { method: "PUT", token, body: payload });
        notify("Clause updated");
      } else {
        await apiRequest("/api/clauses", { method: "POST", token, body: payload });
        notify("Clause created");
      }
      resetClauseForm();
      loadClauses();
    } catch (e) {
      notify(e.message, true);
    }
  };

  const startClauseEdit = (item) => {
    setEditingClauseId(item.id);
    setClause({
      name: item.name || "",
      category: item.category || "",
      content: item.content || "",
      tags: item.tags?.join(", ") || "",
    });
  };

  const resetClauseForm = () => {
    setEditingClauseId(null);
    setClauseError("");
    setClause({ name: "", category: "", content: "", tags: "" });
  };

  const deleteClause = async (id) => {
    try {
      await apiRequest(`/api/clauses/${id}`, { method: "DELETE", token });
      notify("Clause deleted");
      if (editingClauseId === id) {
        resetClauseForm();
      }
      setSelectedClauseIds((prev) => prev.filter((value) => value !== id));
      loadClauses();
    } catch (e) {
      notify(e.message, true);
    }
  };

  const markClauseUsed = async (id) => {
    try {
      await apiRequest(`/api/clauses/${id}/use`, { method: "POST", token });
      notify("Clause usage tracked");
      loadClauses();
    } catch (e) {
      notify(e.message, true);
    }
  };

  const toggleClauseSelection = (id) => {
    setSelectedClauseIds((prev) =>
      prev.includes(id) ? prev.filter((value) => value !== id) : [...prev, id]
    );
  };

  const generateDocument = async () => {
    if (!selectedClauseIds.length) {
      const message = "Select at least one clause to generate";
      notify(message, true);
      return;
    }
    const templateError = required(template, "Template");
    if (templateError) {
      notify(templateError, true);
      return;
    }

    try {
      const data = await apiRequest("/api/clauses/generate", {
        method: "POST",
        token,
        body: {
          template,
          clause_ids: selectedClauseIds,
        },
      });
      setGeneratedDoc(data.generated_document || "");
      notify("Document generated");
    } catch (e) {
      notify(e.message, true);
    }
  };

  const deleteVersion = async (versionId) => {
    try {
      await apiRequest(`/api/documents/versions/${versionId}`, { method: "DELETE", token });
      notify("Version deleted");
      loadVersions();
    } catch (e) {
      notify(e.message, true);
    }
  };

  const loadClauses = async () => {
    try {
      const data = await apiRequest("/api/clauses", { token });
      setClauses(data || []);
      setClausePage(1);
    } catch (e) {
      notify(e.message, true);
    }
  };

  const versionColumns = [
    { key: "version_number", header: "Version", render: (v) => `v${v.version_number}` },
    { key: "file_path", header: "File Path" },
    { key: "created_by", header: "Created By" },
    {
      key: "actions",
      header: "Actions",
      render: (v) => <button className="btn-secondary" onClick={() => deleteVersion(v.id)}>Delete</button>,
    },
  ];

  const clauseColumns = [
    {
      key: "select",
      header: "Select",
      render: (c) => (
        <input
          type="checkbox"
          checked={selectedClauseIds.includes(c.id)}
          onChange={() => toggleClauseSelection(c.id)}
        />
      ),
    },
    { key: "name", header: "Name" },
    {
      key: "category",
      header: "Category",
      render: (c) => c.category || "-",
    },
    {
      key: "usage_count",
      header: "Usage",
    },
    {
      key: "actions",
      header: "Actions",
      render: (c) => (
        <div className="flex flex-wrap gap-2">
          <button className="btn-secondary" onClick={() => startClauseEdit(c)}>Edit</button>
          <button className="btn-secondary" onClick={() => deleteClause(c.id)}>Delete</button>
          <button className="btn-secondary" onClick={() => markClauseUsed(c.id)}>Use</button>
        </div>
      ),
    },
  ];

  const pagedVersions = paginate(versions, versionsPage, 6);
  const pagedClauses = paginate(clauses, clausePage, 6);

  return (
    <div className="grid gap-4 lg:grid-cols-2">
      <div className="card space-y-2">
        <h3 className="font-semibold">Versions</h3>
        <input className="input" placeholder="Contract ID" value={contractId} onChange={(e) => setContractId(e.target.value)} />
        <input className="input" placeholder="File path" value={filePath} onChange={(e) => setFilePath(e.target.value)} />
        <div className="flex gap-2">
          <button className="btn" onClick={uploadVersion}>Upload Version</button>
          <button className="btn-secondary" onClick={loadVersions}>Load History</button>
        </div>
        {versionError && <p className="text-xs text-rose-600">{versionError}</p>}
        <DataTable columns={versionColumns} rows={pagedVersions.rows} emptyMessage="No versions loaded." />
        <PaginationControls page={pagedVersions.page} totalPages={pagedVersions.totalPages} onPageChange={setVersionsPage} />
      </div>

      <div className="card space-y-2">
        <h3 className="font-semibold">Clause Library</h3>
        <input className="input" placeholder="Name" value={clause.name} onChange={(e) => setClause({ ...clause, name: e.target.value })} />
        <input className="input" placeholder="Category" value={clause.category} onChange={(e) => setClause({ ...clause, category: e.target.value })} />
        <input className="input" placeholder="Tags (comma separated)" value={clause.tags} onChange={(e) => setClause({ ...clause, tags: e.target.value })} />
        <textarea className="input" placeholder="Clause content" value={clause.content} onChange={(e) => setClause({ ...clause, content: e.target.value })} />
        <div className="flex gap-2">
          <button className="btn" onClick={saveClause}>{editingClauseId ? "Update Clause" : "Add Clause"}</button>
          {editingClauseId && <button className="btn-secondary" onClick={resetClauseForm}>Cancel</button>}
          <button className="btn-secondary" onClick={loadClauses}>Load Clauses</button>
        </div>
        {clauseError && <p className="text-xs text-rose-600">{clauseError}</p>}
        <DataTable columns={clauseColumns} rows={pagedClauses.rows} emptyMessage="No clauses loaded." />
        <PaginationControls page={pagedClauses.page} totalPages={pagedClauses.totalPages} onPageChange={setClausePage} />

        <textarea
          className="input"
          placeholder="Template text"
          value={template}
          onChange={(e) => setTemplate(e.target.value)}
        />
        <button className="btn-secondary" onClick={generateDocument}>Generate from selected clauses</button>
        {generatedDoc && <pre className="max-h-40 overflow-auto rounded bg-slate-100 p-2 text-xs">{generatedDoc}</pre>}
      </div>
    </div>
  );
}
