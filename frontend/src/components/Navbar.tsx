import { Link, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { Zap, LayoutDashboard, History, Wallet, Settings, LogOut, Coins } from 'lucide-react'
import './Navbar.css'

export default function Navbar() {
  const { user, logout, isAdmin } = useAuth()
  const location = useLocation()
  const navigate = useNavigate()

  const handleLogout = () => { logout(); navigate('/login') }

  const nav = [
    { to: '/',        label: 'Dashboard', icon: LayoutDashboard },
    { to: '/history', label: 'History',   icon: History },
    { to: '/wallet',  label: 'Wallet',    icon: Wallet },
    ...(isAdmin ? [{ to: '/admin', label: 'Admin', icon: Settings }] : []),
  ]

  return (
    <nav className="navbar">
      <div className="navbar-inner">
        <Link to="/" className="navbar-brand">
          <div className="brand-icon"><Zap size={18} /></div>
          <span>ChargeHub</span>
        </Link>

        <div className="navbar-links">
          {nav.map(({ to, label, icon: Icon }) => (
            <Link
              key={to}
              to={to}
              className={`nav-link ${location.pathname === to ? 'active' : ''}`}
            >
              <Icon size={16} />
              <span>{label}</span>
            </Link>
          ))}
        </div>

        <div className="navbar-right">
          <div className="user-info">
            <div className="user-avatar">{user?.full_name?.[0]?.toUpperCase()}</div>
            <div className="user-details">
              <span className="user-name">{user?.full_name}</span>
              {user?.unit_number && <span className="user-unit">Unit {user.unit_number}</span>}
            </div>
          </div>
          <button className="btn btn-sm btn-secondary" onClick={handleLogout} id="logout-btn">
            <LogOut size={14} />
          </button>
        </div>
      </div>
    </nav>
  )
}
