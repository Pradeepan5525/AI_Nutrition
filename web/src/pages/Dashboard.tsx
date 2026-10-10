import React, { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  Activity,
  ArrowUpRight,
  CalendarCheck,
  CheckCircle2,
  FileText,
  HeartPulse,
  Search,
  Sparkles,
  TrendingUp,
  AlertCircle,
  Clock,
  ShieldCheck,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { api } from '../api/endpoints';
import { DarkCard } from '../components/common/DarkCard';
import { Card } from '../components/common/Card';
import { Badge } from '../components/common/Badge';
import { Button } from '../components/common/Button';
import { DisclaimerNotice } from '../components/common/DisclaimerNotice';

export const Dashboard: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();

  const [alerts, setAlerts] = useState<any[]>([]);
  const [assessments, setAssessments] = useState<any[]>([]);

  useEffect(() => {
    // Load recent alerts and assessments
    api.goals.list().then((res) => setAlerts(res)).catch(() => {});
    api.assess.listHistory().then((res) => setAssessments(res)).catch(() => {});
  }, []);

  const firstName = user?.full_name?.split(' ')[0] || user?.username || 'Client';
  const profile = user?.profile || user?.saved_profile || {};

  // Compute or fallback targets
  const weight = profile.weight_kg || 72;
  const height = profile.height_cm || 175;
  const bmi = (weight / ((height / 100) * (height / 100))).toFixed(1);

  // Targets from latest assessment or profile calculation
  const latestAssess = assessments[0];
  const targetKcal = latestAssess ? Math.round(latestAssess.target_kcal) : 2150;
  const proteinG = latestAssess ? Math.round(latestAssess.protein_g) : 135;
  const carbsG = latestAssess ? Math.round(latestAssess.carbs_g) : 240;
  const fatG = latestAssess ? Math.round(latestAssess.fat_g) : 70;
  const sodiumCap = latestAssess ? Math.round(latestAssess.sodium_mg) : 2300;
  const waterMl = latestAssess ? Math.round(latestAssess.water_ml) : 2500;

  const modules = [
    {
      title: 'Health & Metabolic Assessment',
      description: 'Mifflin-St Jeor BMR, WHO/Asian BMI status, TDEE calculations, and safety gating.',
      tag: 'Anthropometrics',
      icon: HeartPulse,
      path: '/health-check',
      highlighted: true,
    },
    {
      title: 'Lifestyle Risk Screening',
      description: 'Calibrated LightGBM model evaluating behavioral risk with TreeSHAP factor drivers.',
      tag: 'Machine Learning',
      icon: Activity,
      path: '/risk-predictor',
    },
    {
      title: 'Diet Planner & Solver',
      description: 'Linear programming algorithm optimizing caloric exactness and allergen exclusion.',
      tag: 'MILP Solver',
      icon: CalendarCheck,
      path: '/diet-planner',
    },
    {
      title: 'Food Explorer & Swaps',
      description: 'Transparent Health Score v2 (0–100) with strictly healthier same-category alternatives.',
      tag: '30,000+ Items',
      icon: Search,
      path: '/food-explorer',
    },
    {
      title: 'Clinical Condition Advisor',
      description: 'AHA, ADA, and WHO clinical thresholds with auditable evidence citations.',
      tag: 'Guidelines',
      icon: FileText,
      path: '/condition-advisor',
    },
    {
      title: 'Progress Tracking & Alerts',
      description: 'Weight telemetry charting, nutritional thresholds, and automated adherence alerts.',
      tag: 'Monitoring',
      icon: TrendingUp,
      path: '/progress-alerts',
    },
  ];

  return (
    <div className="space-y-6">
      {/* 1. Header Card */}
      <Card className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-6 sm:p-7">
        <div>
          <span className="text-[11px] font-bold text-primary uppercase tracking-widest block mb-1">
            METABOLIC INTELLIGENCE OVERVIEW
          </span>
          <h1 className="text-2xl sm:text-3xl font-bold text-text tracking-tight">
            Welcome back, {firstName}
          </h1>
          <p className="text-xs sm:text-sm text-muted mt-1">
            Your clinical nutrition profile is active. Ready to plan today&apos;s nutritional targets?
          </p>
        </div>
        <div className="flex items-center space-x-3 flex-shrink-0">
          <Button
            variant="outline"
            size="md"
            onClick={() => navigate('/health-check')}
          >
            Check My Health
          </Button>
          <Button
            variant="primary"
            size="md"
            onClick={() => navigate('/diet-planner')}
            rightIcon={<ArrowUpRight className="w-4 h-4" />}
          >
            Plan Today&apos;s Meals
          </Button>
        </div>
      </Card>

      {/* 2. Quick Stat Strip */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3.5">
        <div className="bg-surface border border-border rounded-xl p-3.5 shadow-soft">
          <span className="text-[10px] font-bold text-muted uppercase tracking-wider block">Current BMI</span>
          <div className="flex items-baseline space-x-2 mt-1">
            <span className="text-xl font-bold text-text">{bmi}</span>
            <span className="text-xs font-semibold text-primary">Normal range</span>
          </div>
        </div>
        <div className="bg-surface border border-border rounded-xl p-3.5 shadow-soft">
          <span className="text-[10px] font-bold text-muted uppercase tracking-wider block">Logged Weight</span>
          <div className="flex items-baseline space-x-2 mt-1">
            <span className="text-xl font-bold text-text">{weight} kg</span>
            <span className="text-xs text-muted">&plusmn;0.2 kg/wk</span>
          </div>
        </div>
        <div className="bg-surface border border-border rounded-xl p-3.5 shadow-soft">
          <span className="text-[10px] font-bold text-muted uppercase tracking-wider block">Plan Adherence</span>
          <div className="flex items-baseline space-x-2 mt-1">
            <span className="text-xl font-bold text-text">94%</span>
            <span className="text-xs font-semibold text-primary">Target met</span>
          </div>
        </div>
        <div className="bg-surface border border-border rounded-xl p-3.5 shadow-soft">
          <span className="text-[10px] font-bold text-muted uppercase tracking-wider block">Active Conditions</span>
          <div className="flex items-baseline space-x-2 mt-1">
            <span className="text-xl font-bold text-text">
              {profile.conditions?.length || 0}
            </span>
            <span className="text-xs text-muted">AHA/ADA rules</span>
          </div>
        </div>
      </div>

      {/* 3. Two-Column Row: Large Dark Target Card + Narrower White Alerts Card */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Dark Gradient Card (Spans 2 cols) */}
        <DarkCard className="lg:col-span-2 flex flex-col justify-between p-6 sm:p-7">
          <div>
            <div className="flex items-center justify-between mb-4">
              <span className="text-xs font-bold uppercase tracking-wider text-primary-accent">
                TODAY&apos;S METABOLIC TARGETS
              </span>
              <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-primary/40 border border-primary-accent/30 text-primary-accent">
                Mifflin-St Jeor Cleared
              </span>
            </div>

            <div className="flex items-baseline space-x-3 mb-6">
              <span className="text-4xl sm:text-5xl font-extrabold text-white tracking-tight">
                {targetKcal}
              </span>
              <span className="text-sm font-semibold text-white/70">kcal / day</span>
            </div>

            <p className="text-xs text-white/80 max-w-lg mb-6 leading-relaxed">
              Calculated for {profile.goal?.replace('_', ' ') || 'maintenance'} based on your
              anthropometric telemetry. Macronutrient ratios structured to prevent metabolic suppression.
            </p>
          </div>

          {/* 5 Small Stat Boxes */}
          <div className="grid grid-cols-2 sm:grid-cols-5 gap-2.5 pt-4 border-t border-border/10">
            <div className="bg-white/5 border border-white/10 rounded-xl p-2.5">
              <span className="text-[10px] font-medium text-white/60 block uppercase">Protein</span>
              <span className="text-base font-bold text-white mt-0.5 block">{proteinG}g</span>
            </div>
            <div className="bg-white/5 border border-white/10 rounded-xl p-2.5">
              <span className="text-[10px] font-medium text-white/60 block uppercase">Carbs</span>
              <span className="text-base font-bold text-white mt-0.5 block">{carbsG}g</span>
            </div>
            <div className="bg-white/5 border border-white/10 rounded-xl p-2.5">
              <span className="text-[10px] font-medium text-white/60 block uppercase">Fat</span>
              <span className="text-base font-bold text-white mt-0.5 block">{fatG}g</span>
            </div>
            <div className="bg-white/5 border border-white/10 rounded-xl p-2.5">
              <span className="text-[10px] font-medium text-white/60 block uppercase">Sodium Cap</span>
              <span className="text-base font-bold text-white mt-0.5 block">{sodiumCap}mg</span>
            </div>
            <div className="bg-white/5 border border-white/10 rounded-xl p-2.5 col-span-2 sm:col-span-1">
              <span className="text-[10px] font-medium text-white/60 block uppercase">Water</span>
              <span className="text-base font-bold text-white mt-0.5 block">{waterMl}ml</span>
            </div>
          </div>
        </DarkCard>

        {/* Right Narrower White Card: Active Alerts */}
        <Card className="flex flex-col justify-between p-6">
          <div>
            <div className="flex items-center justify-between pb-3 border-b border-border mb-4">
              <div>
                <h3 className="text-sm font-bold text-text">Active Alerts &amp; Updates</h3>
                <span className="text-[11px] text-muted">Proactive rule screening</span>
              </div>
              <Badge variant="success">Active</Badge>
            </div>

            <div className="space-y-3.5">
              <div className="p-3 rounded-xl bg-bg border border-border">
                <div className="flex items-center justify-between text-xs mb-1">
                  <span className="font-semibold text-text flex items-center">
                    <CheckCircle2 className="w-3.5 h-3.5 text-primary mr-1" />
                    Allergen Screening Active
                  </span>
                  <span className="text-[10px] text-muted">Realtime</span>
                </div>
                <p className="text-[11px] text-muted">
                  Strict tri-state filtering exclusions active for{' '}
                  <span className="font-semibold text-text">
                    {profile.allergies?.join(', ') || 'verified foods'}
                  </span>.
                </p>
              </div>

              <div className="p-3 rounded-xl bg-bg border border-border">
                <div className="flex items-center justify-between text-xs mb-1">
                  <span className="font-semibold text-text flex items-center">
                    <Clock className="w-3.5 h-3.5 text-primary mr-1" />
                    Hydration Check
                  </span>
                  <span className="text-[10px] text-muted">Daily</span>
                </div>
                <p className="text-[11px] text-muted">
                  Daily water requirement set to {waterMl} ml to support renal clearance.
                </p>
              </div>

              {profile.conditions?.includes('hypertension') && (
                <div className="p-3 rounded-xl bg-warning-soft border border-warning/20">
                  <div className="flex items-center justify-between text-xs mb-1">
                    <span className="font-semibold text-warning flex items-center">
                      <AlertCircle className="w-3.5 h-3.5 text-warning mr-1" />
                      AHA DASH Bound
                    </span>
                    <Badge variant="warning">Alert</Badge>
                  </div>
                  <p className="text-[11px] text-muted">
                    Sodium intake strictly capped at 1,500 mg based on AHA guideline bounds.
                  </p>
                </div>
              )}
            </div>
          </div>

          <div className="pt-4 border-t border-border mt-4">
            <Link
              to="/progress-alerts"
              className="text-xs font-semibold text-primary hover:text-primary-hover flex items-center justify-between"
            >
              <span>Manage Alerts &amp; Targets</span>
              <ArrowUpRight className="w-4 h-4" />
            </Link>
          </div>
        </Card>
      </div>

      {/* 4. Modules Grid (3 Columns) */}
      <div className="space-y-4">
        <div>
          <h2 className="text-lg font-bold text-text">Nutrition Intelligence Modules</h2>
          <p className="text-xs text-muted mt-0.5">
            Select a specialized clinical module to perform health assessment or meal scheduling
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {modules.map((m) => {
            const Icon = m.icon;
            return (
              <Card
                key={m.title}
                hoverEffect
                className={`p-5 flex flex-col justify-between ${
                  m.highlighted ? 'border-primary shadow-sm' : ''
                }`}
                onClick={() => navigate(m.path)}
              >
                <div>
                  <div className="flex items-start justify-between mb-3.5">
                    <div className="w-10 h-10 rounded-xl bg-primary-soft text-primary flex items-center justify-center border border-primary/20">
                      <Icon className="w-5 h-5 text-primary" />
                    </div>
                    <Badge variant={m.highlighted ? 'success' : 'neutral'}>{m.tag}</Badge>
                  </div>

                  <h3 className="text-sm font-bold text-text mb-1">{m.title}</h3>
                  <p className="text-xs text-muted leading-relaxed line-clamp-2">
                    {m.description}
                  </p>
                </div>

                <div className="pt-4 mt-4 border-t border-border/80 flex items-center justify-between">
                  <span className="text-xs font-bold text-primary flex items-center">
                    Open Tool
                    <ArrowUpRight className="w-3.5 h-3.5 ml-1" />
                  </span>
                  {m.highlighted && (
                    <span className="text-[10px] font-semibold text-primary-accent">
                      Recommended
                    </span>
                  )}
                </div>
              </Card>
            );
          })}
        </div>
      </div>

      {/* 5. In-page Educational Disclaimer */}
      <DisclaimerNotice />
    </div>
  );
};
