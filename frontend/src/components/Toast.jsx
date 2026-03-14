export default function Toast({ message }) {
  if (!message) return null;
  return <div className="rounded border border-slate-200 bg-white p-2 text-sm">{message}</div>;
}
