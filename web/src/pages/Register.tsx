import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Apple, Eye, EyeOff, ShieldCheck, Sparkles, CheckCircle2 } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { Button } from '../components/common/Button';

export const Register: React.FC = () => {
  const { register, user } = useAuth();
  const navigate = useNavigate();

  React.useEffect(() => {
    if (user) {
      navigate('/dashboard', { replace: true });
    }
  }, [user, navigate]);

  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [acceptDisclaimer, setAcceptDisclaimer] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  // Live password strength
  const hasMinLength = password.length >= 8;
  const hasLetter = /[A-Za-z]/.test(password);
  const hasDigit = /\d/.test(password);
  const isPasswordValid = hasMinLength && hasLetter && hasDigit;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);

    if (!isPasswordValid) {
      setErrorMessage('Password must be at least 8 characters long and contain both letters and numbers.');
      return;
    }

    if (password !== confirmPassword) {
      setErrorMessage('Passwords do not match. Please re-enter.');
      return;
    }

    if (!acceptDisclaimer) {
      setErrorMessage('You must acknowledge that this application is for educational purposes.');
      return;
    }

    setIsLoading(true);
    try {
      await register({
        email,
        password,
        full_name: fullName,
        accept_disclaimer: acceptDisclaimer,
      });

      // Send to onboarding wizard on first signup
      navigate('/onboarding', { replace: true });
    } catch (err: any) {
      setErrorMessage(err.message || 'Registration failed. Email may already be registered.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-bg flex items-center justify-center p-4 sm:p-6 lg:p-8">
      <div className="w-full max-w-4xl bg-surface border border-border rounded-card shadow-soft overflow-hidden grid grid-cols-1 md:grid-cols-2">
        {/* Left Dark Gradient Panel */}
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
              Join NutriIntel
            </div>

            <h2 className="text-2xl font-bold text-white tracking-tight leading-snug mb-3">
              Personalized Clinical Nutrition Intelligence
            </h2>
            <p className="text-xs text-muted leading-relaxed mb-8">
              Create an account to track your metabolic targets, screen lifestyle habits, and generate
              diet recommendations tailored to your conditions and allergies.
            </p>

            <div className="space-y-4 text-xs text-white/90">
              <div className="flex items-start space-x-3">
                <CheckCircle2 className="w-4 h-4 text-primary-accent flex-shrink-0 mt-0.5" />
                <div>
                  <span className="font-semibold block text-white">Confidential Profile</span>
                  <span className="text-white/70">Your health data is isolated to your account only.</span>
                </div>
              </div>
              <div className="flex items-start space-x-3">
                <CheckCircle2 className="w-4 h-4 text-primary-accent flex-shrink-0 mt-0.5" />
                <div>
                  <span className="font-semibold block text-white">Evidence-Based Guidelines</span>
                  <span className="text-white/70">Full audit citations from AHA, ADA, and WHO.</span>
                </div>
              </div>
              <div className="flex items-start space-x-3">
                <ShieldCheck className="w-4 h-4 text-primary-accent flex-shrink-0 mt-0.5" />
                <div>
                  <span className="font-semibold block text-white">Full Data Ownership</span>
                  <span className="text-white/70">One-click GDPR data export and account deletion.</span>
                </div>
              </div>
            </div>
          </div>

          <div className="pt-6 border-t border-border/10 text-[11px] text-white/50">
            Privacy: We store minimal personal data necessary solely for metabolic modeling.
          </div>
        </div>

        {/* Right Form Panel */}
        <div className="p-8 sm:p-10 flex flex-col justify-center">
          <div className="mb-6">
            <h1 className="text-xl sm:text-2xl font-bold text-text tracking-tight">Create your account</h1>
            <p className="text-xs sm:text-sm text-muted mt-1">
              Start your personalized nutritional intelligence journey
            </p>
          </div>

          {errorMessage && (
            <div className="mb-4 p-3 rounded-xl bg-danger-soft border border-danger/30 text-xs font-semibold text-danger">
              {errorMessage}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-3.5">
            <div>
              <label
                htmlFor="fullName"
                className="block text-xs font-semibold text-muted uppercase tracking-wider mb-1"
              >
                Full Name <span className="text-danger">*</span>
              </label>
              <input
                id="fullName"
                type="text"
                required
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder="Alex Carter"
                className="w-full px-3.5 py-2 rounded-xl border border-border bg-surface text-text text-sm focus:border-primary focus:ring-1 focus:ring-primary"
              />
            </div>

            <div>
              <label
                htmlFor="regEmail"
                className="block text-xs font-semibold text-muted uppercase tracking-wider mb-1"
              >
                Email Address <span className="text-danger">*</span>
              </label>
              <input
                id="regEmail"
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="name@example.com"
                className="w-full px-3.5 py-2 rounded-xl border border-border bg-surface text-text text-sm focus:border-primary focus:ring-1 focus:ring-primary"
              />
            </div>

            <div>
              <label
                htmlFor="regPassword"
                className="block text-xs font-semibold text-muted uppercase tracking-wider mb-1"
              >
                Password <span className="text-danger">*</span>
              </label>
              <div className="relative">
                <input
                  id="regPassword"
                  type={showPassword ? 'text' : 'password'}
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Min 8 characters, letters & digits"
                  className="w-full px-3.5 py-2 pr-10 rounded-xl border border-border bg-surface text-text text-sm focus:border-primary focus:ring-1 focus:ring-primary"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted hover:text-text p-0.5 rounded"
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>

              {/* Live Strength Hints */}
              <div className="mt-1.5 flex items-center space-x-3 text-[11px] text-muted">
                <span className={hasMinLength ? 'text-primary font-medium' : ''}>
                  &bull; 8+ chars
                </span>
                <span className={hasLetter ? 'text-primary font-medium' : ''}>
                  &bull; Letters
                </span>
                <span className={hasDigit ? 'text-primary font-medium' : ''}>
                  &bull; Numbers
                </span>
              </div>
            </div>

            <div>
              <label
                htmlFor="confirmPassword"
                className="block text-xs font-semibold text-muted uppercase tracking-wider mb-1"
              >
                Confirm Password <span className="text-danger">*</span>
              </label>
              <input
                id="confirmPassword"
                type="password"
                required
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="Re-enter password"
                className="w-full px-3.5 py-2 rounded-xl border border-border bg-surface text-text text-sm focus:border-primary focus:ring-1 focus:ring-primary"
              />
            </div>

            {/* Educational Disclaimer Checkbox */}
            <div className="pt-1">
              <label className="flex items-start space-x-2.5 cursor-pointer">
                <input
                  type="checkbox"
                  required
                  checked={acceptDisclaimer}
                  onChange={(e) => setAcceptDisclaimer(e.target.checked)}
                  className="rounded border-border text-primary focus:ring-primary w-4 h-4 mt-0.5 flex-shrink-0"
                />
                <span className="text-xs text-muted leading-tight">
                  I understand this app is educational and not medical advice.{' '}
                  <span className="text-danger">*</span>
                </span>
              </label>
            </div>

            <Button
              type="submit"
              variant="primary"
              size="lg"
              isLoading={isLoading}
              className="w-full mt-3"
            >
              Create Account
            </Button>
          </form>

          <div className="mt-5 pt-4 border-t border-border text-center text-xs text-muted">
            Already have an account?{' '}
            <Link to="/login" className="font-semibold text-primary hover:underline">
              Sign in
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};
