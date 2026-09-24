import { useEffect, useState } from 'react';
import { Activity, ArrowUpRight, BarChart3, CheckCircle2, ChevronRight, CircleAlert, Clock3, Database, ExternalLink, FileSearch, Gauge, History, LoaderCircle, LockKeyhole, Menu, Radar, ShieldCheck, Sparkles, X, XCircle } from 'lucide-react';
import { Bar, BarChart, CartesianGrid, Cell, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';

const API_BASE = import.meta.env.VITE_API_BASE || '';
const navItems = [
  { id: 'overview', label: 'Overview', icon: Gauge },
  { id: 'analysis', label: 'Live analysis', icon: Radar },
  { id: 'benchmark', label: 'Benchmark ML', icon: Sparkles },
  { id: 'history', label: 'History', icon: History },
  { id: 'model', label: 'Model registry', icon: Database }
];

async function api(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, { ...options, headers: { 'Content-Type': 'application/json', ...(options.headers || {}) } });
  const body = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(body.error || body.detail || `Request failed (${response.status})`);
  return body;
}

function App() {
  const [active, setActive] = useState('overview');
  const [analysis, setAnalysis] = useState(null);
  const [selectedId, setSelectedId] = useState(null);
  const [history, setHistory] = useState([]);
  const [stats, setStats] = useState(null);
  const [model, setModel] = useState(null);
  const [serverState, setServerState] = useState('checking');
  const [mobileNav, setMobileNav] = useState(false);

  async function refreshHistory() {
    const [historyData, statsData] = await Promise.all([api('/api/history'), api('/api/statistics')]);
    setHistory(historyData.results || []);
    setStats(statsData);
  }

  useEffect(() => {
    Promise.all([api('/api/health'), api('/api/model/info'), refreshHistory()])
      .then(([, modelData]) => { setModel(modelData); setServerState('online'); })
      .catch(() => setServerState('offline'));
  }, []);

  async function analyzeUrl(url) {
    const result = await api('/api/analyze', { method: 'POST', body: JSON.stringify({ url }) });
    setAnalysis(result);
    setSelectedId(result.id);
    await refreshHistory();
    setActive('analysis');
    return result;
  }

  async function openHistory(id) {
    const result = await api(`/api/analysis/${id}`);
    setAnalysis(result);
    setSelectedId(id);
    setActive('analysis');
  }

  function navigate(id) { setActive(id); setMobileNav(false); }

  return <div className="app-shell">
    <aside className={`sidebar ${mobileNav ? 'is-open' : ''}`}>
      <div className="brand"><span className="brand-mark"><ShieldCheck size={18} /></span><span><strong>TrustGuard</strong><small>Digital trust framework</small></span><button className="icon-button mobile-close" onClick={() => setMobileNav(false)} aria-label="Close navigation"><X size={18} /></button></div>
      <nav className="main-nav">{navItems.map(({ id, label, icon: Icon }) => <button key={id} className={active === id ? 'nav-item active' : 'nav-item'} onClick={() => navigate(id)}><Icon size={17} /><span>{label}</span>{active === id && <ChevronRight size={14} />}</button>)}</nav>
      <div className="sidebar-foot"><div className="system-status"><span className={`status-dot ${serverState}`}></span><span>API {serverState === 'online' ? 'operational' : serverState === 'offline' ? 'unavailable' : 'checking'}</span></div><p>Analytical estimates from observable evidence. No safety guarantee.</p></div>
    </aside>
    {mobileNav && <button className="scrim" onClick={() => setMobileNav(false)} aria-label="Close navigation"></button>}
    <main className="main-content">
      <header className="topbar"><button className="icon-button menu-button" onClick={() => setMobileNav(true)} aria-label="Open navigation"><Menu size={20} /></button><div className="breadcrumb">TrustGuard <span>/</span> {navItems.find(item => item.id === active)?.label}</div><div className="topbar-right"><span className="version">BENCHMARK <strong>{model?.model_version || 'not loaded'}</strong></span><span className={`api-pill ${serverState}`}><span className="status-dot"></span>{serverState === 'online' ? 'Connected' : serverState === 'offline' ? 'Offline' : 'Checking'}</span></div></header>
      <div className="page-wrap">
        {serverState === 'offline' && <div className="alert error"><CircleAlert size={17} /><span>Backend unavailable. Start the Python API to load live evidence and benchmark explanations.</span></div>}
        {active === 'overview' && <Overview onAnalyze={() => navigate('analysis')} stats={stats} history={history} onOpen={openHistory} />}
        {active === 'analysis' && <AnalysisPage analysis={analysis} onAnalyze={analyzeUrl} onOpenHistory={openHistory} />}
        {active === 'benchmark' && <BenchmarkPage />}
        {active === 'history' && <HistoryPage history={history} onOpen={openHistory} />}
        {active === 'model' && <ModelPage model={model} />}
      </div>
    </main>
  </div>;
}

