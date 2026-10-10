import React from 'react';
import { Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { useAuth } from './context/AuthContext';
import { FullPageSkeleton } from './components/common/FullPageSkeleton';
import { AppShell } from './components/layout/AppShell';
import { Toast } from './components/common/Toast';

// Pages
import { Login } from './pages/Login';
import { Register } from './pages/Register';
import { Onboarding } from './pages/Onboarding';
import { Dashboard } from './pages/Dashboard';
import { HealthCheck } from './pages/HealthCheck';
import { RiskPredictor } from './pages/RiskPredictor';
import { DietPlanner } from './pages/DietPlanner';
import { FoodExplorer } from './pages/FoodExplorer';
import { ConditionAdvisor } from './pages/ConditionAdvisor';
import { ProgressAlerts } from './pages/ProgressAlerts';
import { History } from './pages/History';
import { Profile } from './pages/Profile';
import { NotFound } from './pages/NotFound';

/**
 * Protected Route Guard:
 * - Shows full-page skeleton while checking auth (never flash).
 * - Redirects unauthenticated visitors to /login preserving target location.
 * - Redirects users with incomplete onboarding to /onboarding.
 */
const ProtectedRoute: React.FC<{ children: React.ReactElement }> = ({ children }) => {
  const { user, isLoading } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return <FullPageSkeleton />;
  }

  if (!user) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // If user has not completed onboarding and is not currently on /onboarding
  const profile = user.profile || user.saved_profile;
  const onboardingCompleted = profile?.onboarding_completed;
  if (!onboardingCompleted && location.pathname !== '/onboarding') {
    return <Navigate to="/onboarding" replace />;
  }

  return children;
};

/**
 * Public Route Guard:
 * - Redirects logged-in users away from /login and /register to /dashboard.
 */
const PublicRoute: React.FC<{ children: React.ReactElement }> = ({ children }) => {
  const { user, isLoading } = useAuth();

  if (isLoading) {
    return <FullPageSkeleton />;
  }

  if (user) {
    return <Navigate to="/dashboard" replace />;
  }

  return children;
};

export const App: React.FC = () => {
  const { sessionExpiredToast, dismissSessionToast } = useAuth();

  return (
    <>
      {sessionExpiredToast && (
        <Toast
          type="warning"
          message="Session expired, please sign in again"
          onClose={dismissSessionToast}
        />
      )}
      <Routes>
      {/* Public Routes */}
      <Route
        path="/login"
        element={
          <PublicRoute>
            <Login />
          </PublicRoute>
        }
      />
      <Route
        path="/register"
        element={
          <PublicRoute>
            <Register />
          </PublicRoute>
        }
      />

      {/* Onboarding Wizard Route (Protected) */}
      <Route
        path="/onboarding"
        element={
          <ProtectedRoute>
            <Onboarding />
          </ProtectedRoute>
        }
      />

      {/* Protected App Layout Routes */}
      <Route
        element={
          <ProtectedRoute>
            <AppShell />
          </ProtectedRoute>
        }
      >
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/health-check" element={<HealthCheck />} />
        <Route path="/risk-predictor" element={<RiskPredictor />} />
        <Route path="/diet-planner" element={<DietPlanner />} />
        <Route path="/food-explorer" element={<FoodExplorer />} />
        <Route path="/condition-advisor" element={<ConditionAdvisor />} />
        <Route path="/progress-alerts" element={<ProgressAlerts />} />
        <Route path="/history" element={<History />} />
        <Route path="/profile" element={<Profile />} />
        <Route path="*" element={<NotFound />} />
      </Route>
    </Routes>
    </>
  );
};

export default App;
