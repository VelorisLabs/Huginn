/**
 * 评分颜色工具函数
 */

export interface ScoreColorScheme {
    bar: string;
    text: string;
    bg: string;
    badge: string;
}

/**
 * 获取评分对应的完整颜色方案（用于 PaperList 等需要多种样式的场景）
 */
export function getScoreColorScheme(score: number): ScoreColorScheme {
    if (score >= 8.5) return { bar: 'bg-emerald-500', text: 'text-emerald-600', bg: 'bg-emerald-50', badge: 'bg-emerald-50 text-emerald-700 border-emerald-100' };
    if (score >= 7.5) return { bar: 'bg-blue-500', text: 'text-blue-600', bg: 'bg-blue-50', badge: 'bg-blue-50 text-blue-700 border-blue-100' };
    if (score >= 6.5) return { bar: 'bg-amber-500', text: 'text-amber-600', bg: 'bg-amber-50', badge: 'bg-amber-50 text-amber-700 border-amber-100' };
    return { bar: 'bg-slate-400', text: 'text-slate-600', bg: 'bg-slate-50', badge: 'bg-slate-50 text-slate-600 border-slate-200' };
}

/**
 * 获取评分对应的文字颜色类名（简版，用于 ResearchFocus 等只需要 text color 的场景）
 */
export function getScoreColor(score: number): string {
    if (score >= 8.5) return 'text-emerald-600';
    if (score >= 7.5) return 'text-blue-600';
    if (score >= 6.5) return 'text-amber-600';
    return 'text-slate-500';
}