function PageIntro({ eyebrow, title, description, children }) { return <div className="page-intro"><div><span className="eyebrow">{eyebrow}</span><h1>{title}</h1><p>{description}</p></div>{children}</div>; }

function Overview({ onAnalyze, stats, history, onOpen }) {
  return <><PageIntro eyebrow="Digital trust analytics" title={<>Read the signals<br /><em>behind a website.</em></>} description="TrustGuard assembles observable security, reputation, transparency, reliability, and URL evidence into a clear analytical estimate."><div className="intro-stamp"><Radar size={18} /><span>Evidence-led<br />by design</span></div></PageIntro>
    <section className="hero-grid"><div className="hero-panel"><div className="panel-kicker"><span className="pulse"></span> LIVE WEBSITE ANALYSIS</div><h2>Start with a URL.<br /><span>Leave with context.</span></h2><p>Run a bounded, non-invasive assessment of a public website and see exactly which signals were observed, unavailable, or not detected.</p><button className="primary-button" onClick={onAnalyze}>Analyze a website <ArrowUpRight size={17} /></button></div><div className="hero-aside"><div className="aside-label">CURRENT CAPABILITY</div><div className="capability-list"><Capability icon={LockKeyhole} title="Security posture" text="TLS and header evidence" /><Capability icon={Activity} title="Site reliability" text="Response and availability" /><Capability icon={Sparkles} title="Benchmark XAI" text="Real UCI model + SHAP" /></div></div></section>
    <section className="metric-row"><Metric label="Total analyses" value={stats?.total_analyses ?? '—'} icon={FileSearch} /><Metric label="Average trust score" value={stats?.average_trust_score ?? '—'} icon={BarChart3} /><Metric label="High observed risk" value={stats?.high_risk_analyses ?? '—'} icon={CircleAlert} tone="coral" /><Metric label="Latest assessment" value={history.length ? formatDate(history[0].created_at) : '—'} icon={Clock3} /></section>
    <section className="section-block"><div className="section-header"><div><span className="eyebrow">WORKSPACE</span><h2>Recent assessments</h2></div><button className="quiet-button" onClick={() => onOpen(history[0]?.id)} disabled={!history.length}>View latest <ArrowUpRight size={15} /></button></div><HistoryTable history={history.slice(0, 4)} onOpen={onOpen} /></section>
    <div className="disclaimer-band"><CircleAlert size={16} /><span>This score is an analytical estimate based on observable indicators and available evidence. It does not guarantee website safety.</span></div>
  </>;
}

