import { useDecision } from './DecisionContext';
import { Undo2 } from 'lucide-react';

export function DecisionToast() {
    const { lastDecision, undoLastDecision, isUndoVisible } = useDecision();

    if (!isUndoVisible || !lastDecision) return null;

    const actionText = {
        keep: '已加入阅读清单',
        archive: '已归档',
        reject: '已排除'
    }[lastDecision.type];

    return (
        <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-50 animate-in slide-in-from-bottom-4 fade-in duration-300">
            <div className="bg-slate-900 text-white px-4 py-3 rounded-lg shadow-xl flex items-center gap-4 min-w-[300px] justify-between">
                <div className="flex items-center gap-2">
                    <span className="text-sm font-medium">{actionText}</span>
                    {lastDecision.reason && (
                        <span className="text-xs text-slate-400 border-l border-slate-700 pl-2">
                            {lastDecision.reason}
                        </span>
                    )}
                </div>

                <button
                    onClick={undoLastDecision}
                    className="flex items-center gap-1.5 text-sm font-medium text-emerald-400 hover:text-emerald-300 transition-colors"
                >
                    <Undo2 className="w-4 h-4" />
                    撤销
                </button>
            </div>
        </div>
    );
}
