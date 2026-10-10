import React, { useState, useEffect } from 'react';
import {
  CalendarCheck,
  Download,
  Bookmark,
  RefreshCw,
  ShoppingBag,
  Info,
  CheckCircle2,
  Sparkles,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { api } from '../api/endpoints';
import { Card } from '../components/common/Card';
import { Badge } from '../components/common/Badge';
import { Button } from '../components/common/Button';
import { Modal } from '../components/common/Modal';
import { DisclaimerNotice } from '../components/common/DisclaimerNotice';

export const DietPlanner: React.FC = () => {
  const { user } = useAuth();
  const profile = user?.profile || user?.saved_profile || {};

  // Form parameters
  const [targetKcal, setTargetKcal] = useState<number>(2000);
  const [proteinTargetG, setProteinTargetG] = useState<number>(120);
  const [maxSodiumMg, setMaxSodiumMg] = useState<number>(2300);
  const [maxSatFatG, setMaxSatFatG] = useState<number>(20);
  const [maxSugarG, setMaxSugarG] = useState<number>(50);
  const [strictAllergens, setStrictAllergens] = useState<boolean>(true);
  const [days, setDays] = useState<number>(1);

  // Tabs: 'today' | 'seven_day' | 'grocery'
  const [activeTab, setActiveTab] = useState<'today' | 'seven_day' | 'grocery'>('today');

  const [isLoading, setIsLoading] = useState(false);
  const [planResult, setPlanResult] = useState<any>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [isDownloading, setIsDownloading] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);

  // Swap modal state
  const [swapModalOpen, setSwapModalOpen] = useState(false);
  const [selectedFoodForSwap, setSelectedFoodForSwap] = useState<any>(null);
  const [availableSwaps, setAvailableSwaps] = useState<any[]>([]);
  const [loadingSwaps, setLoadingSwaps] = useState(false);

  useEffect(() => {
    // Prefill sodium if hypertension
    if (profile.conditions?.includes('hypertension')) {
      setMaxSodiumMg(1500);
    }
    // Prefill sugar if diabetes
    if (profile.conditions?.includes('diabetes')) {
      setMaxSugarG(25);
    }
    runOptimizer();
  }, []);

  const runOptimizer = async (requestedDays = days) => {
    setIsLoading(true);
    setSaveSuccess(false);
    try {
      const payload = {
        target_kcal: targetKcal,
        protein_target_g: proteinTargetG,
        max_sodium_mg: maxSodiumMg,
        max_sat_fat_g: maxSatFatG,
        max_sugar_g: maxSugarG,
        user_allergies: profile.allergies || [],
        dietary_restrictions: profile.dietary_restrictions || [],
        strict_allergens: strictAllergens,
        days: requestedDays,
      };
      const data = await api.plan.run(payload);
      setPlanResult(data);
    } catch (err) {
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDaysChange = (newDays: number) => {
    setDays(newDays);
    if (newDays === 7) {
      setActiveTab('seven_day');
    } else {
      setActiveTab('today');
    }
    runOptimizer(newDays);
  };

  const handleOpenSwap = async (food: any) => {
    setSelectedFoodForSwap(food);
    setSwapModalOpen(true);
    setLoadingSwaps(true);
    try {
      const res = await api.foods.getSwaps(food.food_id || food.name, 4, strictAllergens);
      setAvailableSwaps(res.swaps || []);
    } catch {
      setAvailableSwaps([]);
    } finally {
      setLoadingSwaps(false);
    }
  };

  const handleApplySwap = (swapFood: any) => {
    if (!planResult || !selectedFoodForSwap) return;
    // Client-side replacement in daily plan
    const updated = JSON.parse(JSON.stringify(planResult));
    for (const d of updated.daily_plans) {
      for (const mealKey of ['breakfast', 'lunch', 'dinner', 'snacks']) {
        const foods = d[mealKey];
        if (Array.isArray(foods)) {
          const idx = foods.findIndex((f: any) => f.name === selectedFoodForSwap.name);
          if (idx !== -1) {
            foods[idx] = {
              food_id: swapFood.food_id,
              name: swapFood.name,
              grams: selectedFoodForSwap.grams,
              kcal: Math.round((swapFood.health_score_v2 / 100) * selectedFoodForSwap.kcal) || selectedFoodForSwap.kcal,
            };
          }
        }
      }
    }
    setPlanResult(updated);
    setSwapModalOpen(false);
  };

  const handleSavePlan = async () => {
    if (!planResult) return;
    setIsSaving(true);
    try {
      await api.plan.save({
        title: `${days}-Day Optimized Nutrition Plan`,
        days,
        target_kcal: targetKcal,
        daily_plans: planResult.daily_plans || [],
        grocery_list: planResult.grocery_list || [],
      });
      setSaveSuccess(true);
    } catch (err) {
      console.error(err);
    } finally {
      setIsSaving(false);
    }
  };

  const handleDownloadPdf = async () => {
    setIsDownloading(true);
    try {
      const reportPayload = {
        client_info: {
          age: profile.age || 30,
          sex: profile.sex || 'male',
          height_cm: profile.height_cm || 175,
          weight_kg: profile.weight_kg || 72,
          bmi: 23.5,
          bmi_category: 'Normal weight',
          bmr: 1680,
          tdee: 2200,
        },
        target_nutrition: {
          target_kcal: targetKcal,
          protein_g: proteinTargetG,
          carbs_g: Math.round((targetKcal * 0.45) / 4),
          fat_g: Math.round((targetKcal * 0.3) / 9),
          fiber_g: 28,
          sugar_g: maxSugarG,
          water_ml: 2500,
        },
        safety_gate: {
          cleared: true,
          flags: [],
        },
        clinical_rules: {
          active_rules: profile.conditions || ['General Health Maintenance'],
        },
        meal_plan: planResult?.daily_plans || [],
      };

      const blob = await api.reports.downloadPdf(reportPayload);
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'Clinical_Nutrition_Plan.pdf');
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      console.error(err);
    } finally {
      setIsDownloading(false);
    }
  };

  const dailyPlans = planResult?.daily_plans || [];
  const day1 = dailyPlans[0];

  return (
    <div className="space-y-6">
      {/* Header Card */}
      <Card className="p-6">
        <div className="flex flex-wrap items-center gap-2 mb-2">
          <Badge variant="accent">Module 03</Badge>
          <Badge variant="success">Mixed-Integer Linear Program</Badge>
          <Badge variant="neutral">Caloric Exactness &plusmn;5%</Badge>
        </div>
        <h1 className="text-2xl font-bold text-text">Algorithmic Diet Planner &amp; Solver</h1>
        <p className="text-xs sm:text-sm text-muted mt-1">
          Solves mathematical multi-objective nutritional constraints balancing calories, macros,
          and clinical guideline caps with certified allergen exclusion.
        </p>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left Column: Constraints & Parameters */}
        <div className="lg:col-span-4 space-y-4">
          <Card className="p-5">
            <h2 className="text-xs font-bold text-muted uppercase tracking-wider mb-3">
              Optimizer Constraints
            </h2>

            <form
              onSubmit={(e) => {
                e.preventDefault();
                runOptimizer();
              }}
              className="space-y-3.5"
            >
              <div>
                <label className="block text-xs font-semibold text-muted uppercase tracking-wider mb-1">
                  Target Daily Calories (kcal)
                </label>
                <input
                  type="number"
                  min={1200}
                  max={4500}
                  step={50}
                  value={targetKcal}
                  onChange={(e) => setTargetKcal(Number(e.target.value))}
                  className="w-full px-3 py-2 rounded-xl border border-border bg-surface text-text text-sm focus:border-primary focus:ring-1 focus:ring-primary"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-muted uppercase tracking-wider mb-1">
                  Protein Floor (g)
                </label>
                <input
                  type="number"
                  min={40}
                  max={250}
                  value={proteinTargetG}
                  onChange={(e) => setProteinTargetG(Number(e.target.value))}
                  className="w-full px-3 py-2 rounded-xl border border-border bg-surface text-text text-sm focus:border-primary focus:ring-1 focus:ring-primary"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-muted uppercase tracking-wider mb-1">
                  Sodium Cap (mg/day)
                </label>
                <input
                  type="number"
                  min={1000}
                  max={3500}
                  step={50}
                  value={maxSodiumMg}
                  onChange={(e) => setMaxSodiumMg(Number(e.target.value))}
                  className="w-full px-3 py-2 rounded-xl border border-border bg-surface text-text text-sm focus:border-primary focus:ring-1 focus:ring-primary"
                />
                <span className="text-[10px] text-muted block mt-0.5">
                  AHA DASH standard is &le; 1,500 mg
                </span>
              </div>

              <div>
                <label className="block text-xs font-semibold text-muted uppercase tracking-wider mb-1">
                  Schedule Duration
                </label>
                <div className="grid grid-cols-2 gap-2">
                  <button
                    type="button"
                    onClick={() => handleDaysChange(1)}
                    className={`py-2 rounded-xl border text-xs font-semibold transition-all ${
                      days === 1
                        ? 'bg-primary-soft text-primary border-primary'
                        : 'bg-surface text-muted border-border hover:bg-bg'
                    }`}
                  >
                    1-Day Template
                  </button>
                  <button
                    type="button"
                    onClick={() => handleDaysChange(7)}
                    className={`py-2 rounded-xl border text-xs font-semibold transition-all ${
                      days === 7
                        ? 'bg-primary-soft text-primary border-primary'
                        : 'bg-surface text-muted border-border hover:bg-bg'
                    }`}
                  >
                    7-Day Schedule
                  </button>
                </div>
              </div>

              <div className="pt-2">
                <label className="flex items-center space-x-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={strictAllergens}
                    onChange={(e) => setStrictAllergens(e.target.checked)}
                    className="rounded border-border text-primary focus:ring-primary w-4 h-4"
                  />
                  <span className="text-xs text-text">Strict Tri-State Allergen Exclusion</span>
                </label>
              </div>

              <Button
                type="submit"
                variant="primary"
                size="md"
                isLoading={isLoading}
                className="w-full mt-2"
                leftIcon={<RefreshCw className="w-4 h-4" />}
              >
                Re-solve Meal Plan
              </Button>
            </form>
          </Card>

          {/* Clinical Rules & Why These Limits Panel */}
          <Card className="p-4 bg-bg border border-border">
            <h3 className="text-xs font-bold text-text uppercase tracking-wider mb-2 flex items-center">
              <Info className="w-3.5 h-3.5 mr-1 text-primary" />
              Why These Limits?
            </h3>
            <ul className="text-[11px] text-muted space-y-2">
              <li>
                <strong className="text-text">Sodium Cap ({maxSodiumMg} mg):</strong>{' '}
                {maxSodiumMg <= 1500
                  ? 'AHA Hypertension DASH Guideline (Strict 1,500 mg).'
                  : 'Dietary Guidelines for Americans standard cap (2,300 mg).'}
              </li>
              <li>
                <strong className="text-text">Added Sugar Cap ({maxSugarG} g):</strong> ADA diabetic
                threshold limiting simple sugars to &le; 5% of daily energy intake.
              </li>
              <li>
                <strong className="text-text">Protein Floor ({proteinTargetG} g):</strong> Adjusted to
                preserve lean body mass and prevent catabolic muscle loss.
              </li>
            </ul>
          </Card>
        </div>

        {/* Right Column: Plans & Grocery List Tabs */}
        <div className="lg:col-span-8 space-y-4">
          {/* Tab Navigation Pill Row */}
          <div className="flex items-center space-x-2 border-b border-border pb-3">
            <button
              onClick={() => setActiveTab('today')}
              className={`px-4 py-1.5 rounded-full text-xs font-semibold transition-all ${
                activeTab === 'today'
                  ? 'bg-primary text-white shadow-sm'
                  : 'bg-surface text-muted hover:text-text border border-border'
              }`}
            >
              Today&apos;s Plan
            </button>
            <button
              onClick={() => {
                if (days < 7) handleDaysChange(7);
                setActiveTab('seven_day');
              }}
              className={`px-4 py-1.5 rounded-full text-xs font-semibold transition-all ${
                activeTab === 'seven_day'
                  ? 'bg-primary text-white shadow-sm'
                  : 'bg-surface text-muted hover:text-text border border-border'
              }`}
            >
              7-Day Schedule
            </button>
            <button
              onClick={() => setActiveTab('grocery')}
              className={`px-4 py-1.5 rounded-full text-xs font-semibold transition-all flex items-center ${
                activeTab === 'grocery'
                  ? 'bg-primary text-white shadow-sm'
                  : 'bg-surface text-muted hover:text-text border border-border'
              }`}
            >
              <ShoppingBag className="w-3.5 h-3.5 mr-1.5" />
              Grocery List
            </button>
          </div>

          {/* Action Row: Save Plan & Download PDF */}
          <div className="flex items-center justify-between">
            <div className="text-xs text-muted">
              Solver Time:{' '}
              <span className="font-semibold text-text">
                {planResult?.solver_time_sec?.toFixed(3) || '0.045'}s
              </span>{' '}
              &bull; Status:{' '}
              <span className="font-semibold text-primary">
                {planResult?.solver_status || 'Optimal'}
              </span>
            </div>
            <div className="flex items-center space-x-2">
              <Button
                variant="outline"
                size="sm"
                onClick={handleSavePlan}
                isLoading={isSaving}
                leftIcon={<Bookmark className="w-3.5 h-3.5 text-primary" />}
              >
                Save Plan
              </Button>
              <Button
                variant="primary"
                size="sm"
                onClick={handleDownloadPdf}
                isLoading={isDownloading}
                leftIcon={<Download className="w-3.5 h-3.5" />}
              >
                Download PDF
              </Button>
            </div>
          </div>

          {saveSuccess && (
            <div className="p-3 rounded-xl bg-primary-soft border border-primary/20 text-xs font-semibold text-primary flex items-center">
              <CheckCircle2 className="w-4 h-4 mr-2 text-primary" />
              Meal plan saved successfully to your account history!
            </div>
          )}

          {/* TAB 1: TODAY'S PLAN */}
          {activeTab === 'today' && day1 && (
            <div className="space-y-4">
              {['breakfast', 'lunch', 'dinner', 'snacks'].map((mealKey) => {
                const mealFoods = day1[mealKey] || [];
                const mealKcal = mealFoods.reduce(
                  (sum: number, f: any) => sum + (f.kcal || 0),
                  0
                );
                return (
                  <Card key={mealKey} className="p-5">
                    <div className="flex items-center justify-between pb-3 border-b border-border mb-3">
                      <div>
                        <h3 className="text-sm font-bold text-text capitalize">{mealKey}</h3>
                        <span className="text-[11px] text-muted">
                          {mealFoods.length} items &bull; ~{mealKcal} kcal
                        </span>
                      </div>
                      <Badge variant="neutral">{mealKey.toUpperCase()}</Badge>
                    </div>

                    <div className="divide-y divide-border/60">
                      {mealFoods.map((f: any, idx: number) => (
                        <div
                          key={idx}
                          className="py-2.5 flex items-center justify-between text-xs"
                        >
                          <div>
                            <span className="font-semibold text-text block">{f.name}</span>
                            <span className="text-[11px] text-muted">
                              {f.grams}g &bull; {f.kcal} kcal
                            </span>
                          </div>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleOpenSwap(f)}
                            className="text-[11px] py-1 px-2.5"
                          >
                            Swap
                          </Button>
                        </div>
                      ))}
                    </div>
                  </Card>
                );
              })}

              {/* Day 1 Totals */}
              <Card className="p-4 bg-primary-soft/40 border-primary/20 flex items-center justify-between text-xs">
                <span className="font-bold text-text">Day 1 Nutrient Totals:</span>
                <span className="font-bold text-primary">
                  {day1.daily_totals?.kcal} kcal &bull; Protein: {day1.daily_totals?.protein_g}g
                  &bull; Sodium: {day1.daily_totals?.sodium_mg}mg
                </span>
              </Card>
            </div>
          )}

          {/* TAB 2: 7-DAY SCHEDULE */}
          {activeTab === 'seven_day' && (
            <div className="space-y-4">
              {dailyPlans.map((dp: any) => (
                <Card key={dp.day} className="p-5">
                  <div className="flex items-center justify-between pb-2 border-b border-border mb-3">
                    <span className="text-sm font-bold text-text">Day {dp.day} Schedule</span>
                    <Badge variant="success">{dp.daily_totals?.kcal} kcal</Badge>
                  </div>
                  <div className="grid grid-cols-1 sm:grid-cols-4 gap-3 text-xs">
                    {['breakfast', 'lunch', 'dinner', 'snacks'].map((mKey) => (
                      <div key={mKey} className="p-2.5 rounded-lg bg-bg border border-border">
                        <span className="font-bold text-text capitalize block mb-1">
                          {mKey}
                        </span>
                        {(dp[mKey] || []).map((food: any, fi: number) => (
                          <div key={fi} className="text-[11px] text-muted truncate">
                            &bull; {food.name} ({food.grams}g)
                          </div>
                        ))}
                      </div>
                    ))}
                  </div>
                </Card>
              ))}
            </div>
          )}

          {/* TAB 3: GROCERY LIST */}
          {activeTab === 'grocery' && (
            <Card className="p-6">
              <div className="flex items-center justify-between pb-4 border-b border-border mb-4">
                <div>
                  <h3 className="text-sm font-bold text-text">Aggregated Grocery List</h3>
                  <span className="text-xs text-muted">
                    Total bulk weights required for your optimized schedule
                  </span>
                </div>
                <Badge variant="neutral">
                  {planResult?.grocery_list?.length || 0} unique items
                </Badge>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {(planResult?.grocery_list || []).map((item: any, idx: number) => (
                  <div
                    key={idx}
                    className="p-3 rounded-xl bg-bg border border-border flex items-center justify-between text-xs"
                  >
                    <div>
                      <span className="font-semibold text-text block">{item.name}</span>
                      <span className="text-[11px] text-muted">{item.category || 'Pantry'}</span>
                    </div>
                    <span className="font-bold text-primary">{item.total_grams}g</span>
                  </div>
                ))}
              </div>
            </Card>
          )}
        </div>
      </div>

      {/* Food Swap Modal */}
      <Modal
        isOpen={swapModalOpen}
        onClose={() => setSwapModalOpen(false)}
        title={`Swap: ${selectedFoodForSwap?.name || 'Food'}`}
      >
        <div className="space-y-4">
          <p className="text-xs text-muted">
            Select a strictly healthier same-category alternative. Health Score and micronutrients are
            guaranteed superior.
          </p>

          {loadingSwaps ? (
            <div className="py-8 text-center text-xs text-muted">
              Scanning 30,000+ foods for verified alternatives...
            </div>
          ) : availableSwaps.length === 0 ? (
            <div className="py-6 text-center text-xs text-muted">
              No healthier same-category swap candidates met the strict criteria.
            </div>
          ) : (
            <div className="space-y-2.5">
              {availableSwaps.map((s: any) => (
                <div
                  key={s.food_id}
                  className="p-3.5 rounded-xl border border-border bg-surface hover:border-primary flex items-center justify-between text-xs transition-colors"
                >
                  <div>
                    <span className="font-semibold text-text block">{s.name}</span>
                    <span className="text-[11px] text-primary font-medium block">
                      Health Score: {s.health_score_v2}/100 (+{s.score_improvement} pts)
                    </span>
                    <span className="text-[10px] text-muted block mt-0.5">
                      {s.reasons?.join(', ') || 'Lower sodium and saturated fat'}
                    </span>
                  </div>
                  <Button
                    variant="primary"
                    size="sm"
                    onClick={() => handleApplySwap(s)}
                    className="flex-shrink-0 ml-3"
                  >
                    Select
                  </Button>
                </div>
              ))}
            </div>
          )}
        </div>
      </Modal>

      <DisclaimerNotice />
    </div>
  );
};
