import { useState, useMemo } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { adminAPI } from '@/lib/api';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Users, Ticket, Plus, Coins, Search, ChevronDown, ChevronUp,
  Copy, Check, ToggleLeft, ToggleRight, Trash2, ArrowUpDown,
  Shield, Clock, Hash, AlertCircle, RefreshCw, X,
  UserX, UserCheck, RotateCcw, Ban,
} from 'lucide-react';

/* ─── Types ─── */
interface AdminUser {
  id: number;
  email: string;
  username: string;
  credits: number;
  is_active: boolean;
  is_superuser: boolean;
  created_at: string;
}

interface InviteCode {
  id: number;
  code: string;
  credits: number;
  max_uses: number;
  used_count: number;
  is_active: boolean;
  note?: string;
  created_at: string;
  expires_at?: string;
  created_by_id?: number;
}

interface CreditTxn {
  id: number;
  user_id: number;
  amount: number;
  type: string;
  balance_after: number;
  description?: string;
  created_at: string;
}

/* ─── Sub-tabs ─── */
type AdminTab = 'users' | 'invites';

export function AdminPanel() {
  const [tab, setTab] = useState<AdminTab>('users');

  return (
    <div className="space-y-6">
      {/* Sub-tab Switcher */}
      <div className="flex items-center gap-1 p-1 bg-slate-100 rounded-xl w-fit">
        <TabButton active={tab === 'users'} onClick={() => setTab('users')} icon={Users} label="用户管理" />
        <TabButton active={tab === 'invites'} onClick={() => setTab('invites')} icon={Ticket} label="邀请码管理" />
      </div>

      <AnimatePresence mode="wait">
        <motion.div
          key={tab}
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -8 }}
          transition={{ duration: 0.2 }}
        >
          {tab === 'users' ? <UsersPanel /> : <InvitesPanel />}
        </motion.div>
      </AnimatePresence>
    </div>
  );
}

