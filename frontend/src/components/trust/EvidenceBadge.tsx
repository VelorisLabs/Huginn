
import React from 'react';
import clsx from 'clsx';
import { ShieldCheck, Sparkles } from 'lucide-react';

interface EvidenceBadgeProps {
    type: 'extracted' | 'inferred';
    className?: string;
}

export function EvidenceBadge({ type, className }: EvidenceBadgeProps) {
    const isExtracted = type === 'extracted';

    return (
        <div
            className={clsx(
                "inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium border transition-colors cursor-help",
                isExtracted
                    ? "bg-emerald-50 text-emerald-700 border-emerald-200 hover:bg-emerald-100"
                    : "bg-amber-50 text-amber-700 border-amber-200 hover:bg-amber-100",
                className
            )}
            title={isExtracted
                ? "直接引用：从论文原文中提取的内容"
                : "AI 摘要：基于上下文由 AI 生成的分析总结"}
        >
            {isExtracted ? (
                <ShieldCheck className="w-3 h-3" />
            ) : (
                <Sparkles className="w-3 h-3" />
            )}
            <span>{isExtracted ? '原文引用' : 'AI 摘要'}</span>
        </div>
    );
}
