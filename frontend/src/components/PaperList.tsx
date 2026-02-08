
import { useQuery } from '@tanstack/react-query';
import { paperAPI, type Paper } from '@/lib/api';
import { Award, Layers, Users, Calendar, BookOpen, Tag, Search, ChevronLeft, ChevronRight, Check, Archive, XCircle, Undo2 } from 'lucide-react';
import { DecisionBar } from './decision/DecisionBar';
import { BulkActionBar } from './decision/BulkActionBar';
import { useDecision } from './decision/DecisionContext';
// @ts-ignore
import { List } from 'react-window';
import { memo, useState, useCallback, useEffect, useRef, useMemo } from 'react';

const PAGE_SIZE = 8;

interface PaperListProps {
  filterTheme?: string | null;
  filterYear?: number | null;
  filterIds?: number[];
  onPaperClick: (paper: Paper) => void;
  previewMode?: boolean;
  paginationMode?: boolean;
}

interface RowDataProps {
  papers: Paper[];
  onPaperClick: (paper: Paper) => void;
  selectedIds: number[];
  toggleSelection: (id: number) => void;
  selectionMode: boolean;
  focusedIndex: number | null;
  makeDecision: (id: number, type: 'keep' | 'archive' | 'reject') => void;
  clearDecision: (id: number) => void;
  decisions: Record<number, string>;
}

const DECISION_BADGE: Record<string, { icon: React.ElementType; label: string; cls: string }> = {
  keep:    { icon: Check,    label: '已收藏', cls: 'text-emerald-600 bg-emerald-50 border-emerald-200' },
  archive: { icon: Archive,  label: '已归档', cls: 'text-slate-500 bg-slate-50 border-slate-200' },
  reject:  { icon: XCircle,  label: '已排除', cls: 'text-red-400 bg-red-50/60 border-red-100' },
};

function getScoreColor(score: number) {
  if (score >= 8.5) return { bar: 'bg-emerald-500', text: 'text-emerald-600', bg: 'bg-emerald-50', badge: 'bg-emerald-50 text-emerald-700 border-emerald-100' };
  if (score >= 7.5) return { bar: 'bg-blue-500', text: 'text-blue-600', bg: 'bg-blue-50', badge: 'bg-blue-50 text-blue-700 border-blue-100' };
  if (score >= 6.5) return { bar: 'bg-amber-500', text: 'text-amber-600', bg: 'bg-amber-50', badge: 'bg-amber-50 text-amber-700 border-amber-100' };
  return { bar: 'bg-slate-400', text: 'text-slate-600', bg: 'bg-slate-50', badge: 'bg-slate-50 text-slate-600 border-slate-200' };
}

function extractFirstSentence(text: string): string {
  const cleaned = text.replace(/^\d+\.\s*/, '').trim();
  const match = cleaned.match(/^(.{20,120}?)[。，；,.;]/);
  return match ? match[1] : cleaned.slice(0, 100);
}