function AnalysisPage({ analysis, onAnalyze }) {
  const [url, setUrl] = useState('https://example.com'); const [loading, setLoading] = useState(false); const [error, setError] = useState('');
  async function submit(event) { event.preventDefault(); setLoading(true); setError(''); try { await onAnalyze(url); } catch (err) { setError(err.message); } finally { setLoading(false); } }
  return <><PageIntro eyebrow="Live trust analysis" title="See the evidence." description="Inspect one public URL at a time. Every panel below is populated by the live analysis response, never a demo result." />
    <form className="analysis-form" onSubmit={submit}><div className="field-wrap"><label htmlFor="analysis-url">Website or application URL</label><div className="input-shell"><LockKeyhole size={16} /><input id="analysis-url" value={url} onChange={event => setUrl(event.target.value)} placeholder="https://your-application.com" /></div></div><button className="primary-button" disabled={loading || !url.trim()}>{loading ? <><LoaderCircle className="spin" size={17} /> Assessing</> : <>Analyze URL <ArrowUpRight size={17} /></>}</button></form>
    {error && <div className="alert error"><XCircle size={17} /><span>{error}</span></div>}
    {!analysis && !loading && <EmptyState icon={Radar} title="No live analysis selected" text="Enter a public URL above to collect the first evidence snapshot." />}
    {analysis && <LiveResult analysis={analysis} />}
  </>;
}

function LiveResult({ analysis }) {
  const categories = Object.entries(analysis.category_scores || {}); const security = analysis.features?.security || {}; const reliability = analysis.features?.reliability || {}; const transparency = analysis.features?.transparency || {};
  return <div className="result-stack"><div className="result-head"><div><span className="eyebrow">RESULT / {analysis.id.slice(0, 8)}</span><h2 className="result-url">{analysis.url}</h2><span className={`risk-tag ${analysis.risk_level}`}>{formatRisk(analysis.risk_level)}</span></div><div className="score-display"><span>TRUST SCORE</span><strong>{analysis.trust_score}</strong><small>/ 100</small></div></div><div className="section-header compact"><div><span className="eyebrow">LIVE TRUST ANALYSIS</span><h2>Observed dimensions</h2></div><span className="observed-label"><span className="status-dot online"></span>{analysis.status}</span></div><div className="category-grid dashboard-grid">{categories.map(([name, value]) => <CategoryCard key={name} name={name} value={value} />)}</div><div className="detail-grid"><EvidenceCard title="Security posture" icon={LockKeyhole} items={[["HTTPS", security.https ? 'detected' : 'not detected'], ["TLS certificate", security.tls?.status || 'unknown'], ["TLS version", security.tls?.tls_version || 'unavailable'], ["Header score", security.header_score == null ? 'unknown' : `${security.header_score}/100`]]} /><EvidenceCard title="Reliability" icon={Activity} items={[["HTTP status", reliability.http_status || 'unavailable'], ["Response time", reliability.response_time_ms ? `${reliability.response_time_ms} ms` : 'unavailable'], ["Redirects", reliability.redirect_count], ["Availability", reliability.availability]]} /><EvidenceCard title="Transparency" icon={FileSearch} items={[["Privacy policy", transparency.privacy_policy], ["Contact page", transparency.contact_page], ["About page", transparency.about_page], ["Terms page", transparency.terms_page]]} /><EvidenceCard title="Security headers" icon={ShieldCheck} items={Object.entries(security.headers || {}).slice(0, 4)} /></div><div className="benchmark-callout"><Sparkles size={19} /><div><span className="eyebrow">BENCHMARK ML EXPLAINABILITY</span><strong>Not applied to this live URL</strong><p>{analysis.ml_prediction?.message || 'The UCI benchmark feature schema is not compatible with live TrustGuard evidence.'}</p></div></div></div>;
}

