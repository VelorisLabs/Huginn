import { motion, useScroll, useTransform } from 'framer-motion';
import { useRef } from 'react';
import {
  Sparkles, FileText, Brain, Layers,
  ArrowRight, ChevronRight, Zap, BarChart3,
  Upload, TrendingUp, Star, Shield,
} from 'lucide-react';

/* ─── animation helpers ─── */
const fadeUp = {
  hidden: { opacity: 0, y: 32 },
  visible: (i: number = 0) => ({
    opacity: 1, y: 0,
    transition: { duration: 0.6, delay: i * 0.1, ease: [0.25, 0.46, 0.45, 0.94] as const },
  }),
};

const stagger = { visible: { transition: { staggerChildren: 0.08 } } };

/* ─── data ─── */
const FEATURES = [
  {
    icon: Upload,
    title: 'PDF 智能解析',
    desc: '拖拽上传论文 PDF，AI 自动提取标题、摘要、关键词、引用等结构化信息，秒级入库。',
    color: 'from-blue-500 to-blue-600',
    bg: 'bg-blue-50',
    iconColor: 'text-blue-600',
  },
  {
    icon: Brain,
    title: 'AI 多维评估',
    desc: '基于 LLM 从创新性、方法论、实验质量等维度自动评分，量化每篇论文的研究价值。',
    color: 'from-violet-500 to-purple-600',
    bg: 'bg-violet-50',
    iconColor: 'text-violet-600',
  },
  {
    icon: Layers,
    title: '主题聚类发现',
    desc: '利用文本嵌入和聚类算法自动发现论文间的内在关联，构建你的研究知识图谱。',
    color: 'from-emerald-500 to-teal-600',
    bg: 'bg-emerald-50',
    iconColor: 'text-emerald-600',
  },
  {
    icon: BarChart3,
    title: '研究态势概览',
    desc: '交互式仪表盘展示主题分布、年份趋势、评分热力图，一眼洞察研究领域全貌。',
    color: 'from-amber-500 to-orange-600',
    bg: 'bg-amber-50',
    iconColor: 'text-amber-600',
  },
];

const STEPS = [
  { num: '01', title: '上传论文', desc: '拖拽 PDF 或批量上传 ZIP，支持单篇和批量导入', icon: FileText },
  { num: '02', title: 'AI 自动分析', desc: '智能提取元数据，多维度评分，生成结构化画像', icon: Zap },
  { num: '03', title: '获取洞察', desc: '浏览仪表盘、主题聚类、阅读清单，驱动研究决策', icon: TrendingUp },
];

const STATS = [
  { value: '10x', label: '效率提升', desc: '相比手动阅读筛选' },
  { value: '87+', label: '论文库容量', desc: '持续扩展中' },
  { value: '6', label: '评估维度', desc: 'AI 多角度评分' },
  { value: '<30s', label: '分析耗时', desc: '单篇论文处理' },
];

