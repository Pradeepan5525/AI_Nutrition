import React, { useState, useEffect } from 'react';
import { Bookmark, HeartPulse, CheckCircle2, AlertTriangle, ShieldCheck } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { api } from '../api/endpoints';
import { Card } from '../components/common/Card';
import { DarkCard } from '../components/common/DarkCard';
import { Badge } from '../components/common/Badge';
import { Button } from '../components/common/Button';
import { DisclaimerNotice } from '../components/common/DisclaimerNotice';

export const HealthCheck: React.FC = () => {
  const { user } = useAuth();
  const profile = user?.profile || user?.saved_profile || {};

  // Form inputs
  const [age, setAge] = useState<number>(profile.age || 30);
  const [sex, setSex] = useState<'male' | 'female'>((profile.sex as any) || 'male');
  const [heightCm, setHeightCm] = useState<number>(profile.height_cm || 175);
  const [weightKg, setWeightKg] = useState<number>(profile.weight_kg || 72);
  const [activityLevel, setActivityLevel] = useState<string>(profile.activity_level || 'moderate');
  const [goal, setGoal] = useState<string>(profile.goal || 'maintenance');
  const [isAsian, setIsAsian] = useState<boolean>(profile.is_asian || false);
  const [conditions, setConditions] = useState<string[]>(profile.conditions || []);
  const [dietaryRestrictions, setDietaryRestrictions] = useState<string[]>(profile.dietary_restrictions || []);

  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [savedSuccess, setSavedSuccess] = useState(false);

  // Quick Preset Chips
  const presets = [
    {
      name: 'Standard Adult',
      apply: () => {
        setAge(30);
        setSex('male');
        setHeightCm(178);
        setWeightKg(75);
        setActivityLevel('moderate');
        setGoal('maintenance');
        setConditions([]);
      },
    },
    {
      name: 'Weight Loss Female',
      apply: () => {
        setAge(32);
        setSex('female');
        setHeightCm(165);
        setWeightKg(70);
        setActivityLevel('light');
        setGoal('weight_loss');
        setConditions([]);
      },
    },
    {
      name: 'Hypertension DASH',
      apply: () => {
        setAge(52);
        setSex('male');
        setHeightCm(172);
        setWeightKg(84);
        setActivityLevel('sedentary');
        setGoal('weight_loss');
        setConditions(['hypertension']);
      },
    },
    {
      name: 'Senior Evaluation',
      apply: () => {
        setAge(78);
        setSex('female');
        setHeightCm(160);
        setWeightKg(62);
        setActivityLevel('light');
        setGoal('maintenance');
        setConditions(['high_cholesterol']);
      },
    },
  ];

  // Run initial assessment on load
  useEffect(() => {
    runAssessment();
  }, []);

  const runAssessment = async () => {
    setIsLoading(true);
    setSavedSuccess(false);
    try {
      const payload = {
        age,
        sex,
        height_cm: heightCm,
        weight_kg: weightKg,
        activity_level: activityLevel,
        goal,
        is_asian: isAsian,
        is_pregnant: false,
        is_lactating: false,
        has_ed_history: false,
        condition_flags: conditions,
        dietary_restrictions: dietaryRestrictions,
        allergies: profile.allergies || [],
      };
      const data = await api.assess.run(payload);
      setResult(data);
    } catch (err) {
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSaveToHistory = async () => {
    if (!result) return;
    setIsSaving(true);
    try {
      await api.assess.save({
        input_data: { age, sex, height_cm: heightCm, weight_kg: weightKg, activity_level: activityLevel, goal },
        bmi: result.bmi,
        bmi_category: result.bmi_category,
        bmr_kcal: result.bmr_kcal,
        tdee_kcal: result.tdee_kcal,
        target_kcal: result.target_kcal,
        protein_g: result.macros?.protein_g || 120,
        carbs_g: result.macros?.carbs_g || 220,
        fat_g: result.macros?.fat_g || 65,
        sodium_mg: result.clinical_constraints?.max_sodium_mg || 2300,
        water_ml: result.water_ml || 2500,
        safety_cleared: result.safety_gate?.cleared ?? true,
        safety_flags: result.safety_gate?.flags || [],
        clinical_constraints: result.clinical_constraints || {},
      });
      setSavedSuccess(true);
    } catch (err) {
      console.error(err);
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header Card */}
      <Card className="p-6">
        <div className="flex items-center space-x-2 mb-2">
          <Badge variant="accent">Module 01</Badge>
          <Badge variant="neutral">Mifflin-St Jeor Engine</Badge>
        </div>
        <h1 className="text-2xl font-bold text-text">Anthropometric &amp; Metabolic Assessment</h1>
        <p className="text-xs sm:text-sm text-muted mt-1">
          Precision metabolic modeling calculating Basal Metabolic Rate, Total Daily Energy
          Expenditure, macronutrient splits, and clinical safety gates.
        </p>
      </Card>

      {/* Two-Column Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left Column: Form Card */}
        <div className="lg:col-span-5 space-y-4">
          <Card className="p-6">
            <div className="mb-4">
              <span className="text-[11px] font-bold text-muted uppercase tracking-wider block mb-2">
                Quick Preset Scenarios
              </span>
              <div className="grid grid-cols-2 gap-2">
                {presets.map((p) => (
                  <button
                    key={p.name}
                    type="button"
                    onClick={p.apply}
                    className="p-2 rounded-xl text-left border border-border bg-bg hover:bg-surface hover:border-primary text-xs font-semibold text-text transition-all"
                  >
                    {p.name}
                  </button>
                ))}
              </div>
            </div>

            <form
              onSubmit={(e) => {
                e.preventDefault();
                runAssessment();
              }}
              className="space-y-4 pt-4 border-t border-border"
            >
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-muted uppercase tracking-wider mb-1">
                    Age (Years) <span className="text-danger">*</span>
                  </label>
                  <input
                    type="number"
                    min={18}
                    max={120}
                    value={age}
                    onChange={(e) => setAge(Number(e.target.value))}
                    className="w-full px-3 py-2 rounded-xl border border-border bg-surface text-text text-sm focus:border-primary focus:ring-1 focus:ring-primary"
                  />
                  <span className="text-[10px] text-muted block mt-0.5">Mifflin age</span>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-muted uppercase tracking-wider mb-1">
                    Biological Sex <span className="text-danger">*</span>
                  </label>
                  <select
                    value={sex}
                    onChange={(e) => setSex(e.target.value as any)}
                    className="w-full px-3 py-2 rounded-xl border border-border bg-surface text-text text-sm focus:border-primary focus:ring-1 focus:ring-primary"
                  >
                    <option value="male">Male</option>
                    <option value="female">Female</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-muted uppercase tracking-wider mb-1">
                    Height (cm) <span className="text-danger">*</span>
                  </label>
                  <input
                    type="number"
                    min={100}
                    max={250}
                    value={heightCm}
                    onChange={(e) => setHeightCm(Number(e.target.value))}
                    className="w-full px-3 py-2 rounded-xl border border-border bg-surface text-text text-sm focus:border-primary focus:ring-1 focus:ring-primary"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-muted uppercase tracking-wider mb-1">
                    Weight (kg) <span className="text-danger">*</span>
                  </label>
                  <input
                    type="number"
                    min={30}
                    max={300}
                    step={0.5}
                    value={weightKg}
                    onChange={(e) => setWeightKg(Number(e.target.value))}
                    className="w-full px-3 py-2 rounded-xl border border-border bg-surface text-text text-sm focus:border-primary focus:ring-1 focus:ring-primary"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-muted uppercase tracking-wider mb-1">
                  Activity Level
                </label>
                <select
                  value={activityLevel}
                  onChange={(e) => setActivityLevel(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl border border-border bg-surface text-text text-sm focus:border-primary focus:ring-1 focus:ring-primary"
                >
                  <option value="sedentary">Sedentary (1.2x TDEE)</option>
                  <option value="light">Lightly Active (1.375x TDEE)</option>
                  <option value="moderate">Moderately Active (1.55x TDEE)</option>
                  <option value="active">Very Active (1.725x TDEE)</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-muted uppercase tracking-wider mb-1">
                  Goal
                </label>
                <select
                  value={goal}
                  onChange={(e) => setGoal(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl border border-border bg-surface text-text text-sm focus:border-primary focus:ring-1 focus:ring-primary"
                >
                  <option value="weight_loss">Weight Loss (-500 kcal)</option>
                  <option value="maintenance">Maintenance (Isocaloric)</option>
                  <option value="muscle_gain">Muscle Gain (+300 kcal)</option>
                </select>
              </div>

              <div className="pt-2">
                <label className="flex items-center space-x-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={isAsian}
                    onChange={(e) => setIsAsian(e.target.checked)}
                    className="rounded border-border text-primary focus:ring-primary w-4 h-4"
                  />
                  <span className="text-xs text-text">Use Asian-specific BMI thresholds</span>
                </label>
              </div>

              <Button
                type="submit"
                variant="primary"
                size="lg"
                isLoading={isLoading}
                className="w-full"
              >
                Compute Metabolic Assessment
              </Button>
            </form>
          </Card>
        </div>

        {/* Right Column: Results Cards */}
        <div className="lg:col-span-7 space-y-4">
          {result ? (
            <>
              {/* Dark Gradient BMI Result Card */}
              <DarkCard className="p-6">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-xs font-bold uppercase tracking-wider text-primary-accent">
                    BODY MASS INDEX (BMI)
                  </span>
                  <Badge variant={result.bmi_category === 'Normal weight' ? 'accent' : 'warning'}>
                    {result.bmi_category}
                  </Badge>
                </div>

                <div className="flex items-baseline space-x-3 mb-4">
                  <span className="text-4xl sm:text-5xl font-extrabold text-white">
                    {result.bmi}
                  </span>
                  <span className="text-sm font-semibold text-white/70">kg/m&sup2;</span>
                </div>

                {/* Visual Gauge Bar in Green Shades */}
                <div className="space-y-1.5 pt-2 border-t border-border/10">
                  <div className="flex justify-between text-[11px] text-white/70">
                    <span>Underweight (&lt;18.5)</span>
                    <span className="font-bold text-primary-accent">Normal (18.5-24.9)</span>
                    <span>Overweight (25-29.9)</span>
                    <span>Obese (&ge;30)</span>
                  </div>
                  <div className="w-full bg-white/10 h-2.5 rounded-full overflow-hidden flex">
                    <div className="w-[18.5%] bg-primary-soft/40" />
                    <div className="w-[30%] bg-primary-accent" />
                    <div className="w-[20%] bg-warning/80" />
                    <div className="w-[31.5%] bg-danger/80" />
                  </div>
                </div>

                <p className="text-xs text-white/80 mt-4">
                  Healthy weight range for your height ({heightCm} cm):{' '}
                  <strong className="text-white">
                    {result.ideal_weight_min_kg} kg &ndash; {result.ideal_weight_max_kg} kg
                  </strong>
                </p>
              </DarkCard>

              {/* Energy Expenditure & Calorie Target Cards */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <Card className="p-4 text-center">
                  <span className="text-[10px] font-bold text-muted uppercase tracking-wider block">BMR</span>
                  <span className="text-xl font-bold text-text mt-1 block">
                    {Math.round(result.bmr_kcal)}
                  </span>
                  <span className="text-[10px] text-muted block mt-0.5">Basal Metabolic Rate</span>
                </Card>

                <Card className="p-4 text-center">
                  <span className="text-[10px] font-bold text-muted uppercase tracking-wider block">TDEE</span>
                  <span className="text-xl font-bold text-text mt-1 block">
                    {Math.round(result.tdee_kcal)}
                  </span>
                  <span className="text-[10px] text-muted block mt-0.5">Maintenance Energy</span>
                </Card>

                <Card className="p-4 text-center border-primary bg-primary-soft/30">
                  <span className="text-[10px] font-bold text-primary uppercase tracking-wider block">Target Energy</span>
                  <span className="text-xl font-bold text-primary mt-1 block">
                    {Math.round(result.target_kcal)}
                  </span>
                  <span className="text-[10px] text-muted block mt-0.5">
                    {result.deficit_or_surplus_kcal > 0
                      ? `+${result.deficit_or_surplus_kcal} kcal`
                      : `${result.deficit_or_surplus_kcal} kcal`}
                  </span>
                </Card>
              </div>

              {/* Macronutrients Breakdown */}
              <Card className="p-5">
                <h3 className="text-xs font-bold text-muted uppercase tracking-wider mb-3">
                  Macronutrient Distribution Target
                </h3>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                  <div className="p-3 rounded-xl bg-bg border border-border">
                    <span className="text-[10px] font-semibold text-muted block uppercase">Protein</span>
                    <span className="text-lg font-bold text-text mt-0.5 block">
                      {Math.round(result.macros?.protein_g || 0)}g
                    </span>
                    <span className="text-[10px] text-muted">25% of energy</span>
                  </div>
                  <div className="p-3 rounded-xl bg-bg border border-border">
                    <span className="text-[10px] font-semibold text-muted block uppercase">Carbohydrates</span>
                    <span className="text-lg font-bold text-text mt-0.5 block">
                      {Math.round(result.macros?.carbs_g || 0)}g
                    </span>
                    <span className="text-[10px] text-muted">45% of energy</span>
                  </div>
                  <div className="p-3 rounded-xl bg-bg border border-border">
                    <span className="text-[10px] font-semibold text-muted block uppercase">Fats</span>
                    <span className="text-lg font-bold text-text mt-0.5 block">
                      {Math.round(result.macros?.fat_g || 0)}g
                    </span>
                    <span className="text-[10px] text-muted">30% of energy</span>
                  </div>
                  <div className="p-3 rounded-xl bg-bg border border-border">
                    <span className="text-[10px] font-semibold text-muted block uppercase">Daily Hydration</span>
                    <span className="text-lg font-bold text-primary mt-0.5 block">
                      {Math.round(result.water_ml)}ml
                    </span>
                    <span className="text-[10px] text-muted">Water target</span>
                  </div>
                </div>
              </Card>

              {/* Safety Gate Evaluation */}
              <Card className="p-5">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="text-xs font-bold text-text uppercase tracking-wider flex items-center">
                    <ShieldCheck className="w-4 h-4 text-primary mr-1.5" />
                    Clinical Safety Gate Evaluation
                  </h3>
                  <Badge variant={result.safety_gate?.cleared ? 'success' : 'warning'}>
                    {result.safety_gate?.cleared ? 'Cleared' : 'Advisory Flag'}
                  </Badge>
                </div>
                <p className="text-xs text-muted mb-2">{result.safety_gate?.guidance}</p>
                {result.safety_gate?.flags && result.safety_gate.flags.length > 0 && (
                  <ul className="text-xs text-warning space-y-1 mt-2 p-2.5 rounded-lg bg-warning-soft border border-warning/20">
                    {result.safety_gate.flags.map((flag: string, idx: number) => (
                      <li key={idx} className="flex items-start space-x-1.5">
                        <AlertTriangle className="w-3.5 h-3.5 flex-shrink-0 mt-0.5" />
                        <span>{flag}</span>
                      </li>
                    ))}
                  </ul>
                )}
              </Card>

              {/* Action: Save to History */}
              <div className="flex items-center justify-between pt-2">
                <Button
                  variant="outline"
                  onClick={handleSaveToHistory}
                  isLoading={isSaving}
                  leftIcon={<Bookmark className="w-4 h-4 text-primary" />}
                >
                  Save Assessment to History
                </Button>
                {savedSuccess && (
                  <span className="text-xs font-semibold text-primary flex items-center">
                    <CheckCircle2 className="w-4 h-4 mr-1 text-primary" />
                    Saved to your account!
                  </span>
                )}
              </div>
            </>
          ) : (
            <Card className="p-10 text-center text-muted">
              <HeartPulse className="w-8 h-8 text-muted mx-auto mb-2 opacity-50" />
              <p className="text-sm font-semibold">Ready to compute metabolic assessment</p>
              <p className="text-xs text-muted mt-1">
                Adjust anthropometric parameters and press compute.
              </p>
            </Card>
          )}
        </div>
      </div>

      <DisclaimerNotice />
    </div>
  );
};
