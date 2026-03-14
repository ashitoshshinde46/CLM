import { useEffect, useState } from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { apiRequest } from "./api/client";
import AppShell from "./components/AppShell";
import ContractsPanel from "./components/ContractsPanel";
import DocumentsPanel from "./components/DocumentsPanel";
import LoginView from "./components/LoginView";
import ObligationsPanel from "./components/ObligationsPanel";
import ReportsPanel from "./components/ReportsPanel";
import RiskPanel from "./components/RiskPanel";
import Toast from "./components/Toast";
import WorkflowsPanel from "./components/WorkflowsPanel";

export default function App() {
  const [token, setToken] = useState(localStorage.getItem("clm_token") || "");
  const [loading, setLoading] = useState(false);
  const [toast, setToast] = useState("");

  const notify = (message, isError = false) => {
    setToast(`${isError ? "Error: " : ""}${message}`);
    setTimeout(() => setToast(""), 3000);
  };

  useEffect(() => {
    if (token) {
      localStorage.setItem("clm_token", token);
    } else {
      localStorage.removeItem("clm_token");
    }
  }, [token]);

  const handleLogin = async (credentials) => {
    setLoading(true);
    try {
      await apiRequest("/api/auth/seed-admin", { method: "POST" });
      const data = await apiRequest("/api/auth/login", {
        method: "POST",
        body: credentials,
      });
      setToken(data.access_token);
      notify("Login successful");
    } catch (e) {
      notify(e.message, true);
    } finally {
      setLoading(false);
    }
  };

  const logout = () => {
    setToken("");
  };

  if (!token) {
    return <LoginView onLogin={handleLogin} loading={loading} />;
  }

  const moduleProps = { token, notify };

  return (
    <BrowserRouter>
      <AppShell onLogout={logout}>
        <Toast message={toast} />
        <Routes>
          <Route path="/" element={<Navigate to="/contracts" replace />} />
          <Route path="/contracts" element={<ContractsPanel {...moduleProps} />} />
          <Route path="/workflows" element={<WorkflowsPanel {...moduleProps} />} />
          <Route path="/documents" element={<DocumentsPanel {...moduleProps} />} />
          <Route path="/obligations" element={<ObligationsPanel {...moduleProps} />} />
          <Route path="/risk" element={<RiskPanel {...moduleProps} />} />
          <Route path="/reports" element={<ReportsPanel {...moduleProps} />} />
          <Route path="*" element={<Navigate to="/contracts" replace />} />
        </Routes>
      </AppShell>
    </BrowserRouter>
  );
}