/* ─── main component ─── */
export default function Landing() {
  const heroRef = useRef<HTMLDivElement>(null);
  const { scrollYProgress } = useScroll({ target: heroRef, offset: ['start start', 'end start'] });
  const heroY = useTransform(scrollYProgress, [0, 1], [0, 120]);
  const heroOpacity = useTransform(scrollYProgress, [0, 0.8], [1, 0]);

  return (
    <div className="min-h-screen bg-white text-slate-900 overflow-x-hidden">
      {/* ═══ NAV ═══ */}
      <nav className="fixed top-0 inset-x-0 z-50 bg-white/80 backdrop-blur-xl border-b border-slate-100">
        <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
          <a href="/" className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary-500 to-primary-700 flex items-center justify-center">
              <Sparkles className="w-4 h-4 text-white" />
            </div>
            <span className="text-lg font-bold tracking-tight">PaperAI</span>
          </a>
          <div className="hidden md:flex items-center gap-8 text-sm text-slate-500">
            <a href="#features" className="hover:text-slate-900 transition-colors">功能</a>
            <a href="#how-it-works" className="hover:text-slate-900 transition-colors">流程</a>
            <a href="#stats" className="hover:text-slate-900 transition-colors">数据</a>
          </div>
          <div className="flex items-center gap-3">
            <a href="/auth/login" className="text-sm font-medium text-slate-600 hover:text-slate-900 transition-colors px-3 py-2">
              登录
            </a>
            <a href="/auth/register" className="btn-primary text-sm !py-2 !px-4">
              免费开始 <ArrowRight className="w-3.5 h-3.5" />
            </a>
          </div>
        </div>
      </nav>

      {/* ═══ HERO ═══ */}
      <section ref={heroRef} className="relative pt-32 pb-24 md:pt-40 md:pb-32 overflow-hidden">
        {/* bg decorations */}
        <div className="absolute inset-0 pointer-events-none">
          <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[900px] h-[600px] bg-gradient-radial from-primary-100/60 via-primary-50/30 to-transparent rounded-full blur-3xl" />
          <div className="absolute top-20 right-0 w-72 h-72 bg-blue-100/40 rounded-full blur-3xl" />
          <div className="absolute bottom-0 left-0 w-96 h-96 bg-violet-100/30 rounded-full blur-3xl" />
          <div className="absolute inset-0 opacity-[0.35]" style={{
            backgroundImage: `url("data:image/svg+xml,%3Csvg width='20' height='20' xmlns='http://www.w3.org/2000/svg'%3E%3Ccircle cx='1' cy='1' r='0.5' fill='rgba(124,58,237,0.07)'/%3E%3C/svg%3E")`,
            backgroundRepeat: 'repeat',
          }} />
        </div>

        <motion.div style={{ y: heroY, opacity: heroOpacity }} className="relative max-w-4xl mx-auto px-6 text-center">
          <motion.div variants={fadeUp} initial="hidden" animate="visible" custom={0}>
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-primary-50 border border-primary-200/60 text-xs font-semibold text-primary-700 mb-6">
              <Star className="w-3 h-3" /> AI-Powered Research Intelligence
            </span>
          </motion.div>

          <motion.h1
            variants={fadeUp} initial="hidden" animate="visible" custom={1}
            className="text-4xl sm:text-5xl md:text-6xl font-bold tracking-tight leading-[1.1] mb-6"
          >
            让 AI 帮你读论文
            <br />
            <span className="bg-gradient-to-r from-primary-600 via-violet-600 to-blue-600 bg-clip-text text-transparent">
              洞察研究趋势
            </span>
          </motion.h1>

          <motion.p
            variants={fadeUp} initial="hidden" animate="visible" custom={2}
            className="text-lg md:text-xl text-slate-500 max-w-2xl mx-auto mb-10 leading-relaxed"
          >
            上传论文 PDF，AI 自动解析、多维评分、主题聚类。
            <br className="hidden sm:block" />
            将数小时的文献筛选工作压缩到几分钟。
          </motion.p>

          <motion.div
            variants={fadeUp} initial="hidden" animate="visible" custom={3}
            className="flex flex-col sm:flex-row items-center justify-center gap-4"
          >
            <a href="/auth/register" className="btn-primary text-base !py-3 !px-8 shadow-lg shadow-primary-500/25">
              免费开始使用 <ArrowRight className="w-4 h-4" />
            </a>
            <a href="#features" className="btn-secondary text-base !py-3 !px-8">
              了解更多 <ChevronRight className="w-4 h-4" />
            </a>
          </motion.div>
        </motion.div>

        {/* product mockup */}
        <motion.div
          variants={fadeUp} initial="hidden" animate="visible" custom={5}
          className="relative max-w-5xl mx-auto mt-16 px-6"
        >
          <div className="relative rounded-2xl border border-slate-200/80 shadow-2xl shadow-slate-900/10 overflow-hidden bg-gradient-to-b from-slate-50 to-white">
            <div className="flex items-center gap-2 px-4 py-3 bg-slate-50 border-b border-slate-100">
              <div className="flex gap-1.5">
                <div className="w-3 h-3 rounded-full bg-red-400" />
                <div className="w-3 h-3 rounded-full bg-amber-400" />
                <div className="w-3 h-3 rounded-full bg-emerald-400" />
              </div>
              <div className="flex-1 text-center">
                <div className="inline-flex items-center gap-1.5 px-3 py-1 bg-white rounded-md border border-slate-200 text-xs text-slate-400">
                  <Shield className="w-3 h-3" /> huginn.velorislab.com
                </div>
              </div>
            </div>
            <div className="p-6 md:p-8">
              {/* mini dashboard mockup */}
              <div className="grid grid-cols-4 gap-4 mb-6">
                {['论文总数', '平均影响力', '研究主题', '待读清单'].map((t, i) => (
                  <div key={t} className="bg-slate-50 rounded-xl p-4 border border-slate-100">
                    <div className="text-xs text-slate-400 mb-1">{t}</div>
                    <div className="text-xl font-bold text-slate-800">
                      {['87', '7.8', '12', '24'][i]}
                    </div>
                  </div>
                ))}
              </div>
              {/* mini chart placeholder */}
              <div className="flex gap-4">
                <div className="flex-1 bg-slate-50 rounded-xl p-4 border border-slate-100 h-40">
                  <div className="text-xs text-slate-400 mb-3">主题分布</div>
                  <div className="space-y-2">
                    {['Transformer 架构', '强化学习', '多模态融合', 'LLM 对齐'].map((t, i) => (
                      <div key={t} className="flex items-center gap-2">
                        <span className="text-[10px] text-slate-500 w-20 truncate">{t}</span>
                        <div className="flex-1 h-3 bg-primary-100 rounded-full overflow-hidden">
                          <div className="h-full bg-primary-500 rounded-full" style={{ width: `${[85, 65, 50, 40][i]}%` }} />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
                <div className="flex-1 bg-slate-50 rounded-xl p-4 border border-slate-100 h-40">
                  <div className="text-xs text-slate-400 mb-3">评分分布</div>
                  <div className="flex items-end gap-2 h-[calc(100%-24px)] pt-2">
                    {[15, 30, 55, 80, 60, 25].map((h, i) => (
                      <div key={i} className="flex-1 flex flex-col justify-end h-full">
                        <div className="bg-emerald-500 rounded-t" style={{ height: `${h}%` }} />
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>
          {/* glow under mockup */}
          <div className="absolute -bottom-8 left-1/2 -translate-x-1/2 w-3/4 h-16 bg-primary-400/10 blur-3xl rounded-full" />
        </motion.div>
      </section>

      {/* ═══ FEATURES ═══ */}
      <section id="features" className="py-24 md:py-32 bg-slate-50/50">
        <div className="max-w-6xl mx-auto px-6">
          <motion.div
            variants={stagger} initial="hidden" whileInView="visible" viewport={{ once: true, margin: '-80px' }}
            className="text-center mb-16"
          >
            <motion.span variants={fadeUp} className="text-sm font-semibold text-primary-600 tracking-wide uppercase">
              Core Features
            </motion.span>
            <motion.h2 variants={fadeUp} className="text-3xl md:text-4xl font-bold tracking-tight mt-3 mb-4">
              重新定义文献管理体验
            </motion.h2>
            <motion.p variants={fadeUp} className="text-slate-500 max-w-xl mx-auto">
              从论文解析到研究洞察，每一步都由 AI 驱动，让你专注于真正的研究工作。
            </motion.p>
          </motion.div>

          <motion.div
            variants={stagger} initial="hidden" whileInView="visible" viewport={{ once: true, margin: '-60px' }}
            className="grid md:grid-cols-2 gap-6"
          >
            {FEATURES.map((f) => (
              <motion.div
                key={f.title} variants={fadeUp}
                className="group relative bg-white rounded-2xl border border-slate-100 p-7 hover:shadow-card-hover hover:border-slate-200 hover:-translate-y-0.5 transition-all duration-300"
              >
                <div className={`w-11 h-11 rounded-xl ${f.bg} flex items-center justify-center mb-4`}>
                  <f.icon className={`w-5 h-5 ${f.iconColor}`} />
                </div>
                <h3 className="text-lg font-semibold text-slate-900 mb-2">{f.title}</h3>
                <p className="text-sm text-slate-500 leading-relaxed">{f.desc}</p>
                <div className="absolute top-0 right-0 w-24 h-24 bg-gradient-to-bl from-slate-50 to-transparent rounded-bl-[40px] opacity-0 group-hover:opacity-100 transition-opacity" />
              </motion.div>
            ))}
          </motion.div>
        </div>
      </section>

      {/* ═══ HOW IT WORKS ═══ */}
      <section id="how-it-works" className="py-24 md:py-32">
        <div className="max-w-5xl mx-auto px-6">
          <motion.div
            variants={stagger} initial="hidden" whileInView="visible" viewport={{ once: true, margin: '-80px' }}
            className="text-center mb-16"
          >
            <motion.span variants={fadeUp} className="text-sm font-semibold text-primary-600 tracking-wide uppercase">
              How It Works
            </motion.span>
            <motion.h2 variants={fadeUp} className="text-3xl md:text-4xl font-bold tracking-tight mt-3 mb-4">
              三步开启智能研究
            </motion.h2>
            <motion.p variants={fadeUp} className="text-slate-500 max-w-xl mx-auto">
              无需复杂配置，上传即用。
            </motion.p>
          </motion.div>

          <motion.div
            variants={stagger} initial="hidden" whileInView="visible" viewport={{ once: true, margin: '-60px' }}
            className="grid md:grid-cols-3 gap-8"
          >
            {STEPS.map((s, i) => (
              <motion.div key={s.num} variants={fadeUp} className="relative text-center">
                <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-primary-500 to-primary-700 flex items-center justify-center mx-auto mb-5 shadow-glow">
                  <s.icon className="w-6 h-6 text-white" />
                </div>
                <span className="text-xs font-bold text-primary-400 tracking-widest">{s.num}</span>
                <h3 className="text-lg font-semibold mt-1 mb-2">{s.title}</h3>
                <p className="text-sm text-slate-500 leading-relaxed">{s.desc}</p>
                {i < STEPS.length - 1 && (
                  <div className="hidden md:block absolute top-7 left-[calc(50%+40px)] w-[calc(100%-80px)] border-t-2 border-dashed border-primary-200" />
                )}
              </motion.div>
            ))}
          </motion.div>
        </div>
      </section>

      {/* ═══ STATS ═══ */}
      <section id="stats" className="py-24 md:py-32 bg-slate-900 text-white">
        <div className="max-w-5xl mx-auto px-6">
          <motion.div
            variants={stagger} initial="hidden" whileInView="visible" viewport={{ once: true, margin: '-80px' }}
            className="text-center mb-16"
          >
            <motion.h2 variants={fadeUp} className="text-3xl md:text-4xl font-bold tracking-tight mb-4">
              用数据说话
            </motion.h2>
            <motion.p variants={fadeUp} className="text-slate-400 max-w-lg mx-auto">
              PaperAI 正在帮助研究者更高效地管理和理解学术文献。
            </motion.p>
          </motion.div>

          <motion.div
            variants={stagger} initial="hidden" whileInView="visible" viewport={{ once: true, margin: '-60px' }}
            className="grid grid-cols-2 md:grid-cols-4 gap-8"
          >
            {STATS.map((s) => (
              <motion.div key={s.label} variants={fadeUp} className="text-center">
                <div className="text-4xl md:text-5xl font-bold bg-gradient-to-r from-primary-400 to-violet-400 bg-clip-text text-transparent mb-2">
                  {s.value}
                </div>
                <div className="text-sm font-semibold text-white mb-1">{s.label}</div>
                <div className="text-xs text-slate-500">{s.desc}</div>
              </motion.div>
            ))}
          </motion.div>
        </div>
      </section>

      {/* ═══ CTA ═══ */}
      <section className="py-24 md:py-32 relative overflow-hidden">
        <div className="absolute inset-0 pointer-events-none">
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[400px] bg-gradient-radial from-primary-100/50 to-transparent rounded-full blur-3xl" />
        </div>
        <motion.div
          variants={stagger} initial="hidden" whileInView="visible" viewport={{ once: true, margin: '-80px' }}
          className="relative max-w-3xl mx-auto px-6 text-center"
        >
          <motion.h2 variants={fadeUp} className="text-3xl md:text-4xl font-bold tracking-tight mb-4">
            准备好提升你的研究效率了吗？
          </motion.h2>
          <motion.p variants={fadeUp} className="text-slate-500 mb-8 text-lg">
            免费注册，立即体验 AI 驱动的论文分析平台。
          </motion.p>
          <motion.div variants={fadeUp} className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <a href="/auth/register" className="btn-primary text-base !py-3 !px-8 shadow-lg shadow-primary-500/25">
              免费注册 <ArrowRight className="w-4 h-4" />
            </a>
            <a href="/auth/login" className="btn-ghost text-base">
              已有账号？登录 <ChevronRight className="w-4 h-4" />
            </a>
          </motion.div>
        </motion.div>
      </section>

      {/* ═══ FOOTER ═══ */}
      <footer className="border-t border-slate-100 py-10">
        <div className="max-w-6xl mx-auto px-6 flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded-md bg-gradient-to-br from-primary-500 to-primary-700 flex items-center justify-center">
              <Sparkles className="w-3 h-3 text-white" />
            </div>
            <span className="text-sm font-semibold text-slate-700">PaperAI</span>
            <span className="text-xs text-slate-400">by VelorisLab</span>
          </div>
          <div className="text-xs text-slate-400">
            &copy; {new Date().getFullYear()} VelorisLab. All rights reserved.
          </div>
        </div>
      </footer>
    </div>
  );
}
