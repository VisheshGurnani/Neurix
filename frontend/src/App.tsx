import React, { useState, useEffect, useMemo } from 'react';
import { 
  Terminal, 
  ExternalLink, 
  Check, 
  Copy, 
  ChevronRight, 
  FileCode2, 
  Layers, 
  Cpu, 
  ShieldCheck, 
  RotateCcw, 
  Folder, 
  FileText, 
  SlidersHorizontal,
  ArrowRight,
  GitBranch,
  Clock,
  Sparkles,
  Search,
  BookOpen,
  Code2,
  Box
} from 'lucide-react';

interface DetectedFile {
  path: string;
  priority: number;
  size: number;
  category: 'Documentation' | 'Config' | 'Entry Point' | 'Source' | 'Asset';
  snippet?: string;
}

interface AnalysisResult {
  success: boolean;
  message: string;
  explanation?: string;
  error?: string;
  repository?: string;
  files_analyzed?: number;
  context_truncated?: boolean;
  model_used?: string;
  tech_stack?: string[];
  detected_files?: DetectedFile[];
}

type TabType = 'overview' | 'architecture' | 'stack' | 'files' | 'raw';

const API_BASE_URL = (import.meta.env.VITE_BACKEND_URL || '').replace(/\\/$/, '');
const apiUrl = (path: string) => `${API_BASE_URL}${path}`;

