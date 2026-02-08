import { useState } from 'react';
import { Check, Archive, X } from 'lucide-react';
import { useDecision } from './DecisionContext';

interface DecisionBarProps {
    paperId: number;
    className?: string;
    compact?: boolean; // For list view vs detail view
}

export function DecisionBar({ paperId, className = '', compact = false }: DecisionBarProps) {
    const { makeDecision } = useDecision();
    const [showReasons, setShowReasons] = useState(false);

    const buttonBase = "flex items-center gap-1.5 transition-all duration-200 rounded-lg font-medium";
    const compactClasses = "p-1.5";
    const normalClasses = "px-4 py-2";

    const handleRejectClick = () => {
        // Show reason chips before committing
        setShowReasons(true);
    };

    const handleReasonSelect = (reason: string) => {
        makeDecision(paperId, 'reject', reason);
        setShowReasons(false);
    };

    if (showReasons) {
        return (
            <div className={`flex items-center gap-2 animate-in fade-in slide-in-from-right-4 ${className}`}>
                <span className="text-xs text-slate-500 font-medium mr-1">原因？</span>
                {['方法缺陷', '不相关', '过时', '重复'].map(reason => (
                    <button
                        key={reason}
                        onClick={() => handleReasonSelect(reason)}
                        className="px-2 py-1 text-xs bg-red-50 text-red-600 rounded-md hover:bg-red-100 hover:text-red-700 transition-colors border border-red-100"
                    >
                        {reason}
                    </button>
                ))}
                <button
                    onClick={() => setShowReasons(false)}
                    className="p-1 hover:bg-slate-100 rounded-full text-slate-400"
                >
                    <X className="w-3 h-3" />
                </button>
            </div>
        );
    }

    return (
        <div className={`flex items-center gap-2 ${className}`}>
            {/* Keep Action */}
            <button
                onClick={() => makeDecision(paperId, 'keep')}
                className={`
          ${buttonBase} ${compact ? compactClasses : normalClasses}
          text-emerald-600 bg-emerald-50 hover:bg-emerald-100 border border-emerald-100 hover:border-emerald-200
        `}
                title="保留阅读"
            >
                <Check className={compact ? "w-4 h-4" : "w-4 h-4"} />
                {!compact && <span>保留</span>}
            </button>

            {/* Archive Action */}
            <button
                onClick={() => makeDecision(paperId, 'archive')}
                className={`
          ${buttonBase} ${compact ? compactClasses : normalClasses}
          text-slate-500 bg-slate-50 hover:bg-slate-100 border border-slate-200 hover:border-slate-300
        `}
                title="稍后归档"
            >
                <Archive className={compact ? "w-4 h-4" : "w-4 h-4"} />
                {!compact && <span>归档</span>}
            </button>

            {/* Reject Action */}
            <button
                onClick={handleRejectClick}
                className={`
          ${buttonBase} ${compact ? compactClasses : normalClasses}
          text-slate-400 hover:text-red-500 hover:bg-red-50 border border-transparent hover:border-red-100
        `}
                title="排除"
            >
                <X className={compact ? "w-4 h-4" : "w-4 h-4"} />
                {!compact && <span>排除</span>}
            </button>
        </div>
    );
}
