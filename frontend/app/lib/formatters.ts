export const formatCurrency = (
  value: number | null | undefined,
  currency: string = 'BRL'
): string => {
  if (!value && value !== 0) return 'R$ 0,00';
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency,
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value);
};

export const formatNumber = (
  value: number | null | undefined,
  decimals = 0
): string => {
  if (!value && value !== 0) return '0';
  return new Intl.NumberFormat('pt-BR', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(value);
};

export const formatPercent = (
  value: number,
  decimals: number = 1
): string => {
  return `${value.toFixed(decimals)}%`;
};

export const formatCompact = (value: number): string => {
  if (value >= 1_000_000_000) {
    return (value / 1_000_000_000).toFixed(1).replace('.0', '') + 'B';
  }
  if (value >= 1_000_000) {
    return (value / 1_000_000).toFixed(1).replace('.0', '') + 'M';
  }
  if (value >= 1_000) {
    return (value / 1_000).toFixed(1).replace('.0', '') + 'K';
  }
  return value.toString();
};

export const formatTime = (date: Date): string => {
  return date.toLocaleTimeString('pt-BR', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  });
};

export const formatDate = (date: Date): string => {
  return date.toLocaleDateString('pt-BR', {
    weekday: 'short',
    month: 'short',
    day: 'numeric',
  });
};

export const formatDateTime = (date: Date): string => {
  return `${formatDate(date)} ${formatTime(date)}`;
};

export const truncate = (str: string, length: number): string => {
  if (!str || str.length <= length) return str;
  return str.slice(0, length) + '...';
};

export const getStatusColor = (
  status: string
): 'success' | 'warning' | 'error' | 'default' => {
  switch (status?.toLowerCase()) {
    case 'paid':
    case 'completed':
    case 'success':
    case 'active':
      return 'success';
    case 'pending':
    case 'processing':
      return 'warning';
    case 'cancelled':
    case 'failed':
    case 'error':
      return 'error';
    default:
      return 'default';
  }
};