export default function App() {
  const [githubUrl, setGithubUrl] = useState('');
  const [maxFiles, setMaxFiles] = useState(12);
  const [loading, setLoading] = useState(false);
  const [currentStage, setCurrentStage] = useState(0);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<TabType>('overview');
  const [backendStatus, setBackendStatus] = useState<boolean>(true);
  const [backendModel, setBackendModel] = useState<string>('openai/gpt-oss-20b');
  const [copied, setCopied] = useState(false);
  const [selectedFile, setSelectedFile] = useState<DetectedFile | null>(null);
  const [fileFilter, setFileFilter] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [showSettings, setShowSettings] = useState(false);

  // Check health and configuration on mount
  useEffect(() => {
    fetch(apiUrl('/health'))
      .then(res => res.json())
      .then(data => setBackendStatus(data.status === 'healthy'))
      .catch(() => setBackendStatus(false));

    fetch(apiUrl('/config'))
      .then(res => res.json())
      .then(cfg => {
        if (cfg.gemini_model) setBackendModel(cfg.gemini_model);
        else if (cfg.groq_model) setBackendModel(cfg.groq_model);
      })
      .catch(() => {});
  }, []);

  const stages = [
    { title: 'Ingesting repository', detail: 'Connecting to GitHub remote & shallow-cloning HEAD' },
    { title: 'Filtering & mapping', detail: 'Pruning binary artifacts, node_modules, and cache trees' },
    { title: 'Scoring priority files', detail: 'Ranking manifests, entry points, and domain interfaces' },
    { title: 'Bounding context window', detail: 'Structuring UTF-8 text buffers within character limits' },
    { title: 'Synthesizing technical brief', detail: 'Extracting system architecture, patterns, and stack' }
  ];

  const handleAnalyze = async (overrideUrl?: string) => {
    const targetUrl = (overrideUrl || githubUrl).trim();
    if (!targetUrl) {
      setErrorMsg('Please provide a public GitHub repository URL.');
      return;
    }
    if (!targetUrl.toLowerCase().startsWith('https://github.com/')) {
      setErrorMsg('Invalid repository target. URL must begin with https://github.com/owner/repository');
      return;
    }

    setErrorMsg(null);
    setLoading(true);
    setCurrentStage(0);

    // Staged visual progress
    const t1 = setTimeout(() => setCurrentStage(1), 1100);
    const t2 = setTimeout(() => setCurrentStage(2), 2400);
    const t3 = setTimeout(() => setCurrentStage(3), 3900);
    const t4 = setTimeout(() => setCurrentStage(4), 5400);

    try {
      const response = await fetch(apiUrl('/explain'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: targetUrl, max_files: maxFiles })
      });

      clearTimeout(t1);
      clearTimeout(t2);
      clearTimeout(t3);
      clearTimeout(t4);

      const data: AnalysisResult = await response.json();
      if (data.success) {
        setResult(data);
        setErrorMsg(null);
        if (data.detected_files && data.detected_files.length > 0) {
          setSelectedFile(data.detected_files[0]);
        }
        setActiveTab('overview');
        window.scrollTo({ top: 0, behavior: 'smooth' });
      } else {
        setErrorMsg(data.error || data.message || 'Analysis could not be completed.');
      }
    } catch (err: any) {
      clearTimeout(t1);
      clearTimeout(t2);
      clearTimeout(t3);
      clearTimeout(t4);
      setErrorMsg(err.message || 'Network communication error connecting to backend API.');
    } finally {
      setLoading(false);
    }
  };

  const handleCopyBrief = () => {
    if (!result?.explanation) return;
    navigator.clipboard.writeText(result.explanation);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const filteredFiles = useMemo(() => {
    if (!result?.detected_files) return [];
    return result.detected_files.filter(f => {
      const matchesCategory = fileFilter === 'all' || f.category.toLowerCase().replace(' ', '-') === fileFilter;
      const matchesSearch = searchQuery === '' || f.path.toLowerCase().includes(searchQuery.toLowerCase());
      return matchesCategory && matchesSearch;
    });
  }, [result?.detected_files, fileFilter, searchQuery]);

  // Clean formatted markdown renderer for the explanation
  const renderFormattedMarkdown = (markdown: string) => {
    const lines = markdown.split('\n');
    return lines.map((line, idx) => {
      const trimmed = line.trim();
      if (trimmed.startsWith('### ')) {
        return (
          <h4 key={idx} className="text-base font-heading font-semibold text-white mt-6 mb-2 tracking-tight">
            {trimmed.replace('### ', '')}
          </h4>
        );
      }
      if (trimmed.startsWith('## ')) {
        return (
          <h3 key={idx} className="text-xl font-heading font-bold text-white mt-8 mb-3 pb-2 border-b border-white/[0.08] flex items-center gap-2">
            <span className="w-1.5 h-4 bg-blue-500 rounded-full inline-block"></span>
            {trimmed.replace('## ', '')}
          </h3>
        );
      }
      if (trimmed.startsWith('# ')) {
        return (
          <h2 key={idx} className="text-2xl font-heading font-bold text-white mt-8 mb-4">
            {trimmed.replace('# ', '')}
          </h2>
        );
      }
      if (trimmed.startsWith('- ') || trimmed.startsWith('* ')) {
        const itemContent = trimmed.substring(2);
        return (
          <li key={idx} className="ml-5 list-disc text-[#c5cede] my-1.5 leading-relaxed marker:text-blue-500/80">
            <span dangerouslySetInnerHTML={{ __html: formatInline(itemContent) }} />
          </li>
        );
      }
      if (/^\d+\.\s/.test(trimmed)) {
        const numMatch = trimmed.match(/^(\d+)\.\s(.*)/);
        if (numMatch) {
          return (
            <div key={idx} className="flex gap-3 my-2.5 text-[#c5cede] leading-relaxed">
              <span className="font-mono text-blue-400 font-medium text-xs pt-0.5">{numMatch[1]}.</span>
              <span dangerouslySetInnerHTML={{ __html: formatInline(numMatch[2]) }} />
            </div>
          );
        }
      }
      if (!trimmed) {
        return <div key={idx} className="h-2.5" />;
      }
      return (
        <p key={idx} className="text-[#a1b0cb] my-2 leading-relaxed text-sm sm:text-base font-normal" dangerouslySetInnerHTML={{ __html: formatInline(trimmed) }} />
      );
    });
  };

  const formatInline = (str: string) => {
    return str
      .replace(/\*\*(.*?)\*\*/g, '<strong class="text-white font-semibold">$1</strong>')
      .replace(/`([^`]+)`/g, '<code class="bg-[#121824] text-blue-300 px-1.5 py-0.5 rounded text-xs font-mono border border-white/[0.08]">$1</code>');
  };

  return (
    <div className="min-h-screen bg-[#080b11] text-[#ededed] flex flex-col font-sans selection:bg-blue-600/30 selection:text-white relative">
      {/* Subtle architectural grid pattern */}
      <div className="fixed inset-0 tech-grid pointer-events-none z-0"></div>

      {/* Top Navigation */}
      <header className="sticky top-0 z-40 bg-[#080b11]/90 backdrop-blur-md border-b border-white/[0.07] px-6 lg:px-12 py-3.5">
        <div className="max-w-[1480px] mx-auto flex items-center justify-between">
          {/* Brand Mark */}
          <div className="flex items-center gap-4">
            <a 
              href="#" 
              onClick={(e) => { e.preventDefault(); setResult(null); }} 
              className="flex items-center gap-2.5 group cursor-pointer"
            >
              <div className="w-7 h-7 rounded-md bg-[#0e1628] border border-blue-500/30 flex items-center justify-center text-blue-400 group-hover:border-blue-400/60 transition-colors shadow-sm">
                <svg width="14" height="14" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M3 13V3L13 13V3" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
              </div>
              <span className="font-heading font-bold text-sm tracking-wider text-white">NEURIX</span>
            </a>
            <span className="hidden sm:inline-block text-[11px] font-mono text-[#536077] border-l border-white/[0.08] pl-3">
              REPOSITORY INTELLIGENCE
            </span>
          </div>

          {/* Navigation Actions */}
          <div className="flex items-center gap-4 text-xs">
            {result && (
              <button
                onClick={() => {
                  setResult(null);
                  setGithubUrl('');
                }}
                className="hidden sm:flex items-center gap-1.5 text-xs text-[#8e9bb0] hover:text-white bg-white/[0.03] hover:bg-white/[0.07] border border-white/[0.08] px-3 py-1.5 rounded-md transition-colors cursor-pointer"
              >
                <RotateCcw size={12} />
                <span>New Analysis</span>
              </button>
            )}

            <div className="flex items-center gap-2 px-2.5 py-1 rounded-md bg-white/[0.02] border border-white/[0.07] text-[#8e9bb0]">
              <span className={`w-1.5 h-1.5 rounded-full ${backendStatus ? 'bg-emerald-400' : 'bg-red-400'} animate-pulse`}></span>
              <span className="font-mono text-[11px] text-[#8e9bb0]">
                {result?.model_used || backendModel}
              </span>
            </div>

            <a 
              href="https://github.com/VisheshGurnani/Neurix" 
              target="_blank" 
              rel="noreferrer"
              className="text-[#8e9bb0] hover:text-white transition-colors flex items-center gap-1"
            >
              <span>GitHub</span>
              <ExternalLink size={12} className="opacity-70" />
            </a>
          </div>
        </div>
      </header>

      {/* Main Container */}
      <main className="flex-1 relative z-10 w-full max-w-[1480px] mx-auto px-6 lg:px-12 py-8">
        {!result ? (
          /* ========================================================================= */
          /* LANDING STATE: Editorial, Developer-tool Interface                         */
          /* ========================================================================= */
          <div className="space-y-16 lg:space-y-24 pt-4 lg:pt-10">
            {/* Hero Section */}
            <section className="max-w-3xl space-y-5">
              <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded-full bg-blue-500/10 border border-blue-500/20 text-blue-400 text-xs font-mono">
                <span className="w-1.5 h-1.5 rounded-full bg-blue-400"></span>
                <span>Codebase Architecture Engine</span>
              </div>

              <h1 className="text-4xl sm:text-5xl lg:text-6xl font-heading font-bold text-white tracking-tight leading-[1.08]">
                Understand any codebase.<br />
                <span className="text-[#64748b]">Without reading 10,000 lines.</span>
              </h1>

              <p className="text-[#8e9bb0] text-base sm:text-lg leading-relaxed max-w-2xl">
                Neurix shallow-clones public GitHub repositories, ranks architectural manifests, isolates entry points, and produces an authoritative technical brief in seconds.
              </p>
            </section>

            {/* Command Interface Input */}
            <section className="space-y-4">
              <div className="bg-[#0e131f] border border-white/[0.09] hover:border-white/[0.14] focus-within:border-blue-500/60 focus-within:ring-1 focus-within:ring-blue-500/30 rounded-xl p-2 sm:p-2.5 transition-all shadow-xl shadow-black/40">
                <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3">
                  <div className="flex items-center gap-3 px-3 flex-1 text-[#8e9bb0]">
                    <Terminal size={18} className="text-blue-400 shrink-0" />
                    <div className="w-full">
                      <div className="text-[10px] font-mono uppercase tracking-wider text-[#536077]">
                        GitHub repository target
                      </div>
                      <input
                        type="text"
                        value={githubUrl}
                        onChange={(e) => setGithubUrl(e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && !loading && handleAnalyze()}
                        placeholder="https://github.com/owner/repository"
                        className="w-full bg-transparent text-white placeholder-[#3f4a5c] text-sm sm:text-base focus:outline-none font-mono py-0.5"
                        disabled={loading}
                      />
                    </div>
                  </div>

                  <div className="flex items-center gap-2 px-1">
                    <button
                      type="button"
                      onClick={() => setShowSettings(!showSettings)}
                      className="p-2 text-[#8e9bb0] hover:text-white hover:bg-white/[0.05] rounded-lg transition-colors border border-transparent hover:border-white/[0.06] cursor-pointer"
                      title="Adjust analysis depth"
                    >
                      <SlidersHorizontal size={16} />
                    </button>

                    <button
                      onClick={() => handleAnalyze()}
                      disabled={loading}
                      className="bg-blue-600 hover:bg-blue-500 active:scale-[0.99] text-white font-medium text-xs sm:text-sm px-6 py-2.5 rounded-lg flex items-center justify-center gap-2 transition-all disabled:opacity-50 cursor-pointer shadow-sm shadow-blue-600/30"
                    >
                      {loading ? (
                        <>
                          <span className="w-3.5 h-3.5 border-2 border-white/20 border-t-white rounded-full animate-spin"></span>
                          <span>Analyzing...</span>
                        </>
                      ) : (
                        <>
                          <span>Analyze</span>
                          <ArrowRight size={14} />
                        </>
                      )}
                    </button>
                  </div>
                </div>

                {/* Collapsible Settings Row */}
                {showSettings && (
                  <div className="mt-3 pt-3 border-t border-white/[0.06] px-3 pb-1 flex flex-wrap items-center justify-between gap-4 text-xs text-[#8e9bb0]">
                    <div className="flex items-center gap-3">
                      <span>Max files to inspect:</span>
                      <input
                        type="range"
                        min="5"
                        max="30"
                        value={maxFiles}
                        onChange={(e) => setMaxFiles(Number(e.target.value))}
                        className="w-32 accent-blue-500 cursor-pointer"
                      />
                      <span className="font-mono text-white text-xs">{maxFiles} files</span>
                    </div>
                    <span className="text-[11px] text-[#536077]">Priority heuristic sorts high-value files first</span>
                  </div>
                )}
              </div>

              {/* Supporting Metadata & Quick Presets */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs text-[#536077]">
                <div className="flex items-center gap-2">
                  <ShieldCheck size={14} className="text-emerald-400/80" />
                  <span>READ-ONLY ANALYSIS · NO CODE EXECUTION · EPHEMERAL SHALLOW CLONE</span>
                </div>

                <div className="flex items-center gap-2">
                  <span className="text-[#536077]">Curated targets:</span>
                  <button 
                    onClick={() => { setGithubUrl('https://github.com/VisheshGurnani/Neurix'); handleAnalyze('https://github.com/VisheshGurnani/Neurix'); }}
                    className="hover:text-blue-400 font-mono text-[11px] underline underline-offset-2 decoration-white/[0.1] hover:decoration-blue-400 cursor-pointer"
                  >
                    VisheshGurnani/Neurix
                  </button>
                  <span>·</span>
                  <button 
                    onClick={() => { setGithubUrl('https://github.com/pallets/flask'); handleAnalyze('https://github.com/pallets/flask'); }}
                    className="hover:text-blue-400 font-mono text-[11px] underline underline-offset-2 decoration-white/[0.1] hover:decoration-blue-400 cursor-pointer"
                  >
                    pallets/flask
                  </button>
                  <span>·</span>
                  <button 
                    onClick={() => { setGithubUrl('https://github.com/expressjs/express'); handleAnalyze('https://github.com/expressjs/express'); }}
                    className="hover:text-blue-400 font-mono text-[11px] underline underline-offset-2 decoration-white/[0.1] hover:decoration-blue-400 cursor-pointer"
                  >
                    expressjs/express
                  </button>
                </div>
              </div>

              {/* Error Notice */}
              {errorMsg && (
                <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-300 text-xs flex items-start gap-3">
                  <span className="w-1.5 h-1.5 rounded-full bg-red-400 mt-1.5 shrink-0"></span>
                  <div>
                    <strong className="font-semibold text-white">Analysis Halt:</strong> {errorMsg}
                  </div>
                </div>
              )}

              {/* Polished Multi-stage Loading Visualizer */}
              {loading && (
                <div className="mt-8 bg-[#0b0f17] border border-white/[0.08] rounded-xl p-6 space-y-6">
                  <div className="flex items-center justify-between border-b border-white/[0.06] pb-3 text-xs">
                    <div className="flex items-center gap-2 text-white font-medium">
                      <span className="w-2 h-2 rounded-full bg-blue-500 animate-ping"></span>
                      <span>Executing Repository Intelligence Pipeline</span>
                    </div>
                    <span className="font-mono text-[#8e9bb0]">Stage {currentStage + 1} of {stages.length}</span>
                  </div>

                  <div className="space-y-3">
                    {stages.map((stage, idx) => (
                      <div 
                        key={idx}
                        className={`flex items-start gap-3 p-2.5 rounded-lg transition-all ${
                          idx === currentStage 
                            ? 'bg-blue-500/[0.08] border border-blue-500/20 text-white' 
                            : idx < currentStage 
                            ? 'text-emerald-400/90' 
                            : 'text-[#414d62]'
                        }`}
                      >
                        <div className="mt-0.5 shrink-0 font-mono text-xs">
                          {idx < currentStage ? (
                            <Check size={14} className="text-emerald-400" />
                          ) : idx === currentStage ? (
                            <span className="text-blue-400 font-bold">→</span>
                          ) : (
                            <span className="opacity-40">○</span>
                          )}
                        </div>
                        <div className="flex-1">
                          <div className="text-xs font-semibold tracking-tight">{stage.title}</div>
                          <div className="text-[11px] opacity-70 mt-0.5">{stage.detail}</div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </section>

            {/* Workflow Architecture: Editorial Breakdown */}
            <section className="pt-8 border-t border-white/[0.07] space-y-8">
              <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
                <div>
                  <h3 className="text-xs font-mono font-semibold uppercase tracking-widest text-blue-400">
                    SYSTEM METHODOLOGY
                  </h3>
                  <h2 className="text-2xl font-heading font-bold text-white mt-1">
                    How Neurix maps a software system
                  </h2>
                </div>
                <p className="text-xs text-[#8e9bb0] max-w-md">
                  Strictly non-executing. The analysis engine never executes repository code, npm scripts, or builds.
                </p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="bg-[#0e131f] border border-white/[0.07] rounded-xl p-6 space-y-3 relative overflow-hidden group hover:border-white/[0.12] transition-colors">
                  <div className="text-xs font-mono font-bold text-blue-400">01 // INGEST</div>
                  <h4 className="text-base font-heading font-semibold text-white">Shallow-Clone & Prune</h4>
                  <p className="text-xs text-[#8e9bb0] leading-relaxed">
                    Fetches remote HEAD with depth=1. Binary media, bytecode, vendor bundles (node_modules, venv), and test caches are excluded before disk read.
                  </p>
                  <div className="pt-2 font-mono text-[10px] text-[#536077] flex items-center gap-1.5 border-t border-white/[0.05]">
                    <GitBranch size={12} />
                    <span>git clone --depth 1 &lt;target&gt;</span>
                  </div>
                </div>

                <div className="bg-[#0e131f] border border-white/[0.07] rounded-xl p-6 space-y-3 relative overflow-hidden group hover:border-white/[0.12] transition-colors">
                  <div className="text-xs font-mono font-bold text-blue-400">02 // RANK</div>
                  <h4 className="text-base font-heading font-semibold text-white">Heuristic File Scoring</h4>
                  <p className="text-xs text-[#8e9bb0] leading-relaxed">
                    Files are classified by significance: configuration manifests (score 10), entry points (score 8), domain source (score 6), and docs (score 5).
                  </p>
                  <div className="pt-2 font-mono text-[10px] text-[#536077] flex items-center gap-1.5 border-t border-white/[0.05]">
                    <Layers size={12} />
                    <span>Manifest &gt; Entry &gt; Core &gt; Docs</span>
                  </div>
                </div>

                <div className="bg-[#0e131f] border border-white/[0.07] rounded-xl p-6 space-y-3 relative overflow-hidden group hover:border-white/[0.12] transition-colors">
                  <div className="text-xs font-mono font-bold text-blue-400">03 // SYNTHESIZE</div>
                  <h4 className="text-base font-heading font-semibold text-white">Architectural Inference</h4>
                  <p className="text-xs text-[#8e9bb0] leading-relaxed">
                    Text context is structured and synthesized by GenAI models to determine framework architecture, component flow, and critical implementation details.
                  </p>
                  <div className="pt-2 font-mono text-[10px] text-[#536077] flex items-center gap-1.5 border-t border-white/[0.05]">
                    <Cpu size={12} />
                    <span>Structured Markdown brief</span>
                  </div>
                </div>
              </div>
            </section>
          </div>
        ) : (
          /* ========================================================================= */
          /* RESULTS STATE: Repository Intelligence Workspace                           */
          /* ========================================================================= */
          <div className="space-y-8 animate-in fade-in duration-300">
            {/* Workspace Header */}
            <div className="bg-[#0e131f] border border-white/[0.08] rounded-xl p-6 sm:p-8 space-y-6">
              <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6 border-b border-white/[0.07] pb-6">
                <div className="space-y-2">
                  <div className="flex items-center gap-2">
                    <span className="text-[11px] font-mono uppercase tracking-wider text-blue-400 bg-blue-500/10 px-2.5 py-0.5 rounded border border-blue-500/20 font-semibold">
                      Analyzed Repository
                    </span>
                    <span className="text-xs text-[#536077]">·</span>
                    <span className="text-xs text-emerald-400 flex items-center gap-1 font-mono">
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
                      Ready
                    </span>
                  </div>

                  <h1 className="text-2xl sm:text-3xl font-heading font-bold text-white tracking-tight flex items-center gap-3">
                    {result.repository}
                    <a
                      href={`https://github.com/${result.repository}`}
                      target="_blank"
                      rel="noreferrer"
                      className="text-[#8e9bb0] hover:text-white transition-colors"
                      title="Open on GitHub"
                    >
                      <ExternalLink size={18} />
                    </a>
                  </h1>

                  {/* Detected Technologies */}
                  {result.tech_stack && result.tech_stack.length > 0 && (
                    <div className="flex flex-wrap items-center gap-1.5 pt-1">
                      {result.tech_stack.map((tech, i) => (
                        <span 
                          key={i} 
                          className="px-2 py-0.5 rounded bg-white/[0.04] border border-white/[0.08] text-[11px] font-mono text-[#a8b7cf]"
                        >
                          {tech}
                        </span>
                      ))}
                    </div>
                  )}
                </div>

                {/* Workspace Actions */}
                <div className="flex flex-wrap items-center gap-3">
                  <button
                    onClick={handleCopyBrief}
                    className="flex items-center gap-1.5 px-3.5 py-2 rounded-lg bg-white/[0.03] hover:bg-white/[0.08] border border-white/[0.09] text-xs font-medium text-white transition-colors cursor-pointer"
                  >
                    {copied ? <Check size={14} className="text-emerald-400" /> : <Copy size={14} />}
                    <span>{copied ? 'Copied to Clipboard' : 'Copy Brief'}</span>
                  </button>

                  <button
                    onClick={() => {
                      setResult(null);
                      setGithubUrl('');
                    }}
                    className="flex items-center gap-1.5 px-3.5 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-xs font-medium text-white transition-colors cursor-pointer shadow-sm shadow-blue-600/30"
                  >
                    <RotateCcw size={14} />
                    <span>Analyze Another</span>
                  </button>
                </div>
              </div>

              {/* Compact Metrics Strip */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs">
                <div>
                  <div className="text-[11px] text-[#536077] uppercase tracking-wider font-mono">Files Scored</div>
                  <div className="text-base font-semibold text-white mt-1 font-mono">
                    {result.files_analyzed || 0} files
                  </div>
                </div>

                <div>
                  <div className="text-[11px] text-[#536077] uppercase tracking-wider font-mono">Context Status</div>
                  <div className="text-base font-semibold text-white mt-1">
                    {result.context_truncated ? 'Trimmed (60k chars)' : 'Full context'}
                  </div>
                </div>

                <div>
                  <div className="text-[11px] text-[#536077] uppercase tracking-wider font-mono">Model Engine</div>
                  <div className="text-base font-semibold text-white mt-1 font-mono text-blue-400">
                    {result.model_used || 'gemini-2.5-flash'}
                  </div>
                </div>

                <div>
                  <div className="text-[11px] text-[#536077] uppercase tracking-wider font-mono">Analysis Mode</div>
                  <div className="text-base font-semibold text-emerald-400 mt-1 flex items-center gap-1">
                    <ShieldCheck size={14} />
                    <span>Read-only</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Navigation Tabs */}
            <div className="flex border-b border-white/[0.08] gap-6 text-xs sm:text-sm overflow-x-auto scrollbar-none">
              <button
                onClick={() => setActiveTab('overview')}
                className={`pb-3 font-medium transition-colors border-b-2 whitespace-nowrap cursor-pointer flex items-center gap-2 ${
                  activeTab === 'overview'
                    ? 'border-blue-500 text-white font-semibold'
                    : 'border-transparent text-[#8e9bb0] hover:text-white'
                }`}
              >
                <BookOpen size={15} />
                <span>Executive Overview</span>
              </button>

              <button
                onClick={() => setActiveTab('architecture')}
                className={`pb-3 font-medium transition-colors border-b-2 whitespace-nowrap cursor-pointer flex items-center gap-2 ${
                  activeTab === 'architecture'
                    ? 'border-blue-500 text-white font-semibold'
                    : 'border-transparent text-[#8e9bb0] hover:text-white'
                }`}
              >
                <Layers size={15} />
                <span>Architecture Diagram</span>
              </button>

              <button
                onClick={() => setActiveTab('stack')}
                className={`pb-3 font-medium transition-colors border-b-2 whitespace-nowrap cursor-pointer flex items-center gap-2 ${
                  activeTab === 'stack'
                    ? 'border-blue-500 text-white font-semibold'
                    : 'border-transparent text-[#8e9bb0] hover:text-white'
                }`}
              >
                <Box size={15} />
                <span>Technology Stack</span>
              </button>

              <button
                onClick={() => setActiveTab('files')}
                className={`pb-3 font-medium transition-colors border-b-2 whitespace-nowrap cursor-pointer flex items-center gap-2 ${
                  activeTab === 'files'
                    ? 'border-blue-500 text-white font-semibold'
                    : 'border-transparent text-[#8e9bb0] hover:text-white'
                }`}
              >
                <FileCode2 size={15} />
                <span>Important Files ({result.detected_files?.length || 0})</span>
              </button>

              <button
                onClick={() => setActiveTab('raw')}
                className={`pb-3 font-medium transition-colors border-b-2 whitespace-nowrap cursor-pointer flex items-center gap-2 ${
                  activeTab === 'raw'
                    ? 'border-blue-500 text-white font-semibold'
                    : 'border-transparent text-[#8e9bb0] hover:text-white'
                }`}
              >
                <Code2 size={15} />
                <span>Raw Markdown</span>
              </button>
            </div>

            {/* TAB 1: EXECUTIVE OVERVIEW */}
            {activeTab === 'overview' && (
              <div className="bg-[#0e131f] border border-white/[0.08] rounded-xl p-6 sm:p-10 space-y-4">
                <div className="prose prose-invert max-w-none text-[#a1b0cb] leading-relaxed">
                  {result.explanation ? renderFormattedMarkdown(result.explanation) : (
                    <div className="text-sm text-[#8e9bb0]">No explanation generated.</div>
                  )}
                </div>
              </div>
            )}

            {/* TAB 2: ARCHITECTURE DIAGRAM */}
            {activeTab === 'architecture' && (
              <div className="bg-[#0e131f] border border-white/[0.08] rounded-xl p-6 sm:p-10 space-y-8">
                <div className="border-b border-white/[0.07] pb-4">
                  <h3 className="text-lg font-heading font-bold text-white">System Architecture & Execution Flow</h3>
                  <p className="text-xs text-[#8e9bb0] mt-1">
                    Visual model of this codebase's operational boundary, controller patterns, and services.
                  </p>
                </div>

                {/* Polished Visual Flowchart */}
                <div className="space-y-6">
                  <div className="grid grid-cols-1 md:grid-cols-4 gap-4 relative">
                    {/* Step 1: External Inputs */}
                    <div className="bg-[#090d15] border border-white/[0.08] rounded-xl p-5 space-y-3">
                      <div className="text-[10px] font-mono text-blue-400 font-semibold uppercase">Layer 01</div>
                      <div className="font-heading font-semibold text-white text-sm">Client / Consumers</div>
                      <p className="text-xs text-[#8e9bb0] leading-relaxed">
                        Browser interface, CLI tools, external webhooks, or API requests accessing the system endpoints.
                      </p>
                      <div className="pt-2 text-[11px] font-mono text-[#536077]">
                        HTTP · REST · SPA · CLI
                      </div>
                    </div>

                    {/* Step 2: Ingress / Controllers */}
                    <div className="bg-[#090d15] border border-blue-500/30 rounded-xl p-5 space-y-3 relative">
                      <div className="text-[10px] font-mono text-blue-400 font-semibold uppercase">Layer 02</div>
                      <div className="font-heading font-semibold text-white text-sm">Entry & Routing</div>
                      <p className="text-xs text-[#8e9bb0] leading-relaxed">
                        Top-level application entry points, router dispatchers, middleware pipelines, and request validation.
                      </p>
                      <div className="pt-2 text-[11px] font-mono text-blue-400">
                        main.py / server.ts / app.py
                      </div>
                    </div>

                    {/* Step 3: Domain Services */}
                    <div className="bg-[#090d15] border border-white/[0.08] rounded-xl p-5 space-y-3">
                      <div className="text-[10px] font-mono text-blue-400 font-semibold uppercase">Layer 03</div>
                      <div className="font-heading font-semibold text-white text-sm">Services & Logic</div>
                      <p className="text-xs text-[#8e9bb0] leading-relaxed">
                        Core domain implementations, processing routines, file operations, algorithms, and business logic.
                      </p>
                      <div className="pt-2 text-[11px] font-mono text-[#536077]">
                        /services · /core · /lib
                      </div>
                    </div>

                    {/* Step 4: Storage & External APIs */}
                    <div className="bg-[#090d15] border border-white/[0.08] rounded-xl p-5 space-y-3">
                      <div className="text-[10px] font-mono text-blue-400 font-semibold uppercase">Layer 04</div>
                      <div className="font-heading font-semibold text-white text-sm">Storage & External</div>
                      <p className="text-xs text-[#8e9bb0] leading-relaxed">
                        Database engines, cache instances, upstream AI services, or file system persistence layers.
                      </p>
                      <div className="pt-2 text-[11px] font-mono text-[#536077]">
                        Databases · Models · APIs
                      </div>
                    </div>
                  </div>

                  {/* Flow Arrow Indicators */}
                  <div className="hidden md:flex items-center justify-around px-8 text-xs font-mono text-blue-400/80">
                    <span>↓ Ingress</span>
                    <span>↓ Routing</span>
                    <span>↓ Execution</span>
                    <span>↓ Persistence</span>
                  </div>

                  <div className="bg-[#090d15] border border-white/[0.06] rounded-xl p-5 space-y-2 text-xs text-[#8e9bb0]">
                    <div className="font-semibold text-white">How Neurix Parsed This Architecture:</div>
                    <p className="leading-relaxed">
                      Neurix performed static inspection of manifests (`package.json`, `requirements.txt`, etc.), identified entry points (`server.ts`, `main.py`, etc.), mapped internal modules without runtime execution, and provided this topology.
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* TAB 3: TECHNOLOGY STACK */}
            {activeTab === 'stack' && (
              <div className="bg-[#0e131f] border border-white/[0.08] rounded-xl p-6 sm:p-10 space-y-6">
                <div>
                  <h3 className="text-lg font-heading font-bold text-white">Detected Technology Ecosystem</h3>
                  <p className="text-xs text-[#8e9bb0] mt-1">
                    Inferred from repository manifests, imports, and source file extensions.
                  </p>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 pt-2">
                  {result.tech_stack && result.tech_stack.length > 0 ? (
                    result.tech_stack.map((tech, i) => (
                      <div 
                        key={i}
                        className="bg-[#090d15] border border-white/[0.07] rounded-xl p-4 flex items-center justify-between"
                      >
                        <div className="flex items-center gap-3">
                          <div className="w-8 h-8 rounded-lg bg-blue-500/10 border border-blue-500/20 flex items-center justify-center text-blue-400 font-mono text-xs font-bold">
                            {tech.charAt(0)}
                          </div>
                          <div>
                            <div className="text-sm font-semibold text-white">{tech}</div>
                            <div className="text-[11px] text-[#536077]">Active dependency / language</div>
                          </div>
                        </div>
                        <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
                      </div>
                    ))
                  ) : (
                    <div className="text-xs text-[#8e9bb0] col-span-3">No specific framework indicators detected.</div>
                  )}
                </div>
              </div>
            )}

            {/* TAB 4: IMPORTANT FILES EXPLORER */}
            {activeTab === 'files' && (
              <div className="bg-[#0e131f] border border-white/[0.08] rounded-xl overflow-hidden grid grid-cols-1 lg:grid-cols-12 min-h-[500px]">
                {/* File List Column */}
                <div className="lg:col-span-5 border-b lg:border-b-0 lg:border-r border-white/[0.08] p-4 sm:p-6 space-y-4">
                  <div className="flex items-center justify-between">
                    <h4 className="text-sm font-heading font-semibold text-white">Analyzed File Hierarchy</h4>
                    <span className="text-xs font-mono text-blue-400">{filteredFiles.length} files</span>
                  </div>

                  {/* Filter Pills */}
                  <div className="flex flex-wrap gap-1.5 text-xs">
                    {(['all', 'entry-point', 'config', 'source', 'documentation'] as const).map(cat => (
                      <button
                        key={cat}
                        onClick={() => setFileFilter(cat)}
                        className={`px-2.5 py-1 rounded-md text-[11px] font-mono transition-colors cursor-pointer ${
                          fileFilter === cat 
                            ? 'bg-blue-600 text-white' 
                            : 'bg-white/[0.03] text-[#8e9bb0] hover:text-white border border-white/[0.06]'
                        }`}
                      >
                        {cat === 'all' ? 'All Files' : cat.replace('-', ' ')}
                      </button>
                    ))}
                  </div>

                  {/* Search Bar */}
                  <div className="relative">
                    <Search size={14} className="absolute left-3 top-2.5 text-[#536077]" />
                    <input
                      type="text"
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      placeholder="Filter file path..."
                      className="w-full bg-[#090d15] border border-white/[0.08] rounded-lg pl-8 pr-3 py-1.5 text-xs text-white placeholder-[#455064] focus:outline-none focus:border-blue-500/50"
                    />
                  </div>

                  {/* Files List */}
                  <div className="space-y-1.5 max-h-[480px] overflow-y-auto pr-1">
                    {filteredFiles.map((file, i) => (
                      <button
                        key={i}
                        onClick={() => setSelectedFile(file)}
                        className={`w-full text-left p-2.5 rounded-lg text-xs font-mono transition-all flex items-center justify-between cursor-pointer ${
                          selectedFile?.path === file.path
                            ? 'bg-blue-500/15 border border-blue-500/40 text-white'
                            : 'bg-[#090d15]/60 hover:bg-[#090d15] text-[#8e9bb0] border border-transparent'
                        }`}
                      >
                        <div className="flex items-center gap-2 truncate pr-2">
                          <FileText size={13} className={selectedFile?.path === file.path ? 'text-blue-400' : 'text-[#536077]'} />
                          <span className="truncate">{file.path}</span>
                        </div>
                        <div className="flex items-center gap-2 shrink-0">
                          <span className="text-[10px] text-[#536077]">
                            {(file.size / 1024).toFixed(1)}KB
                          </span>
                        </div>
                      </button>
                    ))}
                  </div>
                </div>

                {/* File Snippet Preview Column */}
                <div className="lg:col-span-7 p-4 sm:p-6 flex flex-col justify-between bg-[#080b11]">
                  {selectedFile ? (
                    <div className="space-y-4">
                      <div className="flex items-center justify-between border-b border-white/[0.08] pb-3">
                        <div className="flex items-center gap-2">
                          <FileCode2 size={16} className="text-blue-400" />
                          <span className="text-xs font-mono font-semibold text-white">{selectedFile.path}</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <span className="text-[10px] px-2 py-0.5 rounded bg-blue-500/10 text-blue-400 border border-blue-500/20 font-mono">
                            {selectedFile.category}
                          </span>
                          <span className="text-[10px] text-[#536077] font-mono">
                            Priority: {selectedFile.priority}/10
                          </span>
                        </div>
                      </div>

                      <div className="space-y-2">
                        <div className="text-[11px] font-mono text-[#536077] uppercase tracking-wider">
                          Inspection Snippet
                        </div>
                        <pre className="bg-[#0d131f] border border-white/[0.07] rounded-lg p-4 font-mono text-xs text-[#c5cede] overflow-x-auto max-h-[380px] leading-relaxed">
                          {selectedFile.snippet || '// No text preview available for this file'}
                        </pre>
                      </div>
                    </div>
                  ) : (
                    <div className="h-full flex items-center justify-center text-xs text-[#536077]">
                      Select a file to inspect its content preview
                    </div>
                  )}

                  <div className="pt-4 border-t border-white/[0.06] text-[11px] text-[#536077] flex items-center justify-between">
                    <span>Read safely as static text stream</span>
                    <span>Bounded 50KB read limit</span>
                  </div>
                </div>
              </div>
            )}

            {/* TAB 5: RAW MARKDOWN */}
            {activeTab === 'raw' && (
              <div className="bg-[#0e131f] border border-white/[0.08] rounded-xl p-6 sm:p-8 space-y-4">
                <div className="flex items-center justify-between border-b border-white/[0.07] pb-3">
                  <span className="text-xs font-mono text-[#8e9bb0]">Raw AI Studio Model Response</span>
                  <button
                    onClick={handleCopyBrief}
                    className="flex items-center gap-1.5 text-xs text-blue-400 hover:text-blue-300 font-mono transition-colors cursor-pointer"
                  >
                    {copied ? <Check size={13} /> : <Copy size={13} />}
                    <span>{copied ? 'Copied' : 'Copy Raw Text'}</span>
                  </button>
                </div>

                <pre className="bg-[#090d15] border border-white/[0.07] rounded-lg p-5 font-mono text-xs text-[#c5cede] overflow-x-auto whitespace-pre-wrap leading-relaxed max-h-[600px]">
                  {result.explanation}
                </pre>
              </div>
            )}
          </div>
        )}
      </main>

      {/* Global Minimalist Footer */}
      <footer className="border-t border-white/[0.07] mt-16 py-6 px-6 lg:px-12 text-xs text-[#536077]">
        <div className="max-w-[1480px] mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <span className="font-heading font-bold text-white tracking-wider">NEURIX</span>
            <span>—</span>
            <span>Understand any codebase before you touch it.</span>
          </div>

          <div className="flex items-center gap-4 text-[11px] font-mono">
            <span>Ephemeral Container Runtime</span>
            <span>·</span>
            <span>Node.js v22</span>
            <span>·</span>
            <span>GenAI Models</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
