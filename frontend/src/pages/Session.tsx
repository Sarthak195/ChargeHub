import { useEffect, useState, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { sessionsApi } from '../api/client'
import { Zap, Clock, Coins, StopCircle, TrendingUp, Battery } from 'lucide-react'
import './Session.css'

interface LiveData {
  session_id: number
  energy_kwh: number
  current_power_w: number
  estimated_cost: number
  status: string
}

interface SessionInfo {
  id: number
  plug_name: string | null
  started_at: string
  energy_kwh: number
  coins_per_kwh: number
  coins_per_minute: number
  total_coins_spent: number
  status: string
}

function elapsed(startedAt: string): string {
  const diff = Math.floor((Date.now() - new Date(startedAt).getTime()) / 1000)
  const h = Math.floor(diff / 3600)
  const m = Math.floor((diff % 3600) / 60)
  const s = diff % 60
  return `${h > 0 ? h + 'h ' : ''}${m}m ${s}s`
}

export default function Session() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [session, setSession] = useState<SessionInfo | null>(null)
  const [live, setLive] = useState<LiveData | null>(null)
  const [stopping, setStopping] = useState(false)
  const [tick, setTick] = useState(0)
  const [error, setError] = useState('')
  const esRef = useRef<EventSource | null>(null)

  // Fetch session info
  useEffect(() => {
    sessionsApi.active().then(r => {
      if (r.data) setSession(r.data)
    })
  }, [id])

  // SSE for live data
  useEffect(() => {
    if (!id) return
    const token = localStorage.getItem('token')
    const es = new EventSource(`/api/sessions/live/${id}?token=${token}`)
    esRef.current = es
    es.onmessage = (e) => {
      const data = JSON.parse(e.data)
      if (data.status === 'ended') {
        navigate('/')
        return
      }
      setLive(data)
    }
    es.onerror = () => {} // silent — backend may close it
    return () => { es.close() }
  }, [id, navigate])

  // Elapsed time ticker
  useEffect(() => {
    const t = setInterval(() => setTick(x => x + 1), 1000)
    return () => clearInterval(t)
  }, [])

  const stopSession = async () => {
    setStopping(true)
    setError('')
    try {
      await sessionsApi.stop(Number(id))
      navigate('/')
    } catch (e: any) {
      setError(e.response?.data?.detail || 'Failed to stop session')
      setStopping(false)
    }
  }

  const power = live?.current_power_w ?? 0
  const energyKwh = live?.energy_kwh ?? session?.energy_kwh ?? 0
  const estimatedCoins = live ? live.estimated_cost : (energyKwh * (session?.coins_per_kwh ?? 10))
  const powerPercent = Math.min((power / 2400) * 100, 100)

  return (
    <div className="page fade-in">
      <div className="session-layout">
        {/* Live power meter */}
        <div className="power-card card card--glow">
          <div className="power-header">
            <div>
              <h4>Active Session</h4>
              <h2>{session?.plug_name || `Charger #${id}`}</h2>
            </div>
            <div className="live-badge">
              <span className="live-dot" />
              LIVE
            </div>
          </div>

          <div className="power-display">
            <span className="power-value">{power.toFixed(0)}</span>
            <span className="power-unit">W</span>
          </div>

          <div className="power-bar-wrap">
            <div className="power-bar">
              <div className="power-fill" style={{ width: `${powerPercent}%` }} />
            </div>
            <span className="power-bar-label">{powerPercent.toFixed(0)}% of max (2400W)</span>
          </div>
        </div>

        {/* Stats */}
        <div className="session-stats">
          <div className="stat-card">
            <Battery size={20} style={{ color: 'var(--green-400)' }} />
            <div className="stat-value">{energyKwh.toFixed(3)}</div>
            <div className="stat-label">kWh Consumed</div>
          </div>

          <div className="stat-card">
            <Coins size={20} style={{ color: 'var(--amber-400)' }} />
            <div className="stat-value" style={{ color: 'var(--amber-400)' }}>
              {estimatedCoins.toFixed(1)}
            </div>
            <div className="stat-label">Coins So Far</div>
          </div>

          <div className="stat-card">
            <Clock size={20} style={{ color: 'var(--blue-400)' }} />
            <div className="stat-value" style={{ fontSize: '1.2rem' }}>
              {session ? elapsed(session.started_at) : '—'}
            </div>
            <div className="stat-label">Duration</div>
          </div>

          <div className="stat-card">
            <TrendingUp size={20} style={{ color: 'var(--teal-400)' }} />
            <div className="stat-value">{(energyKwh * 1000).toFixed(0)}</div>
            <div className="stat-label">Wh Total</div>
          </div>
        </div>

        {/* Rate reminder */}
        {session && (
          <div className="rate-reminder card">
            <Zap size={14} style={{ color: 'var(--green-400)' }} />
            <span>Rate: <strong>{session.coins_per_kwh}</strong> coins/kWh + <strong>{session.coins_per_minute}</strong> coins/min</span>
          </div>
        )}

        {error && <div className="alert alert-error">{error}</div>}

        {/* Stop button */}
        <button
          id="stop-session-btn"
          className="btn btn-danger btn-lg stop-btn"
          onClick={stopSession}
          disabled={stopping}
        >
          {stopping
            ? <><span className="spinner" />Stopping...</>
            : <><StopCircle size={20} />Stop Charging</>
          }
        </button>

        <p style={{ textAlign: 'center', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
          Coins will be deducted from your wallet when you stop
        </p>
      </div>
    </div>
  )
}
