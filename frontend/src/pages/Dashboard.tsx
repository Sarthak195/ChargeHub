import { useEffect, useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { plugsApi, sessionsApi, coinsApi } from '../api/client'
import { Zap, MapPin, Coins, RefreshCw, CheckCircle, XCircle, AlertCircle } from 'lucide-react'
import './Dashboard.css'

interface Plug {
  id: number
  name: string
  ip_address: string
  location_description: string | null
  slot_number: number | null
  status: 'available' | 'occupied' | 'offline' | 'maintenance'
  current_power_w: number
}

interface ActiveSession {
  id: number
  plug_id: number
  plug_name: string | null
  energy_kwh: number
  status: string
}

interface CoinBalance {
  coin_balance: number
  coins_per_kwh: number
  coins_per_minute: number
}

const STATUS_META = {
  available:   { label: 'Available',   cls: 'badge-green',  icon: CheckCircle, dot: '#10b981' },
  occupied:    { label: 'In Use',      cls: 'badge-red',    icon: XCircle,     dot: '#ef4444' },
  offline:     { label: 'Offline',     cls: 'badge-muted',  icon: AlertCircle, dot: '#64748b' },
  maintenance: { label: 'Maintenance', cls: 'badge-amber',  icon: AlertCircle, dot: '#f59e0b' },
}

export default function Dashboard() {
  const [plugs, setPlugs] = useState<Plug[]>([])
  const [activeSession, setActiveSession] = useState<ActiveSession | null>(null)
  const [coinData, setCoinData] = useState<CoinBalance | null>(null)
  const [loading, setLoading] = useState(true)
  const [starting, setStarting] = useState<number | null>(null)
  const [error, setError] = useState('')
  const navigate = useNavigate()

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const [plugsRes, sessionRes, coinsRes] = await Promise.all([
        plugsApi.list(),
        sessionsApi.active(),
        coinsApi.balance(),
      ])
      setPlugs(plugsRes.data)
      setActiveSession(sessionRes.data)
      setCoinData(coinsRes.data)
    } catch (e: any) {
      setError('Failed to load data')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { load() }, [load])

  const startSession = async (plugId: number) => {
    if (activeSession) { setError('You already have an active session'); return }
    if ((coinData?.coin_balance ?? 0) <= 0) { setError('Your coin balance is empty. Top up in the Wallet tab.'); return }
    setStarting(plugId)
    setError('')
    try {
      const res = await sessionsApi.start(plugId)
      navigate(`/session/${res.data.id}`)
    } catch (e: any) {
      setError(e.response?.data?.detail || 'Failed to start session')
    } finally {
      setStarting(null)
    }
  }

  const available = plugs.filter(p => p.status === 'available').length

  return (
    <div className="page fade-in">
      {/* Header */}
      <div className="dashboard-header">
        <div>
          <h1>Parking Map</h1>
          <p>{available} of {plugs.length} chargers available</p>
        </div>
        <div className="header-actions">
          {coinData && (
            <div className="coin-chip">
              <Coins size={15} />
              <span>{coinData.coin_balance.toFixed(1)} coins</span>
            </div>
          )}
          <button className="btn btn-secondary btn-sm" onClick={load} id="refresh-plugs">
            <RefreshCw size={14} />
            Refresh
          </button>
        </div>
      </div>

      {error && <div className="alert alert-error mt-2">{error}</div>}

      {/* Active session banner */}
      {activeSession && (
        <div className="active-banner" onClick={() => navigate(`/session/${activeSession.id}`)}>
          <div className="active-pulse" />
          <Zap size={16} style={{ color: 'var(--green-400)', flexShrink: 0 }} />
          <div>
            <strong>Active session on {activeSession.plug_name || `Plug #${activeSession.plug_id}`}</strong>
            <span> — {activeSession.energy_kwh.toFixed(3)} kWh consumed</span>
          </div>
          <span className="view-link">View →</span>
        </div>
      )}

      {/* Rate info */}
      {coinData && (
        <div className="rate-bar">
          <span><strong>{coinData.coins_per_kwh}</strong> coins / kWh</span>
          <span className="rate-sep">·</span>
          <span><strong>{coinData.coins_per_minute}</strong> coins / min</span>
        </div>
      )}

      {/* Plug grid */}
      {loading ? (
        <div className="loading-state">
          <div className="spinner" style={{ width: 32, height: 32 }} />
          <p>Loading chargers...</p>
        </div>
      ) : plugs.length === 0 ? (
        <div className="empty-state">
          <Zap size={48} style={{ color: 'var(--text-muted)' }} />
          <h3>No chargers registered yet</h3>
          <p>Ask your property manager to set up the charging stations.</p>
        </div>
      ) : (
        <div className="plug-grid">
          {plugs.map(plug => {
            const meta = STATUS_META[plug.status] || STATUS_META.offline
            const isMe = activeSession?.plug_id === plug.id
            return (
              <div key={plug.id} className={`plug-card ${plug.status} ${isMe ? 'plug-card--mine' : ''}`}>
                {/* Status dot */}
                <div className="plug-dot-wrap">
                  <div className="plug-dot" style={{ background: meta.dot }}>
                    {(plug.status === 'occupied' || plug.status === 'available') && (
                      <div className="plug-dot-ring" style={{ borderColor: meta.dot }} />
                    )}
                  </div>
                  <span className={`badge ${meta.cls}`}>{meta.label}</span>
                </div>

                {/* Slot */}
                <div className="plug-slot">
                  <span className="plug-slot-num">{plug.slot_number ?? '—'}</span>
                  <span className="plug-name">{plug.name}</span>
                </div>

                {/* Location */}
                {plug.location_description && (
                  <div className="plug-location">
                    <MapPin size={12} />
                    <span>{plug.location_description}</span>
                  </div>
                )}

                {/* Live power */}
                {plug.status === 'occupied' && (
                  <div className="plug-power">
                    <Zap size={13} style={{ color: 'var(--amber-400)' }} />
                    <span>{plug.current_power_w.toFixed(0)} W</span>
                  </div>
                )}

                {/* Action */}
                {plug.status === 'available' && !activeSession && (
                  <button
                    id={`start-session-${plug.id}`}
                    className="btn btn-primary btn-sm plug-action"
                    onClick={() => startSession(plug.id)}
                    disabled={starting === plug.id}
                  >
                    {starting === plug.id ? <span className="spinner" /> : <><Zap size={13} />Start Charging</>}
                  </button>
                )}
                {isMe && (
                  <button
                    className="btn btn-secondary btn-sm plug-action"
                    onClick={() => navigate(`/session/${activeSession!.id}`)}
                  >
                    View Session →
                  </button>
                )}
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
