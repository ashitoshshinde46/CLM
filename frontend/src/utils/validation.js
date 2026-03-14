export function required(value, label) {
  if (value === undefined || value === null || String(value).trim() === "") {
    return `${label} is required`;
  }
  return null;
}

export function positiveInteger(value, label) {
  if (!String(value).trim()) return `${label} is required`;
  const num = Number(value);
  if (!Number.isInteger(num) || num <= 0) {
    return `${label} must be a positive integer`;
  }
  return null;
}

export function nonNegativeNumber(value, label) {
  if (value === "" || value === null || value === undefined) return null;
  const num = Number(value);
  if (Number.isNaN(num) || num < 0) {
    return `${label} must be a non-negative number`;
  }
  return null;
}

export function validYear(value) {
  if (!String(value).trim()) return null;
  const num = Number(value);
  if (!Number.isInteger(num) || num < 2000 || num > 2100) {
    return "Year must be between 2000 and 2100";
  }
  return null;
}
