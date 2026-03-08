/**
 * API 服务层
 */
import axios from 'axios';

const API_BASE_URL = '/api/v1';

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 请求拦截器：添加认证 token。Cookie 会自动发送，localStorage 作为向后兼容回退
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// 标记是否正在刷新 Token，防止并发刷新
let isRefreshing = false;
let failedQueue: Array<{ resolve: (v: unknown) => void; reject: (e: unknown) => void }> = [];

const processQueue = (error: unknown) => {
  failedQueue.forEach(({ resolve, reject }) => {
    if (error) reject(error);
    else resolve(undefined);
  });
  failedQueue = [];
};

// 响应拦截器：401 时尝试刷新 Token，失败再跳转登录
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    
    if (error.response?.status === 401 && !originalRequest._retry) {
      // 登录/刷新接口本身 401 不重试
      if (originalRequest.url?.includes('/auth/login') || originalRequest.url?.includes('/auth/refresh')) {
        return Promise.reject(error);
      }
      
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        }).then(() => api(originalRequest));
      }
      
      originalRequest._retry = true;
      isRefreshing = true;
      
      try {
        const res = await api.post('/auth/refresh', null, { withCredentials: true });
        const { access_token } = res.data;
        if (access_token) {
          localStorage.setItem('access_token', access_token);
        }
        processQueue(null);
        return api(originalRequest);
      } catch (refreshError) {
        processQueue(refreshError);
        localStorage.removeItem('access_token');
        if (typeof window !== 'undefined' && !window.location.pathname.includes('/auth/') && window.location.pathname !== '/') {
          window.location.href = '/auth/login';
        }
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }
    return Promise.reject(error);
  }
);

// 认证 API
export const authAPI = {
  register: (data: { email: string; username: string; password: string; invite_code: string }) =>
    api.post('/auth/register', data),
  
  login: (data: { email: string; password: string }) =>
    api.post('/auth/login', data, { withCredentials: true }),
  
  logout: () => api.post('/auth/logout', null, { withCredentials: true }),
  
  refresh: () => api.post('/auth/refresh', null, { withCredentials: true }),
  
  getMe: () => api.get('/auth/me'),
  
  getCredits: () => api.get('/auth/credits'),
  
  getCreditTransactions: () => api.get('/auth/credits/transactions'),
};