function TabButton({ active, onClick, icon: Icon, label }: {
  active: boolean; onClick: () => void; icon: React.ElementType; label: string;
}) {
  return (
    <button
      onClick={onClick}
      className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
        active
          ? 'bg-white text-slate-800 shadow-sm'
          : 'text-slate-500 hover:text-slate-700'
      }`}
    >
      <Icon className="w-4 h-4" />
      {label}
    </button>
  );
}

/* ═══════════════════════════════════════
   Users Panel
   ═══════════════════════════════════════ */

function UsersPanel() {
  const queryClient = useQueryClient();
  const [search, setSearch] = useState('');
  const [sortBy, setSortBy] = useState<'credits' | 'created_at'>('created_at');
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('desc');
  const [adjustUserId, setAdjustUserId] = useState<number | null>(null);
  const [adjustAmount, setAdjustAmount] = useState('');
  const [adjustDesc, setAdjustDesc] = useState('');
  const [expandedUserId, setExpandedUserId] = useState<number | null>(null);
  const [resetUserId, setResetUserId] = useState<number | null>(null);
  const [resetAmount, setResetAmount] = useState('50');

  const { data: usersRaw, isLoading } = useQuery({
    queryKey: ['admin-users'],
    queryFn: () => adminAPI.listUsers(),
  });
  const users: AdminUser[] = usersRaw?.data || [];

  const filtered = useMemo(() => {
    let result = users.filter(u =>
      u.email.toLowerCase().includes(search.toLowerCase()) ||
      u.username.toLowerCase().includes(search.toLowerCase())
    );
    result.sort((a, b) => {
      const va = sortBy === 'credits' ? a.credits : new Date(a.created_at).getTime();
      const vb = sortBy === 'credits' ? b.credits : new Date(b.created_at).getTime();
      return sortDir === 'asc' ? va - vb : vb - va;
    });
    return result;
  }, [users, search, sortBy, sortDir]);

  const totalCredits = useMemo(() => users.reduce((s, u) => s + u.credits, 0), [users]);

  const adjustMutation = useMutation({
    mutationFn: ({ userId, amount, description }: { userId: number; amount: number; description: string }) =>
      adminAPI.adjustCredits(userId, { amount, description }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-users'] });
      setAdjustUserId(null);
      setAdjustAmount('');
      setAdjustDesc('');
    },
  });

  const toggleMutation = useMutation({
    mutationFn: (userId: number) => adminAPI.toggleUser(userId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['admin-users'] }),
  });

  const deleteMutation = useMutation({
    mutationFn: (userId: number) => adminAPI.deleteUser(userId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['admin-users'] }),
  });

  const resetMutation = useMutation({
    mutationFn: ({ userId, amount }: { userId: number; amount: number }) =>
      adminAPI.resetUser(userId, { amount, description: `管理员重置积分为 ${amount}` }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-users'] });
      setResetUserId(null);
      setResetAmount('50');
    },
  });

  const handleToggleSort = (field: 'credits' | 'created_at') => {
    if (sortBy === field) setSortDir(d => d === 'asc' ? 'desc' : 'asc');
    else { setSortBy(field); setSortDir('desc'); }
  };

  return (
    <div className="space-y-5">
      {/* Stats Row */}
      <div className="grid grid-cols-3 gap-4">
        <MiniStat icon={Users} label="总用户数" value={users.length} color="blue" />
        <MiniStat icon={Coins} label="积分总量" value={totalCredits} color="amber" />
        <MiniStat icon={Shield} label="管理员" value={users.filter(u => u.is_superuser).length} color="violet" />
      </div>

      {/* Search & Sort */}
      <div className="flex items-center gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <input
            type="text"
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder="搜索用户名或邮箱..."
            className="w-full pl-9 pr-4 py-2.5 bg-white border border-slate-200 rounded-xl text-sm focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500 transition-all outline-none"
          />
        </div>
        <button
          onClick={() => handleToggleSort('credits')}
          className={`flex items-center gap-1.5 px-3 py-2.5 rounded-xl border text-xs font-medium transition-all ${
            sortBy === 'credits' ? 'bg-amber-50 border-amber-200 text-amber-700' : 'bg-white border-slate-200 text-slate-600 hover:bg-slate-50'
          }`}
        >
          <Coins className="w-3.5 h-3.5" />
          积分
          {sortBy === 'credits' && (sortDir === 'desc' ? <ChevronDown className="w-3 h-3" /> : <ChevronUp className="w-3 h-3" />)}
        </button>
        <button
          onClick={() => handleToggleSort('created_at')}
          className={`flex items-center gap-1.5 px-3 py-2.5 rounded-xl border text-xs font-medium transition-all ${
            sortBy === 'created_at' ? 'bg-blue-50 border-blue-200 text-blue-700' : 'bg-white border-slate-200 text-slate-600 hover:bg-slate-50'
          }`}
        >
          <Clock className="w-3.5 h-3.5" />
          注册时间
          {sortBy === 'created_at' && (sortDir === 'desc' ? <ChevronDown className="w-3 h-3" /> : <ChevronUp className="w-3 h-3" />)}
        </button>
      </div>

      {/* User Table */}
      <div className="bg-white rounded-2xl border border-slate-100 shadow-card overflow-hidden">
        {isLoading ? (
          <div className="p-8 text-center text-sm text-slate-400">
            <RefreshCw className="w-5 h-5 mx-auto mb-2 animate-spin text-slate-300" />
            加载中...
          </div>
        ) : filtered.length === 0 ? (
          <div className="p-8 text-center text-sm text-slate-400">未找到用户</div>
        ) : (
          <div className="divide-y divide-slate-50">
            {filtered.map(user => (
              <div key={user.id}>
                <div className="flex items-center gap-4 px-5 py-3.5 hover:bg-slate-50/50 transition-colors">
                  {/* Avatar */}
                  <div className={`w-9 h-9 rounded-lg flex items-center justify-center text-xs font-bold shrink-0 ${
                    user.is_superuser
                      ? 'bg-gradient-to-br from-amber-100 to-amber-200 text-amber-700'
                      : 'bg-gradient-to-br from-slate-100 to-slate-200 text-slate-600'
                  }`}>
                    {user.is_superuser ? <Shield className="w-4 h-4" /> : user.username.charAt(0).toUpperCase()}
                  </div>

                  {/* Info */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <p className={`text-sm font-semibold truncate ${user.is_active ? 'text-slate-800' : 'text-slate-400 line-through'}`}>{user.username}</p>
                      {user.is_superuser && (
                        <span className="text-[9px] font-bold bg-amber-100 text-amber-700 px-1.5 py-0.5 rounded-md">ADMIN</span>
                      )}
                      {!user.is_active && (
                        <span className="text-[9px] font-bold bg-red-100 text-red-600 px-1.5 py-0.5 rounded-md">已禁用</span>
                      )}
                    </div>
                    <p className="text-[11px] text-slate-400 truncate">{user.email}</p>
                  </div>

                  {/* Credits */}
                  <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-amber-50 border border-amber-100">
                    <Coins className="w-3.5 h-3.5 text-amber-500" />
                    <span className="text-sm font-bold text-amber-700 tabular-nums">{user.credits}</span>
                  </div>

                  {/* Actions */}
                  <div className="flex items-center gap-1">
                    <button
                      onClick={() => setAdjustUserId(adjustUserId === user.id ? null : user.id)}
                      className="p-2 rounded-lg text-slate-400 hover:text-primary-600 hover:bg-primary-50 transition-colors"
                      title="调整积分"
                    >
                      <ArrowUpDown className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => setResetUserId(resetUserId === user.id ? null : user.id)}
                      className="p-2 rounded-lg text-slate-400 hover:text-amber-600 hover:bg-amber-50 transition-colors"
                      title="重置积分"
                    >
                      <RotateCcw className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => setExpandedUserId(expandedUserId === user.id ? null : user.id)}
                      className="p-2 rounded-lg text-slate-400 hover:text-blue-600 hover:bg-blue-50 transition-colors"
                      title="查看流水"
                    >
                      <Clock className="w-4 h-4" />
                    </button>
                    {!user.is_superuser && (
                      <>
                        <button
                          onClick={() => toggleMutation.mutate(user.id)}
                          className={`p-2 rounded-lg transition-colors ${
                            user.is_active
                              ? 'text-slate-400 hover:text-orange-600 hover:bg-orange-50'
                              : 'text-orange-500 hover:text-emerald-600 hover:bg-emerald-50'
                          }`}
                          title={user.is_active ? '禁用用户' : '启用用户'}
                        >
                          {user.is_active ? <Ban className="w-4 h-4" /> : <UserCheck className="w-4 h-4" />}
                        </button>
                        <button
                          onClick={() => {
                            if (confirm(`确定删除用户 ${user.username}（${user.email}）及其所有数据？此操作不可恢复！`)) {
                              deleteMutation.mutate(user.id);
                            }
                          }}
                          className="p-2 rounded-lg text-slate-400 hover:text-red-600 hover:bg-red-50 transition-colors"
                          title="删除用户"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </>
                    )}
                  </div>

                  {/* Date */}
                  <span className="text-[11px] text-slate-400 tabular-nums shrink-0 w-20 text-right">
                    {new Date(user.created_at).toLocaleDateString('zh-CN')}
                  </span>
                </div>

                {/* Adjust Credits Inline Form */}
                <AnimatePresence>
                  {adjustUserId === user.id && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: 'auto', opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      className="overflow-hidden"
                    >
                      <div className="flex items-center gap-3 px-5 py-3 bg-primary-50/50 border-t border-primary-100">
                        <span className="text-xs font-medium text-primary-700 shrink-0">调整积分:</span>
                        <input
                          type="number"
                          value={adjustAmount}
                          onChange={e => setAdjustAmount(e.target.value)}
                          placeholder="正数=充值 负数=扣除"
                          className="w-40 px-3 py-1.5 bg-white border border-primary-200 rounded-lg text-sm outline-none focus:ring-2 focus:ring-primary-500/20"
                        />
                        <input
                          type="text"
                          value={adjustDesc}
                          onChange={e => setAdjustDesc(e.target.value)}
                          placeholder="备注说明（可选）"
                          className="flex-1 px-3 py-1.5 bg-white border border-primary-200 rounded-lg text-sm outline-none focus:ring-2 focus:ring-primary-500/20"
                        />
                        <button
                          onClick={() => {
                            const amt = parseInt(adjustAmount);
                            if (isNaN(amt) || amt === 0) return;
                            adjustMutation.mutate({ userId: user.id, amount: amt, description: adjustDesc || `管理员手动调整` });
                          }}
                          disabled={adjustMutation.isPending}
                          className="px-4 py-1.5 bg-primary-600 text-white rounded-lg text-xs font-medium hover:bg-primary-700 transition-colors disabled:opacity-50"
                        >
                          {adjustMutation.isPending ? '处理...' : '确认'}
                        </button>
                        <button
                          onClick={() => setAdjustUserId(null)}
                          className="p-1.5 text-slate-400 hover:text-slate-600 transition-colors"
                        >
                          <X className="w-4 h-4" />
                        </button>
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>

                {/* Reset Credits Inline Form */}
                <AnimatePresence>
                  {resetUserId === user.id && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: 'auto', opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      className="overflow-hidden"
                    >
                      <div className="flex items-center gap-3 px-5 py-3 bg-amber-50/50 border-t border-amber-100">
                        <span className="text-xs font-medium text-amber-700 shrink-0">重置积分为:</span>
                        <input
                          type="number"
                          value={resetAmount}
                          onChange={e => setResetAmount(e.target.value)}
                          placeholder="目标积分值"
                          min={0}
                          className="w-32 px-3 py-1.5 bg-white border border-amber-200 rounded-lg text-sm outline-none focus:ring-2 focus:ring-amber-500/20"
                        />
                        <span className="text-[11px] text-slate-400">当前: {user.credits}</span>
                        <button
                          onClick={() => {
                            const amt = parseInt(resetAmount);
                            if (isNaN(amt) || amt < 0) return;
                            resetMutation.mutate({ userId: user.id, amount: amt });
                          }}
                          disabled={resetMutation.isPending}
                          className="px-4 py-1.5 bg-amber-600 text-white rounded-lg text-xs font-medium hover:bg-amber-700 transition-colors disabled:opacity-50"
                        >
                          {resetMutation.isPending ? '处理...' : '确认重置'}
                        </button>
                        <button
                          onClick={() => setResetUserId(null)}
                          className="p-1.5 text-slate-400 hover:text-slate-600 transition-colors"
                        >
                          <X className="w-4 h-4" />
                        </button>
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>

                {/* Transactions Expandable */}
                <AnimatePresence>
                  {expandedUserId === user.id && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: 'auto', opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      className="overflow-hidden"
                    >
                      <UserTransactions userId={user.id} />
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function UserTransactions({ userId }: { userId: number }) {
  const { data, isLoading } = useQuery({
    queryKey: ['admin-user-txns', userId],
    queryFn: () => adminAPI.getUserTransactions(userId),
  });
  const txns: CreditTxn[] = data?.data || [];

  if (isLoading) return <div className="px-5 py-3 text-xs text-slate-400 bg-blue-50/30">加载流水...</div>;
  if (txns.length === 0) return <div className="px-5 py-3 text-xs text-slate-400 bg-blue-50/30">暂无积分流水</div>;

  return (
    <div className="bg-blue-50/30 border-t border-blue-100">
      <div className="px-5 py-2">
        <p className="text-[10px] font-semibold text-blue-600 uppercase tracking-wider mb-2">积分流水</p>
        <div className="space-y-1">
          {txns.slice(0, 10).map(txn => (
            <div key={txn.id} className="flex items-center gap-3 py-1.5 text-xs">
              <span className={`font-bold tabular-nums w-16 text-right ${txn.amount >= 0 ? 'text-emerald-600' : 'text-red-500'}`}>
                {txn.amount >= 0 ? '+' : ''}{txn.amount}
              </span>
              <span className="text-slate-500 flex-1 truncate">{txn.description || txn.type}</span>
              <span className="text-slate-400 tabular-nums shrink-0">余额 {txn.balance_after}</span>
              <span className="text-slate-300 tabular-nums shrink-0 w-24 text-right">
                {new Date(txn.created_at).toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════
   Invites Panel
   ═══════════════════════════════════════ */

function InvitesPanel() {
  const queryClient = useQueryClient();
  const [showCreate, setShowCreate] = useState(false);
  const [newCredits, setNewCredits] = useState('50');
  const [newMaxUses, setNewMaxUses] = useState('1');
  const [newNote, setNewNote] = useState('');
  const [copiedId, setCopiedId] = useState<number | null>(null);

  const { data: codesRaw, isLoading } = useQuery({
    queryKey: ['admin-invite-codes'],
    queryFn: () => adminAPI.listInviteCodes(),
  });
  const codes: InviteCode[] = codesRaw?.data || [];

  const activeCount = codes.filter(c => c.is_active && c.used_count < c.max_uses).length;
  const totalUsed = codes.reduce((s, c) => s + c.used_count, 0);

  const createMutation = useMutation({
    mutationFn: (data: { credits: number; max_uses: number; note?: string }) =>
      adminAPI.createInviteCode(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-invite-codes'] });
      setShowCreate(false);
      setNewCredits('50');
      setNewMaxUses('1');
      setNewNote('');
    },
  });

  const toggleMutation = useMutation({
    mutationFn: (id: number) => adminAPI.toggleInviteCode(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['admin-invite-codes'] }),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => adminAPI.deleteInviteCode(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['admin-invite-codes'] }),
  });

  const copyCode = (code: string, id: number) => {
    navigator.clipboard.writeText(code);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  return (
    <div className="space-y-5">
      {/* Stats */}
      <div className="grid grid-cols-3 gap-4">
        <MiniStat icon={Ticket} label="邀请码总数" value={codes.length} color="violet" />
        <MiniStat icon={ToggleRight} label="可用邀请码" value={activeCount} color="emerald" />
        <MiniStat icon={Hash} label="已使用次数" value={totalUsed} color="blue" />
      </div>

      {/* Create Button + Form */}
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-slate-700">邀请码列表</h3>
        <button
          onClick={() => setShowCreate(!showCreate)}
          className="flex items-center gap-1.5 px-3 py-2 bg-primary-600 text-white rounded-xl text-xs font-medium hover:bg-primary-700 transition-colors shadow-sm"
        >
          <Plus className="w-3.5 h-3.5" />
          生成邀请码
        </button>
      </div>

      <AnimatePresence>
        {showCreate && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="overflow-hidden"
          >
            <div className="bg-white rounded-2xl border border-primary-100 shadow-card p-5">
              <h4 className="text-sm font-semibold text-slate-800 mb-4">生成新邀请码</h4>
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label className="block text-xs font-medium text-slate-600 mb-1.5">赠送积分</label>
                  <input
                    type="number"
                    value={newCredits}
                    onChange={e => setNewCredits(e.target.value)}
                    min={0}
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-600 mb-1.5">最大使用次数</label>
                  <input
                    type="number"
                    value={newMaxUses}
                    onChange={e => setNewMaxUses(e.target.value)}
                    min={1}
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-600 mb-1.5">备注</label>
                  <input
                    type="text"
                    value={newNote}
                    onChange={e => setNewNote(e.target.value)}
                    placeholder="可选"
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500"
                  />
                </div>
              </div>
              <div className="flex items-center gap-3 mt-4">
                <button
                  onClick={() => {
                    const credits = parseInt(newCredits) || 50;
                    const max_uses = parseInt(newMaxUses) || 1;
                    createMutation.mutate({ credits, max_uses, note: newNote || undefined });
                  }}
                  disabled={createMutation.isPending}
                  className="px-5 py-2 bg-primary-600 text-white rounded-xl text-sm font-medium hover:bg-primary-700 transition-colors disabled:opacity-50"
                >
                  {createMutation.isPending ? '生成中...' : '确认生成'}
                </button>
                <button
                  onClick={() => setShowCreate(false)}
                  className="px-4 py-2 text-slate-500 hover:text-slate-700 text-sm transition-colors"
                >
                  取消
                </button>
                {createMutation.isError && (
                  <span className="text-xs text-red-500 flex items-center gap-1">
                    <AlertCircle className="w-3 h-3" />
                    生成失败
                  </span>
                )}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Invite Code Cards */}
      <div className="bg-white rounded-2xl border border-slate-100 shadow-card overflow-hidden">
        {isLoading ? (
          <div className="p-8 text-center text-sm text-slate-400">
            <RefreshCw className="w-5 h-5 mx-auto mb-2 animate-spin text-slate-300" />
            加载中...
          </div>
        ) : codes.length === 0 ? (
          <div className="p-8 text-center text-sm text-slate-400">暂无邀请码</div>
        ) : (
          <div className="divide-y divide-slate-50">
            {codes.map(code => {
              const isExhausted = code.used_count >= code.max_uses;
              const isExpired = code.expires_at && new Date(code.expires_at) < new Date();
              const isAvailable = code.is_active && !isExhausted && !isExpired;

              return (
                <div
                  key={code.id}
                  className={`flex items-center gap-4 px-5 py-3.5 transition-colors ${
                    isAvailable ? 'hover:bg-slate-50/50' : 'opacity-60 bg-slate-50/30'
                  }`}
                >
                  {/* Status Dot */}
                  <div className={`w-2.5 h-2.5 rounded-full shrink-0 ${
                    isAvailable ? 'bg-emerald-500' : 'bg-slate-300'
                  }`} />

                  {/* Code */}
                  <div className="flex items-center gap-2 min-w-0">
                    <code className="text-sm font-mono font-bold text-slate-800 bg-slate-100 px-2.5 py-1 rounded-lg select-all">
                      {code.code}
                    </code>
                    <button
                      onClick={() => copyCode(code.code, code.id)}
                      className="p-1.5 rounded-lg text-slate-400 hover:text-primary-600 hover:bg-primary-50 transition-colors"
                      title="复制邀请码"
                    >
                      {copiedId === code.id ? <Check className="w-3.5 h-3.5 text-emerald-500" /> : <Copy className="w-3.5 h-3.5" />}
                    </button>
                  </div>

                  {/* Credits */}
                  <div className="flex items-center gap-1 px-2 py-1 rounded-md bg-amber-50 border border-amber-100">
                    <Coins className="w-3 h-3 text-amber-500" />
                    <span className="text-[11px] font-bold text-amber-700">{code.credits}</span>
                  </div>

                  {/* Usage */}
                  <div className="flex items-center gap-1.5">
                    <div className="w-16 h-1.5 bg-slate-100 rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full transition-all ${isExhausted ? 'bg-red-400' : 'bg-emerald-400'}`}
                        style={{ width: `${Math.min((code.used_count / code.max_uses) * 100, 100)}%` }}
                      />
                    </div>
                    <span className="text-[11px] text-slate-500 tabular-nums">
                      {code.used_count}/{code.max_uses}
                    </span>
                  </div>

                  {/* Note */}
                  {code.note && (
                    <span className="text-[11px] text-slate-400 truncate max-w-[120px]" title={code.note}>
                      {code.note}
                    </span>
                  )}

                  <div className="flex-1" />

                  {/* Date */}
                  <span className="text-[11px] text-slate-400 tabular-nums shrink-0">
                    {new Date(code.created_at).toLocaleDateString('zh-CN')}
                  </span>

                  {/* Actions */}
                  <div className="flex items-center gap-1">
                    <button
                      onClick={() => toggleMutation.mutate(code.id)}
                      className={`p-1.5 rounded-lg transition-colors ${
                        code.is_active
                          ? 'text-emerald-500 hover:bg-emerald-50'
                          : 'text-slate-400 hover:bg-slate-100'
                      }`}
                      title={code.is_active ? '停用' : '启用'}
                    >
                      {code.is_active ? <ToggleRight className="w-4 h-4" /> : <ToggleLeft className="w-4 h-4" />}
                    </button>
                    <button
                      onClick={() => {
                        if (confirm('确定删除此邀请码？')) deleteMutation.mutate(code.id);
                      }}
                      className="p-1.5 rounded-lg text-slate-400 hover:text-red-500 hover:bg-red-50 transition-colors"
                      title="删除"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}

