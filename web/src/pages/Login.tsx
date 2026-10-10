import React, { useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { Apple, Eye, EyeOff, ShieldCheck, Sparkles, CheckCircle2 } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { Button } from '../components/common/Button';

export const Login: React.FC = () => {
  const { login, user } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  // If already logged in, navigate to dashboard
  React.useEffect(() => {
    if (user) {
      navigate('/dashboard', { replace: true });
    }
  }, [user, navigate]);

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);

    if (!email || !password) {
      setErrorMessage('Please enter both your email address and password.');
      return;
    }

    setIsLoading(true);
    try {
      const loggedInUser = await login({
        username_or_email: email,
        password,
        remember_me: rememberMe,
      });

      // Redirect to onboarding if not yet completed, otherwise dashboard or requested page
      const from = (location.state as any)?.from?.pathname;
      if (loggedInUser.profile?.onboarding_completed === false) {
        navigate('/onboarding', { replace: true });
      } else if (from && from !== '/login' && from !== '/register') {
        navigate(from, { replace: true });
      } else {
        navigate('/dashboard', { replace: true });
      }
    } catch (err: any) {
      setErrorMessage('Invalid email or password.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-bg flex items-center justify-center p-4 sm:p-6 lg:p-8">
      <div className="w-full max-w-4xl bg-surface border border-border rounded-card shadow-soft overflow-hidden grid grid-cols-1 md:grid-cols-2">
        {/* Left Dark Gradient Panel (Visible on Desktop) */}
        <div className="hidden md:flex flex-col justify-between p-8 sm:p-10 hero-gradient text-white">
          <div>
            <div className="flex items-center space-x-2.5 mb-8">
              <div className="w-9 h-9 rounded-xl bg-primary flex items-center justify-center text-white border border-primary-accent/30 shadow-sm">
                <Apple className="w-5 h-5 text-white" />
              </div>
              <div>
                <span className="text-base font-bold tracking-tight text-white block leading-none">
                  NutriIntel
                </span>
                <span className="text-[9px] font-semibold text-primary-accent tracking-wider uppercase block mt-0.5">
                  CLINICAL NUTRITION AI
                </span>
              </div>
            </div>

            <div className="inline-flex items-center px-2.5 py-1 rounded-full bg-primary/40 border border-primary-accent/30 text-primary-accent text-xs font-semibold uppercase tracking-wider mb-4">
              <Sparkles className="w-3.5 h-3.5 mr-1.5 text-primary-accent" />
              Clinical Intelligence
            </div>

            <h2 className="text-2xl font-bold text-white tracking-tight leading-snug mb-3">
              Precision Health Assessment &amp; Smart Dietetics
            </h2>
            <p className="text-xs text-muted leading-relaxed mb-8">
              Access metabolic assessments, calibrated lifestyle risk screening, and mathematically
              optimized nutrition schedules.
            </p>

            {/* 3 Key Benefits */}
            <div className="space-y-4 text-xs text-white/90">
              <div className="flex items-start space-x-3">
                <CheckCircle2 className="w-4 h-4 text-primary-accent flex-shrink-0 mt-0.5" />
                <div>
                  <span className="font-semibold block text-white">Evidence-Based Assessment</span>
                  <span className="text-white/70">Mifflin-St Jeor metabolic expenditure and WHO thresholds.</span>
                </div>
              </div>
              <div className="flex items-start space-x-3">
                <CheckCircle2 className="w-4 h-4 text-primary-accent flex-shrink-0 mt-0.5" />
                <div>
                  <span className="font-semibold block text-white">Optimized Meal Plans</span>
                  <span className="text-white/70">MILP linear solver balancing calorie targets within &plusmn;5%.</span>
                </div>
              </div>
              <div className="flex items-start space-x-3">
                <ShieldCheck className="w-4 h-4 text-primary-accent flex-shrink-0 mt-0.5" />
                <div>
                  <span className="font-semibold block text-white">Safe &amp; Explainable</span>
                  <span className="text-white/70">Tri-state allergen filtering and SHAP risk factor transparency.</span>
                </div>
              </div>
            </div>
          </div>

          <div className="pt-6 border-t border-border/10 text-[11px] text-white/50">
            Secure, encrypted personal session with strict HIPAA/GDPR data isolation.
          </div>
        </div>

        {/* Right Form Panel */}
        <div className="p-8 sm:p-10 flex flex-col justify-center">
          <div className="mb-6">
            {/* Mobile Brand Header */}
            <div className="flex items-center space-x-2 md:hidden mb-4">
              <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center text-white">
                <Apple className="w-4.5 h-4.5 text-white" />
              </div>
              <div>
                <span className="text-sm font-bold text-text block leading-none">NutriIntel</span>
                <span className="text-[9px] font-semibold text-muted tracking-wider uppercase block mt-0.5">
                  CLINICAL NUTRITION AI
                </span>
              </div>
            </div>

            <h1 className="text-xl sm:text-2xl font-bold text-text tracking-tight">Welcome back</h1>
            <p className="text-xs sm:text-sm text-muted mt-1">
              Sign in to continue to your nutrition dashboard
            </p>
          </div>

          {errorMessage && (
            <div className="mb-5 p-3 rounded-xl bg-danger-soft border border-danger/30 text-xs font-semibold text-danger flex items-center">
              <span>{errorMessage}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label
                htmlFor="email"
                className="block text-xs font-semibold text-muted uppercase tracking-wider mb-1"
              >
                Email Address <span className="text-danger">*</span>
              </label>
              <input
                id="email"
                type="email"
                autoComplete="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="name@example.com"
                className="w-full px-3.5 py-2.5 rounded-xl border border-border bg-surface text-text text-sm placeholder:text-muted/60 focus:border-primary focus:ring-1 focus:ring-primary transition-colors"
              />
            </div>

            <div>
              <label
                htmlFor="password"
                className="block text-xs font-semibold text-muted uppercase tracking-wider mb-1"
              >
                Password <span className="text-danger">*</span>
              </label>
              <div className="relative">
                <input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  autoComplete="current-password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter your password"
                  className="w-full px-3.5 py-2.5 pr-10 rounded-xl border border-border bg-surface text-text text-sm placeholder:text-muted/60 focus:border-primary focus:ring-1 focus:ring-primary transition-colors"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted hover:text-text p-0.5 rounded transition-colors"
                  aria-label={showPassword ? 'Hide password' : 'Show password'}
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            <div className="flex items-center justify-between text-xs pt-1">
              <label className="flex items-center space-x-2 cursor-pointer select-none">
                <input
                  type="checkbox"
                  checked={rememberMe}
                  onChange={(e) => setRememberMe(e.target.checked)}
                  className="rounded border-border text-primary focus:ring-primary w-4 h-4"
                />
                <span className="text-muted">Remember me (30 days)</span>
              </label>
            </div>

            <Button
              type="submit"
              variant="primary"
              size="lg"
              isLoading={isLoading}
              className="w-full mt-2"
            >
              Sign In
            </Button>
          </form>

          <div className="mt-6 pt-5 border-t border-border text-center text-xs text-muted">
            Don&apos;t have an account?{' '}
            <Link to="/register" className="font-semibold text-primary hover:underline">
              Create an account
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};
