import { useCallback, useEffect, useState } from 'react';
import {
  AlertCircle,
  ArrowDownToLine,
  ArrowLeft,
  ArrowRight,
  Check,
  Cookie,
  CupSoda,
  Heart,
  LogOut,
  Package,
  Pencil,
  Plus,
  RefreshCw,
  Search,
  Sparkles,
  Trash2,
  X,
} from 'lucide-react';

import api, { clearToken, errorMessage, getStoredToken, storeToken } from './api.js';

const CATEGORIES = ['sweet', 'savoury', 'drink', 'healthy-ish'];
const STATUSES = ['stocked', 'running_low', 'gone'];
const PAGE_SIZE_OPTIONS = [12, 24, 48];
const ACTIVITY_PAGE_SIZE = 8;

function displayStatus(status) {
  return status.replace('_', ' ');
}

function categoryIcon(category) {
  if (category === 'drink') return <CupSoda aria-hidden="true" />;
  if (category === 'sweet') return <Cookie aria-hidden="true" />;
  return <Package aria-hidden="true" />;
}

function Notice({ notice, onDismiss }) {
  if (!notice) return null;
  const Icon = notice.kind === 'error' ? AlertCircle : Check;
  return (
    <div className={`notice notice-${notice.kind}`} role={notice.kind === 'error' ? 'alert' : 'status'}>
      <Icon aria-hidden="true" size={18} />
      <span>{notice.message}</span>
      <button className="icon-button notice-dismiss" type="button" onClick={onDismiss} aria-label="Dismiss message">
        <X size={16} aria-hidden="true" />
      </button>
    </div>
  );
}

function MetricCard({ label, value, icon: Icon, tone }) {
  return (
    <article className="metric-card">
      <div className={`metric-icon ${tone}`}><Icon size={20} aria-hidden="true" /></div>
      <div className="metric-copy">
        <span>{label}</span>
        <strong>{value ?? '—'}</strong>
      </div>
    </article>
  );
}

function SnackRanking({ title, icon: Icon, items, valueKey, unit, loading, emptyMessage }) {
  const maxValue = Math.max(...(items ?? []).map((snack) => snack[valueKey]), 1);

  return (
    <div className="analytics-ranking">
      <div className="activity-list-heading">
        <h3><Icon size={16} aria-hidden="true" />{title}</h3>
        <span>Top 5</span>
      </div>
      {loading ? (
        <p className="panel-muted">Loading snack rankings…</p>
      ) : items?.length ? (
        <ol className="ranked-snack-list">
          {items.map((snack, index) => (
            <li className="ranked-snack" key={snack.snack_id}>
              <span className="rank-number">{index + 1}</span>
              <div className="ranked-snack-copy">
                <strong>{snack.snack_name}</strong>
                <progress
                  max={maxValue}
                  value={snack[valueKey]}
                  aria-label={`${snack[valueKey]} ${unit}${snack[valueKey] === 1 ? '' : 's'}`}
                />
              </div>
              <span className="ranked-snack-total">
                {snack[valueKey]} {unit}{snack[valueKey] === 1 ? '' : 's'}
              </span>
            </li>
          ))}
        </ol>
      ) : (
        <p className="panel-muted">{emptyMessage}</p>
      )}
    </div>
  );
}

function AdminAnalytics({ data, loading, error, onRetry }) {
  return (
    <section className="analytics-panel" aria-labelledby="analytics-title" aria-busy={loading}>
      <div className="activity-panel-heading">
        <div>
          <p className="eyebrow">ADMIN ANALYSIS · ALL TIME</p>
          <h2 id="analytics-title">Pantry analysis</h2>
          <p className="panel-subtitle">Stock movement and member favorites from live pantry data.</p>
        </div>
        <span className="profile-badge">Administrator</span>
      </div>
      {error ? (
        <div className="list-error" role="alert">
          <AlertCircle size={18} aria-hidden="true" />
          <span>{error}</span>
          <button className="button button-outline" type="button" onClick={onRetry}>Try again</button>
        </div>
      ) : (
        <>
          <div className="metrics-grid analytics-grid">
            <MetricCard label="Packets consumed" value={loading && !data ? '…' : data?.consumed_packets} icon={ArrowDownToLine} tone="tone-violet" />
            <MetricCard label="Packets restocked" value={loading && !data ? '…' : data?.restocked_packets} icon={Package} tone="tone-green" />
            <MetricCard label="Consume actions" value={loading && !data ? '…' : data?.consume_events} icon={Check} tone="tone-amber" />
            <MetricCard label="Restock actions" value={loading && !data ? '…' : data?.restock_events} icon={RefreshCw} tone="tone-red" />
          </div>
          <div className="analytics-rankings">
            <SnackRanking
              title="Most consumed"
              icon={ArrowDownToLine}
              items={data?.top_consumed_snacks}
              valueKey="packets_consumed"
              unit="packet"
              loading={loading && !data}
              emptyMessage="No consumption activity has been recorded yet."
            />
            <SnackRanking
              title="Community favorites"
              icon={Heart}
              items={data?.top_favorite_snacks}
              valueKey="vote_count"
              unit="vote"
              loading={loading && !data}
              emptyMessage="No snacks have received votes yet."
            />
          </div>
        </>
      )}
    </section>
  );
}

