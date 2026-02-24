import { useEffect, useState, useMemo, useCallback } from 'react';
import { useAuthStore } from '@/store/authStore';
import { useQuery } from '@tanstack/react-query';
import { paperAPI, type Paper } from '@/lib/api';
import { motion, AnimatePresence } from 'framer-motion';
import { Sparkles, ArrowRight, FileText, Layers, TrendingUp, BookOpen, X, Settings2, Shield, Download } from 'lucide-react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell,
} from 'recharts';

import { Sidebar, type TabKey } from './Sidebar';
import { StatsCard } from './StatsCard';
import { PaperList } from './PaperList';
import { DecisionProvider } from './decision/DecisionContext';
import { DecisionToast } from './decision/DecisionToast';
import { IngestManager } from './ingest/IngestManager';
import { EvidenceDrawer } from './trust/EvidenceDrawer';
import { ReadingList } from './ReadingList';
import { AnalysisView } from './AnalysisView';
import { PaperFullAnalysis } from './PaperFullAnalysis';
import { ResearchFocus } from './ResearchFocus';
import { WorkspaceManager } from './workspace/WorkspaceManager';
import { AdminPanel } from './AdminPanel';
import { ClusteringView } from './ClusteringView';
import { ExportButton } from './ExportButton';

const PAGE_META: Record<TabKey, { title: string; subtitle: string; icon: React.ElementType }> = {
  overview: { title: '研究态势概览', subtitle: '掌握你的研究库全貌，发现高价值论文', icon: Sparkles },
  analysis: { title: '多维价值评估', subtitle: '多角度解读论文质量，洞察研究趋势', icon: TrendingUp },
  clustering: { title: '主题聚类分析', subtitle: '基于文本相似度自动发现论文间的内在关联', icon: Layers },
  'reading-list': { title: '待读清单', subtitle: '收藏感兴趣的论文，系统管理阅读计划', icon: BookOpen },
  upload: { title: '文献入库', subtitle: '上传 PDF 文件，AI 自动分析并建立画像', icon: FileText },
  'workspace-settings': { title: '工作区管理', subtitle: '创建和配置工作区，管理主题桶和评分权重', icon: Settings2 },
  admin: { title: '系统管理', subtitle: '管理用户、邀请码和积分系统', icon: Shield },
};

const pageVariants = {
  initial: { opacity: 0, y: 12 },
  animate: { opacity: 1, y: 0, transition: { duration: 0.3, ease: 'easeOut' as const } },
  exit: { opacity: 0, y: -8, transition: { duration: 0.15 } },
};

