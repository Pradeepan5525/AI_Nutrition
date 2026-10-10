import React, { useState, useEffect } from 'react';
import {
  TrendingUp,
  Plus,
  Trash2,
  Bell,
  CheckCircle2,
  AlertTriangle,
  Clock,
  Target,
} from 'lucide-react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from 'recharts';
import { api } from '../api/endpoints';
import { Card } from '../components/common/Card';
import { Badge } from '../components/common/Badge';
import { Button } from '../components/common/Button';
import { DisclaimerNotice } from '../components/common/DisclaimerNotice';

export const ProgressAlerts: React.FC = () => {
  const [weights, setWeights] = useState<any[]>([]);
  const [goalsAlerts, setGoalsAlerts] = useState<any[]>([]);
  const [notifications, setNotifications] = useState<any[]>([]);

  // Weight entry form
  const [newWeight, setNewWeight] = useState<string>('72.0');
  const [note, setNote] = useState<string>('');
  const [isSubmittingWeight, setIsSubmittingWeight] = useState(false);

  // Goal form
  const [targetWeight, setTargetWeight] = useState<number>(70.0);
  const [calorieCap, setCalorieCap] = useState<number>(2100);
  const [sodiumCap, setSodiumCap] = useState<number>(2300);
  const [waterTarget, setWaterTarget] = useState<number>(2500);
  const [isSavingGoal, setIsSavingGoal] = useState(false);
  const [goalSavedSuccess, setGoalSavedSuccess] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [wList, gList, nList] = await Promise.all([
        api.weights.list(),
        api.goals.list(),
        api.notifications.list(),
      ]);
      setWeights(wList || []);
      setGoalsAlerts(gList || []);
      setNotifications(nList || []);

      if (gList && gList.length > 0) {
        const g = gList[0];
        if (g.target_weight_kg) setTargetWeight(g.target_weight_kg);
        if (g.daily_calorie_cap) setCalorieCap(g.daily_calorie_cap);
        if (g.sodium_cap_mg) setSodiumCap(g.sodium_cap_mg);
        if (g.hydration_target_ml) setWaterTarget(g.hydration_target_ml);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleAddWeight = async (e: React.FormEvent) => {
    e.preventDefault();
    const wtNum = parseFloat(newWeight);
    if (isNaN(wtNum) || wtNum < 30 || wtNum > 300) return;

    setIsSubmittingWeight(true);
    try {
      await api.weights.add({ weight_kg: wtNum, note });
      setNote('');
      await loadData();
    } catch (err) {
      console.error(err);
    } finally {
      setIsSubmittingWeight(false);
    }
  };

  const handleDeleteWeight = async (id: number) => {
    try {
      await api.weights.delete(id);
      await loadData();
    } catch (err) {
      console.error(err);
    }
  };

  const handleSaveGoal = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSavingGoal(true);
    setGoalSavedSuccess(false);
    try {
      await api.goals.update({
        target_weight_kg: targetWeight,
        daily_calorie_cap: calorieCap,
        sodium_cap_mg: sodiumCap,
        hydration_target_ml: waterTarget,
      });
      setGoalSavedSuccess(true);
      await loadData();
    } catch (err) {
      console.error(err);
    } finally {
      setIsSavingGoal(false);
    }
  };

  // Format weights for chart
  const chartData = weights.map((w) => ({
    date: w.logged_at ? new Date(w.logged_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric' }) : 'Log',
    weight: w.weight_kg,
  }));

  const activeAlert = goalsAlerts[0];

  return (
    <div className="space-y-6">
      {/* Header Card */}
      <Card className="p-6">
        <div className="flex items-center space-x-2 mb-2">
          <Badge variant="accent">Module 06</Badge>
          <Badge variant="neutral">Longitudinal Monitoring</Badge>
        </div>
        <h1 className="text-2xl font-bold text-text">Progress Telemetry &amp; Clinical Alerts</h1>
        <p className="text-xs sm:text-sm text-muted mt-1">
          Longitudinal weight tracking, metabolic goal constraints, and active rule-triggered alerts.
        </p>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left Column: Weight Chart & Logger */}
        <div className="lg:col-span-7 space-y-5">
          {/* Weight Line Chart Card */}
          <Card className="p-5">
            <div className="flex items-center justify-between pb-3 border-b border-border mb-4">
              <div>
                <h3 className="text-sm font-bold text-text">Weight Telemetry Trend</h3>
                <span className="text-[11px] text-muted">
                  Tracking changes against your target ({targetWeight} kg)
                </span>
              </div>
              <Badge variant="success">Active Log</Badge>
            </div>

            {chartData.length > 0 ? (
              <div className="h-64 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={chartData} margin={{ top: 10, right: 20, left: -10, bottom: 0 }}>
                    <CartesianGrid stroke="#E5E9EE" strokeDasharray="3 3" vertical={false} />
                    <XAxis
                      dataKey="date"
                      stroke="#64748B"
                      fontSize={11}
                      tickLine={false}
                      axisLine={{ stroke: '#E5E9EE' }}
                    />
                    <YAxis
                      domain={['auto', 'auto']}
                      stroke="#64748B"
                      fontSize={11}
                      tickLine={false}
                      axisLine={{ stroke: '#E5E9EE' }}
                      unit="kg"
                    />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: '#FFFFFF',
                        border: '1px solid #E5E9EE',
                        borderRadius: '12px',
                        fontSize: '12px',
                        boxShadow: '0 4px 6px -1px rgba(15, 23, 42, 0.04)',
                      }}
                      labelStyle={{ color: '#0F172A', fontWeight: 'bold' }}
                      itemStyle={{ color: '#047857' }}
                    />
                    <Line
                      type="monotone"
                      dataKey="weight"
                      name="Weight (kg)"
                      stroke="#047857"
                      strokeWidth={2.5}
                      dot={{ fill: '#10B981', r: 4, stroke: '#FFFFFF', strokeWidth: 2 }}
                      activeDot={{ fill: '#047857', r: 6 }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <div className="h-48 flex items-center justify-center text-xs text-muted border border-dashed border-border rounded-xl">
                No body weight measurements recorded yet. Add your first entry below.
              </div>
            )}
          </Card>

          {/* Add Weight Entry Form */}
          <Card className="p-5">
            <h3 className="text-xs font-bold text-muted uppercase tracking-wider mb-3">
              Log Body Weight Measurement
            </h3>
            <form onSubmit={handleAddWeight} className="grid grid-cols-1 sm:grid-cols-12 gap-3">
              <div className="sm:col-span-4">
                <label className="block text-[11px] font-semibold text-muted uppercase mb-1">
                  Weight (kg) <span className="text-danger">*</span>
                </label>
                <input
                  type="number"
                  step="0.1"
                  min="30"
                  max="300"
                  required
                  value={newWeight}
                  onChange={(e) => setNewWeight(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl border border-border bg-surface text-text text-sm focus:border-primary focus:ring-1 focus:ring-primary"
                />
              </div>

              <div className="sm:col-span-5">
                <label className="block text-[11px] font-semibold text-muted uppercase mb-1">
                  Measurement Note (Optional)
                </label>
                <input
                  type="text"
                  placeholder="e.g. Morning fasted"
                  value={note}
                  onChange={(e) => setNote(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl border border-border bg-surface text-text text-sm focus:border-primary focus:ring-1 focus:ring-primary"
                />
              </div>

              <div className="sm:col-span-3 flex items-end">
                <Button
                  type="submit"
                  variant="primary"
                  size="md"
                  isLoading={isSubmittingWeight}
                  className="w-full h-10"
                  leftIcon={<Plus className="w-4 h-4" />}
                >
                  Log Entry
                </Button>
              </div>
            </form>

            {/* Recent Weight Records List */}
            {weights.length > 0 && (
              <div className="mt-4 pt-3 border-t border-border">
                <span className="text-[11px] font-bold text-muted uppercase block mb-2">
                  Recent Records ({weights.length})
                </span>
                <div className="space-y-1.5 max-h-40 overflow-y-auto">
                  {weights.slice().reverse().map((w) => (
                    <div
                      key={w.id}
                      className="flex items-center justify-between p-2 rounded-lg bg-bg text-xs"
                    >
                      <div>
                        <span className="font-bold text-text">{w.weight_kg} kg</span>
                        {w.bmi && <span className="text-muted ml-2">(BMI: {w.bmi})</span>}
                        {w.note && <span className="text-muted italic ml-2">&bull; {w.note}</span>}
                      </div>
                      <div className="flex items-center space-x-2">
                        <span className="text-[10px] text-muted">
                          {new Date(w.logged_at).toLocaleDateString()}
                        </span>
                        <button
                          onClick={() => handleDeleteWeight(w.id)}
                          className="text-muted hover:text-danger p-0.5"
                          aria-label="Delete entry"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </Card>
        </div>

        {/* Right Column: Goal Settings & My Alerts */}
        <div className="lg:col-span-5 space-y-5">
          {/* Active Alerts Card */}
          <Card className="p-5">
            <div className="flex items-center justify-between pb-3 border-b border-border mb-3">
              <h3 className="text-xs font-bold text-text uppercase tracking-wider flex items-center">
                <Bell className="w-4 h-4 mr-1 text-primary" />
                My Proactive Alerts
              </h3>
              <Badge variant={activeAlert?.status === 'triggered' ? 'warning' : 'success'}>
                {activeAlert?.status === 'triggered' ? 'Triggered!' : 'Active'}
              </Badge>
            </div>

            <div className="p-3.5 rounded-xl bg-bg border border-border space-y-2 text-xs">
              <div className="flex items-center justify-between">
                <span className="font-semibold text-text">Metabolic Monitoring</span>
                <span className="text-[10px] text-muted">Evaluated daily</span>
              </div>
              <p className="text-muted leading-relaxed">
                {activeAlert?.message || 'All nutritional metrics within established clinical bounds.'}
              </p>
              <div className="pt-2 border-t border-border flex items-center justify-between text-[11px]">
                <span className="text-muted">Target Weight: {targetWeight} kg</span>
                <button
                  type="button"
                  onClick={loadData}
                  className="font-semibold text-primary hover:underline"
                >
                  Check Now
                </button>
              </div>
            </div>
          </Card>

          {/* Goal Setting Form */}
          <Card className="p-5">
            <h3 className="text-xs font-bold text-muted uppercase tracking-wider mb-3 flex items-center">
              <Target className="w-4 h-4 mr-1 text-primary" />
              Nutritional Target Configuration
            </h3>

            <form onSubmit={handleSaveGoal} className="space-y-3 text-xs">
              <div>
                <label className="block text-[11px] font-semibold text-muted uppercase mb-1">
                  Target Goal Weight (kg)
                </label>
                <input
                  type="number"
                  step="0.5"
                  value={targetWeight}
                  onChange={(e) => setTargetWeight(Number(e.target.value))}
                  className="w-full px-3 py-2 rounded-xl border border-border bg-surface text-text text-sm focus:border-primary focus:ring-1 focus:ring-primary"
                />
              </div>

              <div>
                <label className="block text-[11px] font-semibold text-muted uppercase mb-1">
                  Daily Calorie Ceiling (kcal)
                </label>
                <input
                  type="number"
                  step="50"
                  value={calorieCap}
                  onChange={(e) => setCalorieCap(Number(e.target.value))}
                  className="w-full px-3 py-2 rounded-xl border border-border bg-surface text-text text-sm focus:border-primary focus:ring-1 focus:ring-primary"
                />
              </div>

              <div>
                <label className="block text-[11px] font-semibold text-muted uppercase mb-1">
                  Sodium Cap (mg/day)
                </label>
                <input
                  type="number"
                  step="50"
                  value={sodiumCap}
                  onChange={(e) => setSodiumCap(Number(e.target.value))}
                  className="w-full px-3 py-2 rounded-xl border border-border bg-surface text-text text-sm focus:border-primary focus:ring-1 focus:ring-primary"
                />
              </div>

              <div>
                <label className="block text-[11px] font-semibold text-muted uppercase mb-1">
                  Hydration Target (ml/day)
                </label>
                <input
                  type="number"
                  step="100"
                  value={waterTarget}
                  onChange={(e) => setWaterTarget(Number(e.target.value))}
                  className="w-full px-3 py-2 rounded-xl border border-border bg-surface text-text text-sm focus:border-primary focus:ring-1 focus:ring-primary"
                />
              </div>

              <Button
                type="submit"
                variant="primary"
                size="md"
                isLoading={isSavingGoal}
                className="w-full mt-2"
              >
                Update Targets
              </Button>

              {goalSavedSuccess && (
                <div className="p-2.5 rounded-lg bg-primary-soft text-primary font-semibold text-center text-xs flex items-center justify-center">
                  <CheckCircle2 className="w-3.5 h-3.5 mr-1" />
                  Target constraints updated!
                </div>
              )}
            </form>
          </Card>
        </div>
      </div>

      <DisclaimerNotice />
    </div>
  );
};
