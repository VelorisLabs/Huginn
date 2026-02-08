import { createContext, useContext, useState, useEffect, useCallback, type ReactNode } from 'react';

type DecisionType = 'keep' | 'archive' | 'reject';

interface Decision {
    paperId: number;
    type: DecisionType;
    reason?: string;
    timestamp: number;
}

interface DecisionContextType {
    lastDecision: Decision | null;
    makeDecision: (paperId: number, type: DecisionType, reason?: string) => void;
    undoLastDecision: () => void;
    clearDecision: (paperId: number) => void;
    isUndoVisible: boolean;
    decisions: Record<number, DecisionType>;
}

const DecisionContext = createContext<DecisionContextType | undefined>(undefined);

export function DecisionProvider({ children }: { children: ReactNode }) {
    const [decisions, setDecisions] = useState<Record<number, DecisionType>>({});
    const [lastDecision, setLastDecision] = useState<Decision | null>(null);
    const [isUndoVisible, setIsUndoVisible] = useState(false);
    const [undoTimer, setUndoTimer] = useState<ReturnType<typeof setTimeout> | null>(null);

    // Load from localStorage on mount
    useEffect(() => {
        const stored = localStorage.getItem('paper_decisions');
        if (stored) {
            try {
                setDecisions(JSON.parse(stored));
            } catch (e) {
                console.error("Failed to parse paper_decisions", e);
            }
        }
    }, []);

    const makeDecision = useCallback(async (paperId: number, type: DecisionType, reason?: string) => {
        // 1. Optimistic UI update
        console.log(`Decision made for ${paperId}: ${type} (${reason})`);

        // Update local state and storage
        setDecisions(prev => {
            const next = { ...prev, [paperId]: type };
            localStorage.setItem('paper_decisions', JSON.stringify(next));
            return next;
        });

        // Clear previous timer
        if (undoTimer) clearTimeout(undoTimer);

        const decision: Decision = { paperId, type, reason, timestamp: Date.now() };
        setLastDecision(decision);
        setIsUndoVisible(true);

        // Auto-dismiss undo after 10 seconds
        const timer = setTimeout(() => {
            setIsUndoVisible(false);
            setLastDecision(null);
        }, 10000);
        setUndoTimer(timer);
    }, [undoTimer]);

    const undoLastDecision = useCallback(async () => {
        if (!lastDecision) return;

        console.log(`Undoing decision for ${lastDecision.paperId}`);

        // Revert local state
        setDecisions(prev => {
            const next = { ...prev };
            delete next[lastDecision.paperId];
            localStorage.setItem('paper_decisions', JSON.stringify(next));
            return next;
        });

        // Reset state
        setIsUndoVisible(false);
        setLastDecision(null);
        if (undoTimer) clearTimeout(undoTimer);
    }, [lastDecision, undoTimer]);

    const clearDecision = useCallback((paperId: number) => {
        setDecisions(prev => {
            const next = { ...prev };
            delete next[paperId];
            localStorage.setItem('paper_decisions', JSON.stringify(next));
            return next;
        });
    }, []);

    return (
        <DecisionContext.Provider value={{ lastDecision, makeDecision, undoLastDecision, clearDecision, isUndoVisible, decisions }}>
            {children}
        </DecisionContext.Provider>
    );
}

export function useDecision() {
    const context = useContext(DecisionContext);
    if (context === undefined) {
        throw new Error('useDecision must be used within a DecisionProvider');
    }
    return context;
}