const Row = memo(({ index, style, papers, onPaperClick, selectedIds, toggleSelection, selectionMode, focusedIndex, makeDecision, clearDecision, decisions }: { index: number; style: React.CSSProperties } & RowDataProps) => {
  const paper = papers[index];
  const isSelected = selectedIds.includes(paper.id);
  const isFocused = focusedIndex === index;
  const score = paper.overall_score || 0;
  const sc = getScoreColor(score);
  const decisionType = decisions[paper.id];
  const decisionInfo = decisionType ? DECISION_BADGE[decisionType] : null;

  return (
    <div style={style} className="px-1 py-1.5">
      <div
        className={`
          group relative h-full rounded-xl transition-all duration-200 overflow-hidden
          flex items-stretch
          ${isSelected ? 'ring-2 ring-primary-200 bg-primary-50/40' :
            isFocused ? 'ring-2 ring-primary-200 shadow-card-hover bg-white z-10' :
              'bg-white hover:bg-slate-50/60 border border-slate-100 hover:border-slate-200 hover:shadow-sm'
          }
        `}
      >
        {/* Left accent bar */}
        <div className={`w-[3px] shrink-0 rounded-l-xl ${sc.bar}`} />

        {/* Checkbox column — only in selection mode */}
        {selectionMode && (
          <div className="flex items-center pl-2.5 shrink-0">
            <div
              className={`
                w-[18px] h-[18px] rounded-md border-[1.5px] cursor-pointer flex items-center justify-center transition-all
                ${isSelected ? 'bg-primary-600 border-primary-600' : 'border-slate-300 hover:border-primary-400 bg-white'}
              `}
              onClick={(e) => { e.stopPropagation(); toggleSelection(paper.id); }}
            >
              {isSelected && <svg className="w-3 h-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}><path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" /></svg>}
            </div>
          </div>
        )}

        {/* Main Content */}
        <div
          className="flex-1 min-w-0 cursor-pointer px-4 py-2.5"
          onClick={() => onPaperClick(paper)}
        >
          {/* Title Row */}
          <div className="flex items-start justify-between gap-4 mb-1">
            <h4 className={`text-[15px] font-semibold leading-snug line-clamp-1 transition-colors ${isSelected ? 'text-primary-800' : 'text-slate-700 group-hover:text-slate-900'}`}>
              {paper.title}
            </h4>
            <span className={`text-[15px] font-bold font-mono shrink-0 ${sc.text}`}>
              {score.toFixed(1)}
            </span>
          </div>

          {/* Meta Line: author · year · venue */}
          <div className="flex items-center gap-3 text-[13px] text-slate-500 mb-1.5">
            {paper.authors && (
              <span className="inline-flex items-center gap-1 truncate max-w-[280px]" title={paper.authors}>
                <Users className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                {paper.authors}
              </span>
            )}
            {paper.year && (
              <span className="inline-flex items-center gap-1 shrink-0">
                <Calendar className="w-3.5 h-3.5 text-slate-400" />
                {paper.year}
              </span>
            )}
            <span className="inline-flex items-center gap-1 truncate shrink-0">
              <BookOpen className="w-3.5 h-3.5 text-slate-400" />
              {paper.venue || 'arXiv'}
            </span>
            {score >= 8.5 && (
              <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-emerald-700 bg-emerald-50 px-1.5 py-0.5 rounded-md border border-emerald-100 shrink-0">
                <Award className="w-3 h-3" />
                高价值
              </span>
            )}
          </div>

          {/* Keywords + Theme Tags */}
          <div className="flex items-center gap-1.5 flex-wrap">
            {paper.keywords && paper.keywords.split(/[,，;；、]/).slice(0, 5).map((kw, i) => (
              <span key={i} className="inline-flex items-center gap-0.5 text-[11px] text-slate-500 bg-slate-50/80 px-2 py-0.5 rounded-md border border-slate-200">
                {i === 0 && <Tag className="w-2.5 h-2.5 text-slate-400" />}
                {kw.trim()}
              </span>
            ))}
            {paper.cluster_topic && (
              <span className="inline-flex items-center gap-0.5 text-[11px] font-medium text-primary-600 bg-primary-50 px-2 py-0.5 rounded-md border border-primary-100">
                <Layers className="w-2.5 h-2.5" />
                {paper.cluster_topic}
              </span>
            )}
          </div>
        </div>

        {/* Decision status or Action Bar */}
        {!isSelected && (
          <div className={`flex items-center pr-3 shrink-0 transition-opacity duration-200 ${decisionInfo ? 'opacity-100' : isFocused ? 'opacity-100' : 'opacity-0 group-hover:opacity-100'}`}>
            {decisionInfo ? (
              <button
                onClick={(e) => { e.stopPropagation(); clearDecision(paper.id); }}
                title="点击撤销决策"
                className={`group/badge inline-flex items-center gap-1 text-[11px] font-medium px-2 py-1 rounded-lg border cursor-pointer hover:opacity-80 transition-all ${decisionInfo.cls}`}
              >
                <decisionInfo.icon className="w-3 h-3 group-hover/badge:hidden" />
                <Undo2 className="w-3 h-3 hidden group-hover/badge:block" />
                <span className="group-hover/badge:hidden">{decisionInfo.label}</span>
                <span className="hidden group-hover/badge:inline">撤销</span>
              </button>
            ) : (
              <DecisionBar paperId={paper.id} compact />
            )}
          </div>
        )}
      </div>
    </div>
  );
});

