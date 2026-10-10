import React from 'react';
import { Apple, CheckCircle2 } from 'lucide-react';
import { Link } from 'react-router-dom';

export const Footer: React.FC = () => {
  return (
    <footer className="bg-surface border-t border-border mt-16 py-10">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-8">
          {/* Logo & Description */}
          <div className="md:col-span-2 space-y-3">
            <div className="flex items-center space-x-2">
              <div className="w-7 h-7 rounded-lg bg-primary flex items-center justify-center text-white">
                <Apple className="w-4 h-4 text-white" />
              </div>
              <span className="text-sm font-bold text-text">NutriIntel AI</span>
            </div>
            <p className="text-xs text-muted max-w-sm leading-relaxed">
              Evidence-based clinical nutrition intelligence combining Mifflin-St Jeor metabolic
              formulations, calibrated LightGBM lifestyle screening, and Mixed-Integer Linear
              Programming optimization.
            </p>
            {/* Operational Status Pill */}
            <div className="inline-flex items-center px-2.5 py-1 rounded-full bg-primary-soft border border-primary/20 text-primary text-xs font-semibold">
              <CheckCircle2 className="w-3.5 h-3.5 mr-1.5 text-primary" />
              Systems Operational (API v1.0.0)
            </div>
          </div>

          {/* Clinical Tools Links */}
          <div>
            <h4 className="text-xs font-bold text-text uppercase tracking-wider mb-3">Clinical Tools</h4>
            <ul className="space-y-2 text-xs text-muted">
              <li>
                <Link to="/health-check" className="hover:text-primary transition-colors">
                  Health & Metabolic Check
                </Link>
              </li>
              <li>
                <Link to="/risk-predictor" className="hover:text-primary transition-colors">
                  Lifestyle Risk Screening
                </Link>
              </li>
              <li>
                <Link to="/diet-planner" className="hover:text-primary transition-colors">
                  LP Diet Optimization
                </Link>
              </li>
              <li>
                <Link to="/food-explorer" className="hover:text-primary transition-colors">
                  Food Explorer & Swaps
                </Link>
              </li>
            </ul>
          </div>

          {/* Privacy & Evidence Links */}
          <div>
            <h4 className="text-xs font-bold text-text uppercase tracking-wider mb-3">Governance</h4>
            <ul className="space-y-2 text-xs text-muted">
              <li>
                <Link to="/condition-advisor" className="hover:text-primary transition-colors">
                  Guideline Citations
                </Link>
              </li>
              <li>
                <Link to="/profile" className="hover:text-primary transition-colors">
                  Privacy & Data Export
                </Link>
              </li>
              <li>
                <span className="text-muted/80">Educational Non-Diagnostic Standard</span>
              </li>
              <li>
                <span className="text-muted/80">HIPAA/GDPR Data Minimization</span>
              </li>
            </ul>
          </div>
        </div>

        {/* Muted Copyright */}
        <div className="pt-6 border-t border-border flex flex-col sm:flex-row items-center justify-between text-xs text-muted">
          <p>&copy; {new Date().getFullYear()} AI Nutrition Intelligence System. All rights reserved.</p>
          <p className="mt-2 sm:mt-0 text-[11px]">
            Designed for educational and metabolic health assessment purposes only.
          </p>
        </div>
      </div>
    </footer>
  );
};