export default function Dashboard() {
  const { user, isAuthenticated, checkAuth, logout } = useAuthStore();
  const [activeTab, setActiveTab] = useState<TabKey>('overview');
  const [selectedPaper, setSelectedPaper] = useState<Paper | null>(null);
  const [fullAnalysisPaper, setFullAnalysisPaper] = useState<Paper | null>(null);
  const [selectedThemes, setSelectedThemes] = useState<Set<string>>(new Set());
  const [selectedYears, setSelectedYears] = useState<Set<number>>(new Set());

  useEffect(() => {
    if (isAuthenticated) checkAuth();
  }, []);

  const { data: stats } = useQuery({
    queryKey: ['stats'],
    queryFn: async () => (await paperAPI.getStats()).data,
    enabled: isAuthenticated,
  });

  const { data: papersResponse } = useQuery({
    queryKey: ['papers-all'],
    queryFn: () => paperAPI.list({ limit: 100 }),
    enabled: isAuthenticated,
  });

  const papers: Paper[] = papersResponse?.data || [];

  const getTheme = useCallback((p: Paper) => p.cluster_topic || p.theme_name || '未分类', []);

  const toggleTheme = useCallback((theme: string) => {
    setSelectedThemes(prev => {
      const next = new Set(prev);
      if (next.has(theme)) next.delete(theme); else next.add(theme);
      return next;
    });
  }, []);

  const toggleYear = useCallback((year: number) => {
    setSelectedYears(prev => {
      const next = new Set(prev);
      if (next.has(year)) next.delete(year); else next.add(year);
      return next;
    });
  }, []);

  const clearAllFilters = useCallback(() => {
    setSelectedThemes(new Set());
    setSelectedYears(new Set());
  }, []);

  const hasFilter = selectedThemes.size > 0 || selectedYears.size > 0;

  const chartData = useMemo(() => {
    if (papers.length === 0) return null;

    const hasT = selectedThemes.size > 0;
    const hasY = selectedYears.size > 0;

    // Cross-filtered subsets
    const papersForThemes = hasY ? papers.filter(p => p.year && selectedYears.has(p.year)) : papers;
    const papersForYears  = hasT ? papers.filter(p => selectedThemes.has(getTheme(p))) : papers;
    const papersForScores = papers.filter(p => {
      if (hasT && !selectedThemes.has(getTheme(p))) return false;
      if (hasY && !(p.year && selectedYears.has(p.year))) return false;
      return true;
    });

    // Theme distribution (filtered by selected years)
    const themeMap = new Map<string, number>();
    papersForThemes.forEach(p => {
      const t = getTheme(p);
      themeMap.set(t, (themeMap.get(t) || 0) + 1);
    });
    const themeDist = Array.from(themeMap.entries())
      .map(([name, value]) => ({ name, value }))
      .sort((a, b) => b.value - a.value)
      .slice(0, 10);

    // Year distribution (filtered by selected themes)
    const yearMap = new Map<number, number>();
    papersForYears.forEach(p => {
      if (p.year) yearMap.set(p.year, (yearMap.get(p.year) || 0) + 1);
    });
    const yearDist = Array.from(yearMap.entries())
      .map(([year, count]) => ({ year, count }))
      .sort((a, b) => a.year - b.year);

    // Score distribution (filtered by both)
    const scoreBuckets = [
      { range: '0-5', count: 0 },
      { range: '5-6', count: 0 },
      { range: '6-7', count: 0 },
      { range: '7-8', count: 0 },
      { range: '8-9', count: 0 },
      { range: '9-10', count: 0 },
    ];
    papersForScores.forEach(p => {
      const s = p.overall_score || 0;
      if (s < 5) scoreBuckets[0].count++;
      else if (s < 6) scoreBuckets[1].count++;
      else if (s < 7) scoreBuckets[2].count++;
      else if (s < 8) scoreBuckets[3].count++;
      else if (s < 9) scoreBuckets[4].count++;
      else scoreBuckets[5].count++;
    });

    // --- Diagnostic insights ---
    // Theme concentration: top theme share
    const totalThemePapers = themeDist.reduce((s, d) => s + d.value, 0);
    const topThemeShare = totalThemePapers > 0 ? (themeDist[0]?.value || 0) / totalThemePapers : 0;
    const themeDiagnosis: { label: string; color: string } =
      topThemeShare > 0.5 ? { label: '高度集中', color: 'text-amber-600 bg-amber-50 border-amber-200' } :
      topThemeShare > 0.3 ? { label: '适度聚焦', color: 'text-emerald-600 bg-emerald-50 border-emerald-200' } :
      { label: '分布均匀', color: 'text-blue-600 bg-blue-50 border-blue-200' };

    // Year trend: compare recent 3 years vs earlier
    const curYear = new Date().getFullYear();
    const recentYearCount = yearDist.filter(d => d.year >= curYear - 2).reduce((s, d) => s + d.count, 0);
    const olderYearCount = yearDist.filter(d => d.year < curYear - 2).reduce((s, d) => s + d.count, 0);
    const yearDiagnosis: { label: string; color: string } =
      recentYearCount > olderYearCount ? { label: '前沿活跃', color: 'text-emerald-600 bg-emerald-50 border-emerald-200' } :
      recentYearCount > 0 ? { label: '稳定积累', color: 'text-blue-600 bg-blue-50 border-blue-200' } :
      { label: '偏向经典', color: 'text-amber-600 bg-amber-50 border-amber-200' };

    // Score health
    const highScoreCount = scoreBuckets[4].count + scoreBuckets[5].count; // 8-10
    const totalScored = scoreBuckets.reduce((s, b) => s + b.count, 0);
    const highRatio = totalScored > 0 ? highScoreCount / totalScored : 0;
    const scoreDiagnosis: { label: string; color: string } =
      highRatio > 0.5 ? { label: '质量优秀', color: 'text-emerald-600 bg-emerald-50 border-emerald-200' } :
      highRatio > 0.25 ? { label: '质量良好', color: 'text-blue-600 bg-blue-50 border-blue-200' } :
      { label: '需提升筛选', color: 'text-amber-600 bg-amber-50 border-amber-200' };

    return {
      themeDist, yearDist, scoreBuckets,
      filteredCount: papersForScores.length,
      filteredIds: papersForScores.map(p => p.id),
      themeDiagnosis, yearDiagnosis, scoreDiagnosis,
    };
  }, [papers, selectedThemes, selectedYears, getTheme]);

  const currentYear = new Date().getFullYear();
  const recentPapers = papers.filter(p => p.year === currentYear || p.year === currentYear - 1);

  // Dynamic top theme from actual data
  const topTheme = useMemo(() => {
    if (papers.length === 0) return null;
    const map = new Map<string, number>();
    papers.forEach(p => {
      const t = getTheme(p);
      map.set(t, (map.get(t) || 0) + 1);
    });
    let best = ''; let max = 0;
    map.forEach((v, k) => { if (v > max) { max = v; best = k; } });
    return best || null;
  }, [papers, getTheme]);

  // Weekly additions count
  const weeklyCount = useMemo(() => {
    const oneWeekAgo = Date.now() - 7 * 24 * 60 * 60 * 1000;
    return papers.filter(p => new Date(p.created_at).getTime() > oneWeekAgo).length;
  }, [papers]);

  // Reading list & review counts from localStorage (same source as DecisionContext)
  const { readingListCount, unreviewedCount } = useMemo(() => {
    try {
      const stored = localStorage.getItem('paper_decisions');
      if (!stored) return { readingListCount: 0, unreviewedCount: papers.length };
      const decisions: Record<string, string> = JSON.parse(stored);
      const kept = Object.values(decisions).filter(d => d === 'keep').length;
      const reviewed = Object.keys(decisions).length;
      return { readingListCount: kept, unreviewedCount: Math.max(0, papers.length - reviewed) };
    } catch { return { readingListCount: 0, unreviewedCount: papers.length }; }
  }, [papers.length]);

  const narrative = topTheme
    ? `您的研究库主要聚焦于 ${topTheme} 领域，近两年产出活跃 (${recentPapers.length} 篇)。`
    : `您的研究库共收录 ${papers.length} 篇论文。`;

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-50 via-primary-50/30 to-slate-50">
        <div className="text-center space-y-6">
          <div className="w-16 h-16 mx-auto rounded-2xl bg-gradient-to-br from-primary-500 to-primary-700 flex items-center justify-center shadow-glow-lg">
            <Sparkles className="w-8 h-8 text-white" />
          </div>
          <div>
            <h1 className="text-3xl font-bold text-slate-900 tracking-tight">PaperAI</h1>
            <p className="text-slate-500 mt-1">Research Intelligence Platform</p>
          </div>
          <a href="/auth/login" className="btn-primary">进入系统</a>
        </div>
      </div>
    );
  }

  if (fullAnalysisPaper) {
    return (
      <DecisionProvider>
        <PaperFullAnalysis
          paper={fullAnalysisPaper}
          onBack={() => setFullAnalysisPaper(null)}
        />
      </DecisionProvider>
    );
  }

  const meta = PAGE_META[activeTab];
  const PageIcon = meta.icon;

  return (
    <DecisionProvider>
      <div className="min-h-screen bg-gray-50">
        {/* Sidebar */}
        <Sidebar
          activeTab={activeTab}
          onTabChange={setActiveTab}
          username={user?.username}
          credits={user?.credits}
          isSuperuser={user?.is_superuser}
          onLogout={logout}
        />

        {/* Main Content Area */}
        <div className="main-content">
          <div className="max-w-[1200px] mx-auto px-8 py-8">

            {/* Hero Section */}
            <div className="hero-section mb-8">
              <div className="relative z-10 flex items-start justify-between">
                <div>
                  <div className="flex items-center gap-3 mb-3">
                    <div className="w-10 h-10 rounded-xl bg-white/80 backdrop-blur-sm shadow-soft flex items-center justify-center">
                      <PageIcon className="w-5 h-5 text-primary-600" />
                    </div>
                    <h1 className="text-hero text-slate-900">{meta.title}</h1>
                  </div>
                  <p className="text-sm text-slate-500 max-w-lg">{meta.subtitle}</p>
                  {activeTab === 'overview' && (
                    <div className="flex items-center gap-2 mt-4 px-3 py-2 bg-white/60 backdrop-blur-sm rounded-xl border border-white/80 max-w-fit">
                      <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse-soft" />
                      <p className="text-sm text-slate-600">{narrative}</p>
                    </div>
                  )}
                </div>
                {activeTab === 'overview' && (
                  <button
                    onClick={() => setActiveTab('upload')}
                    className="btn-primary shrink-0 hidden lg:inline-flex"
                  >
                    <FileText className="w-4 h-4" />
                    导入新文献
                  </button>
                )}
              </div>
            </div>

            {/* Page Content with Animation */}
            <AnimatePresence mode="wait">
              <motion.div
                key={activeTab}
                variants={pageVariants}
                initial="initial"
                animate="animate"
                exit="exit"
              >
                {activeTab === 'overview' && (
                  <div className="space-y-8">
                    {/* Stats Grid */}
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
                      <StatsCard
                        title="论文总数"
                        value={stats?.total_papers || 0}
                        trend={weeklyCount > 0 ? `+${weeklyCount} 本周` : undefined}
                        icon={<FileText className="w-5 h-5" />}
                        color="blue"
                      />
                      <StatsCard
                        title="平均影响力"
                        value={stats?.avg_score ? Number(stats.avg_score).toFixed(1) : '—'}
                        trend={stats?.avg_score && stats.avg_score >= 7.5 ? 'Top 10%' : undefined}
                        icon={<TrendingUp className="w-5 h-5" />}
                        color="emerald"
                        highlight={!!stats?.avg_score && stats.avg_score >= 7.5}
                      />
                      <StatsCard
                        title="研究主题"
                        value={stats?.cluster_count || 0}
                        trend="已聚类"
                        icon={<Layers className="w-5 h-5" />}
                        color="violet"
                      />
                      <StatsCard
                        title="待读清单"
                        value={readingListCount}
                        trend={unreviewedCount > 0 ? `${unreviewedCount} 待审阅` : '已全部审阅'}
                        icon={<BookOpen className="w-5 h-5" />}
                        color="amber"
                      />
                    </div>

                    {/* Research Focus - Decision Card */}
                    <ResearchFocus
                      papers={papers}
                      onPaperClick={(paper) => setSelectedPaper(paper)}
                    />

                    {/* Filter Tags Bar */}
                    <AnimatePresence>
                      {hasFilter && (
                        <motion.div
                          initial={{ opacity: 0, height: 0 }}
                          animate={{ opacity: 1, height: 'auto' }}
                          exit={{ opacity: 0, height: 0 }}
                          className="overflow-hidden"
                        >
                          <div className="flex items-center gap-2 flex-wrap px-1">
                            <span className="text-[11px] text-slate-400 font-medium shrink-0">筛选条件</span>
                            {Array.from(selectedThemes).map(t => (
                              <FilterTag key={`t-${t}`} label={t} color="violet" onRemove={() => toggleTheme(t)} />
                            ))}
                            {Array.from(selectedYears).map(y => (
                              <FilterTag key={`y-${y}`} label={String(y)} color="blue" onRemove={() => toggleYear(y)} />
                            ))}
                            <button
                              onClick={clearAllFilters}
                              className="text-[11px] text-slate-400 hover:text-red-500 font-medium ml-1 transition-colors"
                            >
                              清除全部
                            </button>
                          </div>
                        </motion.div>
                      )}
                    </AnimatePresence>

                    {/* Distribution Charts */}
                    {chartData && (
                      <>
                        {/* Row: Theme (left) + Score (right) */}
                        <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
                          {/* Theme Distribution */}
                          <CompactDistCard title="主题分布" subtitle={`${chartData.themeDist.length} 个主题`} badge={chartData.themeDiagnosis}>
                            {chartData.themeDist.map((d) => (
                              <InlineBar
                                key={d.name}
                                label={d.name}
                                value={d.value}
                                max={chartData.themeDist[0]?.value || 1}
                                color="violet"
                                dimmed={selectedThemes.size > 0 && !selectedThemes.has(d.name)}
                                onClick={() => toggleTheme(d.name)}
                              />
                            ))}
                          </CompactDistCard>

                          {/* Score Distribution */}
                          <CompactDistCard title="评分分布" subtitle={`${chartData.filteredCount} 篇论文`} badge={chartData.scoreDiagnosis}>
                            {chartData.scoreBuckets.map((d) => (
                              <InlineBar
                                key={d.range}
                                label={d.range}
                                value={d.count}
                                max={Math.max(...chartData.scoreBuckets.map(x => x.count), 1)}
                                color="emerald"
                              />
                            ))}
                          </CompactDistCard>
                        </div>

                        {/* Year Distribution - Full width vertical bar chart */}
                        <div className="bg-white rounded-2xl border border-slate-100 shadow-card px-5 py-4 hover:shadow-card-hover transition-shadow duration-300">
                          <div className="flex items-baseline justify-between mb-3">
                            <div className="flex items-center gap-2">
                              <h3 className="text-sm font-semibold text-slate-800">年份分布</h3>
                              <span className={`text-[10px] font-semibold px-1.5 py-0.5 rounded border ${chartData.yearDiagnosis.color}`}>
                                {chartData.yearDiagnosis.label}
                              </span>
                            </div>
                            <span className="text-[11px] text-slate-400">点击柱体筛选年份</span>
                          </div>
                          <ResponsiveContainer width="100%" height={180}>
                            <BarChart data={chartData.yearDist} barCategoryGap="18%">
                              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
                              <XAxis dataKey="year" tick={{ fontSize: 11, fill: '#94a3b8' }} axisLine={false} tickLine={false} />
                              <YAxis tick={{ fontSize: 11, fill: '#94a3b8' }} allowDecimals={false} axisLine={false} tickLine={false} width={28} />
                              <Tooltip
                                contentStyle={{ borderRadius: '10px', border: 'none', boxShadow: '0 4px 16px rgba(0,0,0,0.1)', padding: '6px 10px', fontSize: '12px', backgroundColor: 'rgba(255,255,255,0.95)' }}
                                formatter={(value: number) => [`${value} 篇`, '数量']}
                                cursor={{ fill: 'rgba(59,130,246,0.06)' }}
                              />
                              <Bar dataKey="count" radius={[4, 4, 0, 0]} cursor="pointer" onClick={(data: { year: number }) => toggleYear(data.year)}>
                                {chartData.yearDist.map((entry) => (
                                  <Cell
                                    key={entry.year}
                                    fill={selectedYears.size === 0 || selectedYears.has(entry.year) ? '#3b82f6' : '#e2e8f0'}
                                  />
                                ))}
                              </Bar>
                            </BarChart>
                          </ResponsiveContainer>
                        </div>
                      </>
                    )}

                    {/* Paper List Section */}
                    <div className="bg-white rounded-2xl shadow-card border border-slate-100 overflow-hidden">
                      <div className="flex items-center justify-between px-6 py-5 border-b border-slate-100">
                        <div>
                          <h3 className="text-base font-semibold text-slate-800">
                            {hasFilter ? `筛选结果` : '最新入库'}
                          </h3>
                          <p className="text-xs text-slate-400 mt-0.5">
                            {hasFilter
                              ? `共 ${chartData?.filteredCount ?? 0} 篇符合条件的论文`
                              : '按入库时间排序，点击查看速览'}
                          </p>
                        </div>
                        <div className="flex items-center gap-2">
                          {hasFilter ? (
                            <button
                              onClick={clearAllFilters}
                              className="text-sm font-medium text-slate-400 hover:text-red-500 flex items-center gap-1 transition-colors"
                            >
                              清除筛选 <X className="w-3.5 h-3.5" />
                            </button>
                          ) : (
                            <button className="text-sm font-medium text-primary-600 hover:text-primary-700 flex items-center gap-1 transition-colors">
                              查看全部 <ArrowRight className="w-3.5 h-3.5" />
                            </button>
                          )}
                          <ExportButton />
                        </div>
                      </div>
                      <div className="p-2">
                        <PaperList
                          onPaperClick={(paper) => setSelectedPaper(paper)}
                          filterIds={hasFilter ? chartData?.filteredIds : undefined}
                          paginationMode
                        />
                      </div>
                    </div>
                  </div>
                )}

                {activeTab === 'analysis' && (
                  <AnalysisView onPaperClick={(paper) => setSelectedPaper(paper)} />
                )}

                {activeTab === 'clustering' && (
                  <ClusteringView onPaperClick={async (paper) => {
                    try {
                      const res = await paperAPI.get(paper.id);
                      setSelectedPaper(res.data);
                    } catch {
                      setSelectedPaper(paper as any);
                    }
                  }} />
                )}

                {activeTab === 'reading-list' && (
                  <ReadingList onPaperClick={(paper) => setSelectedPaper(paper)} />
                )}

                {activeTab === 'upload' && (
                  <IngestManager />
                )}

                {activeTab === 'workspace-settings' && (
                  <WorkspaceManager />
                )}

                {activeTab === 'admin' && (
                  <AdminPanel />
                )}
              </motion.div>
            </AnimatePresence>

            {/* Detail Panel (Evidence Drawer) */}
            <EvidenceDrawer
              paper={selectedPaper}
              isOpen={!!selectedPaper}
              onClose={() => setSelectedPaper(null)}
              onFullAnalysis={(paper) => {
                setSelectedPaper(null);
                setFullAnalysisPaper(paper);
              }}
            />
          </div>
        </div>

        <DecisionToast />
      </div>
    </DecisionProvider>
  );
}

