import { Check, Archive, X, Trash2 } from 'lucide-react';
import { useDecision } from './DecisionContext';

interface BulkActionBarProps {
    selectedIds: number[];
    onClearSelection: () => void;
}

export function BulkActionBar({ selectedIds, onClearSelection }: BulkActionBarProps) {
    const { makeDecision } = useDecision();

    if (selectedIds.length === 0) return null;

    const handleBulkAction = (type: 'keep' | 'archive' | 'reject') => {
        selectedIds.forEach(id => makeDecision(id, type));
        onClearSelection();
    };

    return (
        <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-40 animate-in slide-in-from-bottom-4 fade-in duration-300">
            <div className="bg-white/90 backdrop-blur-md border border-slate-200 shadow-xl rounded-2xl px-6 py-3 flex items-center gap-6">

                <div className="flex items-center gap-3 border-r border-slate-200 pr-6">
                    <div className="bg-slate-900 text-white text-xs font-bold rounded-full w-6 h-6 flex items-center justify-center">
                        {selectedIds.length}
                    </div>
                    <span className="text-sm font-medium text-slate-700">已选择</span>
                </div>

                <div className="flex items-center gap-2">
                    <button
                        onClick={() => handleBulkAction('keep')}
                        className="flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-medium text-emerald-700 bg-emerald-50 hover:bg-emerald-100 transition-colors"
                    >
                        <Check className="w-4 h-4" />
                        保留
                    </button>

                    <button
                        onClick={() => handleBulkAction('archive')}
                        className="flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-medium text-slate-700 bg-slate-50 hover:bg-slate-100 transition-colors"
                    >
                        <Archive className="w-4 h-4" />
                        归档
                    </button>

                    <button
                        onClick={() => handleBulkAction('reject')}
                        className="flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-medium text-red-700 bg-red-50 hover:bg-red-100 transition-colors"
                    >
                        <X className="w-4 h-4" />
                        排除
                    </button>
                </div>

                <div className="pl-4 border-l border-slate-200">
                    <button
                        onClick={onClearSelection}
                        className="text-sm text-slate-400 hover:text-slate-600"
                    >
                        取消
                    </button>
                </div>
            </div>
        </div>
    );
}
