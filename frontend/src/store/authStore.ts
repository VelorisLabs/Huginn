/**
 * 认证状态管理
 */
import { create } from 'zustand';
import { authAPI } from '@/lib/api';

interface User {
  id: number;
  email: string;
  username: string;
  is_active: boolean;
  created_at: string;
}

interface AuthStore {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, username: string, password: string) => Promise<void>;
  logout: () => void;
  checkAuth: () => Promise<void>;
}

// 安全获取 localStorage（处理 SSR）
const getStoredToken = () => {
  if (typeof window !== 'undefined') {
    return localStorage.getItem('access_token');
  }
  return null;
};

export const useAuthStore = create<AuthStore>((set) => ({
  user: null,
  token: getStoredToken(),
  isAuthenticated: !!getStoredToken(),

  login: async (email: string, password: string) => {
    const response = await authAPI.login({ email, password });
    const { access_token } = response.data;
    
    if (typeof window !== 'undefined') {
      localStorage.setItem('access_token', access_token);
    }
    
    // 获取用户信息
    const userResponse = await authAPI.getMe();
    
    set({
      token: access_token,
      user: userResponse.data,
      isAuthenticated: true,
    });
  },

  register: async (email: string, username: string, password: string) => {
    await authAPI.register({ email, username, password });
    // 注册后自动登录
    const response = await authAPI.login({ email, password });
    const { access_token } = response.data;

    if (typeof window !== 'undefined') {
      localStorage.setItem('access_token', access_token);
    }
    
    const userResponse = await authAPI.getMe();
    
    set({
      token: access_token,
      user: userResponse.data,
      isAuthenticated: true,
    });
  },

  logout: async () => {
    try {
      await authAPI.logout();
    } catch {
      // Cookie 清除失败不影响前端登出
    }
    if (typeof window !== 'undefined') {
      localStorage.removeItem('access_token');
    }
    set({ user: null, token: null, isAuthenticated: false });
  },

  checkAuth: async () => {
    try {
      const response = await authAPI.getMe();
      set({ user: response.data, isAuthenticated: true });
    } catch (error) {
      if (typeof window !== 'undefined') {
        localStorage.removeItem('access_token');
      }
      set({ user: null, token: null, isAuthenticated: false });
    }
  },
}));
