import { createContext, useContext, useState, useEffect, useCallback, type ReactNode } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { workspaceAPI, setActiveWorkspaceId, getActiveWorkspaceId, type WorkspaceItem } from '@/lib/api';

interface WorkspaceContextType {
  workspaces: WorkspaceItem[];
  activeWorkspace: WorkspaceItem | null;
  isLoading: boolean;
  switchWorkspace: (id: number) => Promise<void>;
  refetchWorkspaces: () => void;
}

const WorkspaceContext = createContext<WorkspaceContextType>({
  workspaces: [],
  activeWorkspace: null,
  isLoading: true,
  switchWorkspace: async () => {},
  refetchWorkspaces: () => {},
});

export function WorkspaceProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient();
  const [activeId, setActiveId] = useState<number | null>(getActiveWorkspaceId());

  const { data, isLoading, refetch } = useQuery({
    queryKey: ['workspaces'],
    queryFn: () => workspaceAPI.list(),
    staleTime: 60_000,
  });

  const workspaces: WorkspaceItem[] = data?.data || [];

  // 自动选择默认工作区（当无 activeId 或 activeId 不在当前用户的工作区列表中时）
  useEffect(() => {
    if (workspaces.length > 0) {
      const match = workspaces.find(w => w.id === activeId);
      if (!match) {
        const defaultWs = workspaces.find(w => w.is_default) || workspaces[0];
        setActiveId(defaultWs.id);
        setActiveWorkspaceId(defaultWs.id);
      }
    }
  }, [workspaces, activeId]);

  const activeWorkspace = workspaces.find(w => w.id === activeId) || null;

  const switchWorkspace = useCallback(async (id: number) => {
    setActiveId(id);
    setActiveWorkspaceId(id);
    try {
      await workspaceAPI.activate(id);
    } catch {
      // 激活失败不影响前端切换
    }
    // 切换后刷新所有数据
    queryClient.invalidateQueries({ queryKey: ['papers'] });
    queryClient.invalidateQueries({ queryKey: ['stats'] });
    queryClient.invalidateQueries({ queryKey: ['themes'] });
    queryClient.invalidateQueries({ queryKey: ['tasks'] });
  }, [queryClient]);

  return (
    <WorkspaceContext.Provider
      value={{
        workspaces,
        activeWorkspace,
        isLoading,
        switchWorkspace,
        refetchWorkspaces: refetch,
      }}
    >
      {children}
    </WorkspaceContext.Provider>
  );
}

export function useWorkspace() {
  return useContext(WorkspaceContext);
}
