import React, { useState, useEffect } from 'react';
import { Activity, Bookmark, CheckCircle2, AlertTriangle, ShieldCheck, HelpCircle } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { api } from '../api/endpoints';
import { Card } from '../components/common/Card';
import { DarkCard } from '../components/common/DarkCard';
import { Badge } from '../components/common/Badge';
import { Button } from '../components/common/Button';
import { DisclaimerNotice } from '../components/common/DisclaimerNotice';

export const RiskPredictor: React.FC = () => {
  const { user } = useAuth();
  const profile = user?.profile || user?.saved_profile || {};

  // Form parameters
  const [age, setAge] = useState<number>(profile.age || 26);
  const [gender, setGender] = useState<string>(
    profile.sex === 'female' ? 'Female' : 'Male'
  );
  const [familyHistory, setFamilyHistory] = useState<string>('yes');
  const [favc, setFavc] = useState<string>('yes');
  const [fcvc, setFcvc] = useState<number>(2.0);
  const [ncp, setNcp] = useState<number>(3.0);
  const [caec, setCaec] = useState<string>('Sometimes');
  const [smoke, setSmoke] = useState<string>('no');
  const [ch2o, setCh2o] = useState<number>(2.0);
  const [scc, setScc] = useState<string>('no');
  const [faf, setFaf] = useState<number>(1.0);
  const [tue, setTue] = useState<number>(1.0);
  const [calc, setCalc] = useState<string>('Sometimes');
  const [mtrans, setMtrans] = useState<string>('Public_Transportation');

  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [savedSuccess, setSavedSuccess] = useState(false);

  // Quick Preset Chips
  const applyPreset = (type: 'office' | 'student' | 'balanced') => {
    if (type === 'office') {
      setFcvc(1.5);
      setNcp(3.0);
      setCh2o(1.5);
      setFaf(0.0);
      setTue(2.0);
      setFavc('yes');
      setMtrans('Automobile');
    } else if (type === 'student') {
      setFcvc(2.0);
      setNcp(3.0);
      setCh2o(2.0);
      setFaf(2.0);
      setTue(1.5);
      setFavc('no');
      setMtrans('Public_Transportation');
    } else {
      setFcvc(3.0);
      setNcp(3.0);
      setCh2o(2.5);
      setFaf(3.0);
      setTue(0.5);
      setFavc('no');
      setMtrans('Walking');
    }
  };

  useEffect(() => {
    runRiskInference();
  }, []);

  const runRiskInference = async () => {
    setIsLoading(true);
    setSavedSuccess(false);
    try {
      const payload = {
        age: Number(age),
        gender: gender.toLowerCase() as 'male' | 'female',
        family_history_with_overweight: familyHistory,
        favc,
        fcvc: Number(fcvc),
        ncp: Number(ncp),
        caec,
        smoke,
        ch2o: Number(ch2o),
        scc,
        faf: Number(faf),
        tue: Number(tue),
        calc,
        mtrans,
      };
      const res = await api.risk.run(payload);
      setResult(res);
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
      await api.risk.save({
        input_habits: { Age: age, Gender: gender, fcvc, faf, tue, favc },
        predicted_tier: result.predicted_category,
        confidence: result.probabilities?.[result.predicted_category] || 0.65,
        probabilities: result.probabilities || {},
        top_risk_factors: result.top_risk_factors || [],
        top_protective_factors: result.top_protective_factors || [],
        disclaimer: result.disclaimer,
      });
      setSavedSuccess(true);
    } catch (err) {
      console.error(err);
    } finally {
      setIsSaving(false);
    }
  };

  // Sort top 3 probabilities
  const sortedProbabilities = result?.probabilities
    ? Object.entries(result.probabilities)
        .map(([tier, prob]: [string, any]) => ({ tier, prob: Number(prob) }))
        .sort((a, b) => b.prob - a.prob)
    : [];

  const winningConfidence = sortedProbabilities[0]
    ? Math.round(sortedProbabilities[0].prob * 100)
    : 0;

  return (
    <div className="space-y-6">
      {/* Header Card */}
      <Card className="p-6">
        <div className="flex items-center space-x-2 mb-2">
          <Badge variant="accent">Module 02</Badge>
          <Badge variant="neutral">Calibrated LightGBM Classifier</Badge>
        </div>
        <h1 className="text-2xl font-bold text-text">Lifestyle Obesity Risk Screening</h1>
        <p className="text-xs sm:text-sm text-muted mt-1">
          Evaluates weight status vulnerability exclusively from daily behavioral habits and physical
          activity. Height and weight are excluded to avoid target circularity.
        </p>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left Column: Form Card */}
        <div className="lg:col-span-5 space-y-4">
          <Card className="p-6">
            <div className="mb-4">
              <span className="text-[11px] font-bold text-muted uppercase tracking-wider block mb-2">
                Quick Lifestyle Presets
              </span>
              <div className="grid grid-cols-3 gap-2">
                <button
                  type="button"
                  onClick={() => applyPreset('office')}
                  className="p-2 rounded-xl text-center border border-border bg-bg hover:border-primary text-xs font-semibold text-text transition-all"
                >
                  Sedentary Office
                </button>
                <button
                  type="button"
                  onClick={() => applyPreset('student')}
                  className="p-2 rounded-xl text-center border border-border bg-bg hover:border-primary text-xs font-semibold text-text transition-all"
                >
                  Active Student
                </button>
                <button
                  type="button"
                  onClick={() => applyPreset('balanced')}
                  className="p-2 rounded-xl text-center border border-border bg-bg hover:border-primary text-xs font-semibold text-text transition-all"
                >
                  Balanced Athlete
                </button>
              </div>
            </div>

            <form
              onSubmit={(e) => {
                e.preventDefault();
                runRiskInference();
              }}
              className="space-y-4 pt-4 border-t border-border"
            >
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-muted uppercase tracking-wider mb-1">
                    Vegetable Intake (FCVC)
                  </label>
                  <select
                    value={fcvc}
                    onChange={(e) => setFcvc(Number(e.target.value))}
                    className="w-full px-3 py-2 rounded-xl border border-border bg-surface text-text text-sm focus:border-primary focus:ring-1 focus:ring-primary"
                  >
                    <option value={1}>Rarely / None (1)</option>
                    <option value={2}>Sometimes (2)</option>
                    <option value={3}>Always with meals (3)</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-muted uppercase tracking-wider mb-1">
                    Daily Meals (NCP)
                  </label>
                  <select
                    value={ncp}
                    onChange={(e) => setNcp(Number(e.target.value))}
                    className="w-full px-3 py-2 rounded-xl border border-border bg-surface text-text text-sm focus:border-primary focus:ring-1 focus:ring-primary"
                  >
                    <option value={1}>1-2 meals</option>
                    <option value={3}>3 structured meals</option>
                    <option value={4}>More than 3 meals</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-muted uppercase tracking-wider mb-1">
                    Water Consumption (CH2O)
                  </label>
                  <select
                    value={ch2o}
                    onChange={(e) => setCh2o(Number(e.target.value))}
                    className="w-full px-3 py-2 rounded-xl border border-border bg-surface text-text text-sm focus:border-primary focus:ring-1 focus:ring-primary"
                  >
                    <option value={1}>&lt; 1 liter / day</option>
                    <option value={2}>1 - 2 liters / day</option>
                    <option value={3}>&gt; 2 liters / day</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-muted uppercase tracking-wider mb-1">
                    Physical Activity (FAF)
                  </label>
                  <select
                    value={faf}
                    onChange={(e) => setFaf(Number(e.target.value))}
                    className="w-full px-3 py-2 rounded-xl border border-border bg-surface text-text text-sm focus:border-primary focus:ring-1 focus:ring-primary"
                  >
                    <option value={0}>None (0 days)</option>
                    <option value={1}>1 - 2 days / week</option>
                    <option value={2}>3 - 4 days / week</option>
                    <option value={3}>&ge; 5 days / week</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-muted uppercase tracking-wider mb-1">
                    Screen Time (TUE)
                  </label>
                  <select
                    value={tue}
                    onChange={(e) => setTue(Number(e.target.value))}
                    className="w-full px-3 py-2 rounded-xl border border-border bg-surface text-text text-sm focus:border-primary focus:ring-1 focus:ring-primary"
                  >
                    <option value={0}>0 - 2 hours / day</option>
                    <option value={1}>3 - 5 hours / day</option>
                    <option value={2}>&gt; 5 hours / day</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-muted uppercase tracking-wider mb-1">
                    High Calorie Foods (FAVC)
                  </label>
                  <select
                    value={favc}
                    onChange={(e) => setFavc(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl border border-border bg-surface text-text text-sm focus:border-primary focus:ring-1 focus:ring-primary"
                  >
                    <option value="yes">Frequent fast food / fried</option>
                    <option value="no">Infrequent / Home cooked</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-muted uppercase tracking-wider mb-1">
                    Snacking Between Meals
                  </label>
                  <select
                    value={caec}
                    onChange={(e) => setCaec(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl border border-border bg-surface text-text text-sm focus:border-primary focus:ring-1 focus:ring-primary"
                  >
                    <option value="no">No snacking</option>
                    <option value="Sometimes">Sometimes</option>
                    <option value="Frequently">Frequently</option>
                    <option value="Always">Always</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-muted uppercase tracking-wider mb-1">
                    Primary Transportation
                  </label>
                  <select
                    value={mtrans}
                    onChange={(e) => setMtrans(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl border border-border bg-surface text-text text-sm focus:border-primary focus:ring-1 focus:ring-primary"
                  >
                    <option value="Automobile">Automobile / Car</option>
                    <option value="Public_Transportation">Public Transit</option>
                    <option value="Walking">Walking / Foot</option>
                    <option value="Bike">Bicycle</option>
                  </select>
                </div>
              </div>

              <Button
                type="submit"
                variant="primary"
                size="lg"
                isLoading={isLoading}
                className="w-full"
              >
                Compute Lifestyle Risk
              </Button>
            </form>
          </Card>
        </div>

        {/* Right Column: Model Output Cards */}
        <div className="lg:col-span-7 space-y-4">
          {result ? (
            <>
              {/* Dark Green Gradient "Highest Likelihood" Card */}
              <DarkCard className="p-6">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-xs font-bold uppercase tracking-wider text-primary-accent">
                    HIGHEST LIKELIHOOD MATCH
                  </span>
                  <Badge variant="accent">
                    {winningConfidence}% Calibrated Confidence
                  </Badge>
                </div>

                <div className="flex items-baseline space-x-3 mb-2">
                  <span className="text-3xl sm:text-4xl font-extrabold text-white">
                    {result.predicted_category}
                  </span>
                </div>

                <p className="text-xs text-white/80 leading-relaxed mt-2">
                  Predicted behavioral weight-status tier from habit signatures. Height and weight were
                  excluded to prevent memorizing current BMI.
                </p>
              </DarkCard>

              {/* Top Likelihood Rankings Progress Bars */}
              <Card className="p-5">
                <h3 className="text-xs font-bold text-muted uppercase tracking-wider mb-4">
                  Top Likelihood Rankings
                </h3>
                <div className="space-y-3.5">
                  {sortedProbabilities.map((item, idx) => {
                    const pct = Math.round(item.prob * 100);
                    return (
                      <div key={item.tier}>
                        <div className="flex justify-between text-xs font-semibold text-text mb-1">
                          <span>{item.tier}</span>
                          <span className={idx === 0 ? 'text-primary font-bold' : 'text-muted'}>
                            {pct}%
                          </span>
                        </div>
                        <div className="w-full bg-bg border border-border h-2.5 rounded-full overflow-hidden">
                          <div
                            className={`h-full rounded-full transition-all duration-300 ${
                              idx === 0 ? 'bg-primary' : 'bg-primary-accent/60'
                            }`}
                            style={{ width: `${pct}%` }}
                          />
                        </div>
                      </div>
                    );
                  })}
                </div>
              </Card>

              {/* What is driving this? SHAP Factors */}
              <Card className="p-5">
                <h3 className="text-xs font-bold text-muted uppercase tracking-wider mb-3">
                  What is Driving This Result (TreeSHAP Explanations)
                </h3>
                <div className="space-y-2.5">
                  {/* Risk Raising Factors (Amber) */}
                  {result.top_risk_factors?.map((f: any, i: number) => (
                    <div
                      key={`risk-${i}`}
                      className="p-3 rounded-xl bg-warning-soft border border-warning/20 flex items-start space-x-2.5 text-xs text-text"
                    >
                      <Badge variant="warning" className="flex-shrink-0 mt-0.5">
                        Raises Risk
                      </Badge>
                      <div>
                        <span className="font-semibold block text-text">
                          {f.factor || f.feature || 'Behavioral Factor'}
                        </span>
                        <span className="text-muted text-[11px] block mt-0.5">
                          {f.explanation || f.impact || 'Contributes toward higher weight status category.'}
                        </span>
                      </div>
                    </div>
                  ))}

                  {/* Protective Factors (Green) */}
                  {result.top_protective_factors?.map((f: any, i: number) => (
                    <div
                      key={`prot-${i}`}
                      className="p-3 rounded-xl bg-primary-soft border border-primary/20 flex items-start space-x-2.5 text-xs text-text"
                    >
                      <Badge variant="success" className="flex-shrink-0 mt-0.5">
                        Lowers Risk
                      </Badge>
                      <div>
                        <span className="font-semibold block text-text">
                          {f.factor || f.feature || 'Protective Habit'}
                        </span>
                        <span className="text-muted text-[11px] block mt-0.5">
                          {f.explanation || f.impact || 'Promotes weight maintenance and metabolic protection.'}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </Card>

              {/* Verification & Model Card Caveat */}
              <Card className="p-4 bg-bg border border-border">
                <div className="flex items-start space-x-2.5">
                  <ShieldCheck className="w-4 h-4 text-primary flex-shrink-0 mt-0.5" />
                  <div className="text-xs text-muted leading-relaxed">
                    <strong className="text-text block mb-0.5">Screening Aid Verification</strong>
                    Model artifacts trained on calibrated lifestyle surveys. Note that real-world
                    lifestyle factors interact with genetic, clinical, and medication variables not captured
                    in survey screening.
                  </div>
                </div>
              </Card>

              {/* Action Button */}
              <div className="flex items-center justify-between pt-2">
                <Button
                  variant="outline"
                  onClick={handleSaveToHistory}
                  isLoading={isSaving}
                  leftIcon={<Bookmark className="w-4 h-4 text-primary" />}
                >
                  Save Screening to History
                </Button>
                {savedSuccess && (
                  <span className="text-xs font-semibold text-primary flex items-center">
                    <CheckCircle2 className="w-4 h-4 mr-1 text-primary" />
                    Saved to history!
                  </span>
                )}
              </div>
            </>
          ) : (
            <Card className="p-10 text-center text-muted">
              <Activity className="w-8 h-8 text-muted mx-auto mb-2 opacity-50" />
              <p className="text-sm font-semibold">Ready to compute lifestyle obesity risk</p>
            </Card>
          )}
        </div>
      </div>

      <DisclaimerNotice />
    </div>
  );
};
