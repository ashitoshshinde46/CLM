export function paginate(items, page, pageSize) {
  const totalPages = Math.max(1, Math.ceil((items?.length || 0) / pageSize));
  const safePage = Math.min(Math.max(page, 1), totalPages);
  const start = (safePage - 1) * pageSize;
  return {
    page: safePage,
    totalPages,
    rows: (items || []).slice(start, start + pageSize),
  };
}
