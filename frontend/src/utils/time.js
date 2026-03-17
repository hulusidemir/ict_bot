/**
 * NY saat formatlama yardımcıları.
 */
export function formatNYTime(nyTimeStr) {
  if (!nyTimeStr) return '—';
  // "2024-01-15 09:35:00 EST" formatından sadece saat kısmını al
  const parts = nyTimeStr.split(' ');
  if (parts.length >= 2) {
    return `${parts[1]} ${parts[2] || ''}`.trim();
  }
  return nyTimeStr;
}

export function formatNYDate(nyTimeStr) {
  if (!nyTimeStr) return '—';
  const parts = nyTimeStr.split(' ');
  return parts[0] || nyTimeStr;
}

export function formatPrice(price) {
  if (price == null) return '—';
  return Number(price).toLocaleString('en-US', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
}

export function formatR(r) {
  if (r == null) return '—';
  const sign = r >= 0 ? '+' : '';
  return `${sign}${r.toFixed(2)}R`;
}
