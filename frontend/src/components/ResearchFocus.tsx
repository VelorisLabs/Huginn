import { useMemo } from 'react';
import { useDecision } from './decision/DecisionContext';
import { DecisionBar } from './decision/DecisionBar';
import { type Paper } from '@/lib/api';
import { getScoreColor } from '@/lib/scoreUtils';
import { Zap, Award, TrendingUp } from 'lucide-react';

interface ResearchFocusProps {
  papers: Paper[];
  onPaperClick: (paper: Paper) => void;
}

export function ResearchFocus({ papers, onPaperClick }: ResearchFocusProps) {
  const { decisions } = useDecision();

  const { unreviewedPapers, topPapers, unreviewedCount, keptCount } = useMemo(() => {
    const decidedIds = new Set(Object.keys(decisions).map(Number));
    const unreviewed = papers.filter(p => !decidedIds.has(p.id));
    const kept = Object.values(decisions).filter(d => d === 'keep').length;

    // Top papers: highest scored unreviewed, max 5
    const top = [...unreviewed]
      .sort((a, b) => (b.overall_score || 0) - (a.overall_score || 0))
      .slice(0, 5);

    return {
      unreviewedPapers: unreviewed,
      topPapers: top,
      unreviewedCount: unreviewed.length,
      keptCount: kept,
    };
  }, [papers, decisions]);

  // Determine insight message (must be before any conditional return)
  const insight = useMemo(() => {
    if (unreviewedCount === 0) {
      return { text: '所有论文已审阅完毕，研究进展良好', type: 'success' as const };
    }
    if (unreviewedCount <= 3) {
      return { text: `仅剩 ${unreviewedCount} 篇待审阅，即将完成全部审阅`, type: 'info' as const };
    }
    const highScoreUnreviewed = unreviewedPapers.filter(p => (p.overall_score || 0) >= 8).length;
    if (highScoreUnreviewed > 0) {
      return { text: `${unreviewedCount} 篇待审阅，其中 ${highScoreUnreviewed} 篇高分论文值得优先关注`, type: 'action' as const };
    }
    return { text: `${unreviewedCount} 篇论文待审阅，以下是评分最高的候选`, type: 'neutral' as const };
  }, [unreviewedCount, unreviewedPapers]);

  if (papers.length === 0) return null;

  const INSIGHT_STYLES = {
    success: 'bg-emerald-50 border-emerald-200 text-emerald-700',
    info: 'bg-blue-50 border-blue-200 text-blue-700',
    action: 'bg-amber-50 border-amber-200 text-amber-700',
    neutral: 'bg-slate-50 border-slate-200 text-slate-600',
  };

  return (
    <div className="rounded-2xl border border-primary-100 bg-gradient-to-br from-primary-50/60 via-white to-blue-50/40 shadow-card overflow-hidden">
      {/* Header */}
      <div className="px-5 pt-5 pb-3">
        <div className="flex items-center gap-2.5 mb-3">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary-500 to-primary-600 flex items-center justify-center shadow-sm">
            <Zap className="w-4 h-4 text-white" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-slate-800">研究焦点</h3>
            <p className="text-[11px] text-slate-400">系统根据评分推荐的优先阅读论文</p>
          </div>
          <div className="ml-auto flex items-center gap-3">
            <div className="text-right">
              <span className="text-[11px] text-slate-400 block">待审阅</span>
              <span className={`text-lg font-bold tabular-nums ${unreviewedCount > 0 ? 'text-amber-600' : 'text-emerald-600'}`}>
                {unreviewedCount}
              </span>
            </div>
            <div className="text-right">
              <span className="text-[11px] text-slate-400 block">已收藏</span>
              <span className="text-lg font-bold tabular-nums text-primary-600">{keptCount}</span>
            </div>
          </div>
        </div>

        {/* Insight Badge */}
        <div className="relative group/tip inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border text-[12px] font-medium cursor-default"
          style={{ /* keep className on next line for readability */ }}
        >
          <div className={`inline-flex items-center gap-1.5 ${INSIGHT_STYLES[insight.type]} rounded-lg`}>
            {insight.type === 'action' && <TrendingUp className="w-3 h-3" />}
            {insight.type === 'success' && <Award className="w-3 h-3" />}
            {insight.text}
          </div>
          {/* Hover Tooltip */}
          {insight.type === 'action' && (
            <div className="absolute left-0 bottom-full mb-2 w-72 p-3 bg-slate-800 text-white text-[11px] leading-relaxed rounded-xl shadow-lg opacity-0 group-hover/tip:opacity-100 pointer-events-none transition-opacity duration-200 z-20">
              <p className="font-semibold mb-1">📊 评判依据</p>
              <p>「高分论文」= 综合评分 ≥ 8.0 的未审阅论文。</p>
              <p className="mt-1 text-slate-300">综合评分由五维加权计算：严谨性、创新性、实用性、影响力、可读性。</p>
              <div className="absolute left-6 top-full w-0 h-0 border-l-[6px] border-l-transparent border-r-[6px] border-r-transparent border-t-[6px] border-t-slate-800" />
            </div>
          )}
        </div>
      </div>

      {/* Top Papers List */}
      {topPapers.length > 0 && (
        <div className="px-3 pb-3">
          <div className="space-y-1">
            {topPapers.map((paper, idx) => (
              <div
                key={paper.id}
                className="group flex items-center gap-3 px-3 py-2.5 rounded-xl bg-white/70 hover:bg-white border border-transparent hover:border-slate-100 hover:shadow-sm transition-all duration-200 cursor-pointer"
                onClick={() => onPaperClick(paper)}
              >
                {/* Rank */}
                <span className={`w-5 h-5 rounded-md flex items-center justify-center text-[10px] font-bold shrink-0 ${
                  idx === 0 ? 'bg-amber-100 text-amber-700' :
                  idx === 1 ? 'bg-slate-100 text-slate-500' :
                  'bg-slate-50 text-slate-400'
                }`}>
                  {idx + 1}
                </span>

                {/* Content */}
                <div className="flex-1 min-w-0">
                  <h4 className="text-[13px] font-semibold text-slate-700 group-hover:text-slate-900 line-clamp-1 transition-colors">
                    {paper.title}
                  </h4>
                  <div className="flex items-center gap-2 mt-0.5">
                    {paper.authors && (
                      <span className="text-[11px] text-slate-400 truncate max-w-[180px]">{paper.authors}</span>
                    )}
                    {paper.year && (
                      <span className="text-[11px] text-slate-400 shrink-0">{paper.year}</span>
                    )}
                    {paper.cluster_topic && (
                      <span className="text-[10px] font-medium text-primary-600 bg-primary-50 px-1.5 py-0.5 rounded border border-primary-100 shrink-0">
                        {paper.cluster_topic}
                      </span>
                    )}
                  </div>
                </div>

                {/* Score */}
                <span className={`text-[15px] font-bold font-mono shrink-0 ${getScoreColor(paper.overall_score || 0)}`}>
                  {(paper.overall_score || 0).toFixed(1)}
                </span>

                {/* Decision Actions */}
                <div className="opacity-0 group-hover:opacity-100 transition-opacity duration-200 shrink-0">
                  <DecisionBar paperId={paper.id} compact />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* All reviewed state */}
      {topPapers.length === 0 && (
        <div className="px-5 pb-5 text-center">
          <div className="py-4">
            <Award className="w-8 h-8 text-emerald-400 mx-auto mb-2" />
            <p className="text-sm text-slate-500">所有论文已完成审阅</p>
          </div>
        </div>
      )}
    </div>
  );
}
