import { useState, useEffect } from 'react';
import type { Paper, DeepAnalysis } from '@/lib/api';
import { paperAPI } from '@/lib/api';
import { openPdfInNewTab } from '@/lib/pdfUtils';
import { extractApiError } from '@/lib/errorUtils';
import {
    ArrowLeft, FileText, User, Tag, BookOpen, Target, FlaskConical,
    Lightbulb, Route, Award, Calendar, BookMarked, Loader2, Brain,
    CheckCircle2, AlertTriangle, Search, Quote, Sparkles, TrendingUp,
    Shield, Eye, ChevronRight, RefreshCw
} from 'lucide-react';
import { Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer } from 'recharts';

interface PaperFullAnalysisProps {
    paper: Paper;
    onBack: () => void;
}

function ScoreBar({ label, score, color }: { label: string; score: number; color: string }) {
    return (
        <div className="flex items-center gap-3">
            <span className="text-sm text-slate-600 w-16 shrink-0">{label}</span>
            <div className="flex-1 h-2.5 bg-slate-100 rounded-full overflow-hidden">
                <div className={`h-full rounded-full transition-all duration-700 ${color}`} style={{ width: `${score * 10}%` }} />
            </div>
            <span className="text-sm font-mono font-semibold text-slate-700 w-8 text-right">{score.toFixed(1)}</span>
        </div>
    );
}

function SectionCard({ icon, title, children, borderColor = 'border-slate-200', bgColor = '' }: {
    icon: React.ReactNode; title: string; children: React.ReactNode; borderColor?: string; bgColor?: string;
}) {
    return (
        <section className={`bg-white rounded-xl border ${borderColor} p-6 ${bgColor}`}>
            <h2 className="text-lg font-semibold text-slate-900 mb-4 flex items-center gap-2">
                {icon}
                {title}
            </h2>
            {children}
        </section>
    );
}

