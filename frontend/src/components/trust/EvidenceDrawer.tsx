
import React from 'react';
import type { Paper } from '@/lib/api';
import { openPdfInNewTab } from '@/lib/pdfUtils';
import { EvidenceBadge } from './EvidenceBadge';
import { X, FileText, ExternalLink, User, Tag, BookOpen, Target, FlaskConical, Lightbulb, Route, Award, BarChart3 } from 'lucide-react';
import { Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer } from 'recharts';

interface EvidenceDrawerProps {
    paper: Paper | null;
    isOpen: boolean;
    onClose: () => void;
    onFullAnalysis?: (paper: Paper) => void;
}

/** Parse text like "1. xxx 2. xxx 3. xxx" into ordered list items */
function parseNumberedText(text: string): string[] {
    // Split on numbered prefixes like "1. ", "2. " etc.
    const parts = text.split(/(?=\d+\.\s)/).map(s => s.trim()).filter(Boolean);
    // Check if the text actually contains numbered items
    if (parts.length > 1 && /^\d+\.\s/.test(parts[0])) {
        return parts.map(p => p.replace(/^\d+\.\s*/, ''));
    }
    return []; // Not a numbered list
}

/** Render text as ordered list if it contains numbered items, otherwise as paragraph */
function NumberedContent({ text, className = '' }: { text: string; className?: string }) {
    const items = parseNumberedText(text);
    if (items.length > 0) {
        return (
            <ol className={`text-sm text-slate-700 leading-relaxed list-decimal list-inside space-y-2 p-3 rounded-lg border ${className}`}>
                {items.map((item, i) => (
                    <li key={i} className="pl-1">{item}</li>
                ))}
            </ol>
        );
    }
    return <p className={`text-sm text-slate-700 leading-relaxed p-3 rounded-lg border ${className}`}>{text}</p>;
}