function MemberProfileActivity({
  user,
  items,
  pagination,
  loading,
  error,
  onPageChange,
  onRetry,
}) {
  return (
    <section className="profile-activity-panel" aria-labelledby="profile-activity-title" aria-busy={loading}>
      <div className="activity-panel-heading profile-heading">
        <div className="profile-summary">
          <div className="user-avatar" aria-hidden="true">{user.name.charAt(0).toUpperCase()}</div>
          <div>
            <p className="eyebrow">MEMBER PROFILE</p>
            <h2>{user.name}</h2>
            <p className="panel-subtitle">{user.email}</p>
          </div>
        </div>
        <span className="profile-badge">Pantry member</span>
      </div>
      <div className="activity-list-heading">
        <h3 id="profile-activity-title">Your activity history</h3>
        <span>{pagination.total} {pagination.total === 1 ? 'event' : 'events'}</span>
      </div>

      {error ? (
        <div className="list-error" role="alert">
          <AlertCircle size={18} aria-hidden="true" />
          <span>{error}</span>
          <button className="button button-outline" type="button" onClick={onRetry}>Try again</button>
        </div>
      ) : loading && items.length === 0 ? (
        <p className="panel-muted">Loading your activity…</p>
      ) : items.length === 0 ? (
        <div className="activity-empty">
          <Package size={20} aria-hidden="true" />
          <p>No snack activity yet. Your successful consume actions will appear here.</p>
        </div>
      ) : (
        <ol className="activity-list">
          {items.map((item) => {
            const Icon = item.action === 'consumed' ? ArrowDownToLine : RefreshCw;
            const actionLabel = item.action === 'consumed' ? 'Consumed' : 'Restocked';
            return (
              <li className="activity-item" key={item.id}>
                <span className={`activity-icon activity-icon-${item.action}`}><Icon size={17} aria-hidden="true" /></span>
                <div className="activity-copy">
                  <strong>{actionLabel} {item.snack_name}</strong>
                  <span>{item.amount} {item.amount === 1 ? 'packet' : 'packets'} · {new Date(item.created_at).toLocaleString()}</span>
                </div>
              </li>
            );
          })}
        </ol>
      )}

      {pagination.pages > 1 && !error && (
        <div className="history-pagination">
          <span>Page {pagination.page} of {pagination.pages}</span>
          <div className="pagination-controls">
            <button
              className="pagination-button"
              type="button"
              onClick={() => onPageChange(Math.max(1, pagination.page - 1))}
              disabled={pagination.page <= 1 || loading}
              aria-label="Previous activity page"
            >
              <ArrowLeft size={17} aria-hidden="true" />
            </button>
            <button
              className="pagination-button"
              type="button"
              onClick={() => onPageChange(Math.min(pagination.pages, pagination.page + 1))}
              disabled={pagination.page >= pagination.pages || loading}
              aria-label="Next activity page"
            >
              <ArrowRight size={17} aria-hidden="true" />
            </button>
          </div>
        </div>
      )}
    </section>
  );
}

