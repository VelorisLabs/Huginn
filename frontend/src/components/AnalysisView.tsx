import { useMemo, useState, useCallback } from 'react';
import { useQuery } from '@tanstack/react-query';
import { paperAPI, type Paper } from '@/lib/api';
import { Target, Lightbulb, Scale, Users, Calendar, BookOpen, ArrowUpDown, ChevronUp, ChevronDown } from 'lucide-react';

type DimKey = 'rigor' | 'innovation' | 'practicality' | 'impact' | 'readability';

const DIM_META: { key: DimKey; label: string; color: string }[] = [
  { key: 'rigor', label: '严谨度', color: 'bg-violet-500' },
  { key: 'innovation', label: '创新性', color: 'bg-blue-500' },
  { key: 'practicality', label: '实用性', color: 'bg-emerald-500' },
  { key: 'impact', label: '影响力', color: 'bg-amber-500' },
  { key: 'readability', label: '可读性', color: 'bg-slate-400' },
];

interface Scenario {
  id: string;
  name: string;
  desc: string;
  icon: typeof Target;
  accent: string;
  ring: string;
  weights: Record<DimKey, number>;
}

const SCENARIOS: Scenario[] = [
  {
    id: 'applied', name: '应用导向型', desc: '侧重实用性与影响力',
    icon: Target, accent: 'text-emerald-600', ring: 'border-emerald-400 ring-emerald-100',
    weights: { rigor: 0.20, innovation: 0.15, practicality: 0.40, impact: 0.20, readability: 0.05 },
  },
  {
    id: 'theoretical', name: '理论突破型', desc: '侧重创新性与严谨度',
    icon: Lightbulb, accent: 'text-blue-600', ring: 'border-blue-400 ring-blue-100',
    weights: { rigor: 0.25, innovation: 0.40, practicality: 0.10, impact: 0.20, readability: 0.05 },
  },
  {
    id: 'balanced', name: '综合均衡型', desc: '五维均衡评估',
    icon: Scale, accent: 'text-violet-600', ring: 'border-violet-400 ring-violet-100',
    weights: { rigor: 0.25, innovation: 0.25, practicality: 0.25, impact: 0.20, readability: 0.05 },
  },
];

function getWeightedScore(paper: Paper, weights: Record<DimKey, number>): number {
  const r = paper.score_rigor || 0;
  const i = paper.score_innovation || 0;
  const p = paper.score_practicality || 0;
  const m = paper.score_impact || 0;
  const d = paper.score_readability || 0;
  return r * weights.rigor + i * weights.innovation + p * weights.practicality + m * weights.impact + d * weights.readability;
}

function scoreColor(s: number): string {
  if (s >= 8) return 'text-emerald-600';
  if (s >= 7) return 'text-blue-600';
  return 'text-slate-500';
}

interface AnalysisViewProps {
  onPaperClick: (paper: Paper) => void;
}