/* ── Compact Distribution Components ── */

const BAR_COLORS: Record<string, { bar: string; bg: string }> = {
  violet:  { bar: 'bg-primary-500', bg: 'bg-primary-50' },
  blue:    { bar: 'bg-blue-500',    bg: 'bg-blue-50' },
  emerald: { bar: 'bg-emerald-500', bg: 'bg-emerald-50' },
};

function CompactDistCard({ title, subtitle, badge, children }: { title: string; subtitle: string; badge?: { label: string; color: string }; children: React.ReactNode }) {
  return (
    <div className="bg-white rounded-2xl border border-slate-100 shadow-card px-5 py-4 hover:shadow-card-hover transition-shadow duration-300">
      <div className="flex items-baseline justify-between mb-3">
        <div className="flex items-center gap-2">
          <h3 className="text-sm font-semibold text-slate-800">{title}</h3>
          {badge && (
            <span className={`text-[10px] font-semibold px-1.5 py-0.5 rounded border ${badge.color}`}>
              {badge.label}
            </span>
          )}
        </div>
        <span className="text-[11px] text-slate-400">{subtitle}</span>
      </div>
      <div className="space-y-1.5">{children}</div>
    </div>
  );
}

function InlineBar({ label, value, max, color = 'violet', dimmed, onClick }: {
  label: string; value: number; max: number; color?: string; dimmed?: boolean; onClick?: () => void;
}) {
  const c = BAR_COLORS[color] || BAR_COLORS.violet;
  const pct = max > 0 ? (value / max) * 100 : 0;
  return (
    <div
      className={`flex items-center gap-2 h-6 group transition-opacity duration-200 ${onClick ? 'cursor-pointer' : ''} ${dimmed ? 'opacity-35' : 'opacity-100'}`}
      onClick={onClick}
    >
      <span className="text-[11px] text-slate-500 w-[90px] truncate shrink-0" title={label}>{label}</span>
      <div className={`flex-1 h-4 ${c.bg} rounded overflow-hidden`}>
        <div
          className={`h-full ${c.bar} rounded transition-all duration-500`}
          style={{ width: `${Math.max(pct, 2)}%` }}
        />
      </div>
      <span className="text-[11px] font-semibold text-slate-600 w-6 text-right tabular-nums shrink-0">{value}</span>
    </div>
  );
}

const FILTER_TAG_COLORS: Record<string, string> = {
  violet: 'bg-primary-50 text-primary-700 border-primary-200',
  blue: 'bg-blue-50 text-blue-700 border-blue-200',
};

function FilterTag({ label, color = 'violet', onRemove }: { label: string; color?: string; onRemove: () => void }) {
  const cls = FILTER_TAG_COLORS[color] || FILTER_TAG_COLORS.violet;
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full border text-[11px] font-medium ${cls}`}>
      {label}
      <button onClick={(e) => { e.stopPropagation(); onRemove(); }} className="hover:opacity-60 transition-opacity">
        <X className="w-3 h-3" />
      </button>
    </span>
  );
}
