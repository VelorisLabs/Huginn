
import React, { useMemo } from 'react';
import { useDecision } from './decision/DecisionContext';
import { PaperList } from './PaperList';
import { BookOpen } from 'lucide-react';
import type { Paper } from '@/lib/api';

interface ReadingListProps {
    onPaperClick: (paper: Paper) => void;
}

function EmptyReadingIllustration() {
    return (
        <svg width="160" height="140" viewBox="0 0 160 140" fill="none" xmlns="http://www.w3.org/2000/svg" className="mx-auto mb-4">
            <rect x="30" y="30" width="100" height="80" rx="8" fill="#f5f3ff" stroke="#ddd6fe" strokeWidth="1.5" />
            <rect x="42" y="48" width="50" height="4" rx="2" fill="#c4b5fd" />
            <rect x="42" y="58" width="36" height="3" rx="1.5" fill="#e2e8f0" />
            <rect x="42" y="66" width="44" height="3" rx="1.5" fill="#e2e8f0" />
            <rect x="42" y="74" width="28" height="3" rx="1.5" fill="#e2e8f0" />
            <circle cx="120" cy="42" r="16" fill="#ede9fe" stroke="#c4b5fd" strokeWidth="1.5" />
            <path d="M114 42l4 4 8-8" stroke="#8b5cf6" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
            <rect x="42" y="86" width="20" height="6" rx="3" fill="#8b5cf6" opacity="0.2" />
            <rect x="66" y="86" width="20" height="6" rx="3" fill="#8b5cf6" opacity="0.1" />
        </svg>
    );
}

export function ReadingList({ onPaperClick }: ReadingListProps) {
    const { decisions } = useDecision();

    const keptIds = useMemo(() => {
        return Object.entries(decisions)
            .filter(([_, type]) => type === 'keep')
            .map(([id]) => parseInt(id, 10));
    }, [decisions]);

    if (keptIds.length === 0) {
        return (
            <div className="bg-white rounded-2xl border border-slate-100 shadow-card p-12 text-center max-w-lg mx-auto">
                <EmptyReadingIllustration />
                <h3 className="text-lg font-semibold text-slate-800 mb-2">阅读清单为空</h3>
                <p className="text-sm text-slate-500 leading-relaxed mb-6">
                    在仪表盘中点击论文卡片的「保留阅读」按钮，<br />或按键盘 <kbd className="px-1.5 py-0.5 bg-slate-100 border border-slate-200 rounded text-xs font-mono">S</kbd> 键即可添加到这里。
                </p>
                <div className="flex items-center justify-center gap-2 text-xs text-slate-400">
                    <BookOpen className="w-3.5 h-3.5" />
                    <span>系统化管理你的阅读计划</span>
                </div>
            </div>
        );
    }

    return (
        <div className="bg-white rounded-2xl border border-slate-100 shadow-card overflow-hidden">
            <div className="flex items-center justify-between px-6 py-5 border-b border-slate-100">
                <div>
                    <h3 className="text-base font-semibold text-slate-800">阅读清单</h3>
                    <p className="text-xs text-slate-400 mt-0.5">{keptIds.length} 篇论文待阅读</p>
                </div>
            </div>
            <div className="p-2">
                <PaperList
                    filterIds={keptIds}
                    onPaperClick={onPaperClick}
                />
            </div>
        </div>
    );
}