export function AnalysisView({ onPaperClick }: AnalysisViewProps) {
  const [activeScenario, setActiveScenario] = useState<string>('balanced');

  const { data: response, isLoading } = useQuery({
    queryKey: ['papers-analysis'],
    queryFn: () => paperAPI.list({ limit: 500 }),
  });

  const papers: Paper[] = response?.data || [];
  const scenario = SCENARIOS.find(s => s.id === activeScenario) || SCENARIOS[2];

  const topPapers = useMemo(() => {
    if (papers.length === 0) return [];
    return [...papers]
      .map(p => ({ paper: p, wscore: getWeightedScore(p, scenario.weights) }))
      .sort((a, b) => b.wscore - a.wscore)
      .slice(0, 10);
  }, [papers, scenario]);

  // Comparison table data
  type SortCol = 'overall' | 'applied' | 'theoretical' | 'balanced';
  const [sortCol, setSortCol] = useState<SortCol>('overall');
  const [sortAsc, setSortAsc] = useState(false);

  const handleSort = useCallback((col: SortCol) => {
    if (sortCol === col) { setSortAsc(a => !a); } else { setSortCol(col); setSortAsc(false); }
  }, [sortCol]);

  const comparisonRows = useMemo(() => {
    if (papers.length === 0) return [];
    const rows = papers.map(p => ({
      paper: p,
      overall: p.overall_score || 0,
      applied: getWeightedScore(p, SCENARIOS[0].weights),
      theoretical: getWeightedScore(p, SCENARIOS[1].weights),
      balanced: getWeightedScore(p, SCENARIOS[2].weights),
    }));
    rows.sort((a, b) => sortAsc ? a[sortCol] - b[sortCol] : b[sortCol] - a[sortCol]);
    return rows;
  }, [papers, sortCol, sortAsc]);

  if (isLoading) {
    return (
      <div className="space-y-6">
        {[1, 2].map(i => (
          <div key={i} className="h-48 bg-slate-100 rounded-xl animate-pulse" />
        ))}
      </div>
    );
  }

  if (papers.length === 0) {
    return (
      <div className="text-center py-20 bg-slate-50/50 rounded-xl border border-dashed border-slate-200">
        <h3 className="text-lg font-medium text-slate-900 mb-2">暂无论文数据</h3>
        <p className="text-slate-500">请先在"导入文献"中上传论文，分析结果将自动生成。</p>
      </div>
    );
  }

  const ScenarioIcon = scenario.icon;

  return (
    <div className="space-y-6">
      {/* Scenario Selector */}
      <div className="bg-white rounded-2xl border border-slate-100 shadow-card overflow-hidden">
        <div className="px-6 py-5 border-b border-slate-100">
          <h3 className="text-base font-semibold text-slate-800">选择应用场景</h3>
          <p className="text-xs text-slate-400 mt-0.5">不同场景下，论文的评分权重会动态调整，帮助你找到最适合的文献</p>
        </div>
        <div className="p-4 grid grid-cols-3 gap-4">
          {SCENARIOS.map(s => {
            const Icon = s.icon;
            const isActive = s.id === activeScenario;
            return (
              <button
                key={s.id}
                onClick={() => setActiveScenario(s.id)}
                className={`text-left rounded-xl p-4 border-2 transition-all duration-200 cursor-pointer ${
                  isActive
                    ? `${s.ring} ring-2 bg-white shadow-sm`
                    : 'border-slate-100 bg-slate-50/50 hover:border-slate-200 hover:bg-white'
                }`}
              >
                <div className="flex items-center gap-2 mb-3">
                  <Icon className={`w-4 h-4 ${isActive ? s.accent : 'text-slate-400'}`} />
                  <span className={`text-sm font-semibold ${isActive ? s.accent : 'text-slate-600'}`}>{s.name}</span>
                </div>
                <div className="space-y-1.5">
                  {DIM_META.map(dim => {
                    const pct = Math.round(s.weights[dim.key] * 100);
                    return (
                      <div key={dim.key} className="flex items-center gap-2">
                        <span className="text-[11px] text-slate-500 w-14 shrink-0">{dim.label}</span>
                        <div className="flex-1 h-[6px] bg-slate-100 rounded-full overflow-hidden">
                          <div
                            className={`h-full rounded-full transition-all duration-300 ${isActive ? dim.color : 'bg-slate-300'}`}
                            style={{ width: `${pct}%` }}
                          />
                        </div>
                        <span className={`text-[11px] font-mono w-8 text-right ${isActive ? 'text-slate-600' : 'text-slate-400'}`}>{pct}%</span>
                      </div>
                    );
                  })}
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {/* Top 10 Ranking */}
      <div className="bg-white rounded-2xl border border-slate-100 shadow-card overflow-hidden">
        <div className="px-6 py-5 border-b border-slate-100 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <ScenarioIcon className={`w-5 h-5 ${scenario.accent}`} />
            <div>
              <h3 className="text-base font-semibold text-slate-800">{scenario.name} - Top 10 推荐</h3>
              <p className="text-xs text-slate-400 mt-0.5">基于场景权重的加权评分排序</p>
            </div>
          </div>
          <span className="text-xs text-slate-400 bg-slate-50 px-2.5 py-1 rounded-lg border border-slate-100">
            共 {papers.length} 篇
          </span>
        </div>
        <div className="divide-y divide-slate-50">
          {topPapers.map(({ paper, wscore }, i) => (
            <div
              key={paper.id}
              className="group px-6 py-3.5 flex items-center gap-4 hover:bg-slate-50/50 cursor-pointer transition-all"
              onClick={() => onPaperClick(paper)}
            >
              <span className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold shrink-0 ${
                i === 0 ? 'bg-gradient-to-br from-amber-400 to-amber-500 text-white shadow-sm' :
                i === 1 ? 'bg-gradient-to-br from-slate-300 to-slate-400 text-white' :
                i === 2 ? 'bg-gradient-to-br from-orange-300 to-orange-400 text-white' :
                'bg-slate-100 text-slate-400'
              }`}>
                {i + 1}
              </span>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-semibold text-slate-700 truncate group-hover:text-slate-900 transition-colors">{paper.title}</p>
                <div className="flex items-center gap-2.5 mt-1 text-[12px] text-slate-400">
                  {paper.authors && (
                    <span className="inline-flex items-center gap-0.5 truncate max-w-[200px]">
                      <Users className="w-3 h-3 shrink-0" />
                      {paper.authors}
                    </span>
                  )}
                  {paper.year && (
                    <span className="inline-flex items-center gap-0.5 shrink-0">
                      <Calendar className="w-3 h-3" />
                      {paper.year}
                    </span>
                  )}
                  <span className="inline-flex items-center gap-0.5 shrink-0">
                    <BookOpen className="w-3 h-3" />
                    {paper.venue || 'arXiv'}
                  </span>
                </div>
              </div>
              <div className="text-right shrink-0">
                <span className={`text-lg font-bold font-mono ${scoreColor(wscore)}`}>
                  {wscore.toFixed(2)}
                </span>
                <p className="text-[10px] text-slate-400 mt-0.5">场景评分</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Scenario Score Comparison Table */}
      <div className="bg-white rounded-2xl border border-slate-100 shadow-card overflow-hidden">
        <div className="px-6 py-5 border-b border-slate-100">
          <h3 className="text-base font-semibold text-slate-800">场景评分对比表</h3>
          <p className="text-xs text-slate-400 mt-0.5">横向对比同一论文在不同场景下的加权得分，发现论文的优势维度</p>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-100 bg-slate-50/50">
                <th className="text-left py-3 px-6 text-xs font-semibold text-slate-500 w-[45%]">论文标题</th>
                {([
                  { key: 'overall' as SortCol, label: '综合评分', color: 'text-slate-600' },
                  { key: 'applied' as SortCol, label: '应用导向型', color: 'text-emerald-600' },
                  { key: 'theoretical' as SortCol, label: '理论突破型', color: 'text-blue-600' },
                  { key: 'balanced' as SortCol, label: '综合均衡型', color: 'text-violet-600' },
                ]).map(col => (
                  <th
                    key={col.key}
                    className="text-center py-3 px-3 cursor-pointer hover:bg-slate-100/50 transition-colors select-none"
                    onClick={() => handleSort(col.key)}
                  >
                    <span className={`inline-flex items-center gap-1 text-xs font-semibold ${col.color}`}>
                      {col.label}
                      {sortCol === col.key ? (
                        sortAsc ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />
                      ) : (
                        <ArrowUpDown className="w-3 h-3 text-slate-300" />
                      )}
                    </span>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-50">
              {comparisonRows.map(row => (
                <tr
                  key={row.paper.id}
                  className="hover:bg-slate-50/50 cursor-pointer transition-colors"
                  onClick={() => onPaperClick(row.paper)}
                >
                  <td className="py-2.5 px-6">
                    <p className="text-sm text-slate-700 truncate max-w-[400px]" title={row.paper.title}>
                      {row.paper.title}
                    </p>
                  </td>
                  <td className="py-2.5 px-3 text-center">
                    <span className="text-sm font-bold font-mono text-slate-600">{row.overall.toFixed(2)}</span>
                  </td>
                  <td className="py-2.5 px-3 text-center">
                    <span className={`text-sm font-bold font-mono ${scoreColor(row.applied)}`}>{row.applied.toFixed(2)}</span>
                  </td>
                  <td className="py-2.5 px-3 text-center">
                    <span className={`text-sm font-bold font-mono ${scoreColor(row.theoretical)}`}>{row.theoretical.toFixed(2)}</span>
                  </td>
                  <td className="py-2.5 px-3 text-center">
                    <span className={`text-sm font-bold font-mono ${scoreColor(row.balanced)}`}>{row.balanced.toFixed(2)}</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