export function EvidenceDrawer({ paper, isOpen, onClose, onFullAnalysis }: EvidenceDrawerProps) {
    if (!paper || !isOpen) return null;

    // Transform scores for Radar Chart
    const data = [
        { subject: '严谨性', A: paper.score_rigor || 0, fullMark: 10 },
        { subject: '创新性', A: paper.score_innovation || 0, fullMark: 10 },
        { subject: '实用性', A: paper.score_practicality || 0, fullMark: 10 },
        { subject: '影响力', A: paper.score_impact || 0, fullMark: 10 },
        { subject: '可读性', A: paper.score_readability || 0, fullMark: 10 },
    ];

    const keywordList = paper.keywords ? paper.keywords.split(/[,;，；]/).map(k => k.trim()).filter(Boolean) : [];

    const handleOpenPdf = async () => {
        try {
            await openPdfInNewTab(paper.id);
        } catch {
            alert('PDF 加载失败，请稍后重试');
        }
    };

    return (
        <div className="fixed inset-0 z-50 flex justify-end" aria-modal="true" role="dialog">
            {/* Backdrop */}
            <div
                className="absolute inset-0 bg-slate-900/30 backdrop-blur-sm transition-opacity animate-fade-in"
                onClick={onClose}
            />

            {/* Drawer Panel */}
            <div className="relative w-full max-w-2xl bg-white shadow-lift h-full flex flex-col animate-slide-in-right rounded-l-2xl overflow-hidden">

                {/* Header */}
                <div className="px-6 py-5 border-b border-slate-100 bg-gradient-to-r from-slate-50/80 to-white">
                    <div className="flex items-start justify-between gap-4">
                        <div className="space-y-2 flex-1 min-w-0">
                            <h2 className="text-lg font-bold text-slate-900 leading-snug">{paper.title}</h2>
                            {paper.authors && (
                                <div className="flex items-center gap-1.5 text-sm text-slate-500">
                                    <User className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                                    <span className="line-clamp-1">{paper.authors}</span>
                                </div>
                            )}
                            <div className="flex items-center gap-2 flex-wrap">
                                <span className="inline-flex items-center gap-1 text-[11px] font-medium text-slate-500 bg-slate-100 px-2 py-0.5 rounded-md">{paper.year}</span>
                                <span className="inline-flex items-center gap-1 text-[11px] font-medium text-slate-500 bg-slate-100 px-2 py-0.5 rounded-md">
                                    <FileText className="w-3 h-3" />
                                    {paper.venue || '未知来源'}
                                </span>
                                <EvidenceBadge type="inferred" />
                            </div>
                        </div>
                        <div className="flex items-center gap-2 shrink-0">
                            {paper.overall_score && (
                                <div className={`px-3 py-1.5 rounded-xl text-center border ${
                                    (paper.overall_score || 0) >= 8 ? 'bg-emerald-50 border-emerald-100 text-emerald-700' :
                                    (paper.overall_score || 0) >= 7 ? 'bg-blue-50 border-blue-100 text-blue-700' :
                                    'bg-slate-50 border-slate-200 text-slate-700'
                                }`}>
                                    <span className="text-xl font-bold font-mono">{paper.overall_score.toFixed(1)}</span>
                                </div>
                            )}
                            <button
                                onClick={onClose}
                                className="p-2 rounded-xl hover:bg-slate-100 transition-colors text-slate-400 hover:text-slate-600"
                            >
                                <X className="w-5 h-5" />
                            </button>
                        </div>
                    </div>
                </div>

                {/* Scrollable Content */}
                <div className="flex-1 overflow-y-auto p-6 space-y-6">

                    {/* 1. 雷达图 (Radar Chart) */}
                    <section>
                        <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">五维评估</h3>
                        <div className="h-52 w-full bg-gradient-to-br from-slate-50 to-primary-50/30 rounded-2xl border border-slate-100 p-2">
                            <ResponsiveContainer width="100%" height="100%">
                                <RadarChart cx="50%" cy="50%" outerRadius="70%" data={data}>
                                    <PolarGrid stroke="#e2e8f0" strokeDasharray="3 3" />
                                    <PolarAngleAxis dataKey="subject" tick={{ fill: '#64748b', fontSize: 11, fontWeight: 500 }} />
                                    <PolarRadiusAxis angle={30} domain={[0, 10]} tick={false} axisLine={false} />
                                    <Radar
                                        name="论文评分"
                                        dataKey="A"
                                        stroke="#7c3aed"
                                        strokeWidth={2}
                                        fill="#8b5cf6"
                                        fillOpacity={0.15}
                                    />
                                </RadarChart>
                            </ResponsiveContainer>
                        </div>
                    </section>

                    {/* 1.5 场景评分对比 (Scenario Scores) */}
                    {paper.scenario_scores && Object.keys(paper.scenario_scores).length > 0 && (
                        <section>
                            <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3 flex items-center gap-1.5">
                                <BarChart3 className="w-3.5 h-3.5" />场景评分对比
                            </h3>
                            <div className="grid grid-cols-3 gap-2">
                                {Object.entries(paper.scenario_scores).map(([name, score]) => {
                                    const isHighest = score === Math.max(...Object.values(paper.scenario_scores!));
                                    return (
                                        <div
                                            key={name}
                                            className={`rounded-xl border p-3 text-center transition-all ${
                                                isHighest
                                                    ? 'border-primary-200 bg-primary-50/50 ring-1 ring-primary-100'
                                                    : 'border-slate-100 bg-slate-50/50'
                                            }`}
                                        >
                                            <p className="text-[11px] text-slate-500 mb-1">{name}</p>
                                            <p className={`text-xl font-bold font-mono ${
                                                isHighest ? 'text-primary-600' : 'text-slate-600'
                                            }`}>
                                                {typeof score === 'number' ? score.toFixed(2) : score}
                                            </p>
                                        </div>
                                    );
                                })}
                            </div>
                        </section>
                    )}

                    {/* 2. 关键词 (Keywords) */}
                    {keywordList.length > 0 && (
                        <section>
                            <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-3 flex items-center gap-1.5">
                                <Tag className="w-3.5 h-3.5" />关键词
                            </h3>
                            <div className="flex flex-wrap gap-2">
                                {keywordList.map((kw, i) => (
                                    <span key={i} className="px-2.5 py-1 bg-primary-50 text-primary-700 text-xs font-medium rounded-full border border-primary-100">
                                        {kw}
                                    </span>
                                ))}
                            </div>
                        </section>
                    )}

                    {/* 3. 研究对象 (Research Subject / Domain Tags) */}
                    {paper.domain_tags && (
                        <section>
                            <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                                <BookOpen className="w-3.5 h-3.5" />研究对象
                            </h3>
                            <p className="text-sm text-slate-700 leading-relaxed bg-slate-50 p-3 rounded-lg border border-slate-100">{paper.domain_tags}</p>
                        </section>
                    )}

                    {/* 4. 研究问题 (Problem) */}
                    <section>
                        <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                            <Target className="w-3.5 h-3.5" />研究问题
                        </h3>
                        {paper.problem
                            ? <NumberedContent text={paper.problem} className="bg-slate-50 border-slate-100" />
                            : <p className="text-sm text-slate-700 leading-relaxed bg-slate-50 p-3 rounded-lg border border-slate-100">暂无研究问题信息</p>
                        }
                    </section>

                    {/* 5. 研究方法 (Methodology) */}
                    <section>
                        <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                            <FlaskConical className="w-3.5 h-3.5" />研究方法
                        </h3>
                        {paper.methodology
                            ? <NumberedContent text={paper.methodology} className="bg-slate-50 border-slate-100" />
                            : <p className="text-sm text-slate-700 leading-relaxed bg-slate-50 p-3 rounded-lg border border-slate-100">暂无研究方法信息</p>
                        }
                    </section>

                    {/* 6. 核心结论 (Core Conclusions) */}
                    <section>
                        <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                            <Lightbulb className="w-3.5 h-3.5" />核心结论
                        </h3>
                        {paper.conclusion
                            ? <NumberedContent text={paper.conclusion} className="bg-emerald-50/50 border-emerald-100" />
                            : <p className="text-sm text-slate-700 leading-relaxed bg-emerald-50/50 p-3 rounded-lg border border-emerald-100">暂无核心结论信息</p>
                        }
                    </section>

                    {/* 7. 实现路径 (Implementation Path) */}
                    {paper.implementation_path && (
                        <section>
                            <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                                <Route className="w-3.5 h-3.5" />实现路径
                            </h3>
                            <NumberedContent text={paper.implementation_path} className="bg-blue-50/50 border-blue-100" />
                        </section>
                    )}

                    {/* 8. 主要贡献 (Main Contributions) */}
                    {paper.contribution && (
                        <section>
                            <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                                <Award className="w-3.5 h-3.5" />主要贡献
                            </h3>
                            <NumberedContent text={paper.contribution} className="bg-amber-50/50 border-amber-100" />
                        </section>
                    )}

                </div>

                {/* Footer Actions */}
                <div className="px-6 py-4 border-t border-slate-100 bg-white flex items-center justify-between gap-3">
                    <button
                        onClick={handleOpenPdf}
                        className="btn-secondary text-sm"
                    >
                        <FileText className="w-4 h-4" />
                        打开 PDF
                    </button>

                    <button
                        onClick={() => onFullAnalysis?.(paper)}
                        className="btn-primary text-sm"
                    >
                        深度分析 <ExternalLink className="w-4 h-4" />
                    </button>
                </div>

            </div>
        </div>
    );
}
