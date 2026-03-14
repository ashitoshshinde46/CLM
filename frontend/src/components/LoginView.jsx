import { useState } from "react";

export default function LoginView({ onLogin, loading }) {
  const [email, setEmail] = useState("admin@example.com");
  const [password, setPassword] = useState("Admin@123");

  const submit = (e) => {
    e.preventDefault();
    onLogin({ email, password });
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-100 p-6">
      <form onSubmit={submit} className="w-full max-w-md space-y-4 rounded-xl bg-white p-6 shadow">
        <h1 className="text-xl font-semibold text-slate-900">GCC Lightweight CLM</h1>
        <p className="text-sm text-slate-500">Sign in to access contract management modules.</p>
        <div>
          <label className="mb-1 block text-sm text-slate-700">Email</label>
          <input className="input" value={email} onChange={(e) => setEmail(e.target.value)} />
        </div>
        <div>
          <label className="mb-1 block text-sm text-slate-700">Password</label>
          <input className="input" type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
        </div>
        <button disabled={loading} className="btn w-full" type="submit">
          {loading ? "Signing in..." : "Sign In"}
        </button>
      </form>
    </div>
  );
}
