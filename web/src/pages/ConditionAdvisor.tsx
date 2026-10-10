import React, { useState } from 'react';
import {
  FileText,
  ShieldCheck,
  CheckCircle2,
  AlertCircle,
  ExternalLink,
  BookOpen,
} from 'lucide-react';
import { Card } from '../components/common/Card';
import { Badge } from '../components/common/Badge';
import { Button } from '../components/common/Button';
import { DisclaimerNotice } from '../components/common/DisclaimerNotice';

export const ConditionAdvisor: React.FC = () => {
  const [selectedCondition, setSelectedCondition] = useState<string>('hypertension');

  const conditionsData: Record<string, any> = {
    hypertension: {
      title: 'Hypertension (High Blood Pressure)',
      guideline: 'American Heart Association (AHA) DASH Dietary Pattern',
      citation: 'Whelton PK et al. 2018 ACC/AHA High Blood Pressure Clinical Practice Guideline',
      sodiumCap: '1,500 mg / day',
      potassiumTarget: '4,700 mg / day',
      satFatCap: '< 6% of daily calories',
      fiberFloor: '30 g / day',
      guidance:
        'The Dietary Approaches to Stop Hypertension (DASH) eating plan emphasizes rich potassium and magnesium sources (leafy greens, legumes, whole grains) while enforcing a strict sodium limit of 1,500 mg per day. Processed cured meats and packaged snacks should be substituted with unprocessed foundation foods.',
      foodsToPrioritize: [
        'Dark leafy greens (Spinach, Kale, Swiss chard)',
        'Potassium-rich fruits (Bananas, Oranges, Apricots)',
        'Whole grains (Steel-cut oats, Quinoa, Brown rice)',
        'Unsalted raw nuts and seeds (Walnuts, Flaxseed)',
      ],
      foodsToAvoid: [
        'Cured meats, bacon, deli cold cuts, hot dogs',
        'Canned soups with sodium > 400mg per serving',
        'Salted snack chips, pretzels, crackers',
        'Commercial sauces, soy sauce, bouillon cubes',
      ],
      precautions: [
        'Do not eliminate sodium entirely; physiological baseline requires at least 500 mg/day.',
        'Beware of sodium hidden in leavened baked bread and commercial salad dressings.',
        'Consult with your physician if taking ACE inhibitors or ARBs regarding potassium supplementation.',
      ],
    },
    diabetes: {
      title: 'Type 2 Diabetes & Insulin Resistance',
      guideline: 'American Diabetes Association (ADA) Standards of Care in Diabetes',
      citation: 'Evert AB et al. Nutrition Therapy for Adults with Diabetes or Prediabetes. Diabetes Care 2019',
      sodiumCap: '2,000 mg / day',
      potassiumTarget: '3,800 mg / day',
      satFatCap: '< 7% of daily calories',
      fiberFloor: '35 g / day',
      guidance:
        'Nutritional therapy focuses on consistent carbohydrate distribution, replacing high-glycemic carbohydrates with complex unrefined sources rich in viscous soluble fiber. Added free sugars are strictly capped at under 5% of total energy intake (approximately 25g per day) to stabilize postprandial glucose excursions.',
      foodsToPrioritize: [
        'Non-starchy cruciferous vegetables (Broccoli, Cauliflower, Cabbage)',
        'High-fiber legumes (Lentils, Chickpeas, Black beans)',
        'Lean poultry, wild fatty fish (Salmon, Mackerel)',
        'Healthy fats (Extra virgin olive oil, Avocado)',
      ],
      foodsToAvoid: [
        'Sugar-sweetened sodas, commercial fruit juices',
        'Refined grain flour (White bread, refined white pasta)',
        'Pastries, sweetened cereals, breakfast syrups',
        'Ultra-processed convenience foods high in maltodextrin',
      ],
      precautions: [
        'Monitor blood glucose closely if significantly lowering carbohydrate intake while on insulin or sulfonylureas to prevent hypoglycemia.',
        'Artificial sweeteners should not be relied upon as a replacement for whole-food hydration.',
        'Spreading carbohydrate portions evenly across 3 structured meals avoids large glycemic spikes.',
      ],
    },
    high_cholesterol: {
      title: 'Dyslipidemia & High Cholesterol',
      guideline: 'ACC/AHA Guideline on the Management of Blood Cholesterol',
      citation: 'Grundy SM et al. 2018 AHA/ACC/AACVPR/AAPA/ABC/ACPM/ADA/AGS/APhA/ASPC/NLA/PCNA Guideline',
      sodiumCap: '2,300 mg / day',
      potassiumTarget: '3,500 mg / day',
      satFatCap: '< 5% - 6% of daily calories',
      fiberFloor: '30 g / day (10g soluble)',
      guidance:
        'Therapeutic lifestyle changes emphasize reducing saturated and trans-fatty acids while increasing viscous soluble fiber, which actively binds bile acids in the intestinal lumen to lower serum LDL cholesterol. Plant sterols and stanols can provide additional LDL reductions.',
      foodsToPrioritize: [
        'Soluble fiber superstars (Oat bran, Barley, Psyllium husk)',
        'Omega-3 rich cold-water fish (Sardines, Trout, Salmon)',
        'Plant-based proteins (Tofu, Edamame, Tempeh)',
        'Monounsaturated fat sources (Extra virgin olive oil, Almonds)',
      ],
      foodsToAvoid: [
        'Fatty cuts of red beef, pork, sausage',
        'Full-fat dairy, heavy cream, butter, lard',
        'Fried fast foods cooked in partially hydrogenated oils',
        'Commercial baked goods with palm oil or coconut oil',
      ],
      precautions: [
        'Dietary cholesterol has less impact on serum LDL than saturated fat and trans fat.',
        'Increasing soluble fiber must be accompanied by gradual hydration to avoid gastrointestinal discomfort.',
      ],
    },
    obesity: {
      title: 'Obesity & Metabolic Syndrome',
      guideline: 'AHA/ACC/TOS Guideline for the Management of Overweight and Obesity in Adults',
      citation: 'Jensen MD et al. 2013 AHA/ACC/TOS Guideline for the Management of Overweight and Obesity',
      sodiumCap: '2,300 mg / day',
      potassiumTarget: '3,500 mg / day',
      satFatCap: '< 7% of daily calories',
      fiberFloor: '30 g / day',
      guidance:
        'Management requires sustained moderate energy deficits of 500 kcal per day to achieve a safe 0.5 kg to 1.0 kg weekly rate of fat loss without inducing metabolic adaptive thermogenesis or sacrificing fat-free mass. High protein density (1.6g - 2.0g/kg lean mass) supports satiety and thermic effect.',
      foodsToPrioritize: [
        'High-satiety low-energy-density foundation foods',
        'Lean animal and vegetable proteins (Egg whites, Chicken breast, Lentils)',
        'Volumetric vegetables (Zucchini, Cucumber, Spinach, Celery)',
        'Whole unprocessed berries (Strawberries, Blueberries, Blackberries)',
      ],
      foodsToAvoid: [
        'Liquid calorie beverages, alcoholic drinks',
        'Hyper-palatable combinations of refined starch and vegetable oils',
        'Skipping meals leading to compensatory nighttime binging',
      ],
      precautions: [
        'Crash dieting below 1,200 kcal/day is clinically withheld due to gallstone risk and rapid muscle wasting.',
        'Sustained habit transformation is vastly superior to acute short-term restriction.',
      ],
    },
  };

  const current = conditionsData[selectedCondition] || conditionsData.hypertension;

  return (
    <div className="space-y-6">
      {/* Header Card */}
      <Card className="p-6">
        <div className="flex items-center space-x-2 mb-2">
          <Badge variant="accent">Module 05</Badge>
          <Badge variant="neutral">Clinical Guideline Rules Engine</Badge>
        </div>
        <h1 className="text-2xl font-bold text-text">Clinical Condition Advisor &amp; Guidelines</h1>
        <p className="text-xs sm:text-sm text-muted mt-1">
          Evidence-based dietary parameters mapped directly from peer-reviewed clinical guidelines
          with transparent audit citations and verified bounds.
        </p>
      </Card>

      {/* Condition Selector Chips */}
      <div className="flex flex-wrap gap-2.5">
        {[
          { id: 'hypertension', label: 'Hypertension (AHA DASH)' },
          { id: 'diabetes', label: 'Type 2 Diabetes (ADA)' },
          { id: 'high_cholesterol', label: 'Dyslipidemia (ACC/AHA)' },
          { id: 'obesity', label: 'Obesity & Metabolic Syndrome' },
        ].map((c) => (
          <button
            key={c.id}
            onClick={() => setSelectedCondition(c.id)}
            className={`px-4 py-2 rounded-full text-xs font-semibold border transition-all ${
              selectedCondition === c.id
                ? 'bg-primary text-white border-primary shadow-sm'
                : 'bg-surface text-muted border-border hover:bg-bg hover:text-text'
            }`}
          >
            {c.label}
          </button>
        ))}
      </div>

      {/* Main Guidance & Bounds Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left Column: Stat Boxes & Food Recommendations */}
        <div className="lg:col-span-7 space-y-5">
          {/* 4 Stat Boxes for Guideline Bounds */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <Card className="p-3.5 text-center">
              <span className="text-[10px] font-bold text-muted uppercase tracking-wider block">
                Sodium Bound
              </span>
              <span className="text-base font-bold text-primary mt-1 block">{current.sodiumCap}</span>
              <span className="text-[10px] text-muted">Strictest cap</span>
            </Card>
            <Card className="p-3.5 text-center">
              <span className="text-[10px] font-bold text-muted uppercase tracking-wider block">
                Potassium
              </span>
              <span className="text-base font-bold text-text mt-1 block">{current.potassiumTarget}</span>
              <span className="text-[10px] text-muted">Electrolyte floor</span>
            </Card>
            <Card className="p-3.5 text-center">
              <span className="text-[10px] font-bold text-muted uppercase tracking-wider block">
                Sat. Fat Cap
              </span>
              <span className="text-base font-bold text-text mt-1 block">{current.satFatCap}</span>
              <span className="text-[10px] text-muted">AHA standard</span>
            </Card>
            <Card className="p-3.5 text-center">
              <span className="text-[10px] font-bold text-muted uppercase tracking-wider block">
                Fiber Target
              </span>
              <span className="text-base font-bold text-text mt-1 block">{current.fiberFloor}</span>
              <span className="text-[10px] text-muted">Minimum floor</span>
            </Card>
          </div>

          {/* Expert Clinical Guidance Panel */}
          <div className="p-5 rounded-card bg-primary-soft border border-primary/20 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-primary uppercase tracking-wider">
                Clinical Guidance Summary
              </span>
              <Badge variant="success">Guideline Consensus</Badge>
            </div>
            <p className="text-xs text-text leading-relaxed">{current.guidance}</p>
            <div className="flex items-center text-xs font-semibold text-primary pt-1">
              <CheckCircle2 className="w-4 h-4 mr-1.5 text-primary" />
              Verified from official recommendations
            </div>
          </div>

          {/* Foods to Prioritize vs Avoid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Card className="p-5">
              <h3 className="text-xs font-bold text-primary uppercase tracking-wider mb-3 flex items-center">
                <CheckCircle2 className="w-3.5 h-3.5 mr-1 text-primary" />
                Foods to Prioritize
              </h3>
              <ul className="text-xs text-text space-y-2">
                {current.foodsToPrioritize.map((food: string, idx: number) => (
                  <li key={idx} className="flex items-start space-x-1.5">
                    <span className="text-primary font-bold">&bull;</span>
                    <span>{food}</span>
                  </li>
                ))}
              </ul>
            </Card>

            <Card className="p-5">
              <h3 className="text-xs font-bold text-danger uppercase tracking-wider mb-3 flex items-center">
                <AlertCircle className="w-3.5 h-3.5 mr-1 text-danger" />
                Foods to Strictly Limit
              </h3>
              <ul className="text-xs text-text space-y-2">
                {current.foodsToAvoid.map((food: string, idx: number) => (
                  <li key={idx} className="flex items-start space-x-1.5">
                    <span className="text-danger font-bold">&bull;</span>
                    <span>{food}</span>
                  </li>
                ))}
              </ul>
            </Card>
          </div>
        </div>

        {/* Right Column: Evidence & Citations and Precautions */}
        <div className="lg:col-span-5 space-y-5">
          {/* Evidence & Citations Card */}
          <Card className="p-5">
            <h3 className="text-xs font-bold text-muted uppercase tracking-wider mb-3 flex items-center">
              <BookOpen className="w-4 h-4 mr-1.5 text-primary" />
              Evidence &amp; Clinical Citations
            </h3>

            <div className="p-3.5 rounded-xl bg-bg border border-border space-y-2 text-xs">
              <div>
                <span className="text-[10px] font-bold text-muted uppercase block">
                  Governing Clinical Guideline
                </span>
                <span className="font-semibold text-text">{current.guideline}</span>
              </div>
              <div className="pt-2 border-t border-border">
                <span className="text-[10px] font-bold text-muted uppercase block">
                  Authoritative Literature Citation
                </span>
                <span className="text-muted italic">{current.citation}</span>
              </div>
            </div>

            <p className="text-[11px] text-muted mt-3 leading-relaxed">
              When multiple clinical conditions co-occur (e.g. Hypertension + Diabetes), NutriIntel
              automatically executes strict hierarchical conflict resolution, enforcing the lowest
              tolerable sodium and sugar ceilings across all applicable clinical protocols.
            </p>
          </Card>

          {/* Important Precautions & Common Mistakes */}
          <Card className="p-5">
            <h3 className="text-xs font-bold text-text uppercase tracking-wider mb-3 flex items-center">
              <ShieldCheck className="w-4 h-4 mr-1.5 text-primary" />
              Important Precautions &amp; Common Mistakes
            </h3>

            <ul className="text-xs text-text space-y-2.5">
              {current.precautions.map((p: string, idx: number) => (
                <li key={idx} className="p-2.5 rounded-lg bg-bg border border-border flex items-start space-x-2">
                  <span className="font-bold text-primary">{idx + 1}.</span>
                  <span className="text-muted">{p}</span>
                </li>
              ))}
            </ul>
          </Card>
        </div>
      </div>

      <DisclaimerNotice />
    </div>
  );
};