function SnackCard({
  snack,
  isAdmin,
  busy,
  onConsume,
  onRestock,
  onVote,
  onEdit,
  onDelete,
}) {
  const [consumeAmount, setConsumeAmount] = useState('1');
  const [restockAmount, setRestockAmount] = useState('10');

  function submitConsume(event) {
    event.preventDefault();
    const amount = Number(consumeAmount);
    if (Number.isInteger(amount) && amount > 0) onConsume(snack, amount);
  }

  function submitRestock(event) {
    event.preventDefault();
    const amount = Number(restockAmount);
    if (Number.isInteger(amount) && amount > 0) onRestock(snack, amount);
  }

  return (
    <article className="snack-card">
      <div className="snack-card-top">
        <div className={`snack-icon snack-icon-${snack.category}`}>{categoryIcon(snack.category)}</div>
        <span className={`status-pill status-${snack.status}`} aria-label={`Stock status: ${displayStatus(snack.status)}`}>
          <span className="status-dot" />
          {displayStatus(snack.status)}
        </span>
      </div>

      <div className="snack-title-row">
        <div>
          <p className="eyebrow">{snack.category}</p>
          <h3>{snack.name}</h3>
        </div>
        <button
          className={`vote-button ${snack.voted ? 'is-voted' : ''}`}
          type="button"
          onClick={() => onVote(snack)}
          disabled={busy}
          aria-label={snack.voted ? `Remove vote for ${snack.name}` : `Vote for ${snack.name}`}
          title={snack.voted ? 'Remove your vote' : 'Vote for this snack'}
        >
          <Heart size={17} fill={snack.voted ? 'currentColor' : 'none'} aria-hidden="true" />
          <span>{snack.vote_count}</span>
        </button>
      </div>

      <div className="stock-row">
        <strong>{snack.quantity}</strong>
        <span>{snack.quantity === 1 ? 'packet available' : 'packets available'}</span>
        <span className="threshold">Low at {snack.low_stock_threshold}</span>
      </div>

      <div className="card-actions">
        {!isAdmin && (
          <form className="inline-action" onSubmit={submitConsume}>
            <label className="sr-only" htmlFor={`consume-${snack.id}`}>Packets to consume for {snack.name}</label>
            <input
              id={`consume-${snack.id}`}
              type="number"
              min="1"
              step="1"
              inputMode="numeric"
              value={consumeAmount}
              onChange={(event) => setConsumeAmount(event.target.value)}
              disabled={busy || snack.quantity === 0}
            />
            <button className="button button-primary" type="submit" disabled={busy || snack.quantity === 0}>
              Consume
            </button>
          </form>
        )}

        {isAdmin && (
          <>
            <form className="inline-action admin-restock" onSubmit={submitRestock}>
              <label className="sr-only" htmlFor={`restock-${snack.id}`}>Packets to restock for {snack.name}</label>
              <input
                id={`restock-${snack.id}`}
                type="number"
                min="1"
                step="1"
                inputMode="numeric"
                value={restockAmount}
                onChange={(event) => setRestockAmount(event.target.value)}
                disabled={busy}
              />
              <button className="button button-secondary" type="submit" disabled={busy}>
                <ArrowDownToLine size={16} aria-hidden="true" />
                Restock
              </button>
            </form>
            <div className="admin-card-actions">
              <button className="button button-quiet" type="button" onClick={() => onEdit(snack)} disabled={busy}>
                <Pencil size={15} aria-hidden="true" /> Edit
              </button>
              <button className="button button-quiet button-danger-quiet" type="button" onClick={() => onDelete(snack)} disabled={busy}>
                <Trash2 size={15} aria-hidden="true" /> Delete
              </button>
            </div>
          </>
        )}
      </div>
    </article>
  );
}

function SnackEditor({ snack, saving, onCancel, onSave }) {
  const [name, setName] = useState(snack?.name ?? '');
  const [category, setCategory] = useState(snack?.category ?? 'savoury');
  const [quantity, setQuantity] = useState(snack?.quantity ?? 0);
  const [threshold, setThreshold] = useState(snack?.low_stock_threshold ?? 5);
  const isEditing = Boolean(snack);

  function submit(event) {
    event.preventDefault();
    onSave({
      name: name.trim(),
      category,
      ...(isEditing ? {} : { quantity: Number(quantity) }),
      low_stock_threshold: Number(threshold),
    });
  }

  return (
    <div className="modal-backdrop" onMouseDown={(event) => event.target === event.currentTarget && onCancel()}>
      <section className="editor-modal" role="dialog" aria-modal="true" aria-labelledby="editor-title">
        <div className="modal-heading">
          <div>
            <p className="eyebrow">{isEditing ? 'INVENTORY SETTINGS' : 'NEW INVENTORY ITEM'}</p>
            <h2 id="editor-title">{isEditing ? 'Edit snack' : 'Add a snack'}</h2>
          </div>
          <button className="icon-button" type="button" onClick={onCancel} aria-label="Close dialog">
            <X size={20} aria-hidden="true" />
          </button>
        </div>
        <form className="editor-form" onSubmit={submit}>
          <label>
            Snack name
            <input autoFocus maxLength="120" required value={name} onChange={(event) => setName(event.target.value)} />
          </label>
          <label>
            Category
            <select value={category} onChange={(event) => setCategory(event.target.value)}>
              {CATEGORIES.map((value) => <option key={value} value={value}>{value}</option>)}
            </select>
          </label>
          {!isEditing && (
            <label>
              Starting quantity
              <input type="number" min="0" step="1" required value={quantity} onChange={(event) => setQuantity(event.target.value)} />
            </label>
          )}
          <label>
            Low-stock threshold
            <input type="number" min="0" step="1" required value={threshold} onChange={(event) => setThreshold(event.target.value)} />
          </label>
          <div className="modal-actions">
            <button className="button button-quiet" type="button" onClick={onCancel} disabled={saving}>Cancel</button>
            <button className="button button-primary" type="submit" disabled={saving}>
              {saving ? 'Saving…' : isEditing ? 'Save changes' : 'Add snack'}
            </button>
          </div>
        </form>
      </section>
    </div>
  );
}

function LoadingCards() {
  return (
    <div className="snack-grid" aria-label="Loading snacks">
      {[0, 1, 2].map((item) => <div className="snack-skeleton" key={item} />)}
    </div>
  );
}

