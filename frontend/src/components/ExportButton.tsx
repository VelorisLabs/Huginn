import { useState, useRef, useEffect } from 'react';
import { Download, FileSpreadsheet, FileJson, FileText, Loader2 } from 'lucide-react';
import { exportAPI } from '@/lib/api';
import { downloadBlob } from '@/lib/exportUtils';

type ExportFormat = 'csv' | 'json' | 'excel';

const FORMAT_OPTIONS: { format: ExportFormat; label: string; icon: React.ElementType; ext: string }[] = [
    { format: 'csv', label: 'CSV', icon: FileText, ext: '.csv' },
    { format: 'json', label: 'JSON', icon: FileJson, ext: '.json' },
    { format: 'excel', label: 'Excel', icon: FileSpreadsheet, ext: '.xlsx' },
];

export function ExportButton() {
    const [open, setOpen] = useState(false);
    const [loading, setLoading] = useState<ExportFormat | null>(null);
    const ref = useRef<HTMLDivElement>(null);

    // Close on outside click
    useEffect(() => {
        if (!open) return;
        const handler = (e: MouseEvent) => {
            if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
        };
        document.addEventListener('mousedown', handler);
        return () => document.removeEventListener('mousedown', handler);
    }, [open]);

    const handleExport = async (format: ExportFormat) => {
        setLoading(format);
        try {
            const res = await exportAPI.exportPapers({ format, include_scenarios: true });
            const ext = FORMAT_OPTIONS.find(f => f.format === format)!.ext;
            downloadBlob(res.data, `papers${ext}`);
            setOpen(false);
        } catch {
            alert('导出失败，请稍后重试');
        } finally {
            setLoading(null);
        }
    };

    return (
        <div ref={ref} className="relative">
            <button
                onClick={() => setOpen(!open)}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium text-slate-600 bg-white border border-slate-200 rounded-lg hover:bg-slate-50 hover:border-slate-300 transition-all"
            >
                <Download className="w-4 h-4" />
                导出
            </button>

            {open && (
                <div className="absolute right-0 top-full mt-1.5 w-40 bg-white border border-slate-200 rounded-xl shadow-lg z-30 overflow-hidden animate-in fade-in slide-in-from-top-1 duration-150">
                    {FORMAT_OPTIONS.map(({ format, label, icon: Icon }) => (
                        <button
                            key={format}
                            onClick={() => handleExport(format)}
                            disabled={loading !== null}
                            className="w-full flex items-center gap-2.5 px-3.5 py-2.5 text-sm text-slate-700 hover:bg-slate-50 transition-colors disabled:opacity-50"
                        >
                            {loading === format ? (
                                <Loader2 className="w-4 h-4 animate-spin text-primary-500" />
                            ) : (
                                <Icon className="w-4 h-4 text-slate-400" />
                            )}
                            {label}
                        </button>
                    ))}
                </div>
            )}
        </div>
    );
}
