import React, { useState, useRef, useEffect } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import {
  Activity,
  Bell,
  CalendarCheck,
  ChevronDown,
  FileText,
  HeartPulse,
  LayoutDashboard,
  LogOut,
  Menu,
  Search,
  TrendingUp,
  User,
  History as HistoryIcon,
  X,
  Apple,
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { api } from '../../api/endpoints';

export const Navbar: React.FC = () => {
  const { user, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();

  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [userDropdownOpen, setUserDropdownOpen] = useState(false);
  const [notificationsOpen, setNotificationsOpen] = useState(false);
  const [notifications, setNotifications] = useState<any[]>([]);

  const userMenuRef = useRef<HTMLDivElement>(null);
  const notifMenuRef = useRef<HTMLDivElement>(null);

  // Close menus on outside click
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (userMenuRef.current && !userMenuRef.current.contains(event.target as Node)) {
        setUserDropdownOpen(false);
      }
      if (notifMenuRef.current && !notifMenuRef.current.contains(event.target as Node)) {
        setNotificationsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Fetch notifications
  useEffect(() => {
    if (user) {
      api.notifications
        .list()
        .then((res) => setNotifications(res))
        .catch(() => {});
    }
  }, [user]);

  const navItems = [
    { name: 'Dashboard', path: '/dashboard', icon: LayoutDashboard },
    { name: 'Health Check', path: '/health-check', icon: HeartPulse },
    { name: 'Risk Predictor', path: '/risk-predictor', icon: Activity },
    { name: 'Diet Planner', path: '/diet-planner', icon: CalendarCheck },
    { name: 'Food Explorer', path: '/food-explorer', icon: Search },
    { name: 'Condition Advisor', path: '/condition-advisor', icon: FileText },
    { name: 'Progress & Alerts', path: '/progress-alerts', icon: TrendingUp },
  ];

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  const initial = user?.full_name ? user.full_name[0].toUpperCase() : user?.email ? user.email[0].toUpperCase() : 'U';
  const unreadCount = notifications.filter((n) => !n.is_read).length;

  return (
    <nav className="sticky top-0 z-40 bg-surface border-b border-border shadow-soft">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo & Brand */}
          <div className="flex items-center space-x-3 flex-shrink-0">
            <Link to="/dashboard" className="flex items-center space-x-2.5">
              <div className="w-9 h-9 rounded-xl bg-primary flex items-center justify-center text-white shadow-sm">
                <Apple className="w-5 h-5 text-white" />
              </div>
              <div>
                <span className="text-base font-bold tracking-tight text-text block leading-none">
                  NutriIntel
                </span>
                <span className="text-[10px] font-semibold text-muted tracking-wider uppercase block mt-0.5">
                  CLINICAL NUTRITION AI
                </span>
              </div>
            </Link>
          </div>

          {/* Desktop Navigation Links */}
          <div className="hidden lg:flex items-center space-x-1.5">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname === item.path;
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`inline-flex items-center px-3 py-1.5 rounded-full text-xs font-semibold transition-all duration-150 ${
                    isActive
                      ? 'bg-primary-soft text-primary border border-primary'
                      : 'text-muted hover:text-text hover:bg-bg border border-transparent'
                  }`}
                >
                  <Icon className={`w-3.5 h-3.5 mr-1.5 ${isActive ? 'text-primary' : 'text-muted'}`} />
                  {item.name}
                </Link>
              );
            })}
          </div>

          {/* Right Controls: Notifications & User Avatar */}
          <div className="hidden sm:flex items-center space-x-3">
            {/* Bell Dropdown */}
            <div className="relative" ref={notifMenuRef}>
              <button
                onClick={() => setNotificationsOpen(!notificationsOpen)}
                className="relative p-2 rounded-xl text-muted hover:text-text hover:bg-bg border border-border transition-colors"
                aria-label="Notifications"
              >
                <Bell className="w-4 h-4 text-muted" />
                {unreadCount > 0 && (
                  <span className="absolute -top-1 -right-1 w-4 h-4 rounded-full bg-primary text-white text-[10px] font-bold flex items-center justify-center">
                    {unreadCount}
                  </span>
                )}
              </button>

              {notificationsOpen && (
                <div className="absolute right-0 mt-2 w-80 bg-surface rounded-card border border-border shadow-lg p-3 z-50 animate-in fade-in zoom-in-95 duration-150">
                  <div className="flex items-center justify-between pb-2 border-b border-border mb-2">
                    <span className="text-xs font-bold uppercase tracking-wider text-muted">
                      Alerts & Updates
                    </span>
                    <span className="text-xs text-primary font-semibold">
                      {unreadCount} unread
                    </span>
                  </div>
                  <div className="space-y-2 max-h-64 overflow-y-auto">
                    {notifications.length === 0 ? (
                      <p className="text-xs text-muted py-3 text-center">No notifications</p>
                    ) : (
                      notifications.slice(0, 5).map((n) => (
                        <div
                          key={n.id}
                          className={`p-2.5 rounded-lg border text-xs ${
                            n.is_read
                              ? 'bg-surface border-border text-muted'
                              : 'bg-primary-soft border-primary/20 text-text'
                          }`}
                        >
                          <p className="font-semibold">{n.title}</p>
                          <p className="text-muted mt-0.5 line-clamp-2">{n.message}</p>
                        </div>
                      ))
                    )}
                  </div>
                </div>
              )}
            </div>

            {/* Avatar Circle & User Menu */}
            <div className="relative" ref={userMenuRef}>
              <button
                id="user-menu-btn"
                onClick={() => setUserDropdownOpen(!userDropdownOpen)}
                className="flex items-center space-x-2 pl-2 pr-2.5 py-1.5 rounded-full hover:bg-bg border border-border transition-all"
              >
                <div className="w-7 h-7 rounded-full bg-primary-soft text-primary font-bold text-xs flex items-center justify-center border border-primary/20">
                  {initial}
                </div>
                <span className="text-xs font-semibold text-text max-w-[120px] truncate">
                  {user?.full_name || user?.username || 'Account'}
                </span>
                <ChevronDown className="w-3.5 h-3.5 text-muted" />
              </button>

              {userDropdownOpen && (
                <div className="absolute right-0 mt-2 w-52 bg-surface rounded-card border border-border shadow-lg p-1.5 z-50 animate-in fade-in zoom-in-95 duration-150">
                  <div className="px-3 py-2 border-b border-border mb-1">
                    <p className="text-xs font-bold text-text truncate">{user?.full_name || 'User'}</p>
                    <p className="text-[11px] text-muted truncate">{user?.email}</p>
                  </div>
                  <Link
                    to="/profile"
                    onClick={() => setUserDropdownOpen(false)}
                    className="flex items-center px-3 py-2 rounded-lg text-xs font-medium text-text hover:bg-bg transition-colors"
                  >
                    <User className="w-3.5 h-3.5 mr-2 text-muted" />
                    Profile & Settings
                  </Link>
                  <Link
                    to="/history"
                    onClick={() => setUserDropdownOpen(false)}
                    className="flex items-center px-3 py-2 rounded-lg text-xs font-medium text-text hover:bg-bg transition-colors"
                  >
                    <HistoryIcon className="w-3.5 h-3.5 mr-2 text-muted" />
                    Saved History
                  </Link>
                  <div className="border-t border-border my-1" />
                  <button
                    id="logout-btn"
                    onClick={handleLogout}
                    className="w-full flex items-center px-3 py-2 rounded-lg text-xs font-medium text-danger hover:bg-danger-soft transition-colors"
                  >
                    <LogOut className="w-3.5 h-3.5 mr-2 text-danger" />
                    Sign out
                  </button>
                </div>
              )}
            </div>
          </div>

          {/* Mobile menu button */}
          <div className="flex lg:hidden items-center space-x-2">
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="p-2 rounded-xl text-muted hover:text-text hover:bg-bg border border-border"
              aria-label="Toggle Navigation Menu"
            >
              {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile menu dropdown panel */}
      {mobileMenuOpen && (
        <div className="lg:hidden border-t border-border bg-surface px-4 pt-2 pb-4 space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.path;
            return (
              <Link
                key={item.path}
                to={item.path}
                onClick={() => setMobileMenuOpen(false)}
                className={`flex items-center px-3 py-2.5 rounded-xl text-sm font-semibold transition-colors ${
                  isActive
                    ? 'bg-primary-soft text-primary border border-primary'
                    : 'text-muted hover:text-text hover:bg-bg'
                }`}
              >
                <Icon className={`w-4 h-4 mr-3 ${isActive ? 'text-primary' : 'text-muted'}`} />
                {item.name}
              </Link>
            );
          })}
          <div className="pt-3 border-t border-border space-y-1">
            <Link
              to="/profile"
              onClick={() => setMobileMenuOpen(false)}
              className="flex items-center px-3 py-2 rounded-xl text-sm text-text hover:bg-bg"
            >
              <User className="w-4 h-4 mr-3 text-muted" />
              Profile
            </Link>
            <Link
              to="/history"
              onClick={() => setMobileMenuOpen(false)}
              className="flex items-center px-3 py-2 rounded-xl text-sm text-text hover:bg-bg"
            >
              <HistoryIcon className="w-4 h-4 mr-3 text-muted" />
              History
            </Link>
            <button
              onClick={() => {
                setMobileMenuOpen(false);
                handleLogout();
              }}
              className="w-full flex items-center px-3 py-2 rounded-xl text-sm text-danger hover:bg-danger-soft"
            >
              <LogOut className="w-4 h-4 mr-3 text-danger" />
              Sign out
            </button>
          </div>
        </div>
      )}
    </nav>
  );
};