function BenchmarkPage() {
  const [global, setGlobal] = useState(null); const [local, setLocal] = useState(null); const [sample, setSample] = useState('0'); const [loading, setLoading] = useState(true); const [error, setError] = useState('');
  useEffect(() => { api('/api/ml/feature-importance').then(setGlobal).catch(err => setError(err.message)).finally(() => setLoading(false)); }, []);
  async function loadSample(event) { event?.preventDefault(); setError(''); try { setLocal(await api(`/api/ml/explanation/test-${String(Math.max(0, Math.min(339, Number(sample) || 0))).padStart(5, '0')}`)); } catch (err) { setError(err.message); } }
  const chartData = global?.importance?.slice(0, 10).map(item => ({ name: item.feature, value: Number(item.mean_absolute_shap_value.toFixed(4)) })).reverse() || [];
  return <><PageIntro eyebrow="Benchmark ML explainability" title="Open the model." description="Explore real SHAP values from the corrected UCI phishing-risk benchmark. This is not a live website prediction and does not explain the complete Digital Trust Score." />
    {loading && <LoadingState text="Loading global SHAP importance from the backend..." />}{error && <div className="alert error"><CircleAlert size={17} />{error}</div>}
    {global && <><div className="benchmark-meta"><span><strong>{global.model}</strong> / {global.model_version}</span><span>{global.sample_count} test samples · {global.feature_count} features</span></div><section className="section-block benchmark-chart"><div className="section-header"><div><span className="eyebrow">GLOBAL IMPORTANCE</span><h2>Mean absolute SHAP value</h2></div><span className="scope-chip">UCI TEST SET</span></div><div className="chart-wrap"><ResponsiveContainer width="100%" height={350}><BarChart data={chartData} layout="vertical" margin={{ left: 20, right: 30 }}><CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#d9ddd4" /><XAxis type="number" tick={{ fill: '#788078', fontSize: 11 }} /><YAxis dataKey="name" type="category" width={155} tick={{ fill: '#4f5b54', fontSize: 11 }} /><Tooltip formatter={value => [value, 'mean |SHAP|']} /><Bar dataKey="value" fill="#e46d52" radius={[0, 3, 3, 0]} /></BarChart></ResponsiveContainer></div></section><div className="benchmark-grid"><section className="section-block importance-list"><div className="section-header"><div><span className="eyebrow">RANKED FEATURES</span><h2>What moves the model</h2></div></div>{global.importance.slice(0, 8).map(item => <div className="importance-row" key={item.feature}><span className="rank">{String(item.rank).padStart(2, '0')}</span><span className="importance-name">{item.feature}</span><strong>{item.mean_absolute_shap_value.toFixed(4)}</strong></div>)}</section><section className="section-block sample-panel"><div className="section-header"><div><span className="eyebrow">LOCAL EXPLANATION</span><h2>Inspect a test sample</h2></div></div><form className="sample-form" onSubmit={loadSample}><label htmlFor="sample">Benchmark sample index (0–339)</label><div><input id="sample" type="number" min="0" max="339" value={sample} onChange={event => setSample(event.target.value)} /><button className="primary-button">Explain <ArrowUpRight size={16} /></button></div></form>{local ? <LocalExplanation data={local} /> : <EmptyState icon={Sparkles} title="Choose a sample" text="The explanation will use the actual saved test vector and SHAP output." />}</section></div></>}
  </>;
}

function LocalExplanation({ data }) { return <div className="local-result"><div className="local-prediction"><div><span className="eyebrow">PREDICTION</span><strong className={data.prediction === 'phishing' ? 'prediction-bad' : 'prediction-good'}>{data.prediction}</strong></div><div className="probability"><span>PHISHING PROBABILITY</span><strong>{(data.probability * 100).toFixed(2)}%</strong></div></div><div className="base-line"><span>Base value</span><strong>{data.base_value.toFixed(4)}</strong></div><p className="explanation-copy">{data.explanation}</p><div className="contributor-columns"><ContributionList title="Increasing phishing" items={data.top_positive_features} tone="bad" /><ContributionList title="Decreasing phishing" items={data.top_negative_features} tone="good" /></div><span className="scope-note">Benchmark UCI phishing-risk model · not live trust analysis</span></div>; }
function ContributionList({ title, items, tone }) { return <div className="contribution-list"><span className="eyebrow">{title}</span>{items.map(item => <div className="contribution" key={item.feature}><span>{item.feature}</span><strong className={tone}>{item.shap_value > 0 ? '+' : ''}{item.shap_value.toFixed(4)}</strong></div>)}</div>; }

function HistoryPage({ history, onOpen }) { return <><PageIntro eyebrow="Analysis history" title="A trail of evidence." description="Every row below comes from the persisted analysis history endpoint. Select one to reopen its full result." /><section className="section-block"><div className="section-header"><div><span className="eyebrow">STORED RESULTS</span><h2>{history.length} assessments</h2></div></div><HistoryTable history={history} onOpen={onOpen} /></section></>; }
function HistoryTable({ history, onOpen }) { if (!history.length) return <EmptyState icon={History} title="No stored assessments" text="Run a live analysis to start building history." />; return <div className="table-wrap"><table><thead><tr><th>URL</th><th>Score</th><th>Risk level</th><th>Created</th><th></th></tr></thead><tbody>{history.map(item => <tr key={item.id} onClick={() => onOpen(item.id)}><td className="url-cell">{item.url}</td><td><strong>{item.trust_score}/100</strong></td><td><span className={`risk-tag ${item.risk_level}`}>{formatRisk(item.risk_level)}</span></td><td>{formatDate(item.created_at)}</td><td><ChevronRight size={15} /></td></tr>)}</tbody></table></div>; }

function ModelPage({ model }) { const metrics = model?.metrics ? Object.entries(model.metrics).filter(([key]) => key !== 'model') : []; return <><PageIntro eyebrow="Model registry" title="Know what powers the result." description="The registry reflects the actual persisted benchmark artifact and its measured evaluation run." />{!model?.loaded ? <EmptyState icon={Database} title="No trained model loaded" text="Train the benchmark model before opening its registry details." /> : <><div className="model-hero"><div><span className="eyebrow">ACTIVE BENCHMARK MODEL</span><h2>{model.model_name}</h2><p>{model.dataset_name} · {model.feature_count} features · trained {model.training_date}</p></div><span className="loaded-tag"><CheckCircle2 size={15} /> loaded</span></div><section className="metric-row model-metrics">{metrics.map(([key, value]) => <Metric key={key} label={key.replaceAll('_', ' ')} value={typeof value === 'number' ? value.toFixed(4) : value} icon={BarChart3} />)}</section><div className="disclaimer-band"><CircleAlert size={16} /><span><strong>BENCHMARK RESULTS:</strong> These metrics describe the corrected UCI test split. They are not real-world accuracy for arbitrary current websites. The model is not used for live website predictions.</span></div></>}</>; }

function Capability({ icon: Icon, title, text }) { return <div className="capability"><span className="capability-icon"><Icon size={16} /></span><span><strong>{title}</strong><small>{text}</small></span></div>; }
function Metric({ label, value, icon: Icon, tone = '' }) { return <div className={`metric-card ${tone}`}><span className="metric-icon"><Icon size={17} /></span><span className="metric-label">{label}</span><strong>{value}</strong></div>; }
function CategoryCard({ name, value }) { return <div className="category-card"><div className="category-card-head"><span>{name}</span><strong>{value.toFixed(0)}</strong></div><div className="progress"><i style={{ width: `${value}%` }}></i></div><small>Observed dimension score</small></div>; }
function EvidenceCard({ title, icon: Icon, items }) { return <div className="evidence-card"><div className="evidence-title"><Icon size={16} /><h3>{title}</h3></div>{items.map(([label, value]) => <div className="evidence-item" key={label}><span>{label}</span><EvidenceValue value={value} /></div>)}</div>; }
function EvidenceValue({ value }) { const normalized = String(value).toLowerCase(); const positive = ['detected', 'observed', 'true'].includes(normalized); const unavailable = ['unknown', 'unavailable', 'not_detected', 'not detected'].includes(normalized); return <strong className={positive ? 'value-positive' : unavailable ? 'value-muted' : ''}>{String(value).replaceAll('_', ' ')}</strong>; }
function EmptyState({ icon: Icon, title, text }) { return <div className="empty-state"><Icon size={23} /><strong>{title}</strong><p>{text}</p></div>; }
function LoadingState({ text }) { return <div className="loading-state"><LoaderCircle className="spin" size={19} /><span>{text}</span></div>; }
function formatDate(value) { if (!value) return '—'; return new Intl.DateTimeFormat('en', { month: 'short', day: 'numeric', year: 'numeric' }).format(new Date(value)); }
function formatRisk(value) { return String(value || 'unknown').replaceAll('_', ' '); }

export { api };
export default App;