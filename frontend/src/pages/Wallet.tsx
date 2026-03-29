import { useEffect, useState } from 'react'
import { coinsApi } from '../api/client'
import { Coins, ArrowDownLeft, ArrowUpRight, Plus } from 'lucide-react'
import './Wallet.css'

interface CoinBalance { coin_balance: number; coins_per_kwh: number; coins_per_minute: number; coin_topup_rate_usd: number }
interface CoinTx { id: number; amount: number; tx_type: string; description: string | null; balance_after: number; created_at: string }

const TX_META: Record<string, { icon: any; cls: string; label: string }> = {
  topup:         { icon: ArrowUpRight,   cls: 'tx-credit', label: 'Top-up' },
  admin_credit:  { icon: ArrowUpRight,   cls: 'tx-credit', label: 'Admin Credit' },
  refund:        { icon: ArrowUpRight,   cls: 'tx-credit', label: 'Refund' },
  session_debit: { icon: ArrowDownLeft,  cls: 'tx-debit',  label: 'Session' },
}

export default function Wallet() {
  const [balance, setBalance] = useState<CoinBalance | null>(null)
  const [txs, setTxs] = useState<CoinTx[]>([])
  const [topupAmount, setTopupAmount] = useState(50)
  const [loading, setLoading] = useState(true)
  const [topping, setTopping] = useState(false)
  const [msg, setMsg] = useState('')

  useEffect(() => {
    Promise.all([coinsApi.balance(), coinsApi.transactions(30)])
      .then(([b, t]) => { setBalance(b.data); setTxs(t.data) })
      .finally(() => setLoading(false))
  }, [])

  const handleTopup = async () => {
    setTopping(true)
    setMsg('')
    try {
      const r = await coinsApi.topup(topupAmount)
      // In production: open Stripe modal with r.data.client_secret
      // For now, show the amount
      setMsg(`💳 Stripe checkout would open for $${r.data.amount_usd} USD (${topupAmount} coins). Configure STRIPE_PUBLISHABLE_KEY to activate payments.`)
    } catch (e: any) {
      setMsg(e.response?.data?.detail || 'Top-up failed')
    } finally {
      setTopping(false)
    }
  }

  if (loading) return (
    <div className="page" style={{ display: 'flex', justifyContent: 'center', padding: '4rem' }}>
      <div className="spinner" style={{ width: 32, height: 32 }} />
    </div>
  )

  return (
    <div className="page fade-in">
      <h1 style={{ marginBottom: '1.5rem' }}>My Wallet</h1>

      <div className="wallet-layout">
        {/* Balance card */}
        <div className="balance-card card card--glow">
          <div className="balance-label">Coin Balance</div>
          <div className="balance-value">
            <Coins size={32} style={{ color: 'var(--amber-400)' }} />
            <span>{balance?.coin_balance.toFixed(1)}</span>
          </div>
          <div className="balance-rates">
            <span>{balance?.coins_per_kwh} coins/kWh</span>
            <span>·</span>
            <span>{balance?.coins_per_minute} coins/min</span>
          </div>
        </div>

        {/* Top-up */}
        <div className="card">
          <h3 style={{ marginBottom: '1rem' }}>Top Up Coins</h3>
          <div className="topup-presets">
            {[25, 50, 100, 200].map(n => (
              <button
                key={n}
                className={`preset-btn ${topupAmount === n ? 'active' : ''}`}
                onClick={() => setTopupAmount(n)}
              >
                {n} coins
                <span>${(n * (balance?.coin_topup_rate_usd ?? 0.1)).toFixed(2)}</span>
              </button>
            ))}
          </div>

          <div className="topup-custom">
            <label className="form-label">Custom amount</label>
            <input
              type="number"
              className="input"
              min={10}
              max={1000}
              value={topupAmount}
              onChange={e => setTopupAmount(Number(e.target.value))}
            />
          </div>

          <div className="topup-summary">
            <span>You'll get <strong>{topupAmount} coins</strong></span>
            <span className="topup-price">${(topupAmount * (balance?.coin_topup_rate_usd ?? 0.1)).toFixed(2)} USD</span>
          </div>

          {msg && <div className="alert alert-info" style={{ marginTop: '0.75rem', fontSize: '0.8rem' }}>{msg}</div>}

          <button id="topup-btn" className="btn btn-primary w-full" style={{ marginTop: '1rem' }} onClick={handleTopup} disabled={topping}>
            {topping ? <><span className="spinner" />Processing...</> : <><Plus size={16} />Buy {topupAmount} Coins</>}
          </button>
        </div>
      </div>

      {/* Transaction history */}
      <div className="card" style={{ marginTop: '1.5rem' }}>
        <h3 style={{ marginBottom: '1rem' }}>Transaction History</h3>
        {txs.length === 0 ? (
          <p style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>No transactions yet</p>
        ) : (
          <div className="tx-list">
            {txs.map(tx => {
              const meta = TX_META[tx.tx_type] || TX_META.session_debit
              const Icon = meta.icon
              const isCredit = tx.amount > 0
              return (
                <div key={tx.id} className="tx-item">
                  <div className={`tx-icon ${meta.cls}`}>
                    <Icon size={14} />
                  </div>
                  <div className="tx-info">
                    <div className="tx-desc">{tx.description || meta.label}</div>
                    <div className="tx-date">{new Date(tx.created_at).toLocaleString()}</div>
                  </div>
                  <div className={`tx-amount ${isCredit ? 'tx-credit' : 'tx-debit'}`}>
                    {isCredit ? '+' : ''}{tx.amount.toFixed(1)}
                  </div>
                  <div className="tx-balance">{tx.balance_after.toFixed(1)}</div>
                </div>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}
