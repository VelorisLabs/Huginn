import { useState, useRef, useEffect } from 'react';
import {
  LayoutDashboard, BarChart3, BookmarkCheck, Upload,
  ChevronLeft, ChevronRight, LogOut, Sparkles,
  FolderKanban, ChevronDown, Plus, Settings2, Layers
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { useWorkspace } from './workspace/WorkspaceContext';

export type TabKey = 'overview' | 'analysis' | 'clustering' | 'reading-list' | 'upload' | 'workspace-settings';

interface SidebarProps {
  activeTab: TabKey;
  onTabChange: (tab: TabKey) => void;
  username?: string;
  onLogout: () => void;
}

const NAV_ITEMS: { key: TabKey; label: string; icon: React.ElementType; badge?: string }[] = [
  { key: 'overview', label: '仪表盘', icon: LayoutDashboard },
  { key: 'analysis', label: '深度分析', icon: BarChart3 },
  { key: 'clustering', label: '主题聚类', icon: Layers },
  { key: 'reading-list', label: '阅读清单', icon: BookmarkCheck },
  { key: 'upload', label: '导入文献', icon: Upload },
  { key: 'workspace-settings', label: '工作区管理', icon: Settings2 },
];

export function Sidebar({ activeTab, onTabChange, username, onLogout }: SidebarProps) {
  const [collapsed, setCollapsed] = useState(false);
  const [wsDropdownOpen, setWsDropdownOpen] = useState(false);
  const wsDropdownRef = useRef<HTMLDivElement>(null);
  const { workspaces, activeWorkspace, switchWorkspace } = useWorkspace();

  // Close dropdown on outside click
  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (wsDropdownRef.current && !wsDropdownRef.current.contains(e.target as Node)) {
        setWsDropdownOpen(false);
      }
    }
    if (wsDropdownOpen) document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, [wsDropdownOpen]);

  return (
    <aside className={`sidebar ${collapsed ? 'sidebar-collapsed' : ''}`}>
      {/* Logo */}
      <div className="flex items-center gap-3 px-5 h-16 border-b border-slate-100 shrink-0">
        <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-primary-500 to-primary-700 flex items-center justify-center shadow-md shadow-primary-500/20 shrink-0">
          <Sparkles className="w-5 h-5 text-white" />
        </div>
        <AnimatePresence>
          {!collapsed && (
            <motion.div
              initial={{ opacity: 0, width: 0 }}
              animate={{ opacity: 1, width: 'auto' }}
              exit={{ opacity: 0, width: 0 }}
              className="overflow-hidden whitespace-nowrap"
            >
              <span className="text-lg font-bold bg-gradient-to-r from-primary-600 to-primary-800 bg-clip-text text-transparent">
                PaperAI
              </span>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Workspace Switcher */}
      <div className="px-3 pt-3 pb-1 shrink-0" ref={wsDropdownRef}>
        <div className="relative">
          <button
            onClick={() => setWsDropdownOpen(!wsDropdownOpen)}
            className={`w-full flex items-center gap-2.5 px-3 py-2.5 rounded-xl border border-slate-100 bg-slate-50/80 hover:bg-white hover:border-slate-200 transition-all duration-200 group ${
              collapsed ? 'justify-center' : ''
            }`}
            title={collapsed ? activeWorkspace?.name || '工作区' : undefined}
          >
            <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-indigo-100 to-indigo-200 flex items-center justify-center shrink-0">
              <FolderKanban className="w-3.5 h-3.5 text-indigo-600" />
            </div>
            {!collapsed && (
              <>
                <div className="flex-1 min-w-0 text-left">
                  <p className="text-xs font-semibold text-slate-700 truncate">
                    {activeWorkspace?.name || '加载中...'}
                  </p>
                  <p className="text-[10px] text-slate-400">
                    {activeWorkspace ? `${activeWorkspace.paper_count} 篇论文` : ''}
                  </p>
                </div>
                <ChevronDown className={`w-3.5 h-3.5 text-slate-400 transition-transform duration-200 ${
                  wsDropdownOpen ? 'rotate-180' : ''
                }`} />
              </>
            )}
          </button>

          {/* Dropdown */}
          <AnimatePresence>
            {wsDropdownOpen && !collapsed && (
              <motion.div
                initial={{ opacity: 0, y: -4, scale: 0.97 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: -4, scale: 0.97 }}
                transition={{ duration: 0.15 }}
                className="absolute z-50 top-full left-0 right-0 mt-1 bg-white rounded-xl border border-slate-100 shadow-lg shadow-slate-200/50 overflow-hidden"
              >
                <div className="max-h-48 overflow-y-auto py-1">
                  {workspaces.map(ws => (
                    <button
                      key={ws.id}
                      onClick={() => {
                        switchWorkspace(ws.id);
                        setWsDropdownOpen(false);
                      }}
                      className={`w-full flex items-center gap-2.5 px-3 py-2 text-left hover:bg-slate-50 transition-colors ${
                        ws.id === activeWorkspace?.id ? 'bg-indigo-50' : ''
                      }`}
                    >
                      <div className={`w-2 h-2 rounded-full shrink-0 ${
                        ws.id === activeWorkspace?.id ? 'bg-indigo-500' : 'bg-slate-200'
                      }`} />
                      <div className="flex-1 min-w-0">
                        <p className={`text-xs font-medium truncate ${
                          ws.id === activeWorkspace?.id ? 'text-indigo-700' : 'text-slate-700'
                        }`}>{ws.name}</p>
                        <p className="text-[10px] text-slate-400">{ws.paper_count} 篇 · {ws.theme_count} 个主题</p>
                      </div>
                      {ws.is_default && (
                        <span className="text-[9px] font-medium text-slate-400 bg-slate-100 px-1 py-0.5 rounded">默认</span>
                      )}
                    </button>
                  ))}
                </div>
                <div className="border-t border-slate-100 p-1">
                  <button
                    onClick={() => {
                      setWsDropdownOpen(false);
                      onTabChange('workspace-settings');
                    }}
                    className="w-full flex items-center gap-2 px-3 py-2 text-xs text-slate-500 hover:text-indigo-600 hover:bg-slate-50 rounded-lg transition-colors"
                  >
                    <Plus className="w-3.5 h-3.5" />
                    管理工作区
                  </button>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto scrollbar-hide">
        <div className="px-3 mb-3">
          {!collapsed && (
            <span className="text-[10px] font-semibold uppercase tracking-widest text-slate-400">
              导航
            </span>
          )}
        </div>
        {NAV_ITEMS.map(({ key, label, icon: Icon, badge }) => {
          const isActive = activeTab === key;
          return (
            <button
              key={key}
              onClick={() => onTabChange(key)}
              className={`sidebar-item w-full ${isActive ? 'sidebar-item-active' : ''} ${collapsed ? 'justify-center px-0' : ''}`}
              title={collapsed ? label : undefined}
            >
              <div className="relative">
                <Icon className={`w-[18px] h-[18px] shrink-0 ${isActive ? 'text-primary-600' : ''}`} />
                {isActive && (
                  <motion.div
                    layoutId="sidebar-indicator"
                    className="absolute -left-[18px] top-1/2 -translate-y-1/2 w-[3px] h-5 bg-primary-600 rounded-r-full"
                    transition={{ type: 'spring', stiffness: 350, damping: 30 }}
                  />
                )}
              </div>
              {!collapsed && (
                <span className="truncate">{label}</span>
              )}
              {!collapsed && badge && (
                <span className="ml-auto text-[10px] font-bold bg-primary-100 text-primary-700 px-1.5 py-0.5 rounded-md">
                  {badge}
                </span>
              )}
            </button>
          );
        })}
      </nav>

      {/* Footer */}
      <div className="border-t border-slate-100 p-3 space-y-2 shrink-0">
        {/* User */}
        <div className={`flex items-center gap-3 px-3 py-2 rounded-xl ${collapsed ? 'justify-center' : ''}`}>
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-slate-100 to-slate-200 flex items-center justify-center text-xs font-bold text-slate-600 shrink-0">
            {username?.charAt(0).toUpperCase() || 'U'}
          </div>
          {!collapsed && (
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-slate-700 truncate">{username || 'User'}</p>
              <p className="text-[11px] text-slate-400">研究者</p>
            </div>
          )}
          {!collapsed && (
            <button
              onClick={onLogout}
              className="p-1.5 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition-colors"
              title="退出登录"
            >
              <LogOut className="w-4 h-4" />
            </button>
          )}
        </div>

        {/* Collapse Toggle */}
        <button
          onClick={() => setCollapsed(!collapsed)}
          className={`w-full flex items-center gap-2 px-3 py-2 rounded-xl text-xs font-medium text-slate-400 hover:text-slate-600 hover:bg-slate-50 transition-colors ${collapsed ? 'justify-center' : ''}`}
        >
          {collapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
          {!collapsed && <span>收起侧栏</span>}
        </button>
      </div>
    </aside>
  );
}
