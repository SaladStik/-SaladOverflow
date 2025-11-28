import { parseISO } from 'date-fns';

export function formatTimeAgo(date: string | Date | undefined): string {
  // If it's already a formatted string (from the API), just return it
  if (typeof date === 'string' && !date.includes('T') && !date.includes('Z')) {
    return date;
  }
  
  // Otherwise parse and format (fallback for old data)
  const utcDate = typeof date === 'string' ? parseISO(date) : date;
  
  if (!utcDate || isNaN(utcDate.getTime())) {
    return 'Unknown';
  }
  
  // Convert to local timezone string
  const options: Intl.DateTimeFormatOptions = {
    month: 'short',
    day: 'numeric', 
    year: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
    hour12: true
  };
  
  const formatted = utcDate.toLocaleString('en-US', options);
  return formatted.replace(',', ' at').replace(',', '');
}

export function formatNumber(num: number): string {
  if (num >= 1000000) {
    return (num / 1000000).toFixed(1) + 'M';
  }
  if (num >= 1000) {
    return (num / 1000).toFixed(1) + 'k';
  }
  return num.toString();
}

export function cn(...classes: (string | boolean | undefined)[]): string {
  return classes.filter(Boolean).join(' ');
}

export function getAvatarUrl(displayName: string): string {
  return `https://api.dicebear.com/7.x/avataaars/svg?seed=${displayName}`;
}

export function truncateText(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text;
  return text.slice(0, maxLength) + '...';
}
