import { useState, FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { Zap, Mail, Lock, User, Hash } from 'lucide-react'
import './Auth.css'

export default function Register() {
  const [form, setForm] = useState({ email: '', password: '', full_name: '', unit_number: '' })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const { register } = useAuth()
  const navigate = useNavigate()

  const set = (k: string) => (e: any) => setForm(f => ({ ...f, [k]: e.target.value }))

  const submit = async (e: FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await register(form)
      navigate('/')
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Registration failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-page">
      <div className="auth-glow" />
      <div className="auth-card fade-in">
        <div className="auth-brand">
          <div className="brand-icon" style={{ width: 48, height: 48 }}>
            <Zap size={24} />
          </div>
          <h1>Create Account</h1>
          <p>Join ChargeHub as a resident</p>
        </div>

        {error && <div className="alert alert-error">{error}</div>}

        <form onSubmit={submit} className="auth-form">
          <div className="form-group">
            <label className="form-label">Full Name</label>
            <div className="input-icon-wrap">
              <User size={16} className="input-icon" />
              <input className="input input-with-icon" placeholder="Your name" value={form.full_name} onChange={set('full_name')} required />
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">Email</label>
            <div className="input-icon-wrap">
              <Mail size={16} className="input-icon" />
              <input type="email" className="input input-with-icon" placeholder="you@email.com" value={form.email} onChange={set('email')} required />
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">Password</label>
            <div className="input-icon-wrap">
              <Lock size={16} className="input-icon" />
              <input type="password" className="input input-with-icon" placeholder="••••••••" value={form.password} onChange={set('password')} required />
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">Unit Number <span style={{color:'var(--text-muted)'}}>optional</span></label>
            <div className="input-icon-wrap">
              <Hash size={16} className="input-icon" />
              <input className="input input-with-icon" placeholder="e.g. 4B" value={form.unit_number} onChange={set('unit_number')} />
            </div>
          </div>

          <button id="register-btn" type="submit" className="btn btn-primary btn-lg w-full" disabled={loading}>
            {loading ? <><span className="spinner" />Creating account...</> : 'Create Account'}
          </button>
        </form>

        <p className="auth-footer">
          Already have an account? <Link to="/login">Sign in</Link>
        </p>
      </div>
    </div>
  )
}
