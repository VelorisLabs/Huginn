import { useState, useMemo, useCallback, useEffect, useRef } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { clusteringAPI, type ClusterGroup, type ClusterPaper, type ClusteringResults } from '@/lib/api';
import {
  Layers, Play, RefreshCw, ChevronDown, Users, Calendar, BookOpen,
  AlertCircle, Check, ArrowUpDown, ChevronUp, Tag, Hash, Sparkles
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

type SortKey = 'score-desc' | 'score-asc' | 'year' | 'id';

interface ClusteringViewProps {
  onPaperClick?: (paper: ClusterPaper) => void;
}

export function ClusteringView({ onPaperClick }: ClusteringViewProps) {
  const queryClient = useQueryClient();
  const [selectedCluster, setSelectedCluster] = useState<number | null>(null);
  const [sortBy, setSortBy] = useState<SortKey>('score-desc');
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [taskId, setTaskId] = useState<string | null>(null);
  const [polling, setPolling] = useState(false);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Fetch clustering results
  const { data: resultsData, isLoading } = useQuery({
    queryKey: ['clustering-results'],
    queryFn: async () => {
      const res = await clusteringAPI.getResults();
      return res.data as ClusteringResults;
    },
  });

  const hasResults = resultsData?.has_results ?? false;
  const clusters = resultsData?.clusters ?? [];

  // Auto-select first cluster
  useEffect(() => {
    if (clusters.length > 0 && selectedCluster === null) {
      setSelectedCluster(clusters[0].cluster_id);
    }
  }, [clusters, selectedCluster]);

  // Close dropdown on outside click
  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setDropdownOpen(false);
      }
    }
    if (dropdownOpen) document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, [dropdownOpen]);

  // Run clustering mutation
  const runMut = useMutation({
    mutationFn: () => clusteringAPI.run(),
    onSuccess: (res) => {
      const id = res.data?.task_id;
      if (id) {
        setTaskId(id);
        setPolling(true);
      }
    },
  });

  // Poll task status
  const [progress, setProgress] = useState(0);
  const [currentStep, setCurrentStep] = useState('');

  useEffect(() => {
    if (!polling || !taskId) return;

    const poll = async () => {
      try {
        const res = await clusteringAPI.getStatus(taskId);
        const data = res.data;
        setProgress(data.progress || 0);
        setCurrentStep(data.current_step || '');

        if (data.status === 'completed') {
          setPolling(false);
          setTaskId(null);
          setSelectedCluster(null);
          queryClient.invalidateQueries({ queryKey: ['clustering-results'] });
          queryClient.invalidateQueries({ queryKey: ['stats'] });
          queryClient.invalidateQueries({ queryKey: ['papers-analysis'] });
        } else if (data.status === 'failed') {
          setPolling(false);
          setTaskId(null);
        }
      } catch {
        // ignore polling errors
      }
    };

    pollRef.current = setInterval(poll, 1500);
    poll(); // immediate first call

    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, [polling, taskId, queryClient]);

  // Current cluster data
  const currentCluster = useMemo(() => {
    if (selectedCluster === null) return null;
    return clusters.find(c => c.cluster_id === selectedCluster) ?? null;
  }, [clusters, selectedCluster]);

  // Sorted papers
  const sortedPapers = useMemo(() => {
    if (!currentCluster) return [];
    const papers = [...currentCluster.papers];
    switch (sortBy) {
      case 'score-desc':
        return papers.sort((a, b) => (b.overall_score || 0) - (a.overall_score || 0));
      case 'score-asc':
        return papers.sort((a, b) => (a.overall_score || 0) - (b.overall_score || 0));
      case 'year':
        return papers.sort((a, b) => (b.year || 0) - (a.year || 0));
      case 'id':
        return papers.sort((a, b) => a.id - b.id);
      default:
        return papers;
    }
  }, [currentCluster, sortBy]);

  const clusterLabel = useCallback((c: ClusterGroup) => {
    return `主题 ${c.cluster_id + 1}: ${c.topic_keywords.slice(0, 3).join(', ')}`;
  }, []);

  // Score color helper
  const scoreColor = (s: number) => {
    if (s >= 8) return 'text-emerald-600';
    if (s >= 7) return 'text-blue-600';
    return 'text-slate-500';
  };

  // Loading state
  if (isLoading) {
    return (
      <div className="space-y-6">
        {[1, 2].map(i => (
          <div key={i} className="h-48 bg-slate-100 rounded-xl animate-pulse" />
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header Card */}
      <div className="bg-white rounded-2xl border border-slate-100 shadow-card overflow-hidden">
        <div className="px-6 py-5 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-violet-100 to-violet-200 flex items-center justify-center">
              <Layers className="w-5 h-5 text-violet-600" />
            </div>
            <div>
              <h3 className="text-base font-semibold text-slate-800">主题聚类分析</h3>
              <p className="text-xs text-slate-400 mt-0.5">
                基于 TF-IDF + 余弦相似度，自动发现论文间的内在关联
              </p>
            </div>
          </div>
          <button
            onClick={() => runMut.mutate()}
            disabled={runMut.isPending || polling}
            className="px-4 py-2 text-sm font-medium text-white bg-violet-600 hover:bg-violet-700 rounded-xl transition-colors flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed shadow-sm"
          >
            {polling ? (
              <RefreshCw className="w-4 h-4 animate-spin" />
            ) : (
              <Play className="w-4 h-4" />
            )}
            {polling ? '分析中...' : hasResults ? '重新聚类' : '开始聚类分析'}
          </button>
        </div>

        {/* Progress Bar */}
        <AnimatePresence>
          {polling && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              className="overflow-hidden"
            >
              <div className="px-6 pb-5 space-y-2">
                <div className="flex items-center justify-between text-xs">
                  <span className="text-violet-600 font-medium">{currentStep || '准备中...'}</span>
                  <span className="text-slate-400 font-mono">{progress}%</span>
                </div>
                <div className="w-full h-2 bg-violet-100 rounded-full overflow-hidden">
                  <motion.div
                    className="h-full bg-gradient-to-r from-violet-500 to-violet-600 rounded-full"
                    initial={{ width: 0 }}
                    animate={{ width: `${progress}%` }}
                    transition={{ duration: 0.3 }}
                  />
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Error */}
        {runMut.isError && (
          <div className="px-6 pb-5">
            <div className="flex items-center gap-2 text-sm text-red-600 bg-red-50 px-3 py-2 rounded-lg">
              <AlertCircle className="w-4 h-4 shrink-0" />
              {(runMut.error as any)?.response?.data?.detail || '聚类分析失败'}
            </div>
          </div>
        )}
      </div>

      {/* No Results */}
      {!hasResults && !polling && (
        <div className="text-center py-16 bg-slate-50/50 rounded-xl border border-dashed border-slate-200">
          <Layers className="w-12 h-12 text-slate-300 mx-auto mb-3" />
          <h3 className="text-lg font-medium text-slate-700 mb-2">尚未进行聚类分析</h3>
          <p className="text-sm text-slate-400 max-w-md mx-auto">
            点击上方「开始聚类分析」，系统将自动分析所有论文的文本相似度，
            发现跨主题桶的内在关联，帮助你快速识别研究脉络。
          </p>
        </div>
      )}

      {/* Clustering Results */}
      {hasResults && clusters.length > 0 && (
        <>
          {/* Stats */}
          <div className="grid grid-cols-3 gap-4">
            <div className="bg-white rounded-2xl border border-slate-100 shadow-card px-5 py-4">
              <div className="flex items-center gap-2 mb-1">
                <Sparkles className="w-4 h-4 text-violet-500" />
                <span className="text-xs text-slate-400">发现聚类</span>
              </div>
              <p className="text-2xl font-bold text-slate-800">{resultsData?.cluster_count}</p>
            </div>
            <div className="bg-white rounded-2xl border border-slate-100 shadow-card px-5 py-4">
              <div className="flex items-center gap-2 mb-1">
                <Hash className="w-4 h-4 text-blue-500" />
                <span className="text-xs text-slate-400">已聚类论文</span>
              </div>
              <p className="text-2xl font-bold text-slate-800">{resultsData?.clustered_papers}</p>
            </div>
            <div className="bg-white rounded-2xl border border-slate-100 shadow-card px-5 py-4">
              <div className="flex items-center gap-2 mb-1">
                <BookOpen className="w-4 h-4 text-emerald-500" />
                <span className="text-xs text-slate-400">论文总数</span>
              </div>
              <p className="text-2xl font-bold text-slate-800">{resultsData?.total_papers}</p>
            </div>
          </div>

          {/* Cluster Explorer */}
          <div className="bg-white rounded-2xl border border-slate-100 shadow-card overflow-hidden">
            {/* Cluster Selector */}
            <div className="px-6 py-5 border-b border-slate-100">
              <h3 className="text-base font-semibold text-slate-800 mb-3">探索主题详情</h3>
              <div className="flex items-start gap-4">
                {/* Dropdown */}
                <div className="flex-1" ref={dropdownRef}>
                  <label className="text-xs text-slate-500 mb-1.5 block">选择要探索的主题：</label>
                  <div className="relative">
                    <button
                      onClick={() => setDropdownOpen(!dropdownOpen)}
                      className="w-full flex items-center justify-between px-4 py-3 rounded-xl border-2 border-violet-200 bg-white hover:border-violet-300 transition-colors text-left"
                    >
                      <span className="text-sm font-semibold text-slate-700">
                        {currentCluster ? clusterLabel(currentCluster) : '选择聚类主题...'}
                      </span>
                      <ChevronDown className={`w-4 h-4 text-slate-400 transition-transform ${dropdownOpen ? 'rotate-180' : ''}`} />
                    </button>

                    <AnimatePresence>
                      {dropdownOpen && (
                        <motion.div
                          initial={{ opacity: 0, y: -4 }}
                          animate={{ opacity: 1, y: 0 }}
                          exit={{ opacity: 0, y: -4 }}
                          className="absolute z-50 top-full left-0 right-0 mt-1.5 bg-white rounded-xl shadow-lg shadow-slate-200/60 overflow-hidden border border-slate-200 ring-1 ring-slate-100"
                        >
                          <div className="max-h-64 overflow-y-auto py-1">
                            {clusters.map(c => (
                              <button
                                key={c.cluster_id}
                                onClick={() => {
                                  setSelectedCluster(c.cluster_id);
                                  setDropdownOpen(false);
                                }}
                                className={`w-full text-left px-4 py-3 text-sm transition-all duration-150 ${
                                  c.cluster_id === selectedCluster
                                    ? 'bg-violet-50 text-violet-700 font-semibold border-l-2 border-violet-500'
                                    : 'text-slate-600 hover:bg-slate-50 hover:text-slate-800 border-l-2 border-transparent'
                                }`}
                              >
                                {clusterLabel(c)}
                              </button>
                            ))}
                          </div>
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </div>
                </div>
              </div>

              {/* Topic Keywords Tags */}
              {currentCluster && (
                <div className="flex flex-wrap gap-2 mt-4">
                  {currentCluster.topic_keywords.map((kw, i) => (
                    <span
                      key={i}
                      className="px-3 py-1 text-xs font-medium text-violet-700 bg-violet-100 rounded-full border border-violet-200"
                    >
                      {kw}
                    </span>
                  ))}
                </div>
              )}
            </div>

            {/* Papers in Cluster */}
            {currentCluster && (
              <div>
                <div className="px-6 py-4 border-b border-slate-50 flex items-center justify-between">
                  <h4 className="text-sm font-semibold text-slate-800">
                    主题 {currentCluster.cluster_id + 1} 中的论文 ({currentCluster.paper_count} 篇)
                  </h4>
                  <div className="flex items-center gap-1 text-xs text-slate-500">
                    <span>排序方式：</span>
                    {([
                      { key: 'score-desc' as SortKey, label: '评分 (高到低)' },
                      { key: 'score-asc' as SortKey, label: '评分 (低到高)' },
                      { key: 'id' as SortKey, label: '编号' },
                      { key: 'year' as SortKey, label: '年份' },
                    ]).map(opt => (
                      <button
                        key={opt.key}
                        onClick={() => setSortBy(opt.key)}
                        className={`px-2 py-1 rounded-md transition-colors ${
                          sortBy === opt.key
                            ? 'bg-violet-100 text-violet-700 font-medium'
                            : 'hover:bg-slate-100 text-slate-500'
                        }`}
                      >
                        {opt.label}
                      </button>
                    ))}
                  </div>
                </div>

                <div className="divide-y divide-slate-50">
                  {sortedPapers.map((paper) => (
                    <div
                      key={paper.id}
                      className="px-6 py-4 hover:bg-slate-50/50 cursor-pointer transition-all group"
                      onClick={() => onPaperClick?.(paper)}
                    >
                      <div className="flex items-start gap-3">
                        <span className="text-xs font-mono text-slate-400 bg-slate-100 px-2 py-1 rounded-md shrink-0 mt-0.5">
                          {paper.id}
                        </span>
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-semibold text-slate-700 group-hover:text-slate-900 transition-colors leading-relaxed">
                            {paper.title}
                          </p>
                          <div className="flex items-center gap-3 mt-1.5 text-xs text-slate-400">
                            {paper.authors && (
                              <span className="inline-flex items-center gap-1 truncate max-w-[200px]">
                                <Users className="w-3 h-3 shrink-0" />
                                {paper.authors}
                              </span>
                            )}
                            {paper.year && (
                              <span className="inline-flex items-center gap-1 shrink-0">
                                <Calendar className="w-3 h-3" />
                                {paper.year}
                              </span>
                            )}
                            {paper.venue && (
                              <span className="inline-flex items-center gap-1 shrink-0">
                                <BookOpen className="w-3 h-3" />
                                {paper.venue}
                              </span>
                            )}
                            {paper.theme_name && (
                              <span className="inline-flex items-center gap-1 shrink-0 text-violet-500">
                                <Tag className="w-3 h-3" />
                                {paper.theme_name}
                              </span>
                            )}
                          </div>
                        </div>
                        {paper.overall_score != null && (
                          <div className="text-right shrink-0">
                            <span className={`text-lg font-bold font-mono ${scoreColor(paper.overall_score)}`}>
                              {paper.overall_score.toFixed(1)}
                            </span>
                            <p className="text-[10px] text-slate-400">评分</p>
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Cluster Overview Cards */}
          <div className="bg-white rounded-2xl border border-slate-100 shadow-card overflow-hidden">
            <div className="px-6 py-5 border-b border-slate-100">
              <h3 className="text-base font-semibold text-slate-800">聚类概览</h3>
              <p className="text-xs text-slate-400 mt-0.5">所有聚类主题一览，点击可切换查看</p>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 p-4">
              {clusters.map(c => {
                const isActive = c.cluster_id === selectedCluster;
                return (
                  <button
                    key={c.cluster_id}
                    onClick={() => {
                      setSelectedCluster(c.cluster_id);
                      window.scrollTo({ top: 0, behavior: 'smooth' });
                    }}
                    className={`text-left rounded-xl p-4 border-2 transition-all duration-200 ${
                      isActive
                        ? 'border-violet-300 ring-2 ring-violet-100 bg-white shadow-sm'
                        : 'border-slate-100 bg-slate-50/50 hover:border-slate-200 hover:bg-white'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <span className={`text-sm font-bold ${isActive ? 'text-violet-700' : 'text-slate-700'}`}>
                        主题 {c.cluster_id + 1}
                      </span>
                      <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${
                        isActive ? 'bg-violet-100 text-violet-600' : 'bg-slate-100 text-slate-500'
                      }`}>
                        {c.paper_count} 篇
                      </span>
                    </div>
                    <div className="flex flex-wrap gap-1.5">
                      {c.topic_keywords.slice(0, 5).map((kw, i) => (
                        <span
                          key={i}
                          className={`text-[11px] px-2 py-0.5 rounded-md ${
                            isActive
                              ? 'bg-violet-50 text-violet-600 border border-violet-100'
                              : 'bg-slate-100 text-slate-500'
                          }`}
                        >
                          {kw}
                        </span>
                      ))}
                    </div>
                  </button>
                );
              })}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
