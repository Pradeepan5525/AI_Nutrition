# Clinical Nutrition Rules and Guidelines Documentation (CLINICAL_RULES.md)

This document formalizes the evidence-based nutritional guidelines, quantitative nutrient constraints, clinical citations, and multi-condition conflict resolution logic embedded in the Nutrition Intelligence System.

---

## 1. Supported Clinical Conditions and Authoritative Guidelines

### 1.1 Hypertension / Elevated Blood Pressure
- **Clinical Pattern:** Dietary Approaches to Stop Hypertension (DASH).
- **Authoritative Citation:** American Heart Association (AHA) / American College of Cardiology (ACC) Guideline for the Prevention, Detection, Evaluation, and Management of High Blood Pressure in Adults (Whelton et al., 2017).
- **Core Constraints:**
  - **Sodium Cap:** $\le 1,500\text{ mg/day}$ (AHA lower threshold for blood pressure reduction).
  - **Dietary Fiber Target:** $\ge 16.0\text{ g per 1,000 kcal}$.
- **Dietary Priorities:** High potassium and magnesium from whole vegetables, fruits, and legumes; avoidance of salted snacks, processed meats, and high-sodium condiments.

### 1.2 Type 2 Diabetes / Dysglycemia
- **Clinical Pattern:** Glycemic Control & Medical Nutrition Therapy.
- **Authoritative Citation:** American Diabetes Association (ADA) Standards of Care in Diabetes (2024), Chapter 5: Facilitating Positive Health Behaviors.
- **Core Constraints:**
  - **Free / Added Sugar Cap:** $\le 5.0\%$ of total daily caloric intake (e.g., $\le 25\text{ g}$ on a 2,000 kcal plan).
  - **Dietary Fiber Target:** $\ge 18.0\text{ g per 1,000 kcal}$ (viscous soluble fiber to blunt postprandial glucose spikes).
  - **Carbohydrate Distribution:** Spaced across meals; complex unrefined carbohydrate sources favored over high-glycemic starches.

### 1.3 Hypercholesterolemia / Dyslipidemia
- **Clinical Pattern:** Atherosclerotic Cardiovascular Disease (ASCVD) Risk Reduction.
- **Authoritative Citation:** AHA/ACC Guideline on the Management of Blood Cholesterol (Grundy et al., 2018) & NCEP ATP III.
- **Core Constraints:**
  - **Saturated Fat Cap:** $\le 7.0\%$ of total daily caloric intake (lowers circulating LDL particles).
  - **Dietary Cholesterol Cap:** $\le 200.0\text{ mg/day}$.
  - **Dietary Fiber Target:** $\ge 16.0\text{ g per 1,000 kcal}$ (soluble fiber increases intestinal bile acid excretion).

### 1.4 Overweight / Obesity
- **Clinical Pattern:** Energy Balance, Satiety Optimization, and Lean Mass Retention.
- **Authoritative Citation:** AHA/ACC/The Obesity Society (TOS) Guideline for the Management of Overweight and Obesity in Adults (Jensen et al., 2013).
- **Core Constraints:**
  - **Daily Deficit:** $250\text{ to }500\text{ kcal/day}$ below TDEE (rate of $0.25\text{--}0.5\text{ kg/week}$).
  - **Caloric Floors:** Never below $1,200\text{ kcal}$ (women) or $1,500\text{ kcal}$ (men) without clinical intervention.
  - **Protein Target:** $1.4\text{ to }1.6\text{ g/kg body weight}$ to preserve skeletal muscle during deficit.
  - **Fiber Target:** $\ge 16.0\text{ g per 1,000 kcal}$ to maximize gastric fullness.

---

## 2. Supported Dietary Restrictions Vocabulary

The system natively supports dietary preferences and restrictions matching the raw dataset vocabulary:
- **Low Sodium:** Sodium $\le 1,500\text{ mg/day}$.
- **Low Sugar:** Free added sugar $\le 5.0\%$ of daily energy.
- **Vegetarian:** Complete exclusion of meat, poultry, fish, and animal gelatin.
- **Vegan:** Vegetarian + complete exclusion of dairy, eggs, and honey.
- **Gluten-Free:** Excludes wheat, barley, rye, spelt, triticale, and unverified malt products.
- **Dairy-Free:** Excludes all mammalian milk, butter, cheese, whey, casein, and yogurt.
- **Nut-Free:** Excludes all tree nuts (almonds, walnuts, cashews, etc.) and peanuts.

---

## 3. Multi-Condition Conflict Resolution Hierarchy

When a user presents with multiple co-morbidities (e.g., Hypertension + Type 2 Diabetes + Hypercholesterolemia):

```
                   Clinical Inputs
      [Hypertension]   [Diabetes]   [Dyslipidemia]
             │              │              │
             ▼              ▼              ▼
       Sodium ≤ 1500mg  Sugar ≤ 5%     Sat Fat ≤ 7%
       Fiber ≥ 16g      Fiber ≥ 18g    Cholesterol ≤ 200mg
             │              │              │
             └──────────────┼──────────────┘
                            │
                            ▼
              Strictest Bound Resolver
     ┌──────────────────────────────────────────────┐
     │  Max Bounds (Upper Limits):                  │
     │    min(2300, 1500)       --> Sodium = 1500mg │
     │    min(10%, 5%)          --> Sugar = 5%      │
     │    min(10%, 7%)          --> Sat Fat = 7%    │
     │    min(300, 200)         --> Chol = 200mg    │
     │                                              │
     │  Min Bounds (Lower Targets):                 │
     │    max(14g, 16g, 18g)    --> Fiber = 18g/1k  │
     └──────────────────────────────────────────────┘
                            │
                            ▼
         Adjusted Targets + "Why This Limit" Audit
```

### Deterministic Principles:
1. **Upper Bounds (Toxicity / Risk Capping):** The numerical **minimum** across all active rules is selected. (e.g. Hypertension 1,500 mg overrides standard 2,300 mg).
2. **Lower Bounds (Therapeutic Floor):** The numerical **maximum** across all active rules is selected. (e.g. Diabetes 18 g/1,000 kcal overrides standard 14 g).
3. **Transparent Audit Trail:** For every nutrient parameter, the resulting metadata preserves:
   - `final_value`: Numeric value enforced.
   - `ruling_condition`: Which specific condition dictated the constraint.
   - `citation`: Medical guideline authority.
   - `reason`: Clinical rationale.

---

## 4. Extension Point for Custom Conditions

New clinical guidelines or institutional protocols can be registered dynamically via:
```python
from nutri.rules.conditions import register_custom_condition_rule

register_custom_condition_rule(
    "chronic_kidney_disease_stage3",
    {
        "name": "CKD Stage 3 (Non-Dialysis)",
        "citation": "KDOQI Clinical Practice Guideline for Nutrition in CKD (2020)",
        "constraints": {
            "max_sodium_mg": {"value": 2000.0, "reason": "Fluid balance management."},
            "max_protein_g_per_kg": {
                "value": 0.8,
                "reason": "Reduce uremic toxins and proteinuria.",
            },
        },
        "guidance": ["Limit dietary protein to 0.55-0.8 g/kg to preserve renal function."],
    },
)
```