function Login({ onLogin, onSignup, onClearMessage, loading, message }) {
  const [signupMode, setSignupMode] = useState(false);
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [validationMessage, setValidationMessage] = useState('');

  function submit(event) {
    event.preventDefault();
    setValidationMessage('');
    if (signupMode) {
      if (password !== confirmPassword) {
        setValidationMessage('Passwords do not match.');
        return;
      }
      onSignup(name.trim(), email.trim(), password);
      return;
    }
    onLogin(email.trim(), password);
  }

  function toggleMode() {
    setSignupMode((mode) => !mode);
    setValidationMessage('');
    onClearMessage();
  }

  return (
    <main className="login-shell">
      <section className="login-panel">
        <div className="brand-lockup">
          <span className="brand-mark"><Cookie size={23} aria-hidden="true" /></span>
          <span>snack<span className="brand-accent">overflow</span></span>
        </div>
        <div className="login-intro">
          <p className="eyebrow">YOUR OFFICE PANTRY</p>
          <h1>{signupMode ? <>Join the pantry.<br />Share the good stuff.</> : <>Good snacks.<br />Better workdays.</>}</h1>
          <p>{signupMode ? 'Create your member account to explore the pantry.' : 'Sign in to see what’s fresh in the pantry.'}</p>
        </div>
        {(validationMessage || message) && (
          <div className="inline-error" role="alert"><AlertCircle size={17} />{validationMessage || message}</div>
        )}
        <form className="login-form" onSubmit={submit}>
          {signupMode && (
            <>
              <label htmlFor="signup-name">Your name</label>
              <input
                id="signup-name"
                autoComplete="name"
                type="text"
                maxLength={120}
                required
                value={name}
                onChange={(event) => setName(event.target.value)}
                placeholder="Your name"
              />
            </>
          )}
          <label htmlFor="login-email">Work email</label>
          <input
            id="login-email"
            autoComplete="username"
            type="email"
            required
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            placeholder="you@company.com"
          />
          <label htmlFor="login-password">{signupMode ? 'Create password' : 'Password'}</label>
          <input
            id="login-password"
            autoComplete={signupMode ? 'new-password' : 'current-password'}
            type="password"
            minLength={signupMode ? 8 : undefined}
            maxLength={signupMode ? 128 : undefined}
            required
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            placeholder={signupMode ? 'At least 8 characters' : 'Enter your password'}
          />
          {signupMode && (
            <>
              <label htmlFor="confirm-password">Confirm password</label>
              <input
                id="confirm-password"
                autoComplete="new-password"
                type="password"
                minLength={8}
                maxLength={128}
                required
                value={confirmPassword}
                onChange={(event) => setConfirmPassword(event.target.value)}
                placeholder="Enter your password again"
              />
            </>
          )}
          <button className="button button-primary login-submit" type="submit" disabled={loading}>
            {loading
              ? <><span className="spinner" /> {signupMode ? 'Creating account…' : 'Signing in…'}</>
              : signupMode ? 'Create member account' : 'Sign in'}
          </button>
        </form>
        <p className="login-footnote">
          {signupMode ? 'Already have an account? ' : 'New to the pantry? '}
          <button className="auth-switch" type="button" onClick={toggleMode} disabled={loading}>
            {signupMode ? 'Sign in' : 'Create a member account'}
          </button>
          {signupMode && <span className="auth-note"> Admin access is provisioned separately.</span>}
        </p>
      </section>
      <aside className="login-art" aria-hidden="true">
        <div className="art-glow" />
        <div className="art-content">
          <span className="art-kicker"><Sparkles size={16} /> THE GOOD STUFF, IN ONE PLACE</span>
          <div className="art-snack art-snack-one"><span>🥨</span><div><strong>Salty, sweet, sorted.</strong><small>Everything in its right place.</small></div></div>
          <div className="art-snack art-snack-two"><span>🍊</span><div><strong>Fresh from the pantry.</strong><small>Know what’s in stock before you go.</small></div></div>
          <div className="art-footer"><span>Made for shared snack spaces</span><span className="art-dots">● ● ●</span></div>
        </div>
      </aside>
    </main>
  );
}