/* ─── Shared Components ─── */

function MiniStat({ icon: Icon, label, value, color }: {
  icon: React.ElementType; label: string; value: number; color: string;
}) {
  const colors: Record<string, string> = {
    blue: 'from-blue-50 to-blue-100/50 border-blue-100 text-blue-600',
    amber: 'from-amber-50 to-amber-100/50 border-amber-100 text-amber-600',
    violet: 'from-primary-50 to-primary-100/50 border-primary-100 text-primary-600',
    emerald: 'from-emerald-50 to-emerald-100/50 border-emerald-100 text-emerald-600',
  };
  const iconColors: Record<string, string> = {
    blue: 'bg-blue-100 text-blue-600',
    amber: 'bg-amber-100 text-amber-600',
    violet: 'bg-primary-100 text-primary-600',
    emerald: 'bg-emerald-100 text-emerald-600',
  };

  return (
    <div className={`flex items-center gap-3 px-4 py-3.5 rounded-2xl border bg-gradient-to-br ${colors[color]}`}>
      <div className={`w-9 h-9 rounded-xl flex items-center justify-center ${iconColors[color]}`}>
        <Icon className="w-4.5 h-4.5" />
      </div>
      <div>
        <p className="text-[11px] text-slate-500 font-medium">{label}</p>
        <p className="text-lg font-bold tabular-nums">{value}</p>
      </div>
    </div>
  );
}
