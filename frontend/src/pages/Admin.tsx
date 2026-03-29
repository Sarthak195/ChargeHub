import { useEffect, useState } from 'react'
import { plugsApi, analyticsApi, coinsApi, sessionsApi } from '../api/client'
import { Plus, Trash2, Wifi, WifiOff, Users, Zap, BarChart3, Coins } from 'lucide-react'
import './Admin.css'

interface Plug { id: number; name: string; ip_address: string; location_description: string | null; slot_number: number | null; status: string; current_power_w: number }
interface PlugForm { name: string; ip_address: string; location_description: string; slot_number: string }
interface OverallStats { total_sessions: number; total_kwh: number; total_cost: number; active_sessions: number; avg_kwh_per_session: number }
interface PlugUsage { plug_id: number; plug_name: string; total_sessions: number; total_kwh: number }
interface AdminCreditForm { user_id: string; coins: string; reason: string }

export default function Admin() {
  const [plugs, setPlugs] = useState<Plug[]>([])
  const [stats, setStats] = useState<OverallStats | null>(null)
  const [plugUsage, setPlugUsage] = useState<PlugUsage[]>([])
  const [sessions, setSessions] = useState<any[]>([])
  const [form, setForm] = useState<PlugForm>({ name: '', ip_address: '', location_description: '', slot_number: '' })
  const [creditForm, setCreditForm] = useState<AdminCreditForm>({ user_id: '', coins: '', reason: '' })
  const [loading, setLoading] = useState(true)
  const [testing, setTesting] = useState<number | null>(null)
  const [testResults, setTestResults] = useState<Record<number, any>>({})
  const [msg, setMsg] = useState('')
  const [creditMsg, setCreditMsg] = useState('')

  const load = async () => {
    setLoading(true)
    try {
      const [plugsRes, statsRes, usageRes, sessRes] = await Promise.all([
        plugsApi.list(),
        analyticsApi.adminOverview(),
        analyticsApi.plugUsage(),
        sessionsApi.allAdmin(20),
      ])
      setPlugs(plugsRes.data)
      setStats(statsRes.data)
      setPlugUsage(usageRes.data)
      setSessions(sessRes.data)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  const setF = (k: keyof PlugForm) => (e: any) => setForm(f => ({ ...f, [k]: e.target.value }))
  const setCF = (k: keyof AdminCreditForm) => (e: any) => setCreditForm(f => ({ ...f, [k]: e.target.value }))

  const addPlug = async (e: any) => {
    e.preventDefault()
    try {
      await plugsApi.create({ ...form, slot_number: form.slot_number ? Number(form.slot_number) : null })
      setForm({ name: '', ip_address: '', location_description: '', slot_number: '' })
      setMsg('Plug added successfully!')
      load()
    } catch (err: any) {
      setMsg(err.response?.data?.detail || 'Failed to add plug')
    }
  }

  const deletePlug = async (id: number) => {
    if (!confirm('Remove this plug?')) return
    await plugsApi.delete(id)
    load()
  }

  const testPlug = async (id: number) => {
    setTesting(id)
    try {
      const r = await plugsApi.test(id)
      setTestResults(prev => ({ ...prev, [id]: r.data }))
    } finally {
      setTesting(null)
    }
  }

  const creditCoins = async (e: any) => {
    e.preventDefault()
    try {
      await coinsApi.adminCredit(Number(creditForm.user_id), Number(creditForm.coins), creditForm.reason)
      setCreditMsg(`✓ Credited ${creditForm.coins} coins to user #${creditForm.user_id}`)
      setCreditForm({ user_id: '', coins: '', reason: '' })
    } catch (err: any) {
      setCreditMsg(err.response?.data?.detail || 'Failed to credit coins')
    }
  }

  return (
    <div className="page fade-in">
      <h1 style={{ marginBottom: '1.5rem' }}>Admin Panel</h1>

      {/* Overview stats */}
      {stats && (
        <div className="stat-grid" style={{ marginBottom: '1.5rem' }}>
          <div className="stat-card">
            <Zap size={18} style={{ color: 'var(--green-400)' }} />
            <div className="stat-value">{stats.total_sessions}</div>
            <div className="stat-label">Total Sessions</div>
            {stats.active_sessions > 0 && <div className="stat-delta">⚡ {stats.active_sessions} active now</div>}
          </div>
          <div className="stat-card">
            <BarChart3 size={18} style={{ color: 'var(--teal-400)' }} />
            <div className="stat-value">{stats.total_kwh.toFixed(1)}</div>
            <div className="stat-label">Total kWh Delivered</div>
          </div>
          <div className="stat-card">
            <Coins size={18} style={{ color: 'var(--amber-400)' }} />
            <div className="stat-value" style={{ color: 'var(--amber-400)' }}>{stats.total_cost.toFixed(0)}</div>
            <div className="stat-label">Total Coins Collected</div>
          </div>
          <div className="stat-card">
            <Users size={18} style={{ color: 'var(--blue-400)' }} />
            <div className="stat-value">{plugs.length}</div>
            <div className="stat-label">Active Chargers</div>
          </div>
        </div>
      )}

      <div className="admin-grid">
        {/* Plug management */}
        <div className="card">
          <h3 style={{ marginBottom: '1rem' }}>Registered Chargers</h3>
          {loading ? <div className="spinner" /> : plugs.map(plug => (
            <div key={plug.id} className="plug-row">
              <div className="plug-row-info">
                <strong>{plug.name}</strong>
                <span className="text-muted text-xs">{plug.ip_address}</span>
                {plug.location_description && <span className="text-muted text-xs">{plug.location_description}</span>}
              </div>
              <div className="plug-row-actions">
                {testResults[plug.id] && (
                  <span className={`badge ${testResults[plug.id].reachable ? 'badge-green' : 'badge-red'}`}>
                    {testResults[plug.id].reachable ? `${testResults[plug.id].current_power_w?.toFixed(0)}W` : 'Offline'}
                  </span>
                )}
                <button className="btn btn-secondary btn-sm" onClick={() => testPlug(plug.id)} disabled={testing === plug.id}>
                  {testing === plug.id ? <span className="spinner" /> : <Wifi size={13} />}
                </button>
                <button className="btn btn-danger btn-sm" onClick={() => deletePlug(plug.id)}>
                  <Trash2 size={13} />
                </button>
              </div>
            </div>
          ))}

          <div className="divider" />
          <h4>Add New Charger</h4>
          {msg && <div className={`alert ${msg.startsWith('Plug added') ? 'alert-success' : 'alert-error'}`} style={{ margin: '0.75rem 0' }}>{msg}</div>}
          <form onSubmit={addPlug} className="add-plug-form">
            <input className="input" placeholder="Name (e.g. Slot A1)" value={form.name} onChange={setF('name')} required />
            <input className="input" placeholder="IP Address (e.g. 192.168.1.51)" value={form.ip_address} onChange={setF('ip_address')} required />
            <input className="input" placeholder="Location (e.g. Level 1, Row A)" value={form.location_description} onChange={setF('location_description')} />
            <input className="input" placeholder="Slot # (e.g. 1)" type="number" value={form.slot_number} onChange={setF('slot_number')} />
            <button id="add-plug-btn" type="submit" className="btn btn-primary">
              <Plus size={15} />Add Charger
            </button>
          </form>
        </div>

        {/* Right column */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {/* Plug usage */}
          <div className="card">
            <h3 style={{ marginBottom: '1rem' }}>Charger Usage</h3>
            {plugUsage.map(pu => (
              <div key={pu.plug_id} className="usage-row">
                <span className="font-semibold" style={{ color: 'var(--text-primary)' }}>{pu.plug_name}</span>
                <span className="text-sm text-muted">{pu.total_sessions} sessions</span>
                <span className="text-green font-semibold text-sm">{pu.total_kwh.toFixed(1)} kWh</span>
              </div>
            ))}
            {plugUsage.length === 0 && <p className="text-muted text-sm">No usage data yet</p>}
          </div>

          {/* Admin coin credit */}
          <div className="card">
            <h3 style={{ marginBottom: '1rem' }}>Credit Coins to User</h3>
            {creditMsg && <div className={`alert ${creditMsg.startsWith('✓') ? 'alert-success' : 'alert-error'}`} style={{ marginBottom: '0.75rem' }}>{creditMsg}</div>}
            <form onSubmit={creditCoins} style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              <input className="input" placeholder="User ID" type="number" value={creditForm.user_id} onChange={setCF('user_id')} required />
              <input className="input" placeholder="Coins to credit" type="number" value={creditForm.coins} onChange={setCF('coins')} required />
              <input className="input" placeholder="Reason (e.g. Cash payment)" value={creditForm.reason} onChange={setCF('reason')} required />
              <button id="credit-coins-btn" type="submit" className="btn btn-primary">
                <Coins size={14} />Credit Coins
              </button>
            </form>
          </div>
        </div>
      </div>

      {/* All sessions */}
      <div className="card" style={{ marginTop: '1.5rem' }}>
        <h3 style={{ marginBottom: '1rem' }}>Recent Sessions (All Users)</h3>
        <div className="table-wrapper">
          <table>
            <thead>
              <tr>
                <th>#</th><th>User</th><th>Charger</th><th>Energy</th><th>Coins</th><th>Status</th><th>Date</th>
              </tr>
            </thead>
            <tbody>
              {sessions.map(s => (
                <tr key={s.id}>
                  <td className="text-muted">{s.id}</td>
                  <td>User #{s.user_id}</td>
                  <td style={{ color: 'var(--text-primary)' }}>{s.plug_name || `Plug #${s.plug_id}`}</td>
                  <td className="text-green">{s.energy_kwh.toFixed(3)} kWh</td>
                  <td className="text-amber">{s.total_coins_spent?.toFixed(1) ?? '—'}</td>
                  <td><span className={`badge ${s.status === 'paid' ? 'badge-green' : s.status === 'active' ? 'badge-red' : 'badge-muted'}`}>{s.status}</span></td>
                  <td className="text-muted">{new Date(s.started_at).toLocaleDateString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
