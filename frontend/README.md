# 论文分析系统 - 前端

基于 Astro + React + Tailwind CSS 的现代化前端应用。

## 技术栈

- **Astro** - 静态站点生成
- **React 18** - UI 组件
- **Tailwind CSS** - 样式框架
- **TypeScript** - 类型安全
- **Zustand** - 状态管理
- **React Query** - 数据获取和缓存
- **Axios** - HTTP 客户端
- **Recharts** - 图表可视化
- **Lucide React** - 图标库

## 快速开始

### 1. 安装依赖

```bash
cd web/frontend
npm install
```

### 2. 配置环境变量

创建 `.env` 文件：

```env
PUBLIC_API_URL=http://localhost:8000/api/v1
```

### 3. 启动开发服务器

```bash
npm run dev
```

访问：http://localhost:4321

### 4. 构建生产版本

```bash
npm run build
```

## 项目结构

```
frontend/
├── src/
│   ├── components/       # React 组件
│   │   ├── Dashboard.tsx
│   │   ├── UploadZone.tsx
│   │   ├── PaperList.tsx
│   │   └── StatsCard.tsx
│   ├── layouts/          # Astro 布局
│   ├── pages/            # 页面路由
│   ├── lib/              # 工具库
│   │   ├── api.ts       # API 客户端
│   │   └── utils.ts     # 工具函数
│   ├── store/            # 状态管理
│   │   └── authStore.ts
│   └── styles/           # 全局样式
├── package.json
└── astro.config.mjs
```

## 主要功能

- ✅ 用户认证和登录
- ✅ 文件上传（拖拽/点击）
- ✅ 论文列表和搜索
- ✅ 统计数据展示
- ✅ 数据导出
- ✅ 实时任务进度
- ✅ 响应式设计

## 开发注意事项

1. **组件客户端渲染**：需要交互的组件使用 `client:load` 指令
2. **API 代理**：开发环境已配置 `/api` 代理到后端
3. **类型安全**：确保使用 TypeScript 类型定义
4. **样式规范**：使用 Tailwind CSS utility classes

## 部署

参考项目根目录的 Docker 配置或部署文档。