export function PaperFullAnalysis({ paper, onBack }: PaperFullAnalysisProps) {
    const [deepData, setDeepData] = useState<DeepAnalysis | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [generating, setGenerating] = useState(false);

    const radarData = [
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

    const fetchOrGenerate = async () => {
        setLoading(true);
        setError(null);
        try {
            const res = await paperAPI.getDeepAnalysis(paper.id);
            if (res.data.status === 'ready') {
                setDeepData(res.data.data);
                setLoading(false);
            } else {
                setGenerating(true);
                setLoading(false);
                const genRes = await paperAPI.generateDeepAnalysis(paper.id);
                if (genRes.data.status === 'ready') {
                    setDeepData(genRes.data.data);
                }
                setGenerating(false);
            }
        } catch (err: any) {
            const status = err?.response?.status;
            const detail = err?.response?.data?.detail;
            let msg: string;
            if (status === 402) {
                msg = typeof detail === 'object'
                    ? `积分不足：需要 ${detail.required} 积分，当前余额 ${detail.current}`
                    : '积分不足，无法进行精读分析（每次消耗 1 积分）';
            } else {
                msg = extractApiError(err, '深度分析失败，请稍后重试');
            }
            setError(msg);
            setLoading(false);
            setGenerating(false);
        }
    };

    useEffect(() => {
        fetchOrGenerate();
    }, [paper.id]);

    return (
        <div className="flex flex-col h-full bg-slate-50">
                {/* Top Bar */}
                <div className="sticky top-0 z-20 bg-white/80 backdrop-blur-md border-b border-slate-200">
                    <div className="max-w-6xl mx-auto px-6 h-14 flex items-center justify-between">
                        <button
                            onClick={onBack}
                            className="flex items-center gap-2 text-sm font-medium text-slate-600 hover:text-slate-900 transition-colors"
                        >
                            <ArrowLeft className="w-4 h-4" />
                            返回
                        </button>
                        <div className="flex items-center gap-3">
                            <span className="text-xs text-slate-400 bg-slate-100 px-2.5 py-1 rounded-full flex items-center gap-1">
                                <Brain className="w-3 h-3" />
                                精读报告
                            </span>
                            <button
                                onClick={handleOpenPdf}
                                className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors text-sm font-medium"
                            >
                                <FileText className="w-4 h-4" />
                                打开原文 PDF
                            </button>
                        </div>
                    </div>
                </div>

                <div className="max-w-6xl mx-auto px-6 py-10">
                {/* Header */}
                <header className="mb-10">
                    <h1 className="text-3xl font-bold text-slate-900 leading-tight mb-4">{paper.title}</h1>
                    <div className="flex flex-wrap items-center gap-4 text-sm text-slate-500">
                        {paper.authors && (
                            <span className="flex items-center gap-1.5">
                                <User className="w-4 h-4 text-slate-400" />
                                {paper.authors}
                            </span>
                        )}
                        {paper.year && (
                            <span className="flex items-center gap-1.5">
                                <Calendar className="w-4 h-4 text-slate-400" />
                                {paper.year}
                            </span>
                        )}
                        {paper.venue && (
                            <span className="flex items-center gap-1.5">
                                <BookMarked className="w-4 h-4 text-slate-400" />
                                {paper.venue}
                            </span>
                        )}
                    </div>
                </header>

                {/* Loading / Generating State */}
                {(loading || generating) && (
                    <div className="flex flex-col items-center justify-center py-24 gap-4">
                        <div className="relative">
                            <Loader2 className="w-12 h-12 text-primary-500 animate-spin" />
                            <Brain className="w-5 h-5 text-primary-700 absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2" />
                        </div>
                        <div className="text-center">
                            <p className="text-lg font-medium text-slate-700">
                                {generating ? 'AI 正在精读这篇论文...' : '正在加载精读报告...'}
                            </p>
                            {generating && (
                                <p className="text-sm text-slate-400 mt-2">首次生成需要 30-60 秒，生成后将自动缓存</p>
                            )}
                        </div>
                    </div>
                )}

                {/* Error State */}
                {error && !loading && !generating && (
                    <div className="flex flex-col items-center justify-center py-24 gap-4">
                        <AlertTriangle className="w-12 h-12 text-amber-500" />
                        <p className="text-lg font-medium text-slate-700">{error}</p>
                        <button
                            onClick={fetchOrGenerate}
                            className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors text-sm font-medium"
                        >
                            <RefreshCw className="w-4 h-4" />
                            重新生成
                        </button>
                    </div>
                )}

                {/* Deep Analysis Content */}
                {deepData && !loading && !generating && (
                    <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                        {/* Left Column: Deep Analysis */}
                        <div className="lg:col-span-2 space-y-8">

                            {/* 扩展摘要 */}
                            {deepData.detailed_summary && (
                                <SectionCard
                                    icon={<Sparkles className="w-5 h-5 text-purple-500" />}
                                    title="深度摘要"
                                    borderColor="border-purple-200"
                                    bgColor="bg-purple-50/20"
                                >
                                    <p className="text-sm text-slate-700 leading-relaxed whitespace-pre-line">
                                        {deepData.detailed_summary}
                                    </p>
                                </SectionCard>
                            )}

                            {/* 理论框架 */}
                            {deepData.theoretical_framework && (
                                <SectionCard
                                    icon={<BookOpen className="w-5 h-5 text-indigo-500" />}
                                    title="理论框架"
                                    borderColor="border-indigo-200"
                                    bgColor="bg-indigo-50/20"
                                >
                                    <div className="space-y-4">
                                        {deepData.theoretical_framework.theories?.length > 0 && (
                                            <div>
                                                <h3 className="text-xs font-semibold text-indigo-600 uppercase tracking-wider mb-2">依托理论</h3>
                                                <div className="flex flex-wrap gap-2">
                                                    {deepData.theoretical_framework.theories.map((t, i) => (
                                                        <span key={i} className="px-3 py-1.5 bg-indigo-50 text-indigo-700 text-xs font-medium rounded-lg border border-indigo-100">
                                                            {t}
                                                        </span>
                                                    ))}
                                                </div>
                                            </div>
                                        )}
                                        {deepData.theoretical_framework.positioning && (
                                            <div>
                                                <h3 className="text-xs font-semibold text-indigo-600 uppercase tracking-wider mb-2">学科定位</h3>
                                                <p className="text-sm text-slate-700 leading-relaxed">{deepData.theoretical_framework.positioning}</p>
                                            </div>
                                        )}
                                        {deepData.theoretical_framework.literature_gap && (
                                            <div>
                                                <h3 className="text-xs font-semibold text-indigo-600 uppercase tracking-wider mb-2">文献空白</h3>
                                                <p className="text-sm text-slate-700 leading-relaxed">{deepData.theoretical_framework.literature_gap}</p>
                                            </div>
                                        )}
                                    </div>
                                </SectionCard>
                            )}

                            {/* 详细方法论 */}
                            {deepData.detailed_methodology && (
                                <SectionCard
                                    icon={<FlaskConical className="w-5 h-5 text-blue-500" />}
                                    title="详细方法论"
                                >
                                    <div className="space-y-4">
                                        {(['research_design', 'data_collection', 'data_analysis', 'validity'] as const).map(key => {
                                            const labels: Record<string, string> = {
                                                research_design: '研究设计', data_collection: '数据收集',
                                                data_analysis: '数据分析', validity: '信效度保障'
                                            };
                                            const val = deepData.detailed_methodology[key];
                                            if (!val) return null;
                                            return (
                                                <div key={key}>
                                                    <h3 className="text-xs font-semibold text-blue-600 uppercase tracking-wider mb-1">{labels[key]}</h3>
                                                    <p className="text-sm text-slate-700 leading-relaxed">{val}</p>
                                                </div>
                                            );
                                        })}
                                    </div>
                                </SectionCard>
                            )}

                            {/* 论证逻辑链 */}
                            {deepData.argument_chain?.length > 0 && (
                                <SectionCard
                                    icon={<Route className="w-5 h-5 text-teal-500" />}
                                    title="论证逻辑链"
                                    borderColor="border-teal-200"
                                    bgColor="bg-teal-50/20"
                                >
                                    <div className="space-y-1">
                                        {deepData.argument_chain.map((step, i) => (
                                            <div key={i} className="relative pl-8 pb-6 last:pb-0">
                                                {i < deepData.argument_chain.length - 1 && (
                                                    <div className="absolute left-[13px] top-7 bottom-0 w-0.5 bg-teal-200" />
                                                )}
                                                <div className="absolute left-0 top-0.5 w-7 h-7 rounded-full bg-teal-100 border-2 border-teal-400 flex items-center justify-center text-xs font-bold text-teal-700">
                                                    {i + 1}
                                                </div>
                                                <div>
                                                    <div className="flex items-center gap-2 mb-1">
                                                        <span className="text-sm font-semibold text-slate-800">{step.step}</span>
                                                        <span className="px-2 py-0.5 bg-teal-50 text-teal-600 text-[10px] font-medium rounded-full border border-teal-100">
                                                            {step.evidence_type}
                                                        </span>
                                                    </div>
                                                    <p className="text-sm text-slate-600 leading-relaxed">{step.content}</p>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </SectionCard>
                            )}

                            {/* 优势与局限 */}
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                {deepData.strengths?.length > 0 && (
                                    <SectionCard
                                        icon={<CheckCircle2 className="w-5 h-5 text-emerald-500" />}
                                        title="优势"
                                        borderColor="border-emerald-200"
                                        bgColor="bg-emerald-50/20"
                                    >
                                        <ul className="space-y-3">
                                            {deepData.strengths.map((s, i) => (
                                                <li key={i} className="text-sm text-slate-700 leading-relaxed flex gap-2">
                                                    <ChevronRight className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                                                    <span>{s}</span>
                                                </li>
                                            ))}
                                        </ul>
                                    </SectionCard>
                                )}
                                {deepData.limitations?.length > 0 && (
                                    <SectionCard
                                        icon={<AlertTriangle className="w-5 h-5 text-amber-500" />}
                                        title="局限"
                                        borderColor="border-amber-200"
                                        bgColor="bg-amber-50/20"
                                    >
                                        <ul className="space-y-3">
                                            {deepData.limitations.map((l, i) => (
                                                <li key={i} className="text-sm text-slate-700 leading-relaxed flex gap-2">
                                                    <ChevronRight className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
                                                    <span>{l}</span>
                                                </li>
                                            ))}
                                        </ul>
                                    </SectionCard>
                                )}
                            </div>

                            {/* 研究空白与未来方向 */}
                            {deepData.research_gaps?.length > 0 && (
                                <SectionCard
                                    icon={<Search className="w-5 h-5 text-sky-500" />}
                                    title="研究空白与未来方向"
                                >
                                    <ul className="space-y-3">
                                        {deepData.research_gaps.map((g, i) => (
                                            <li key={i} className="text-sm text-slate-700 leading-relaxed flex gap-2">
                                                <TrendingUp className="w-4 h-4 text-sky-400 shrink-0 mt-0.5" />
                                                <span>{g}</span>
                                            </li>
                                        ))}
                                    </ul>
                                </SectionCard>
                            )}

                            {/* 实践启示 */}
                            {deepData.practical_implications?.length > 0 && (
                                <SectionCard
                                    icon={<Lightbulb className="w-5 h-5 text-yellow-500" />}
                                    title="实践启示"
                                    borderColor="border-yellow-200"
                                    bgColor="bg-yellow-50/20"
                                >
                                    <ul className="space-y-3">
                                        {deepData.practical_implications.map((p, i) => (
                                            <li key={i} className="text-sm text-slate-700 leading-relaxed flex gap-2">
                                                <Lightbulb className="w-4 h-4 text-yellow-400 shrink-0 mt-0.5" />
                                                <span>{p}</span>
                                            </li>
                                        ))}
                                    </ul>
                                </SectionCard>
                            )}

                            {/* 关键引文 */}
                            {deepData.key_quotes?.length > 0 && (
                                <SectionCard
                                    icon={<Quote className="w-5 h-5 text-slate-500" />}
                                    title="关键引文"
                                >
                                    <div className="space-y-4">
                                        {deepData.key_quotes.map((q, i) => (
                                            <blockquote key={i} className="border-l-3 border-primary-300 pl-4 py-2 bg-primary-50/30 rounded-r-lg">
                                                <p className="text-sm text-slate-800 italic leading-relaxed">"{q.quote}"</p>
                                                <p className="text-xs text-slate-400 mt-1.5">{q.context}</p>
                                            </blockquote>
                                        ))}
                                    </div>
                                </SectionCard>
                            )}

                            {/* 综合批判性评价 */}
                            {deepData.critical_review && (
                                <SectionCard
                                    icon={<Eye className="w-5 h-5 text-rose-500" />}
                                    title="综合批判性评价"
                                    borderColor="border-rose-200"
                                    bgColor="bg-rose-50/20"
                                >
                                    <p className="text-sm text-slate-700 leading-relaxed whitespace-pre-line">
                                        {deepData.critical_review}
                                    </p>
                                </SectionCard>
                            )}
                        </div>

                        {/* Right Column: Score & Meta (sticky) */}
                        <div className="space-y-6">
                            <div className="lg:sticky lg:top-20">
                                <div className="space-y-6">
                                    {/* 综合评分 */}
                                    <div className="bg-white rounded-xl border border-slate-200 p-6">
                                        <div className="text-center mb-4">
                                            <div className="text-4xl font-bold text-primary-600 font-mono">
                                                {paper.overall_score?.toFixed(1)}
                                            </div>
                                            <div className="text-xs text-slate-400 mt-1">综合评分 / 10</div>
                                        </div>
                                        <div className="h-52">
                                            <ResponsiveContainer width="100%" height="100%">
                                                <RadarChart cx="50%" cy="50%" outerRadius="70%" data={radarData}>
                                                    <PolarGrid stroke="#e2e8f0" />
                                                    <PolarAngleAxis dataKey="subject" tick={{ fill: '#64748b', fontSize: 11 }} />
                                                    <PolarRadiusAxis angle={30} domain={[0, 10]} tick={false} axisLine={false} />
                                                    <Radar name="评分" dataKey="A" stroke="#7c3aed" strokeWidth={2} fill="#8b5cf6" fillOpacity={0.2} />
                                                </RadarChart>
                                            </ResponsiveContainer>
                                        </div>
                                    </div>

                                    {/* 五维评分详情 */}
                                    <div className="bg-white rounded-xl border border-slate-200 p-6 space-y-3">
                                        <h3 className="text-sm font-semibold text-slate-500 uppercase tracking-wider mb-4">五维评分</h3>
                                        <ScoreBar label="严谨性" score={paper.score_rigor || 0} color="bg-violet-500" />
                                        <ScoreBar label="创新性" score={paper.score_innovation || 0} color="bg-blue-500" />
                                        <ScoreBar label="实用性" score={paper.score_practicality || 0} color="bg-emerald-500" />
                                        <ScoreBar label="影响力" score={paper.score_impact || 0} color="bg-amber-500" />
                                        <ScoreBar label="可读性" score={paper.score_readability || 0} color="bg-rose-500" />
                                    </div>

                                    {/* 关键词 */}
                                    {keywordList.length > 0 && (
                                        <div className="bg-white rounded-xl border border-slate-200 p-6">
                                            <h3 className="text-sm font-semibold text-slate-500 uppercase tracking-wider mb-3 flex items-center gap-1.5">
                                                <Tag className="w-3.5 h-3.5" />关键词
                                            </h3>
                                            <div className="flex flex-wrap gap-2">
                                                {keywordList.map((kw, i) => (
                                                    <span key={i} className="px-2.5 py-1 bg-primary-50 text-primary-700 text-xs font-medium rounded-full border border-primary-100">
                                                        {kw}
                                                    </span>
                                                ))}
                                            </div>
                                        </div>
                                    )}

                                    {/* 研究对象 */}
                                    {paper.domain_tags && (
                                        <div className="bg-white rounded-xl border border-slate-200 p-6">
                                            <h3 className="text-sm font-semibold text-slate-500 uppercase tracking-wider mb-3 flex items-center gap-1.5">
                                                <BookOpen className="w-3.5 h-3.5" />研究对象
                                            </h3>
                                            <p className="text-sm text-slate-700 leading-relaxed">{paper.domain_tags}</p>
                                        </div>
                                    )}
                                </div>
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
