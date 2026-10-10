import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Check, ChevronRight, ChevronLeft, AlertTriangle } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { api } from '../api/endpoints';
import { Button } from '../components/common/Button';
import { Card } from '../components/common/Card';

export const Onboarding: React.FC = () => {
  const { user, updateUser } = useAuth();
  const navigate = useNavigate();

  const [step, setStep] = useState(1);
  const [isLoading, setIsLoading] = useState(false);
  const [safetyAdvisory, setSafetyAdvisory] = useState<string | null>(null);

  // Form State
  const [age, setAge] = useState<number>(30);
  const [sex, setSex] = useState<'male' | 'female'>('male');
  const [heightCm, setHeightCm] = useState<number>(175);
  const [weightKg, setWeightKg] = useState<number>(72);
  const [isAsian, setIsAsian] = useState<boolean>(false);

  const [activityLevel, setActivityLevel] = useState<string>('moderate');
  const [goal, setGoal] = useState<string>('maintenance');

  const [conditions, setConditions] = useState<string[]>([]);
  const [allergies, setAllergies] = useState<string[]>([]);
  const [restrictions, setRestrictions] = useState<string[]>([]);
  const [preferredCuisine, setPreferredCuisine] = useState<string>('Balanced Mediterranean');

  const availableConditions = [
    { id: 'hypertension', label: 'Hypertension' },
    { id: 'diabetes', label: 'Type 2 Diabetes' },
    { id: 'high_cholesterol', label: 'High Cholesterol' },
    { id: 'obesity', label: 'Obesity' },
  ];

  const availableAllergies = [
    'gluten',
    'peanuts',
    'dairy',
    'nuts',
    'soy',
    'eggs',
    'fish',
  ];

  const availableRestrictions = [
    { id: 'low_sodium', label: 'Low Sodium' },
    { id: 'low_sugar', label: 'Low Sugar' },
    { id: 'vegetarian', label: 'Vegetarian' },
    { id: 'vegan', label: 'Vegan' },
  ];

  const handleToggle = (list: string[], setList: React.Dispatch<React.SetStateAction<string[]>>, item: string) => {
    if (list.includes(item)) {
      setList(list.filter((x) => x !== item));
    } else {
      setList([...list, item]);
    }
  };

  const validateStep = () => {
    setSafetyAdvisory(null);
    if (step === 1) {
      if (age < 18) {
        setSafetyAdvisory('Safety Gate Note: This app is configured for adults aged 18+. Minors should consult a pediatric clinician.');
      } else if (age > 75) {
        setSafetyAdvisory('Safety Gate Note: Seniors aged 75+ should have nutrition plans reviewed by a geriatric specialist.');
      }
      const bmi = weightKg / ((heightCm / 100) * (heightCm / 100));
      if (bmi < 16.0 || bmi > 45.0) {
        setSafetyAdvisory(`Extreme BMI detected (${bmi.toFixed(1)}). Clinical supervision is advised.`);
      }
    }
    return true;
  };

  const handleNext = () => {
    if (validateStep()) {
      setStep((s) => Math.min(s + 1, 3));
    }
  };

  const handleBack = () => {
    setSafetyAdvisory(null);
    setStep((s) => Math.max(s - 1, 1));
  };

  const handleComplete = async () => {
    setIsLoading(true);
    try {
      const profileData = {
        age,
        sex,
        height_cm: heightCm,
        weight_kg: weightKg,
        is_asian: isAsian,
        activity_level: activityLevel,
        goal,
        conditions,
        allergies,
        dietary_restrictions: restrictions,
        preferred_cuisine: preferredCuisine,
        onboarding_completed: true,
      };

      const updated = await api.users.updateProfile(profileData);
      updateUser(updated);
      navigate('/dashboard', { replace: true });
    } catch (err: any) {
      setSafetyAdvisory(err.message || 'Failed to save profile. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-bg flex items-center justify-center p-4 sm:p-6 lg:p-8">
      <div className="w-full max-w-2xl">
        {/* Progress Bar & Header */}
        <div className="mb-6 text-center">
          <div className="inline-flex items-center px-3 py-1 rounded-full bg-primary-soft text-primary text-xs font-semibold uppercase tracking-wider mb-2">
            Step {step} of 3
          </div>
          <h1 className="text-2xl font-bold text-text">Welcome to NutriIntel</h1>
          <p className="text-xs sm:text-sm text-muted mt-1">
            Let&apos;s personalize your clinical targets and food constraints
          </p>

          <div className="w-full bg-border h-2 rounded-full overflow-hidden mt-4">
            <div
              className="bg-primary h-full transition-all duration-300 rounded-full"
              style={{ width: `${(step / 3) * 100}%` }}
            />
          </div>
        </div>

        <Card className="p-6 sm:p-8">
          {safetyAdvisory && (
            <div className="mb-6 p-3.5 rounded-xl bg-warning-soft border border-warning/30 text-xs text-warning flex items-start space-x-2.5">
              <AlertTriangle className="w-4 h-4 flex-shrink-0 mt-0.5" />
              <span>{safetyAdvisory}</span>
            </div>
          )}

          {/* STEP 1: BASICS */}
          {step === 1 && (
            <div className="space-y-5 animate-in fade-in duration-150">
              <h2 className="text-base font-bold text-text border-b border-border pb-2">
                Step 1: Anthropometric Metrics
              </h2>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-muted uppercase tracking-wider mb-1">
                    Age (Years) <span className="text-danger">*</span>
                  </label>
                  <input
                    type="number"
                    min={18}
                    max={110}
                    value={age}
                    onChange={(e) => setAge(Number(e.target.value))}
                    className="w-full px-3.5 py-2.5 rounded-xl border border-border bg-surface text-text text-sm focus:border-primary focus:ring-1 focus:ring-primary"
                  />
                  <span className="text-[11px] text-muted block mt-1">Mifflin-St Jeor metabolic age</span>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-muted uppercase tracking-wider mb-1">
                    Biological Sex <span className="text-danger">*</span>
                  </label>
                  <div className="grid grid-cols-2 gap-2">
                    <button
                      type="button"
                      onClick={() => setSex('male')}
                      className={`py-2.5 rounded-xl border text-xs font-semibold transition-all ${
                        sex === 'male'
                          ? 'bg-primary-soft text-primary border-primary'
                          : 'bg-surface text-text border-border hover:bg-bg'
                      }`}
                    >
                      Male
                    </button>
                    <button
                      type="button"
                      onClick={() => setSex('female')}
                      className={`py-2.5 rounded-xl border text-xs font-semibold transition-all ${
                        sex === 'female'
                          ? 'bg-primary-soft text-primary border-primary'
                          : 'bg-surface text-text border-border hover:bg-bg'
                      }`}
                    >
                      Female
                    </button>
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-muted uppercase tracking-wider mb-1">
                    Height (cm) <span className="text-danger">*</span>
                  </label>
                  <input
                    type="number"
                    min={120}
                    max={230}
                    value={heightCm}
                    onChange={(e) => setHeightCm(Number(e.target.value))}
                    className="w-full px-3.5 py-2.5 rounded-xl border border-border bg-surface text-text text-sm focus:border-primary focus:ring-1 focus:ring-primary"
                  />
                  <span className="text-[11px] text-muted block mt-1">e.g. 175 cm (5 ft 9 in)</span>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-muted uppercase tracking-wider mb-1">
                    Current Weight (kg) <span className="text-danger">*</span>
                  </label>
                  <input
                    type="number"
                    min={35}
                    max={250}
                    step={0.5}
                    value={weightKg}
                    onChange={(e) => setWeightKg(Number(e.target.value))}
                    className="w-full px-3.5 py-2.5 rounded-xl border border-border bg-surface text-text text-sm focus:border-primary focus:ring-1 focus:ring-primary"
                  />
                  <span className="text-[11px] text-muted block mt-1">e.g. 72 kg (158.7 lbs)</span>
                </div>
              </div>

              <div className="pt-2">
                <label className="flex items-center space-x-2.5 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={isAsian}
                    onChange={(e) => setIsAsian(e.target.checked)}
                    className="rounded border-border text-primary focus:ring-primary w-4 h-4"
                  />
                  <span className="text-xs text-text">
                    Apply Asian-specific BMI cutoffs (Overweight &ge; 23.0, Obesity &ge; 27.5)
                  </span>
                </label>
              </div>
            </div>
          )}

          {/* STEP 2: LIFESTYLE & GOALS */}
          {step === 2 && (
            <div className="space-y-5 animate-in fade-in duration-150">
              <h2 className="text-base font-bold text-text border-b border-border pb-2">
                Step 2: Activity Level &amp; Nutritional Goal
              </h2>

              <div>
                <label className="block text-xs font-semibold text-muted uppercase tracking-wider mb-2">
                  Physical Activity Frequency
                </label>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                  {[
                    { id: 'sedentary', label: 'Sedentary', sub: 'Desk job, little to no exercise (1.2x)' },
                    { id: 'light', label: 'Lightly Active', sub: 'Light exercise 1-3 days/week (1.375x)' },
                    { id: 'moderate', label: 'Moderately Active', sub: 'Moderate exercise 3-5 days/week (1.55x)' },
                    { id: 'active', label: 'Very Active', sub: 'Hard training 6-7 days/week (1.725x)' },
                  ].map((act) => (
                    <button
                      key={act.id}
                      type="button"
                      onClick={() => setActivityLevel(act.id)}
                      className={`p-3 rounded-xl border text-left transition-all ${
                        activityLevel === act.id
                          ? 'bg-primary-soft text-text border-primary shadow-sm'
                          : 'bg-surface text-text border-border hover:bg-bg'
                      }`}
                    >
                      <span className="font-semibold text-xs block">{act.label}</span>
                      <span className="text-[11px] text-muted block mt-0.5">{act.sub}</span>
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-muted uppercase tracking-wider mb-2">
                  Primary Caloric Goal
                </label>
                <div className="grid grid-cols-3 gap-2.5">
                  {[
                    { id: 'weight_loss', label: 'Weight Loss', desc: '-500 kcal/day deficit' },
                    { id: 'maintenance', label: 'Maintenance', desc: 'Isocaloric energy balance' },
                    { id: 'muscle_gain', label: 'Muscle Gain', desc: '+300 kcal/day surplus' },
                  ].map((g) => (
                    <button
                      key={g.id}
                      type="button"
                      onClick={() => setGoal(g.id)}
                      className={`p-3 rounded-xl border text-center transition-all ${
                        goal === g.id
                          ? 'bg-primary-soft text-text border-primary shadow-sm'
                          : 'bg-surface text-text border-border hover:bg-bg'
                      }`}
                    >
                      <span className="font-semibold text-xs block">{g.label}</span>
                      <span className="text-[10px] text-muted block mt-0.5">{g.desc}</span>
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* STEP 3: HEALTH CONTEXT & ALLERGENS */}
          {step === 3 && (
            <div className="space-y-5 animate-in fade-in duration-150">
              <h2 className="text-base font-bold text-text border-b border-border pb-2">
                Step 3: Clinical Context &amp; Food Constraints
              </h2>

              <div>
                <label className="block text-xs font-semibold text-muted uppercase tracking-wider mb-1.5">
                  Clinical Conditions (Triggers dynamic guidelines)
                </label>
                <div className="flex flex-wrap gap-2">
                  {availableConditions.map((cond) => {
                    const isSelected = conditions.includes(cond.id);
                    return (
                      <button
                        key={cond.id}
                        type="button"
                        onClick={() => handleToggle(conditions, setConditions, cond.id)}
                        className={`px-3 py-1.5 rounded-full text-xs font-semibold border transition-all ${
                          isSelected
                            ? 'bg-primary text-white border-primary'
                            : 'bg-surface text-muted border-border hover:bg-bg'
                        }`}
                      >
                        {cond.label}
                      </button>
                    );
                  })}
                  <button
                    type="button"
                    onClick={() => setConditions([])}
                    className={`px-3 py-1.5 rounded-full text-xs font-semibold border transition-all ${
                      conditions.length === 0
                        ? 'bg-primary-soft text-primary border-primary'
                        : 'bg-surface text-muted border-border'
                    }`}
                  >
                    None / General Health
                  </button>
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-muted uppercase tracking-wider mb-1.5">
                  Allergen Exclusions (Strict Tri-State Safety Gating)
                </label>
                <div className="flex flex-wrap gap-2">
                  {availableAllergies.map((allg) => {
                    const isSelected = allergies.includes(allg);
                    return (
                      <button
                        key={allg}
                        type="button"
                        onClick={() => handleToggle(allergies, setAllergies, allg)}
                        className={`px-3 py-1.5 rounded-full text-xs font-semibold capitalize border transition-all ${
                          isSelected
                            ? 'bg-danger text-white border-danger'
                            : 'bg-surface text-muted border-border hover:bg-bg'
                        }`}
                      >
                        {allg}
                      </button>
                    );
                  })}
                </div>
                <span className="text-[11px] text-muted block mt-1">
                  Excluded foods with present or unknown status are filtered automatically.
                </span>
              </div>

              <div>
                <label className="block text-xs font-semibold text-muted uppercase tracking-wider mb-1.5">
                  Dietary Restrictions
                </label>
                <div className="flex flex-wrap gap-2">
                  {availableRestrictions.map((r) => {
                    const isSelected = restrictions.includes(r.id);
                    return (
                      <button
                        key={r.id}
                        type="button"
                        onClick={() => handleToggle(restrictions, setRestrictions, r.id)}
                        className={`px-3 py-1.5 rounded-full text-xs font-semibold border transition-all ${
                          isSelected
                            ? 'bg-primary text-white border-primary'
                            : 'bg-surface text-muted border-border hover:bg-bg'
                        }`}
                      >
                        {r.label}
                      </button>
                    );
                  })}
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-muted uppercase tracking-wider mb-1">
                  Preferred Cuisine Style
                </label>
                <select
                  value={preferredCuisine}
                  onChange={(e) => setPreferredCuisine(e.target.value)}
                  className="w-full px-3.5 py-2 rounded-xl border border-border bg-surface text-text text-sm focus:border-primary focus:ring-1 focus:ring-primary"
                >
                  <option value="Balanced Mediterranean">Balanced Mediterranean</option>
                  <option value="Indian Traditional">Indian Traditional</option>
                  <option value="Asian Fusion">Asian Fusion</option>
                  <option value="Low-GI Diabetic Friendly">Low-GI Diabetic Friendly</option>
                  <option value="High-Protein Athletic">High-Protein Athletic</option>
                </select>
              </div>
            </div>
          )}

          {/* Wizard Action Buttons */}
          <div className="mt-8 pt-5 border-t border-border flex items-center justify-between">
            {step > 1 ? (
              <Button
                type="button"
                variant="outline"
                onClick={handleBack}
                leftIcon={<ChevronLeft className="w-4 h-4" />}
              >
                Back
              </Button>
            ) : (
              <div />
            )}

            {step < 3 ? (
              <Button
                type="button"
                variant="primary"
                onClick={handleNext}
                rightIcon={<ChevronRight className="w-4 h-4" />}
              >
                Continue
              </Button>
            ) : (
              <Button
                type="button"
                variant="primary"
                isLoading={isLoading}
                onClick={handleComplete}
                leftIcon={<Check className="w-4 h-4" />}
              >
                Finish &amp; Launch Dashboard
              </Button>
            )}
          </div>
        </Card>
      </div>
    </div>
  );
};