// 上传 API
export const uploadAPI = {
  // 异步上传（推荐）- 立即返回，后台处理
  uploadPDFAsync: (file: File, themeId: number) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('theme_id', themeId.toString());
    return api.post('/upload/pdf/async', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  
  // 查询任务状态
  getTaskStatus: (taskId: string) => {
    return api.get(`/upload/task/${taskId}`);
  },
  
  uploadMultiplePDFs: (files: File[], themeId: number) => {
    const formData = new FormData();
    files.forEach(file => formData.append('files', file));
    formData.append('theme_id', themeId.toString());
    return api.post('/upload/pdfs', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  
  uploadZip: (file: File, themeId: number) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('theme_id', themeId.toString());
    return api.post('/upload/zip', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
};

// 论文 API
export const paperAPI = {
  list: (params?: {
    skip?: number;
    limit?: number;
    search?: string;
    year?: number;
    cluster_id?: number;
    min_score?: number;
  }) => api.get('/papers', { params }),
  
  get: (id: number) => api.get(`/papers/${id}`),
  
  delete: (id: number) => api.delete(`/papers/${id}`),
  
  getPdf: (id: number) => api.get(`/papers/${id}/pdf`, { responseType: 'blob' }),
  
  getStats: () => api.get('/papers/stats/overview'),
  
  getDeepAnalysis: (id: number) => api.get(`/papers/${id}/deep-analysis`),
  
  generateDeepAnalysis: (id: number) => api.post(`/papers/${id}/deep-analysis`),
};

// 聚类分析 API
export const clusteringAPI = {
  run: () => api.post('/clustering/run'),
  getStatus: (taskId: string) => api.get(`/clustering/status/${taskId}`),
  getResults: () => api.get('/clustering/results'),
};

export type ClusterPaper = {
  id: number;
  title: string;
  authors?: string;
  year?: number;
  venue?: string;
  keywords?: string;
  overall_score?: number;
  theme_name?: string;
  cluster_topic?: string;
};

export type ClusterGroup = {
  cluster_id: number;
  topic_keywords: string[];
  paper_count: number;
  papers: ClusterPaper[];
};

export type ClusteringResults = {
  has_results: boolean;
  cluster_count?: number;
  total_papers?: number;
  clustered_papers?: number;
  clusters: ClusterGroup[];
};

// 主题 API（所有方法支持可选 workspaceId，显式指定目标工作区）
function wsHeaders(workspaceId?: number) {
  return workspaceId ? { 'X-Workspace-Id': String(workspaceId) } : {};
}

export const themesAPI = {
  list: (workspaceId?: number) => api.get('/themes', { headers: wsHeaders(workspaceId) }),
  create: (data: { name: string; tags?: string }, workspaceId?: number) =>
    api.post('/themes', data, { headers: wsHeaders(workspaceId) }),
  update: (id: number, data: { name?: string; tags?: string; order?: number }) =>
    api.put(`/themes/${id}`, data),
  delete: (id: number) => api.delete(`/themes/${id}`),
  importConfig: (content: string, workspaceId?: number) =>
    api.post('/themes/import', { content }, { headers: wsHeaders(workspaceId) }),
  exportConfig: (workspaceId?: number) =>
    api.get('/themes/export', { headers: wsHeaders(workspaceId) }),
  generateByAI: (topic: string, bucket_count?: number, workspaceId?: number) =>
    api.post('/themes/generate', { topic, bucket_count: bucket_count || 8 }, { headers: wsHeaders(workspaceId) }),
};

export type ThemeItem = {
  id: number;
  name: string;
  tags?: string;
  paper_count?: number;
};

// 工作区 API
export const workspaceAPI = {
  list: () => api.get('/workspaces'),
  get: (id: number) => api.get(`/workspaces/${id}`),
  create: (data: { name: string; description?: string; scenario_weights?: any; prompt_config?: any }) =>
    api.post('/workspaces', data),
  update: (id: number, data: { name?: string; description?: string; scenario_weights?: any; prompt_config?: any; order?: number }) =>
    api.put(`/workspaces/${id}`, data),
  delete: (id: number) => api.delete(`/workspaces/${id}`),
  activate: (id: number) => api.post(`/workspaces/${id}/activate`),
};

export type WorkspaceItem = {
  id: number;
  name: string;
  description?: string;
  is_default: boolean;
  order: number;
  theme_count: number;
  paper_count: number;
  scenario_weights?: any;
  prompt_config?: any;
  created_at?: string;
  updated_at?: string;
};

// ── 工作区 Header 注入 ──
let _activeWorkspaceId: number | null = null;

export function setActiveWorkspaceId(id: number | null) {
  _activeWorkspaceId = id;
  if (id) {
    localStorage.setItem('active_workspace_id', String(id));
  } else {
    localStorage.removeItem('active_workspace_id');
  }
}

export function getActiveWorkspaceId(): number | null {
  if (_activeWorkspaceId) return _activeWorkspaceId;
  const stored = localStorage.getItem('active_workspace_id');
  if (stored) {
    _activeWorkspaceId = parseInt(stored, 10);
    return _activeWorkspaceId;
  }
  return null;
}

// 请求拦截器：自动注入 X-Workspace-Id header（不覆盖手动设置的值）
api.interceptors.request.use((config) => {
  if (!config.headers['X-Workspace-Id']) {
    const wsId = getActiveWorkspaceId();
    if (wsId) {
      config.headers['X-Workspace-Id'] = String(wsId);
    }
  }
  return config;
});

// 管理员 API
export const adminAPI = {
  // 邀请码
  createInviteCode: (data: { credits?: number; max_uses?: number; note?: string }) =>
    api.post('/admin/invite-codes', data),
  listInviteCodes: () => api.get('/admin/invite-codes'),
  toggleInviteCode: (id: number) => api.patch(`/admin/invite-codes/${id}`),
  deleteInviteCode: (id: number) => api.delete(`/admin/invite-codes/${id}`),

  // 用户管理
  listUsers: () => api.get('/admin/users'),
  adjustCredits: (userId: number, data: { amount: number; description?: string }) =>
    api.post(`/admin/users/${userId}/credits`, data),
  getUserTransactions: (userId: number) => api.get(`/admin/users/${userId}/credits/transactions`),
  toggleUser: (userId: number) => api.patch(`/admin/users/${userId}/toggle`),
  deleteUser: (userId: number) => api.delete(`/admin/users/${userId}`),
  resetUser: (userId: number, data: { amount: number; description?: string }) =>
    api.post(`/admin/users/${userId}/reset`, data),
};

// 导出 API
export const exportAPI = {
  exportPapers: (data: {
    paper_ids?: number[];
    format: 'csv' | 'json' | 'excel';
    include_scenarios?: boolean;
  }) => api.post('/export/papers', data, { responseType: 'blob' }),
};

export type Paper = {
  id: number;
  title: string;
  authors?: string;
  year?: number;
  venue?: string;
  keywords?: string;
  domain_tags?: string;
  paper_type?: string;
  problem?: string;
  methodology?: string;
  conclusion?: string;
  contribution?: string;
  implementation_path?: string;
  score_rigor?: number;
  score_innovation?: number;
  score_practicality?: number;
  score_impact?: number;
  score_readability?: number;
  overall_score?: number;
  recommendation_level?: string;
  scenario_scores?: Record<string, number>;
  cluster_id?: number;
  cluster_topic?: string;
  theme_id?: number;
  theme_name?: string;
  created_at: string;
};

export type TaskStatus = {
  task_id: string;
  status: string;
  progress: number;
  current_step?: string;
  total_items?: number;
  processed_items?: number;
};

export type DeepAnalysis = {
  detailed_summary: string;
  theoretical_framework: {
    theories: string[];
    positioning: string;
    literature_gap: string;
  };
  detailed_methodology: {
    research_design: string;
    data_collection: string;
    data_analysis: string;
    validity: string;
  };
  argument_chain: Array<{
    step: string;
    content: string;
    evidence_type: string;
  }>;
  strengths: string[];
  limitations: string[];
  research_gaps: string[];
  practical_implications: string[];
  key_quotes: Array<{
    quote: string;
    context: string;
  }>;
  critical_review: string;
};

export type Stats = {
  total_papers: number;
  avg_score: number;
  cluster_count: number;
  year_distribution: Record<string, number>;
};