export default function App() {
  const [user, setUser] = useState(null);
  const [authLoading, setAuthLoading] = useState(true);
  const [loginLoading, setLoginLoading] = useState(false);
  const [authMessage, setAuthMessage] = useState('');
  const [summary, setSummary] = useState(null);
  const [adminAnalytics, setAdminAnalytics] = useState(null);
  const [adminModule, setAdminModule] = useState('overview');
  const [analyticsLoading, setAnalyticsLoading] = useState(false);
  const [analyticsError, setAnalyticsError] = useState('');
  const [memberActivity, setMemberActivity] = useState([]);
  const [activityPage, setActivityPage] = useState(1);
  const [activityPagination, setActivityPagination] = useState({
    page: 1,
    per_page: ACTIVITY_PAGE_SIZE,
    total: 0,
    pages: 0,
  });
  const [activityLoading, setActivityLoading] = useState(false);
  const [activityError, setActivityError] = useState('');
  const [items, setItems] = useState([]);
  const [pagination, setPagination] = useState({ page: 1, per_page: 12, total: 0, pages: 0 });
  const [searchInput, setSearchInput] = useState('');
  const [search, setSearch] = useState('');
  const [category, setCategory] = useState('');
  const [status, setStatus] = useState('');
  const [page, setPage] = useState(1);
  const [perPage, setPerPage] = useState(12);
  const [listLoading, setListLoading] = useState(false);
  const [summaryLoading, setSummaryLoading] = useState(false);
  const [listError, setListError] = useState('');
  const [notice, setNotice] = useState(null);
  const [actionBusy, setActionBusy] = useState(false);
  const [dataVersion, setDataVersion] = useState(0);
  const [editorOpen, setEditorOpen] = useState(false);
  const [editingSnack, setEditingSnack] = useState(null);
  const [savingSnack, setSavingSnack] = useState(false);
  const isAdmin = user?.role === 'admin';
  const showAdminAnalysis = isAdmin && adminModule === 'analysis';

  useEffect(() => {
    function onUnauthorized() {
      setUser(null);
      setAuthLoading(false);
      setAuthMessage('Your session expired. Please sign in again.');
    }
    window.addEventListener('snack-overflow:unauthorized', onUnauthorized);
    return () => window.removeEventListener('snack-overflow:unauthorized', onUnauthorized);
  }, []);

  useEffect(() => {
    if (!getStoredToken()) {
      setAuthLoading(false);
      return undefined;
    }
    let active = true;
    api.get('/auth/me')
      .then(({ data }) => { if (active) setUser(data); })
      .catch((error) => {
        if (active && error.response?.status !== 401) setAuthMessage(errorMessage(error));
        if (active) clearToken();
      })
      .finally(() => { if (active) setAuthLoading(false); });
    return () => { active = false; };
  }, []);

  useEffect(() => {
    const timeout = window.setTimeout(() => {
      setSearch(searchInput.trim());
      setPage(1);
    }, 250);
    return () => window.clearTimeout(timeout);
  }, [searchInput]);

  useEffect(() => {
    if (!user) return undefined;
    const controller = new AbortController();
    setListLoading(true);
    setListError('');
    api.get('/snacks', {
      params: { search, category, status, page, per_page: perPage },
      signal: controller.signal,
    })
      .then(({ data }) => {
        setItems(data.items);
        setPagination({
          page: data.page,
          per_page: data.per_page,
          total: data.total,
          pages: data.pages,
        });
      })
      .catch((error) => {
        if (error.code !== 'ERR_CANCELED') setListError(errorMessage(error));
      })
      .finally(() => {
        if (!controller.signal.aborted) setListLoading(false);
      });
    return () => controller.abort();
  }, [user, search, category, status, page, perPage, dataVersion]);

  useEffect(() => {
    if (!user) return undefined;
    const controller = new AbortController();
    setSummaryLoading(true);
    api.get('/snacks/summary', { signal: controller.signal })
      .then(({ data }) => setSummary(data))
      .catch((error) => {
        if (error.code !== 'ERR_CANCELED') {
          setNotice({ kind: 'error', message: errorMessage(error) });
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) setSummaryLoading(false);
      });
    return () => controller.abort();
  }, [user, dataVersion]);

  useEffect(() => {
    if (!user || !isAdmin) return undefined;
    const controller = new AbortController();
    setAnalyticsLoading(true);
    setAnalyticsError('');
    api.get('/activity/summary', { signal: controller.signal })
      .then(({ data }) => setAdminAnalytics(data))
      .catch((error) => {
        if (error.code !== 'ERR_CANCELED') setAnalyticsError(errorMessage(error));
      })
      .finally(() => {
        if (!controller.signal.aborted) setAnalyticsLoading(false);
      });
    return () => controller.abort();
  }, [user, isAdmin, dataVersion]);

  useEffect(() => {
    if (!user || isAdmin) return undefined;
    const controller = new AbortController();
    setActivityLoading(true);
    setActivityError('');
    api.get('/activity', {
      params: { page: activityPage, per_page: ACTIVITY_PAGE_SIZE },
      signal: controller.signal,
    })
      .then(({ data }) => {
        setMemberActivity(data.items);
        setActivityPagination({
          page: data.page,
          per_page: data.per_page,
          total: data.total,
          pages: data.pages,
        });
      })
      .catch((error) => {
        if (error.code !== 'ERR_CANCELED') setActivityError(errorMessage(error));
      })
      .finally(() => {
        if (!controller.signal.aborted) setActivityLoading(false);
      });
    return () => controller.abort();
  }, [user, isAdmin, activityPage, dataVersion]);

  const handleLogin = useCallback(async (email, password) => {
    setLoginLoading(true);
    setAuthMessage('');
    try {
      const { data } = await api.post('/auth/login', { email, password });
      storeToken(data.access_token);
      setUser(data.user);
      setNotice({ kind: 'success', message: `Welcome, ${data.user.name.split(' ')[0]}.` });
    } catch (error) {
      setAuthMessage(errorMessage(error));
    } finally {
      setLoginLoading(false);
      setAuthLoading(false);
    }
  }, []);

  const handleSignup = useCallback(async (name, email, password) => {
    setLoginLoading(true);
    setAuthMessage('');
    try {
      const { data } = await api.post('/auth/register', { name, email, password });
      storeToken(data.access_token);
      setUser(data.user);
      setNotice({ kind: 'success', message: `Welcome to the pantry, ${data.user.name.split(' ')[0]}.` });
    } catch (error) {
      setAuthMessage(errorMessage(error));
    } finally {
      setLoginLoading(false);
      setAuthLoading(false);
    }
  }, []);

  function logout() {
    clearToken();
    setUser(null);
    setSummary(null);
    setItems([]);
    setAdminAnalytics(null);
    setAdminModule('overview');
    setMemberActivity([]);
    setActivityPage(1);
    setActivityPagination({ page: 1, per_page: ACTIVITY_PAGE_SIZE, total: 0, pages: 0 });
    setAnalyticsError('');
    setActivityError('');
    setNotice(null);
    setAuthMessage('');
  }

  async function runAction(action, successMessage) {
    setActionBusy(true);
    setNotice(null);
    try {
      await action();
      setNotice({ kind: 'success', message: successMessage });
      setDataVersion((version) => version + 1);
    } catch (error) {
      setNotice({ kind: 'error', message: errorMessage(error) });
    } finally {
      setActionBusy(false);
    }
  }

  function consume(snack, amount) {
    return runAction(
      () => api.post(`/snacks/${snack.id}/consume`, { amount }),
      `Consumed ${amount} ${amount === 1 ? 'packet' : 'packets'} of ${snack.name}.`,
    );
  }

  function restock(snack, amount) {
    return runAction(
      () => api.post(`/snacks/${snack.id}/restock`, { amount }),
      `Restocked ${snack.name} by ${amount}.`,
    );
  }

  function toggleVote(snack) {
    return runAction(
      () => (snack.voted
        ? api.delete(`/snacks/${snack.id}/vote`)
        : api.post(`/snacks/${snack.id}/vote`)),
      snack.voted ? `Your vote for ${snack.name} was removed.` : `Your vote for ${snack.name} was recorded.`,
    );
  }

  async function saveSnack(values) {
    setSavingSnack(true);
    setNotice(null);
    try {
      if (editingSnack) {
        await api.patch(`/snacks/${editingSnack.id}`, values);
        setNotice({ kind: 'success', message: `${editingSnack.name} was updated.` });
      } else {
        await api.post('/snacks', values);
        setNotice({ kind: 'success', message: `${values.name} was added to the pantry.` });
      }
      setEditorOpen(false);
      setEditingSnack(null);
      setDataVersion((version) => version + 1);
    } catch (error) {
      setNotice({ kind: 'error', message: errorMessage(error) });
    } finally {
      setSavingSnack(false);
    }
  }

  function deleteSnack(snack) {
    if (!window.confirm(`Delete "${snack.name}"? This cannot be undone.`)) return;
    runAction(
      () => api.delete(`/snacks/${snack.id}`),
      `${snack.name} was deleted.`,
    );
  }

  function startCreate() {
    setEditingSnack(null);
    setEditorOpen(true);
  }

  function startEdit(snack) {
    setEditingSnack(snack);
    setEditorOpen(true);
  }

  if (authLoading) {
    return <main className="auth-loading"><span className="spinner spinner-dark" />Checking your session…</main>;
  }

  if (!user) {
    return (
      <Login
        onLogin={handleLogin}
        onSignup={handleSignup}
        onClearMessage={() => setAuthMessage('')}
        loading={loginLoading}
        message={authMessage}
      />
    );
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <a className="brand-lockup sidebar-brand" href="#dashboard" aria-label="Snack Overflow dashboard">
          <span className="brand-mark"><Cookie size={21} aria-hidden="true" /></span>
          <span>snack<span className="brand-accent">overflow</span></span>
        </a>
        <nav className="sidebar-nav" aria-label="Dashboard modules">
          <p className="sidebar-section-label">PANTRY</p>
          <button
            className={`sidebar-link ${adminModule === 'overview' ? 'active' : ''}`}
            type="button"
            onClick={() => setAdminModule('overview')}
            aria-current={adminModule === 'overview' ? 'page' : undefined}
          >
            <Package size={18} aria-hidden="true" />Overview
          </button>
          {isAdmin && (
            <button
              className={`sidebar-link ${adminModule === 'analysis' ? 'active' : ''}`}
              type="button"
              onClick={() => setAdminModule('analysis')}
              aria-current={adminModule === 'analysis' ? 'page' : undefined}
            >
              <Sparkles size={18} aria-hidden="true" />Analysis
            </button>
          )}
        </nav>
        {isAdmin && <span className="sidebar-role"><Sparkles size={15} aria-hidden="true" /> Admin workspace</span>}
        <div className="sidebar-bottom">
          <div className="user-avatar" aria-hidden="true">{user.name.charAt(0).toUpperCase()}</div>
          <div className="user-meta">
            <strong>{user.name}</strong>
            <span>{isAdmin ? 'Administrator' : 'Pantry member'}</span>
          </div>
          <button className="icon-button logout-button" type="button" onClick={logout} aria-label="Sign out" title="Sign out">
            <LogOut size={18} aria-hidden="true" />
          </button>
        </div>
      </aside>

      <main className="dashboard" id="dashboard">
        <header className="topbar">
          <div>
            <p className="eyebrow">OFFICE PANTRY / {showAdminAnalysis ? 'ANALYSIS' : isAdmin ? 'ADMIN OVERVIEW' : 'MEMBER OVERVIEW'}</p>
            <h1>{showAdminAnalysis ? 'Pantry analysis' : `Good ${new Date().getHours() < 12 ? 'morning' : new Date().getHours() < 18 ? 'afternoon' : 'evening'}, ${user.name.split(' ')[0]}`}</h1>
            <p className="page-subtitle">
              {showAdminAnalysis
                ? 'Explore stock movement and community favorite snacks.'
                : isAdmin
                  ? 'Manage live pantry stock and inventory.'
                  : 'Your profile, pantry history, and what’s available today.'}
            </p>
          </div>
          <div className="topbar-actions">
            {isAdmin && !showAdminAnalysis && (
              <button className="button button-primary" type="button" onClick={startCreate}>
                <Plus size={17} aria-hidden="true" /> Add snack
              </button>
            )}
            <button
              className="button button-outline refresh-button"
              type="button"
              onClick={() => setDataVersion((version) => version + 1)}
              disabled={listLoading || summaryLoading || analyticsLoading || activityLoading}
            >
              <RefreshCw
                size={16}
                aria-hidden="true"
                className={listLoading || summaryLoading || analyticsLoading || activityLoading ? 'spin-icon' : ''}
              />
              Refresh
            </button>
          </div>
        </header>

        <Notice notice={notice} onDismiss={() => setNotice(null)} />

        {showAdminAnalysis ? (
          <AdminAnalytics
            data={adminAnalytics}
            loading={analyticsLoading}
            error={analyticsError}
            onRetry={() => setDataVersion((version) => version + 1)}
          />
        ) : (
          <>
            <section className="metrics-grid" aria-label="Live pantry summary">
              <MetricCard label="Total snacks" value={summaryLoading && !summary ? '…' : summary?.total} icon={Package} tone="tone-violet" />
              <MetricCard label="Stocked" value={summaryLoading && !summary ? '…' : summary?.stocked} icon={Check} tone="tone-green" />
              <MetricCard label="Running low" value={summaryLoading && !summary ? '…' : summary?.running_low} icon={AlertCircle} tone="tone-amber" />
              <MetricCard label="Gone" value={summaryLoading && !summary ? '…' : summary?.gone} icon={ArrowDownToLine} tone="tone-red" />
            </section>

            <section className="spotlight" aria-label="Snack of the week">
              <div className="spotlight-icon"><Sparkles size={21} aria-hidden="true" /></div>
              {summary?.snack_of_week ? (
                <div className="spotlight-copy">
                  <p className="eyebrow">SNACK OF THE WEEK</p>
                  <h2>{summary.snack_of_week.name}</h2>
                  <p>{summary.snack_of_week.vote_count} {summary.snack_of_week.vote_count === 1 ? 'pantry pick' : 'pantry picks'} · {summary.snack_of_week.quantity} available</p>
                </div>
              ) : (
                <div className="spotlight-copy">
                  <p className="eyebrow">SNACK OF THE WEEK</p>
                  <h2>{summaryLoading ? 'Finding the pantry favorite…' : 'No snacks to spotlight yet'}</h2>
                  <p>{summaryLoading ? 'Loading live pantry picks.' : 'Add a snack and cast the first vote.'}</p>
                </div>
              )}
              <span className="spotlight-star" aria-hidden="true">✦</span>
            </section>

            {!isAdmin && (
              <MemberProfileActivity
                user={user}
                items={memberActivity}
                pagination={activityPagination}
                loading={activityLoading}
                error={activityError}
                onPageChange={setActivityPage}
                onRetry={() => setDataVersion((version) => version + 1)}
              />
            )}

            <section className="inventory-section" aria-labelledby="inventory-title">
              <div className="inventory-heading">
                <div>
                  <p className="eyebrow">WHAT’S AVAILABLE</p>
                  <h2 id="inventory-title">Pantry inventory</h2>
                </div>
                <span className="result-count">{pagination.total} {pagination.total === 1 ? 'item' : 'items'}</span>
              </div>

              <div className="filter-toolbar">
                <label className="search-field">
                  <Search size={18} aria-hidden="true" />
                  <span className="sr-only">Search by snack name</span>
                  <input
                    type="search"
                    placeholder="Search snacks…"
                    value={searchInput}
                    onChange={(event) => setSearchInput(event.target.value)}
                  />
                  {searchInput && (
                    <button className="icon-button clear-search" type="button" onClick={() => setSearchInput('')} aria-label="Clear search">
                      <X size={15} aria-hidden="true" />
                    </button>
                  )}
                </label>
                <label className="filter-select">
                  <span className="sr-only">Filter by category</span>
                  <select value={category} onChange={(event) => { setCategory(event.target.value); setPage(1); }}>
                    <option value="">All categories</option>
                    {CATEGORIES.map((value) => <option key={value} value={value}>{value}</option>)}
                  </select>
                </label>
                <label className="filter-select">
                  <span className="sr-only">Filter by stock status</span>
                  <select value={status} onChange={(event) => { setStatus(event.target.value); setPage(1); }}>
                    <option value="">All stock statuses</option>
                    {STATUSES.map((value) => <option key={value} value={value}>{displayStatus(value)}</option>)}
                  </select>
                </label>
              </div>

              {listError && (
                <div className="list-error" role="alert">
                  <AlertCircle size={18} aria-hidden="true" />
                  <span>{listError}</span>
                  <button className="button button-outline" type="button" onClick={() => setDataVersion((version) => version + 1)}>Try again</button>
                </div>
              )}

              {listLoading ? (
                <LoadingCards />
              ) : listError ? null : items.length === 0 ? (
                <div className="empty-state">
                  <div className="empty-icon"><Search size={23} aria-hidden="true" /></div>
                  <h3>{search || category || status ? 'No snacks match those filters' : 'The pantry is waiting for its first snack'}</h3>
                  <p>{search || category || status ? 'Try another search or clear a filter.' : isAdmin ? 'Add a snack to get the pantry started.' : 'Check back when the pantry is stocked.'}</p>
                  {(search || category || status) && (
                    <button className="button button-outline" type="button" onClick={() => { setSearchInput(''); setCategory(''); setStatus(''); setPage(1); }}>
                      Clear filters
                    </button>
                  )}
                  {isAdmin && !search && !category && !status && (
                    <button className="button button-primary" type="button" onClick={startCreate}><Plus size={16} /> Add the first snack</button>
                  )}
                </div>
              ) : (
                <div className="snack-grid">
                  {items.map((snack) => (
                    <SnackCard
                      key={snack.id}
                      snack={snack}
                      isAdmin={isAdmin}
                      busy={actionBusy}
                      onConsume={consume}
                      onRestock={restock}
                      onVote={toggleVote}
                      onEdit={startEdit}
                      onDelete={deleteSnack}
                    />
                  ))}
                </div>
              )}

              {!listLoading && !listError && pagination.total > 0 && (
                <div className="pagination">
                  <span>Showing {Math.min((page - 1) * perPage + 1, pagination.total)}–{Math.min(page * perPage, pagination.total)} of {pagination.total}</span>
                  <div className="pagination-controls">
                    <label>
                      <span className="sr-only">Items per page</span>
                      <select value={perPage} onChange={(event) => { setPerPage(Number(event.target.value)); setPage(1); }}>
                        {PAGE_SIZE_OPTIONS.map((size) => <option key={size} value={size}>{size} / page</option>)}
                      </select>
                    </label>
                    <button
                      className="pagination-button"
                      type="button"
                      onClick={() => setPage((current) => Math.max(1, current - 1))}
                      disabled={page <= 1}
                      aria-label="Previous page"
                    >
                      <ArrowLeft size={17} aria-hidden="true" />
                    </button>
                    <span className="page-number">{page} <span>of</span> {Math.max(pagination.pages, 1)}</span>
                    <button
                      className="pagination-button"
                      type="button"
                      onClick={() => setPage((current) => Math.min(pagination.pages, current + 1))}
                      disabled={page >= pagination.pages}
                      aria-label="Next page"
                    >
                      <ArrowRight size={17} aria-hidden="true" />
                    </button>
                  </div>
                </div>
              )}
            </section>
          </>
        )}
        <footer className="page-footer">Snack Overflow <span>·</span> Pantry inventory, made easy.</footer>
      </main>

      {editorOpen && (
        <SnackEditor
          key={editingSnack?.id ?? 'new'}
          snack={editingSnack}
          saving={savingSnack}
          onCancel={() => { if (!savingSnack) { setEditorOpen(false); setEditingSnack(null); } }}
          onSave={saveSnack}
        />
      )}
    </div>
  );
}
