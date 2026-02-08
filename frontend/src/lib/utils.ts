/**
 * 工具函数
 */
import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatDate(date: string | Date): string {
  return new Date(date).toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  });
}

export function downloadFile(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

export function getScoreColor(score: number): string {
  if (score >= 9) return 'text-green-600';
  if (score >= 7.5) return 'text-blue-600';
  if (score >= 6) return 'text-yellow-600';
  if (score >= 4) return 'text-orange-600';
  return 'text-red-600';
}

export function getScoreLabel(score: number): string {
  if (score >= 9) return '优秀';
  if (score >= 7.5) return '良好';
  if (score >= 6) return '中等';
  if (score >= 4) return '较差';
  return '不合格';
}
