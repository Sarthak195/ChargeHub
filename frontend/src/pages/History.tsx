import { useEffect, useState } from 'react'
import { analyticsApi, sessionsApi } from '../api/client'
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'
import { Zap, Battery, Coins, TrendingUp } from 'lucide-react'
import './History.css'

interface DaySummary { date: string; total_kwh: number; total_cost: number; session_count: number }
interface OverallStats { total_sessions: number; total_kwh: number; total_cost: number; active_sessions: number; avg_kwh_per_session: number }
interface Session { id: number; plug_name: string | null; started_at: string; ended_at: string | null; energy_kwh: number; total_coins_spent: number; status: string }

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null
  return (
    <div className="chart-tooltip">
      <div className="tooltip-date">{label}</div>
      <div className="tooltip-row"><span>Energy</span><strong>{payload[0]?.value?.toFixed(2)} kWh</strong></div>
      <div className="tooltip-row"><span>Sessions</span><strong>{payload[1]?.value}</strong></div>
    </div>
  )
}

export default function History() {
  const [stats, setStats] = useState<OverallStats | null>(null)
  const [daily, setDaily] = useState<DaySummary[]>([])
  const [sessions, setSessions] = useState<Session[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([analyticsApi.mySummary(), analyticsApi.myDaily(30), sessionsApi.history(20)])
      .then(([s, d, h]) => {
        setStats(s.data)
        setDaily(d.data)
        setSessions(h.data)
      })
      .finally(() => setLoading(false))
  }, [])

  if (loading) return (
    <div className="page" style={{ display:'flex', justifyContent:'center', padding:'4rem' }}>
      <div className="spinner" style={{ width:32, height:32 }} />
    </div>
  )

  const statusBadge = (s: string) => {
    const map: Record<string, string> = { paid: 'badge-green', active: 'badge-red', cancelled: 'badge-muted' }
    return map[s] || 'badge-muted'
  }

  return (
    <div className="page fade-in">
      <h1 style={{ marginBottom: '1.5rem' }}>Charging History</h1>

      {/* Summary stats */}
      {stats && (
        <div className="stat-grid" style={{ marginBottom: '1.5rem' }}>
          <div className="stat-card">
            <Zap size={18} style={{ color: 'var(--green-400)' }} />
            <div className="stat-value">{stats.total_sessions}</div>
            <div className="stat-label">Total Sessions</div>
          </div>
          <div className="stat-card">
            <Battery size={18} style={{ color: 'var(--teal-400)' }} />
            <div className="stat-value">{stats.total_kwh.toFixed(1)}</div>
            <div className="stat-label">Total kWh</div>
          </div>
          <div className="stat-card">
            <Coins size={18} style={{ color: 'var(--amber-400)' }} />
            <div className="stat-value" style={{ color: 'var(--amber-400)' }}>{stats.total_cost.toFixed(0)}</div>
            <div className="stat-label">Coins Spent</div>
          </div>
          <div className="stat-card">
            <TrendingUp size={18} style={{ color: 'var(--blue-400)' }} />
            <div className="stat-value">{stats.avg_kwh_per_session.toFixed(2)}</div>
            <div className="stat-label">Avg kWh / Session</div>
          </div>
        </div>
      )}

      {/* Energy chart */}
      {daily.length > 0 && (
        <div className="card" style={{ marginBottom: '1.5rem' }}>
          <h3 style={{ marginBottom: '1.25rem' }}>Energy Usage — Last 30 Days</h3>
          <ResponsiveContainer width="100%" height={220}>
            <AreaChart data={daily} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
              <defs>
                <linearGradient id="kwhGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#10b981" stopOpacity={0.3} />
                  <stop offset="100%" stopColor="#10b981" stopOpacity={0} />
                </linearGradient>
              </defs>
              <XAxis dataKey="date" tick={{ fontSize: 10, fill: '#64748b' }} tickLine={false} axisLine={false} />
              <YAxis tick={{ fontSize: 10, fill: '#64748b' }} tickLine={false} axisLine={false} />
              <Tooltip content={<CustomTooltip />} />
              <Area type="monotone" dataKey="total_kwh" stroke="#10b981" fill="url(#kwhGrad)" strokeWidth={2} dot={false} />
              <Area type="monotone" dataKey="session_count" stroke="#2dd4bf" fill="transparent" strokeWidth={1.5} strokeDasharray="4 2" dot={false} />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Session table */}
      <div className="card">
        <h3 style={{ marginBottom: '1rem' }}>Recent Sessions</h3>
        {sessions.length === 0 ? (
          <p style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>No sessions yet</p>
        ) : (
          <div className="table-wrapper">
            <table>
              <thead>
                <tr>
                  <th>Charger</th>
                  <th>Date</th>
                  <th>Energy</th>
                  <th>Coins</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {sessions.map(s => (
                  <tr key={s.id}>
                    <td style={{ color: 'var(--text-primary)', fontWeight: 500 }}>{s.plug_name || `Plug #${s.id}`}</td>
                    <td>{new Date(s.started_at).toLocaleDateString()}</td>
                    <td><span className="text-green font-semibold">{s.energy_kwh.toFixed(3)}</span> kWh</td>
                    <td><span className="text-amber font-semibold">{s.total_coins_spent.toFixed(1)}</span> ⚡</td>
                    <td><span className={`badge ${statusBadge(s.status)}`}>{s.status}</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
