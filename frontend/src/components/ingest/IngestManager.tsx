import { useState, useCallback, useEffect, useRef } from 'react';
import { useDropzone } from 'react-dropzone';
import { useMutation, useQueryClient, useQuery } from '@tanstack/react-query';
import { uploadAPI, themesAPI, type ThemeItem } from '@/lib/api';
import { Loader2, CheckCircle2, XCircle, AlertCircle, RefreshCw, FileText, Upload, FolderOpen } from 'lucide-react';

interface IngestItem {
    id: string; // Task ID or temp ID
    fileName: string;
    status: 'uploading' | 'pending' | 'processing' | 'completed' | 'failed';
    progress: number;
    message?: string;
    isLocal?: boolean; // True if just client-side upload state
}

export function IngestManager() {
    const queryClient = useQueryClient();
    const [items, setItems] = useState<IngestItem[]>([]);
    const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null);
    const [selectedThemeId, setSelectedThemeId] = useState<number | null>(null);

    const { data: themesRes, isLoading: themesLoading } = useQuery({
        queryKey: ['themes'],
        queryFn: () => themesAPI.list(),
    });
    const themes: ThemeItem[] = themesRes?.data || [];
    const selectedTheme = themes.find(t => t.id === selectedThemeId);

    // Poll active tasks for status updates
    useEffect(() => {
        const activeItems = items.filter(i => i.status === 'processing');
        if (activeItems.length === 0) {
            if (pollingRef.current) { clearInterval(pollingRef.current); pollingRef.current = null; }
            return;
        }
        pollingRef.current = setInterval(async () => {
            for (const item of activeItems) {
                try {
                    const res = await uploadAPI.getTaskStatus(item.id);
                    const task = res.data;
                    setItems(prev => prev.map(p =>
                        p.id === item.id
                            ? { ...p, status: task.status === 'completed' ? 'completed' : task.status === 'failed' ? 'failed' : p.status, progress: task.progress || p.progress, message: task.current_step || p.message }
                            : p
                    ));
                    if (task.status === 'completed') {
                        queryClient.invalidateQueries({ queryKey: ['papers'] });
                        queryClient.invalidateQueries({ queryKey: ['papers-analysis'] });
                    }
                } catch { /* ignore polling errors */ }
            }
        }, 3000);
        return () => { if (pollingRef.current) clearInterval(pollingRef.current); };
    }, [items, queryClient]);

    // Upload Mutation
    const uploadMutation = useMutation({
        mutationFn: async (file: File) => {
            if (!selectedThemeId) throw new Error('请先选择主题桶');
            const res = await uploadAPI.uploadPDFAsync(file, selectedThemeId);
            return res.data;
        },
        onSuccess: (data, file) => {
            const taskId = data.task_id;
            setItems(prev => prev.map(item =>
                item.fileName === file.name && item.status === 'uploading'
                    ? { ...item, id: taskId, status: 'processing', progress: 10, message: '正在分析中...' }
                    : item
            ));
        },
        onError: (_err, file) => {
            setItems(prev => prev.map(item =>
                item.fileName === file.name
                    ? { ...item, status: 'failed', message: '上传失败' }
                    : item
            ));
        },
    });

    const onDrop = useCallback((acceptedFiles: File[]) => {
        const newItems: IngestItem[] = acceptedFiles.map(file => ({
            id: `temp-${Date.now()}-${file.name}`,
            fileName: file.name,
            status: 'uploading',
            progress: 0,
        }));
        setItems(prev => [...newItems, ...prev]);
        acceptedFiles.forEach(file => uploadMutation.mutate(file));
    }, [uploadMutation]);

    const { getRootProps, getInputProps, isDragActive } = useDropzone({
        onDrop,
        accept: { 'application/pdf': ['.pdf'] },
        multiple: true,
        disabled: !selectedThemeId,
    });

    const allItems = items;
    const activeCount = allItems.filter(i => ['uploading', 'pending', 'processing'].includes(i.status)).length;
    const failedCount = allItems.filter(i => i.status === 'failed').length;

    return (
        <div className="max-w-3xl mx-auto space-y-6">
            {/* Theme Selector */}
            <div className="bg-white rounded-2xl border border-slate-100 shadow-card p-5">
                <label className="text-sm font-semibold text-slate-700 mb-3 flex items-center gap-2">
                    <FolderOpen className="w-4 h-4 text-primary-500" />
                    选择目标主题桶
                    <span className="text-[10px] font-normal text-red-400 ml-1">* 必选</span>
                </label>
                {themesLoading ? (
                    <div className="text-sm text-slate-400 py-2">加载主题列表...</div>
                ) : themes.length === 0 ? (
                    <div className="flex items-center gap-2 p-3 bg-amber-50 border border-amber-200 rounded-xl text-sm text-amber-700 mt-2">
                        <AlertCircle className="w-4 h-4 shrink-0" />
                        <span>尚未配置主题桶。请先在「主题管理」页面创建主题，论文需要归属到对应主题下才能正确评分。</span>
                    </div>
                ) : (
                    <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 mt-2">
                        {themes.map(theme => (
                            <button
                                key={theme.id}
                                onClick={() => setSelectedThemeId(theme.id === selectedThemeId ? null : theme.id)}
                                className={`text-left px-3 py-2.5 rounded-xl border-2 transition-all duration-200 ${
                                    theme.id === selectedThemeId
                                        ? 'border-primary-400 bg-primary-50 ring-2 ring-primary-100 shadow-sm'
                                        : 'border-slate-100 bg-slate-50/50 hover:border-slate-200 hover:bg-white'
                                }`}
                            >
                                <p className={`text-sm font-semibold truncate ${
                                    theme.id === selectedThemeId ? 'text-primary-700' : 'text-slate-700'
                                }`}>{theme.name}</p>
                                <p className="text-[11px] text-slate-400 mt-0.5">
                                    {theme.paper_count || 0} 篇论文
                                </p>
                            </button>
                        ))}
                    </div>
                )}
            </div>

            {/* Dropzone */}
            <div
                {...getRootProps()}
                className={`
                    relative overflow-hidden rounded-2xl border-2 border-dashed p-10 text-center
                    transition-all duration-300 group
                    ${!selectedThemeId
                        ? 'border-slate-200 bg-slate-50 cursor-not-allowed opacity-60'
                        : isDragActive
                            ? 'border-primary-500 bg-primary-50/60 scale-[1.01] shadow-glow cursor-pointer'
                            : 'border-slate-200 bg-white hover:border-primary-300 hover:bg-primary-50/20 shadow-card cursor-pointer'}
                `}
            >
                <input {...getInputProps()} />
                <div className="space-y-3">
                    <div className={`w-16 h-16 mx-auto rounded-2xl flex items-center justify-center transition-all duration-300 ${isDragActive ? 'bg-primary-100 scale-110' : 'bg-slate-100 group-hover:bg-primary-50'}`}>
                        <Upload className={`w-7 h-7 transition-colors ${isDragActive ? 'text-primary-600 animate-bounce' : 'text-slate-400 group-hover:text-primary-500'}`} />
                    </div>
                    <div>
                        <p className="text-base font-semibold text-slate-700">
                            {isDragActive ? '松开鼠标开始上传' : '拖拽 PDF 文件到此处'}
                        </p>
                        <p className="text-xs text-slate-400 mt-1">
                            {selectedThemeId
                                ? `上传到主题：${selectedTheme?.name || ''}，AI 将自动分析每篇论文`
                                : '请先在上方选择目标主题桶'}
                        </p>
                    </div>
                    {!isDragActive && (
                        <button type="button" className="btn-secondary text-sm mt-2">
                            <FileText className="w-4 h-4" />
                            选择文件
                        </button>
                    )}
                </div>
            </div>

            {/* Pipeline Status */}
            {(activeCount > 0 || failedCount > 0) && (
                <div className="flex items-center gap-4 px-4 py-3 bg-white rounded-xl border border-slate-100 shadow-soft">
                    {activeCount > 0 && (
                        <span className="text-sm text-primary-600 flex items-center gap-1.5 font-medium">
                            <Loader2 className="w-4 h-4 animate-spin" />
                            {activeCount} 处理中
                        </span>
                    )}
                    {failedCount > 0 && (
                        <span className="text-sm text-red-600 flex items-center gap-1.5 font-medium">
                            <AlertCircle className="w-4 h-4" />
                            {failedCount} 失败
                        </span>
                    )}
                </div>
            )}

            {/* Task List */}
            <div className="bg-white rounded-2xl shadow-card border border-slate-100 overflow-hidden">
                {allItems.length === 0 ? (
                    <div className="p-10 text-center">
                        <svg width="120" height="100" viewBox="0 0 120 100" fill="none" xmlns="http://www.w3.org/2000/svg" className="mx-auto mb-4 opacity-60">
                            <rect x="20" y="15" width="80" height="60" rx="6" fill="#f5f3ff" stroke="#ddd6fe" strokeWidth="1.5" />
                            <rect x="32" y="32" width="40" height="3" rx="1.5" fill="#c4b5fd" />
                            <rect x="32" y="40" width="28" height="3" rx="1.5" fill="#e2e8f0" />
                            <rect x="32" y="48" width="34" height="3" rx="1.5" fill="#e2e8f0" />
                            <circle cx="85" cy="65" r="14" fill="#ede9fe" stroke="#c4b5fd" strokeWidth="1.5" />
                            <path d="M85 58v14M78 65h14" stroke="#8b5cf6" strokeWidth="2" strokeLinecap="round" />
                        </svg>
                        <p className="text-sm font-medium text-slate-500">暂无处理任务</p>
                        <p className="text-xs text-slate-400 mt-1">上传 PDF 文件后，处理进度将在此显示</p>
                    </div>
                ) : (
                    <div className="divide-y divide-slate-50">
                        {allItems.map(item => (
                            <div key={item.id} className="p-4 flex items-center justify-between gap-4 hover:bg-slate-50/50 transition-colors">
                                <div className="flex items-center gap-3 min-w-0 flex-1">
                                    <div className={`w-9 h-9 rounded-xl flex items-center justify-center shrink-0 ${
                                        item.status === 'completed' ? 'bg-emerald-50' :
                                        item.status === 'failed' ? 'bg-red-50' :
                                        'bg-primary-50'
                                    }`}>
                                        {getStatusIcon(item.status)}
                                    </div>
                                    <div className="min-w-0">
                                        <p className="text-sm font-medium text-slate-800 truncate">{item.fileName}</p>
                                        <p className="text-[11px] text-slate-400 mt-0.5">
                                            {item.message || item.status}
                                            {item.progress > 0 && item.progress < 100 && ` · ${item.progress}%`}
                                        </p>
                                    </div>
                                </div>

                                {(item.status === 'processing' || item.status === 'uploading') && (
                                    <div className="w-28 h-1.5 bg-slate-100 rounded-full overflow-hidden shrink-0">
                                        <div
                                            className="h-full bg-gradient-to-r from-primary-400 to-primary-600 rounded-full transition-all duration-700 ease-out"
                                            style={{ width: `${Math.max(item.progress, 5)}%` }}
                                        />
                                    </div>
                                )}

                                {item.status === 'failed' && (
                                    <button className="flex items-center gap-1 text-xs font-medium text-primary-600 hover:text-primary-700 px-2 py-1 rounded-lg hover:bg-primary-50 transition-colors">
                                        <RefreshCw className="w-3 h-3" />
                                        重试
                                    </button>
                                )}

                                {item.status === 'completed' && (
                                    <span className="text-[11px] font-medium text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded-lg">
                                        完成
                                    </span>
                                )}
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}

function getStatusIcon(status: string) {
    switch (status) {
        case 'completed': return <CheckCircle2 className="w-5 h-5 text-emerald-500" />;
        case 'failed': return <XCircle className="w-5 h-5 text-red-500" />;
        case 'processing':
        case 'uploading': return <Loader2 className="w-5 h-5 text-primary-500 animate-spin" />;
        default: return <FileText className="w-5 h-5 text-slate-400" />;
    }
}
