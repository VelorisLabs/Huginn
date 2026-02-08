import { useState, useCallback } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { workspaceAPI, themesAPI, type WorkspaceItem, type ThemeItem } from '@/lib/api';
import { useWorkspace } from './WorkspaceContext';
import { ThemeManager } from './ThemeManager';
import {
  Plus, Trash2, Save, FolderKanban, ChevronRight, ChevronDown,
  AlertCircle, Check, X, FileText, Tags, Settings2, Weight, Sparkles, Pencil
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

export function WorkspaceManager() {
  const queryClient = useQueryClient();
  const { activeWorkspace, switchWorkspace, refetchWorkspaces } = useWorkspace();
  const [expandedId, setExpandedId] = useState<number | null>(null);
  const [createMode, setCreateMode] = useState(false);
  const [newName, setNewName] = useState('');
  const [newDesc, setNewDesc] = useState('');
  const [editWeights, setEditWeights] = useState<Record<number, any>>({});
  const [themeImportWsId, setThemeImportWsId] = useState<number | null>(null);
  const [themeImportContent, setThemeImportContent] = useState('');
  const [themeManagerWsId, setThemeManagerWsId] = useState<number | null>(null);

  const { data: wsListData, isLoading } = useQuery({
    queryKey: ['workspaces'],
    queryFn: () => workspaceAPI.list(),
  });
  const workspaces: WorkspaceItem[] = wsListData?.data || [];

  // Create workspace
  const createMut = useMutation({
    mutationFn: (data: { name: string; description?: string }) => workspaceAPI.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['workspaces'] });
      refetchWorkspaces();
      setCreateMode(false);
      setNewName('');
      setNewDesc('');
    },
  });

  // Delete workspace
  const deleteMut = useMutation({
    mutationFn: (id: number) => workspaceAPI.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['workspaces'] });
      refetchWorkspaces();
    },
  });

  // Update workspace
  const updateMut = useMutation({
    mutationFn: ({ id, data }: { id: number; data: any }) => workspaceAPI.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['workspaces'] });
      refetchWorkspaces();
    },
  });

  // Import themes
  const importThemesMut = useMutation({
    mutationFn: (content: string) => themesAPI.importConfig(content),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['themes'] });
      queryClient.invalidateQueries({ queryKey: ['workspaces'] });
      refetchWorkspaces();
      setThemeImportWsId(null);
      setThemeImportContent('');
    },
  });

  const handleCreate = useCallback(() => {
    if (!newName.trim()) return;
    createMut.mutate({ name: newName.trim(), description: newDesc.trim() || undefined });
  }, [newName, newDesc, createMut]);

  const handleSaveWeights = useCallback((wsId: number) => {
    const weights = editWeights[wsId];
    if (!weights) return;
    updateMut.mutate({ id: wsId, data: { scenario_weights: weights } });
  }, [editWeights, updateMut]);

  // If ThemeManager sub-view is active, render it instead
  if (themeManagerWsId !== null) {
    return (
      <ThemeManager
        workspaceId={themeManagerWsId}
        onBack={() => setThemeManagerWsId(null)}
      />
    );
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-bold text-slate-800 flex items-center gap-2">
            <FolderKanban className="w-5 h-5 text-indigo-600" />
            工作区管理
          </h2>
          <p className="text-sm text-slate-500 mt-1">
            创建和管理工作区，每个工作区拥有独立的主题桶、评分权重和 LLM 配置
          </p>
        </div>
        <button
          onClick={() => setCreateMode(true)}
          className="btn-primary text-sm"
        >
          <Plus className="w-4 h-4" />
          新建工作区
        </button>
      </div>

      {/* Create Form */}
      <AnimatePresence>
        {createMode && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="overflow-hidden"
          >
            <div className="bg-white rounded-2xl border border-indigo-100 shadow-card p-5 space-y-4">
              <h3 className="text-sm font-semibold text-slate-700">创建新工作区</h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="text-xs font-medium text-slate-500 mb-1 block">名称 *</label>
                  <input
                    value={newName}
                    onChange={e => setNewName(e.target.value)}
                    placeholder="例：教育信息化研究"
                    className="w-full px-3 py-2 rounded-xl border border-slate-200 text-sm focus:ring-2 focus:ring-indigo-200 focus:border-indigo-400 outline-none transition-all"
                  />
                </div>
                <div>
                  <label className="text-xs font-medium text-slate-500 mb-1 block">描述</label>
                  <input
                    value={newDesc}
                    onChange={e => setNewDesc(e.target.value)}
                    placeholder="简要描述工作区用途"
                    className="w-full px-3 py-2 rounded-xl border border-slate-200 text-sm focus:ring-2 focus:ring-indigo-200 focus:border-indigo-400 outline-none transition-all"
                  />
                </div>
              </div>
              <div className="flex items-center gap-2 justify-end">
                <button
                  onClick={() => { setCreateMode(false); setNewName(''); setNewDesc(''); }}
                  className="px-3 py-1.5 text-sm text-slate-500 hover:text-slate-700 rounded-lg hover:bg-slate-50 transition-colors"
                >
                  取消
                </button>
                <button
                  onClick={handleCreate}
                  disabled={!newName.trim() || createMut.isPending}
                  className="px-4 py-1.5 text-sm font-medium bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-1.5"
                >
                  {createMut.isPending ? <span className="w-3 h-3 border-2 border-white/30 border-t-white rounded-full animate-spin" /> : <Plus className="w-3.5 h-3.5" />}
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

      {/* Workspace List */}
      {isLoading ? (
        <div className="text-center py-12 text-slate-400">加载中...</div>
      ) : workspaces.length === 0 ? (
        <div className="text-center py-12 text-slate-400">暂无工作区</div>
      ) : (
        <div className="space-y-3">
          {workspaces.map(ws => {
            const isExpanded = expandedId === ws.id;
            const isActive = activeWorkspace?.id === ws.id;
            return (
              <div
                key={ws.id}
                className={`bg-white rounded-2xl border shadow-card transition-all duration-200 ${
                  isActive ? 'border-indigo-200 ring-1 ring-indigo-100' : 'border-slate-100'
                }`}
              >
                {/* Workspace Header */}
                <div
                  className="flex items-center gap-4 px-5 py-4 cursor-pointer"
                  onClick={() => setExpandedId(isExpanded ? null : ws.id)}
                >
                  <div className={`w-10 h-10 rounded-xl flex items-center justify-center shrink-0 ${
                    isActive
                      ? 'bg-gradient-to-br from-indigo-100 to-indigo-200'
                      : 'bg-slate-100'
                  }`}>
                    <FolderKanban className={`w-5 h-5 ${isActive ? 'text-indigo-600' : 'text-slate-400'}`} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <h3 className="text-sm font-semibold text-slate-800">{ws.name}</h3>
                      {ws.is_default && (
                        <span className="text-[10px] font-medium text-indigo-600 bg-indigo-50 px-1.5 py-0.5 rounded">默认</span>
                      )}
                      {isActive && (
                        <span className="text-[10px] font-medium text-emerald-600 bg-emerald-50 px-1.5 py-0.5 rounded">当前</span>
                      )}
                    </div>
                    <p className="text-xs text-slate-400 mt-0.5">
                      {ws.description || '无描述'} · {ws.theme_count} 个主题 · {ws.paper_count} 篇论文
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    {!isActive && (
                      <button
                        onClick={(e) => { e.stopPropagation(); switchWorkspace(ws.id); }}
                        className="px-3 py-1 text-xs font-medium text-indigo-600 bg-indigo-50 hover:bg-indigo-100 rounded-lg transition-colors"
                      >
                        切换
                      </button>
                    )}
                    {isExpanded ? (
                      <ChevronDown className="w-4 h-4 text-slate-400" />
                    ) : (
                      <ChevronRight className="w-4 h-4 text-slate-400" />
                    )}
                  </div>
                </div>

                {/* Expanded Detail */}
                <AnimatePresence>
                  {isExpanded && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: 'auto', opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      transition={{ duration: 0.2 }}
                      className="overflow-hidden"
                    >
                      <WorkspaceDetail
                        workspace={ws}
                        onDelete={() => deleteMut.mutate(ws.id)}
                        deleteError={(deleteMut.error as any)?.response?.data?.detail}
                        isDeleting={deleteMut.isPending}
                        onSaveWeights={handleSaveWeights}
                        editWeights={editWeights}
                        setEditWeights={setEditWeights}
                        onImportThemes={() => setThemeImportWsId(ws.id)}
                        onManageThemes={() => setThemeManagerWsId(ws.id)}
                      />
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            );
          })}
        </div>
      )}

      {/* Theme Import Modal */}
      <AnimatePresence>
        {themeImportWsId !== null && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 bg-black/30 flex items-center justify-center p-4"
            onClick={() => setThemeImportWsId(null)}
          >
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              className="bg-white rounded-2xl shadow-xl w-full max-w-lg p-6 space-y-4"
              onClick={e => e.stopPropagation()}
            >
              <h3 className="text-base font-semibold text-slate-800">导入主题桶配置</h3>
              <p className="text-xs text-slate-500">
                粘贴 theme_buckets.md 格式的内容，将替换当前工作区的主题配置。
              </p>
              <textarea
                value={themeImportContent}
                onChange={e => setThemeImportContent(e.target.value)}
                placeholder="## 主题名称&#10;- 标签1&#10;- 标签2&#10;&#10;## 另一个主题&#10;- ..."
                rows={12}
                className="w-full px-3 py-2 rounded-xl border border-slate-200 text-sm font-mono focus:ring-2 focus:ring-indigo-200 focus:border-indigo-400 outline-none resize-none"
              />
              <div className="flex justify-end gap-2">
                <button
                  onClick={() => { setThemeImportWsId(null); setThemeImportContent(''); }}
                  className="px-3 py-1.5 text-sm text-slate-500 hover:text-slate-700 rounded-lg hover:bg-slate-50 transition-colors"
                >
                  取消
                </button>
                <button
                  onClick={() => importThemesMut.mutate(themeImportContent)}
                  disabled={!themeImportContent.trim() || importThemesMut.isPending}
                  className="px-4 py-1.5 text-sm font-medium bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 transition-colors flex items-center gap-1.5"
                >
                  {importThemesMut.isPending ? (
                    <span className="w-3 h-3 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  ) : (
                    <FileText className="w-3.5 h-3.5" />
                  )}
                  导入
                </button>
              </div>
              {importThemesMut.isError && (
                <div className="flex items-center gap-2 text-sm text-red-600 bg-red-50 px-3 py-2 rounded-lg">
                  <AlertCircle className="w-4 h-4 shrink-0" />
                  {(importThemesMut.error as any)?.response?.data?.detail || '导入失败'}
                </div>
              )}
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

// ── Workspace Detail Panel ──

interface WorkspaceDetailProps {
  workspace: WorkspaceItem;
  onDelete: () => void;
  deleteError?: string;
  isDeleting: boolean;
  onSaveWeights: (wsId: number) => void;
  editWeights: Record<number, any>;
  setEditWeights: React.Dispatch<React.SetStateAction<Record<number, any>>>;
  onImportThemes: () => void;
  onManageThemes: () => void;
}

function WorkspaceDetail({ workspace, onDelete, deleteError, isDeleting, onSaveWeights, editWeights, setEditWeights, onImportThemes, onManageThemes }: WorkspaceDetailProps) {
  const [confirmDelete, setConfirmDelete] = useState(false);
  const { activeWorkspace, switchWorkspace } = useWorkspace();

  // Fetch full workspace detail (with scenario_weights)
  const { data: detailData } = useQuery({
    queryKey: ['workspace-detail', workspace.id],
    queryFn: () => workspaceAPI.get(workspace.id),
  });
  const detail: WorkspaceItem | undefined = detailData?.data;

  // Fetch themes for this workspace
  const needsSwitch = activeWorkspace?.id !== workspace.id;
  const { data: themesData } = useQuery({
    queryKey: ['themes', workspace.id],
    queryFn: async () => {
      // Temporarily set header for this specific request
      const { api } = await import('@/lib/api');
      return api.get('/themes', { headers: { 'X-Workspace-Id': String(workspace.id) } });
    },
  });
  const themes: ThemeItem[] = themesData?.data || [];

  const scenarioWeights = editWeights[workspace.id] ?? detail?.scenario_weights;
  const scenarios = scenarioWeights?.scenarios || {};

  return (
    <div className="border-t border-slate-100 px-5 pb-5 space-y-5">
      {/* Themes Section */}
      <div className="pt-4">
        <div className="flex items-center justify-between mb-3">
          <h4 className="text-xs font-semibold text-slate-600 flex items-center gap-1.5">
            <Tags className="w-3.5 h-3.5" />
            主题桶 ({themes.length})
          </h4>
          <div className="flex items-center gap-3">
            <button
              onClick={onManageThemes}
              className="text-[11px] text-indigo-600 hover:text-indigo-700 font-medium flex items-center gap-1 px-2 py-1 rounded-md hover:bg-indigo-50 transition-colors"
            >
              <Pencil className="w-3 h-3" />
              管理主题
            </button>
            <button
              onClick={onImportThemes}
              className="text-[11px] text-slate-500 hover:text-slate-600 font-medium flex items-center gap-1"
            >
              <FileText className="w-3 h-3" />
              导入配置
            </button>
          </div>
        </div>
        {themes.length === 0 ? (
          <p className="text-xs text-slate-400 py-2">暂无主题桶，点击「导入配置」添加</p>
        ) : (
          <div className="flex flex-wrap gap-2">
            {themes.map(t => (
              <div key={t.id} className="px-2.5 py-1.5 bg-slate-50 rounded-lg border border-slate-100">
                <p className="text-xs font-medium text-slate-700">{t.name}</p>
                <p className="text-[10px] text-slate-400">{t.paper_count || 0} 篇</p>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Scenario Weights Section */}
      <div>
        <h4 className="text-xs font-semibold text-slate-600 flex items-center gap-1.5 mb-3">
          <Weight className="w-3.5 h-3.5" />
          场景评分权重
        </h4>
        {Object.keys(scenarios).length === 0 ? (
          <p className="text-xs text-slate-400 py-2">使用全局默认权重配置</p>
        ) : (
          <div className="space-y-3">
            {Object.entries(scenarios).map(([name, config]: [string, any]) => (
              <div key={name} className="bg-slate-50 rounded-xl p-3">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-semibold text-slate-700">{name}</span>
                  <span className="text-[10px] text-slate-400">{config.description || ''}</span>
                </div>
                <div className="grid grid-cols-5 gap-2">
                  {['rigor', 'innovation', 'practicality', 'impact', 'readability'].map(dim => {
                    const labels: Record<string, string> = {
                      rigor: '严谨', innovation: '创新', practicality: '实用',
                      impact: '影响', readability: '可读'
                    };
                    return (
                      <div key={dim} className="text-center">
                        <p className="text-[10px] text-slate-400 mb-1">{labels[dim]}</p>
                        <input
                          type="number"
                          step="0.05"
                          min="0"
                          max="1"
                          value={config.weights?.[dim] ?? 0.2}
                          onChange={(e) => {
                            const val = parseFloat(e.target.value) || 0;
                            setEditWeights(prev => {
                              const current = prev[workspace.id] ?? detail?.scenario_weights ?? {};
                              const newScenarios = { ...current.scenarios };
                              newScenarios[name] = {
                                ...newScenarios[name],
                                weights: { ...newScenarios[name]?.weights, [dim]: val }
                              };
                              return { ...prev, [workspace.id]: { ...current, scenarios: newScenarios } };
                            });
                          }}
                          className="w-full px-1.5 py-1 text-xs text-center rounded-lg border border-slate-200 focus:ring-1 focus:ring-indigo-200 focus:border-indigo-400 outline-none"
                        />
                      </div>
                    );
                  })}
                </div>
              </div>
            ))}
            {editWeights[workspace.id] && (
              <button
                onClick={() => onSaveWeights(workspace.id)}
                className="text-xs font-medium text-indigo-600 hover:text-indigo-700 flex items-center gap-1"
              >
                <Save className="w-3 h-3" />
                保存权重修改
              </button>
            )}
          </div>
        )}
      </div>

      {/* Danger Zone */}
      {!workspace.is_default && (
        <div className="pt-3 border-t border-slate-100">
          {!confirmDelete ? (
            <button
              onClick={() => setConfirmDelete(true)}
              className="text-xs text-red-500 hover:text-red-600 flex items-center gap-1 transition-colors"
            >
              <Trash2 className="w-3 h-3" />
              删除工作区
            </button>
          ) : (
            <div className="flex items-center gap-3 bg-red-50 px-3 py-2 rounded-lg">
              <AlertCircle className="w-4 h-4 text-red-500 shrink-0" />
              <span className="text-xs text-red-600 flex-1">确定删除「{workspace.name}」？此操作不可恢复。</span>
              <button
                onClick={onDelete}
                disabled={isDeleting}
                className="px-2 py-1 text-xs font-medium text-white bg-red-500 hover:bg-red-600 rounded-lg disabled:opacity-50 transition-colors"
              >
                {isDeleting ? '删除中...' : '确定'}
              </button>
              <button
                onClick={() => setConfirmDelete(false)}
                className="px-2 py-1 text-xs text-slate-500 hover:text-slate-700 rounded-lg hover:bg-slate-100 transition-colors"
              >
                取消
              </button>
            </div>
          )}
          {deleteError && (
            <p className="text-xs text-red-500 mt-2">{deleteError}</p>
          )}
        </div>
      )}
    </div>
  );
}