export function PaperList({ filterTheme, filterYear, filterIds, onPaperClick, previewMode = false, paginationMode = false }: PaperListProps) {
  const [selectedIds, setSelectedIds] = useState<number[]>([]);
  const [focusedIndex, setFocusedIndex] = useState<number | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const listRef = useRef<any>(null);
  const [containerSize, setContainerSize] = useState<{ width: number; height: number }>({ width: 0, height: 0 });
  const roRef = useRef<ResizeObserver | null>(null);
  const containerRef = useCallback((el: HTMLDivElement | null) => {
    if (roRef.current) {
      roRef.current.disconnect();
      roRef.current = null;
    }
    if (el) {
      setContainerSize({ width: el.clientWidth, height: el.clientHeight });
      const ro = new ResizeObserver(() => {
        setContainerSize({ width: el.clientWidth, height: el.clientHeight });
      });
      ro.observe(el);
      roRef.current = ro;
    }
  }, []);
  const { makeDecision, clearDecision, decisions } = useDecision();

  const { data: response, isLoading } = useQuery({
    queryKey: ['papers', filterTheme, filterYear],
    queryFn: () => paperAPI.list({ limit: 500 }),
  });

  let papers: Paper[] = response?.data || [];

  if (filterYear) {
    papers = papers.filter(p => p.year === filterYear);
  }

  if (filterIds) {
    papers = papers.filter(p => filterIds.includes(p.id));
  }

  // Search filtering
  const displayPapers = useMemo(() => {
    if (!searchQuery.trim()) return papers;
    const q = searchQuery.trim().toLowerCase();
    return papers.filter(p =>
      p.title.toLowerCase().includes(q) ||
      (p.authors && p.authors.toLowerCase().includes(q)) ||
      (p.keywords && p.keywords.toLowerCase().includes(q)) ||
      (p.venue && p.venue.toLowerCase().includes(q)) ||
      (p.cluster_topic && p.cluster_topic.toLowerCase().includes(q))
    );
  }, [papers, searchQuery]);

  // Reset page when search changes
  useEffect(() => { setCurrentPage(1); }, [searchQuery]);

  // Pagination
  const totalPages = Math.max(1, Math.ceil(displayPapers.length / PAGE_SIZE));
  const safePage = Math.min(currentPage, totalPages);
  const pagedPapers = paginationMode
    ? displayPapers.slice((safePage - 1) * PAGE_SIZE, safePage * PAGE_SIZE)
    : displayPapers;

  const toggleSelection = useCallback((id: number) => {
    setSelectedIds(prev =>
      prev.includes(id) ? prev.filter(pId => pId !== id) : [...prev, id]
    );
  }, []);

  const clearSelection = useCallback(() => {
    setSelectedIds([]);
  }, []);

  // Keyboard Navigation Logic
  useEffect(() => {
    if (previewMode || displayPapers.length === 0) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      // Ignore if typing in input
      if ((e.target as HTMLElement).tagName === 'INPUT') return;

      switch (e.key) {
        case 'j': // Down
        case 'ArrowDown':
          setFocusedIndex(prev => {
            const next = prev === null ? 0 : Math.min(prev + 1, displayPapers.length - 1);
            listRef.current?.scrollToItem(next);
            return next;
          });
          break;
        case 'k': // Up
        case 'ArrowUp':
          setFocusedIndex(prev => {
            const next = prev === null ? displayPapers.length - 1 : Math.max(prev - 1, 0);
            listRef.current?.scrollToItem(next);
            return next;
          });
          break;
        case 's': // Keep (Save)
        case 'Enter':
          if (focusedIndex !== null) {
            makeDecision(displayPapers[focusedIndex].id, 'keep');
          }
          break;
        case 'x': // Reject
          if (focusedIndex !== null) {
            makeDecision(displayPapers[focusedIndex].id, 'reject');
          }
          break;
        case 'a': // Archive
          if (focusedIndex !== null) {
            makeDecision(displayPapers[focusedIndex].id, 'archive');
          }
          break;
        case ' ': // Space: Toggle Selection
          e.preventDefault(); // Prevent scroll
          if (focusedIndex !== null) {
            toggleSelection(displayPapers[focusedIndex].id);
          }
          break;
        case 'Escape':
          setFocusedIndex(null);
          clearSelection();
          break;
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [displayPapers, focusedIndex, makeDecision, toggleSelection, clearSelection, previewMode]);

  if (isLoading) {
    return (
      <div className="space-y-4 p-4">
        {[1, 2, 3].map(i => (
          <div key={i} className="h-28 bg-slate-100 rounded-xl animate-pulse" />
        ))}
      </div>
    );
  }

  if (papers.length === 0) {
    return (
      <div className="text-center py-12 text-slate-400 bg-slate-50/50 rounded-xl border border-dashed border-slate-200">
        <p>未找到符合条件的论文。</p>
      </div>
    );
  }

  // Preview Mode: Render simple list (Top 5)
  if (previewMode) {
    const previewPapers = papers.slice(0, 5);
    return (
      <div className="space-y-3">
        {previewPapers.map((paper, index) => (
          <Row
            key={paper.id}
            index={index}
            style={{}}
            papers={previewPapers}
            onPaperClick={onPaperClick}
            selectedIds={[]}
            toggleSelection={() => { }}
            selectionMode={false}
            focusedIndex={null}
            makeDecision={makeDecision}
            clearDecision={clearDecision}
            decisions={decisions}
          />
        ))}
      </div>
    );
  }

  // Shared Search Bar
  const searchBar = (
    <div className="px-4 pt-3 pb-2">
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => { setSearchQuery(e.target.value); setFocusedIndex(null); }}
          placeholder="搜索论文标题、作者、关键词..."
          className="w-full pl-9 pr-4 py-2.5 text-sm bg-slate-50 border border-slate-200 rounded-xl
            placeholder:text-slate-400 text-slate-700
            focus:outline-none focus:ring-2 focus:ring-primary-200 focus:border-primary-300 focus:bg-white
            transition-all duration-200"
        />
        {searchQuery && (
          <button
            onClick={() => setSearchQuery('')}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 transition-colors"
          >
            <span className="text-xs">✕</span>
          </button>
        )}
      </div>
      {searchQuery && (
        <p className="text-[11px] text-slate-400 mt-1.5 ml-1">
          找到 {displayPapers.length} 篇匹配的论文
        </p>
      )}
    </div>
  );

  // Pagination Mode
  if (paginationMode) {
    // Build visible page numbers (max 5 around current)
    const pageNumbers: (number | '...')[] = [];
    if (totalPages <= 5) {
      for (let i = 1; i <= totalPages; i++) pageNumbers.push(i);
    } else {
      pageNumbers.push(1);
      if (safePage > 3) pageNumbers.push('...');
      for (let i = Math.max(2, safePage - 1); i <= Math.min(totalPages - 1, safePage + 1); i++) pageNumbers.push(i);
      if (safePage < totalPages - 2) pageNumbers.push('...');
      pageNumbers.push(totalPages);
    }

    return (
      <div className="flex flex-col">
        {searchBar}

        {/* Paper Cards */}
        <div className="space-y-0" role="region" aria-label="Paper List">
          {pagedPapers.length === 0 ? (
            <div className="text-center py-12 text-slate-400">
              <Search className="w-8 h-8 mx-auto mb-2 text-slate-300" />
              <p className="text-sm">未找到匹配「{searchQuery}」的论文</p>
            </div>
          ) : (
            pagedPapers.map((paper, index) => (
              <Row
                key={paper.id}
                index={index}
                style={{}}
                papers={pagedPapers}
                onPaperClick={onPaperClick}
                selectedIds={selectedIds}
                toggleSelection={toggleSelection}
                selectionMode={selectedIds.length > 0}
                focusedIndex={focusedIndex}
                makeDecision={makeDecision}
                clearDecision={clearDecision}
                decisions={decisions}
              />
            ))
          )}
        </div>

        {/* Pagination Controls */}
        {displayPapers.length > PAGE_SIZE && (
          <div className="flex items-center justify-center gap-1.5 py-4 border-t border-slate-100 mt-1">
            <button
              onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
              disabled={safePage <= 1}
              className="inline-flex items-center gap-1 px-3 py-1.5 text-xs font-medium rounded-lg border border-slate-200 text-slate-500 hover:bg-slate-50 hover:text-slate-700 disabled:opacity-30 disabled:cursor-not-allowed transition-all"
            >
              <ChevronLeft className="w-3.5 h-3.5" />
              上一页
            </button>

            {pageNumbers.map((pn, i) =>
              pn === '...' ? (
                <span key={`e-${i}`} className="w-8 text-center text-xs text-slate-300">...</span>
              ) : (
                <button
                  key={pn}
                  onClick={() => setCurrentPage(pn)}
                  className={`w-8 h-8 rounded-lg text-xs font-semibold transition-all ${
                    pn === safePage
                      ? 'bg-primary-600 text-white shadow-sm'
                      : 'text-slate-500 hover:bg-slate-100 hover:text-slate-700'
                  }`}
                >
                  {pn}
                </button>
              )
            )}

            <button
              onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
              disabled={safePage >= totalPages}
              className="inline-flex items-center gap-1 px-3 py-1.5 text-xs font-medium rounded-lg border border-slate-200 text-slate-500 hover:bg-slate-50 hover:text-slate-700 disabled:opacity-30 disabled:cursor-not-allowed transition-all"
            >
              下一页
              <ChevronRight className="w-3.5 h-3.5" />
            </button>
          </div>
        )}

        <BulkActionBar
          selectedIds={selectedIds}
          onClearSelection={clearSelection}
        />
      </div>
    );
  }

  // Virtualized Mode (default)
  return (
    <div className="flex flex-col">
      {searchBar}

      {/* Paper List */}
      <div ref={containerRef} className="relative h-[calc(100vh-300px)] w-full min-h-[400px] outline-none" role="region" aria-label="Paper List">
        {displayPapers.length === 0 ? (
          <div className="text-center py-12 text-slate-400">
            <Search className="w-8 h-8 mx-auto mb-2 text-slate-300" />
            <p className="text-sm">未找到匹配「{searchQuery}」的论文</p>
          </div>
        ) : containerSize.height > 0 && containerSize.width > 0 && (
          // @ts-ignore - react-window v2 generic inference issue
          <List
            listRef={listRef}
            style={{ height: containerSize.height, width: containerSize.width }}
            rowCount={displayPapers.length}
            rowHeight={124}
            rowComponent={Row}
            rowProps={{
              papers: displayPapers,
              onPaperClick,
              selectedIds,
              toggleSelection,
              selectionMode: selectedIds.length > 0,
              focusedIndex,
              makeDecision,
              clearDecision,
              decisions
            }}
            className="scrollbar-hide"
          />
        )}

        <BulkActionBar
          selectedIds={selectedIds}
          onClearSelection={clearSelection}
        />
      </div>
    </div>
  );
}

