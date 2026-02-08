import { useState, useCallback } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { themesAPI, type ThemeItem } from '@/lib/api';
import {
  ArrowLeft, Plus, Trash2, Pencil, X, Check, FileText, Download,
  Upload, AlertCircle, Tags, FolderOpen
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

interface ThemeManagerProps {
  workspaceId: number;
  onBack: () => void;
}

export function ThemeManager({ workspaceId, onBack }: ThemeManagerProps) {
  const queryClient = useQueryClient();
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editName, setEditName] = useState('');
  const [editTags, setEditTags] = useState('');
  const [showAddForm, setShowAddForm] = useState(false);
  const [newName, setNewName] = useState('');
  const [newTags, setNewTags] = useState('');
  const [showImport, setShowImport] = useState(false);
  const [importContent, setImportContent] = useState('');
  const [deleteConfirmId, setDeleteConfirmId] = useState<number | null>(null);

  // Fetch themes with workspace header
  const { data: themesData, isLoading } = useQuery({
    queryKey: ['themes', workspaceId],
    queryFn: async () => {
      const { api } = await import('@/lib/api');
      return api.get('/themes', { headers: { 'X-Workspace-Id': String(workspaceId) } });
    },
  });
  const themes: ThemeItem[] = themesData?.data || [];

  const invalidate = useCallback(() => {
    queryClient.invalidateQueries({ queryKey: ['themes', workspaceId] });
    queryClient.invalidateQueries({ queryKey: ['themes'] });
    queryClient.invalidateQueries({ queryKey: ['workspaces'] });
  }, [queryClient, workspaceId]);

  // Create
  const createMut = useMutation({
    mutationFn: (data: { name: string; tags?: string }) => themesAPI.create(data),
    onSuccess: () => {
      invalidate();
      setShowAddForm(false);
      setNewName('');
      setNewTags('');
    },
  });

  // Update
  const updateMut = useMutation({
    mutationFn: ({ id, data }: { id: number; data: { name?: string; tags?: string } }) =>
      themesAPI.update(id, data),
    onSuccess: () => {
      invalidate();
      setEditingId(null);
    },
  });

  // Delete
  const deleteMut = useMutation({
    mutationFn: (id: number) => themesAPI.delete(id),
    onSuccess: () => {
      invalidate();
      setDeleteConfirmId(null);
    },
  });

  // Import
  const importMut = useMutation({
    mutationFn: (content: string) => themesAPI.importConfig(content),
    onSuccess: () => {
      invalidate();
      setShowImport(false);
      setImportContent('');
    },
  });

  // Export
  const exportMut = useMutation({
    mutationFn: () => themesAPI.exportConfig(),
    onSuccess: (res) => {
      const content = res.data?.content || '';
      const blob = new Blob([content], { type: 'text/markdown' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'theme_buckets.md';
      a.click();
      URL.revokeObjectURL(url);
    },
  });

  const startEdit = useCallback((theme: ThemeItem) => {
    setEditingId(theme.id);
    setEditName(theme.name);
    setEditTags(theme.tags || '');
  }, []);

  const handleSaveEdit = useCallback(() => {
    if (!editingId || !editName.trim()) return;
    updateMut.mutate({
      id: editingId,
      data: { name: editName.trim(), tags: editTags.trim() || undefined },
    });
  }, [editingId, editName, editTags, updateMut]);

  const handleCreate = useCallback(() => {
    if (!newName.trim()) return;
    createMut.mutate({ name: newName.trim(), tags: newTags.trim() || undefined });
  }, [newName, newTags, createMut]);

  const tagList = (tags: string | undefined): string[] => {
    if (!tags) return [];
    return tags.split(',').map(t => t.trim()).filter(Boolean);
  };

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <button
            onClick={onBack}
            className="w-8 h-8 flex items-center justify-center rounded-lg hover:bg-slate-100 text-slate-500 hover:text-slate-700 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
          </button>
          <div>
            <h2 className="text-lg font-bold text-slate-800 flex items-center gap-2">
              <FolderOpen className="w-5 h-5 text-amber-500" />
              主题管理
            </h2>
            <p className="text-sm text-slate-500 mt-0.5">管理你的研究主题分类</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowImport(true)}
            className="px-3 py-1.5 text-xs font-medium text-amber-700 bg-amber-50 hover:bg-amber-100 border border-amber-200 rounded-lg transition-colors flex items-center gap-1.5"
          >
            <Upload className="w-3.5 h-3.5" />
            导入配置
          </button>
          <button
            onClick={() => exportMut.mutate()}
            disabled={exportMut.isPending || themes.length === 0}
            className="px-3 py-1.5 text-xs font-medium text-emerald-700 bg-emerald-50 hover:bg-emerald-100 border border-emerald-200 rounded-lg transition-colors flex items-center gap-1.5 disabled:opacity-50"
          >
            <Download className="w-3.5 h-3.5" />
            导出配置
          </button>
          <button
            onClick={() => setShowAddForm(true)}
            className="px-3 py-1.5 text-xs font-medium text-white bg-indigo-600 hover:bg-indigo-700 rounded-lg transition-colors flex items-center gap-1.5 shadow-sm"
          >
            <Plus className="w-3.5 h-3.5" />
            添加主题
          </button>
        </div>
      </div>

      {/* Add Theme Form */}
      <AnimatePresence>
        {showAddForm && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="overflow-hidden"
          >
            <div className="bg-white rounded-2xl border border-indigo-100 shadow-card p-5 space-y-4">
              <h3 className="text-sm font-semibold text-slate-700 flex items-center gap-2">
                <Plus className="w-4 h-4 text-indigo-500" />
                添加新主题
              </h3>
              <div className="space-y-3">
                <div>
                  <label className="text-xs font-medium text-slate-500 mb-1 block">主题名称 *</label>
                  <input
                    value={newName}
                    onChange={e => setNewName(e.target.value)}
                    placeholder="例：教育数字化转型"
                    className="w-full px-3 py-2 rounded-xl border border-slate-200 text-sm focus:ring-2 focus:ring-indigo-200 focus:border-indigo-400 outline-none transition-all"
                    onKeyDown={e => e.key === 'Enter' && handleCreate()}
                  />
                </div>
                <div>
                  <label className="text-xs font-medium text-slate-500 mb-1 block">标签（逗号分隔）</label>
                  <input
                    value={newTags}
                    onChange={e => setNewTags(e.target.value)}
                    placeholder="例：数字化转型,智慧教育,教育信息化"
                    className="w-full px-3 py-2 rounded-xl border border-slate-200 text-sm focus:ring-2 focus:ring-indigo-200 focus:border-indigo-400 outline-none transition-all"
                    onKeyDown={e => e.key === 'Enter' && handleCreate()}
                  />
                </div>
              </div>
              <div className="flex items-center gap-2 justify-end">
                <button
                  onClick={() => { setShowAddForm(false); setNewName(''); setNewTags(''); }}
                  className="px-3 py-1.5 text-sm text-slate-500 hover:text-slate-700 rounded-lg hover:bg-slate-50 transition-colors"
                >
                  取消
                </button>
                <button
                  onClick={handleCreate}
                  disabled={!newName.trim() || createMut.isPending}
                  className="px-4 py-1.5 text-sm font-medium bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-1.5"
                >
                  {createMut.isPending ? (
                    <span className="w-3 h-3 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  ) : (
                    <Plus className="w-3.5 h-3.5" />
                  )}
                  创建
                </button>
              </div>
              {createMut.isError && (
                <div className="flex items-center gap-2 text-sm text-red-600 bg-red-50 px-3 py-2 rounded-lg">
                  <AlertCircle className="w-4 h-4 shrink-0" />
                  {(createMut.error as any)?.response?.data?.detail || '创建失败'}
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Theme Cards Grid */}
      {isLoading ? (
        <div className="text-center py-12 text-slate-400">加载中...</div>
      ) : themes.length === 0 ? (
        <div className="text-center py-16 space-y-3">
          <Tags className="w-10 h-10 text-slate-300 mx-auto" />
          <p className="text-sm text-slate-400">暂无主题桶</p>
          <p className="text-xs text-slate-400">点击「添加主题」或「导入配置」开始</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {themes.map(theme => {
            const isEditing = editingId === theme.id;
            const isDeleting = deleteConfirmId === theme.id;
            const tags = tagList(theme.tags);

            return (
              <motion.div
                key={theme.id}
                layout
                className={`bg-white rounded-2xl border p-5 transition-all duration-200 ${
                  isEditing
                    ? 'border-indigo-300 ring-2 ring-indigo-100 shadow-lg'
                    : 'border-slate-150 shadow-card hover:shadow-md hover:border-slate-200'
                }`}
              >
                {isEditing ? (
                  /* ── Edit Mode ── */
                  <div className="space-y-3">
                    <div>
                      <label className="text-xs font-medium text-slate-500 mb-1 block">主题名称</label>
                      <input
                        value={editName}
                        onChange={e => setEditName(e.target.value)}
                        className="w-full px-3 py-2 rounded-xl border border-indigo-200 text-sm font-semibold focus:ring-2 focus:ring-indigo-200 focus:border-indigo-400 outline-none transition-all"
                        autoFocus
                        onKeyDown={e => {
                          if (e.key === 'Enter') handleSaveEdit();
                          if (e.key === 'Escape') setEditingId(null);
                        }}
                      />
                    </div>
                    <div>
                      <label className="text-xs font-medium text-slate-500 mb-1 block">标签（逗号分隔）</label>
                      <input
                        value={editTags}
                        onChange={e => setEditTags(e.target.value)}
                        className="w-full px-3 py-2 rounded-xl border border-slate-200 text-sm focus:ring-2 focus:ring-indigo-200 focus:border-indigo-400 outline-none transition-all"
                        placeholder="标签1,标签2,标签3"
                        onKeyDown={e => {
                          if (e.key === 'Enter') handleSaveEdit();
                          if (e.key === 'Escape') setEditingId(null);
                        }}
                      />
                    </div>
                    <div className="flex items-center gap-2 justify-end pt-1">
                      <button
                        onClick={() => setEditingId(null)}
                        className="px-3 py-1.5 text-xs text-slate-500 hover:text-slate-700 rounded-lg hover:bg-slate-50 transition-colors flex items-center gap-1"
                      >
                        <X className="w-3 h-3" />
                        取消
                      </button>
                      <button
                        onClick={handleSaveEdit}
                        disabled={!editName.trim() || updateMut.isPending}
                        className="px-3 py-1.5 text-xs font-medium text-white bg-indigo-600 hover:bg-indigo-700 rounded-lg disabled:opacity-50 transition-colors flex items-center gap-1"
                      >
                        {updateMut.isPending ? (
                          <span className="w-3 h-3 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                        ) : (
                          <Check className="w-3 h-3" />
                        )}
                        保存
                      </button>
                    </div>
                    {updateMut.isError && (
                      <div className="flex items-center gap-2 text-xs text-red-600 bg-red-50 px-3 py-2 rounded-lg">
                        <AlertCircle className="w-3.5 h-3.5 shrink-0" />
                        {(updateMut.error as any)?.response?.data?.detail || '保存失败'}
                      </div>
                    )}
                  </div>
                ) : (
                  /* ── View Mode ── */
                  <div>
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex-1 min-w-0">
                        <h3 className="text-sm font-bold text-slate-800 leading-tight">{theme.name}</h3>
                        <p className="text-xs text-slate-400 mt-1">{theme.paper_count || 0} 篇论文</p>
                      </div>
                      <div className="flex items-center gap-1 ml-2 shrink-0">
                        <button
                          onClick={() => startEdit(theme)}
                          className="w-7 h-7 flex items-center justify-center rounded-lg text-amber-500 hover:text-amber-600 hover:bg-amber-50 transition-colors"
                          title="编辑主题"
                        >
                          <Pencil className="w-3.5 h-3.5" />
                        </button>
                        <button
                          onClick={() => setDeleteConfirmId(theme.id)}
                          className="w-7 h-7 flex items-center justify-center rounded-lg text-red-400 hover:text-red-500 hover:bg-red-50 transition-colors"
                          title="删除主题"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </div>

                    {/* Tags */}
                    {tags.length > 0 && (
                      <div className="flex flex-wrap gap-1.5 mt-3">
                        {tags.map((tag, i) => (
                          <span
                            key={i}
                            className="px-2 py-0.5 text-[11px] font-medium text-indigo-600 bg-indigo-50 rounded-md border border-indigo-100"
                          >
                            {tag}
                          </span>
                        ))}
                      </div>
                    )}

                    {/* Delete Confirmation */}
                    <AnimatePresence>
                      {isDeleting && (
                        <motion.div
                          initial={{ opacity: 0, height: 0 }}
                          animate={{ opacity: 1, height: 'auto' }}
                          exit={{ opacity: 0, height: 0 }}
                          className="overflow-hidden"
                        >
                          <div className="mt-3 flex items-center gap-2 bg-red-50 px-3 py-2 rounded-lg border border-red-100">
                            <AlertCircle className="w-3.5 h-3.5 text-red-500 shrink-0" />
                            <span className="text-xs text-red-600 flex-1">
                              {(theme.paper_count || 0) > 0
                                ? `该主题下有 ${theme.paper_count} 篇论文，无法删除`
                                : '确定删除此主题？此操作不可恢复'}
                            </span>
                            {(theme.paper_count || 0) === 0 && (
                              <button
                                onClick={() => deleteMut.mutate(theme.id)}
                                disabled={deleteMut.isPending}
                                className="px-2 py-1 text-[11px] font-medium text-white bg-red-500 hover:bg-red-600 rounded-md disabled:opacity-50 transition-colors"
                              >
                                {deleteMut.isPending ? '删除中...' : '确定删除'}
                              </button>
                            )}
                            <button
                              onClick={() => setDeleteConfirmId(null)}
                              className="px-2 py-1 text-[11px] text-slate-500 hover:text-slate-700 rounded-md hover:bg-white transition-colors"
                            >
                              取消
                            </button>
                          </div>
                          {deleteMut.isError && (
                            <div className="mt-2 text-xs text-red-500">
                              {(deleteMut.error as any)?.response?.data?.detail || '删除失败'}
                            </div>
                          )}
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </div>
                )}
              </motion.div>
            );
          })}
        </div>
      )}

      {/* Import Modal */}
      <AnimatePresence>
        {showImport && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 bg-black/30 flex items-center justify-center p-4"
            onClick={() => setShowImport(false)}
          >
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              className="bg-white rounded-2xl shadow-xl w-full max-w-lg p-6 space-y-4"
              onClick={e => e.stopPropagation()}
            >
              <h3 className="text-base font-semibold text-slate-800 flex items-center gap-2">
                <Upload className="w-4 h-4 text-amber-500" />
                导入主题桶配置
              </h3>
              <p className="text-xs text-slate-500">
                粘贴 theme_buckets.md 格式的内容。无论文关联的旧主题将被替换。
              </p>
              <textarea
                value={importContent}
                onChange={e => setImportContent(e.target.value)}
                placeholder={"## 主题名称\n- 标签1\n- 标签2\n\n## 另一个主题\n- ..."}
                rows={12}
                className="w-full px-3 py-2 rounded-xl border border-slate-200 text-sm font-mono focus:ring-2 focus:ring-indigo-200 focus:border-indigo-400 outline-none resize-none"
              />
              <div className="flex justify-end gap-2">
                <button
                  onClick={() => { setShowImport(false); setImportContent(''); }}
                  className="px-3 py-1.5 text-sm text-slate-500 hover:text-slate-700 rounded-lg hover:bg-slate-50 transition-colors"
                >
                  取消
                </button>
                <button
                  onClick={() => importMut.mutate(importContent)}
                  disabled={!importContent.trim() || importMut.isPending}
                  className="px-4 py-1.5 text-sm font-medium bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 transition-colors flex items-center gap-1.5"
                >
                  {importMut.isPending ? (
                    <span className="w-3 h-3 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  ) : (
                    <Upload className="w-3.5 h-3.5" />
                  )}
                  导入
                </button>
              </div>
              {importMut.isError && (
                <div className="flex items-center gap-2 text-sm text-red-600 bg-red-50 px-3 py-2 rounded-lg">
                  <AlertCircle className="w-4 h-4 shrink-0" />
                  {(importMut.error as any)?.response?.data?.detail || '导入失败'}
                </div>
              )}
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Export Error */}
      {exportMut.isError && (
        <div className="flex items-center gap-2 text-sm text-red-600 bg-red-50 px-3 py-2 rounded-lg">
          <AlertCircle className="w-4 h-4 shrink-0" />
          {(exportMut.error as any)?.response?.data?.detail || '导出失败'}
        </div>
      )}
    </div>
  );
}
