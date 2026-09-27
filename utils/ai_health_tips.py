# ============================================================
# utils/ai_health_tips.py — Dynamic AI Health Advisor Engine
# ============================================================

import random
from datetime import datetime

AI_TIPS_DATABASE = [
    # ── Cardiometabolic & Glycemic Balance ──────────────────────
    {
        'id': 'meta_01',
        'title': 'Post-Meal Ambulatory Glucose Clearance',
        'category': 'Cardiometabolic',
        'category_slug': 'cardiometabolic',
        'icon': '🩸',
        'rationale': 'Post-prandial skeletal muscle contractions activate non-insulin dependent GLUT-4 translocation, curbing blood sugar excursions by up to 35%.',
        'action_step': 'Take a brisk 10 to 15-minute walk within 30 minutes following your carbohydrate-rich meal today.',
        'target_biomarker': 'Post-Prandial Glycemia & Insulin Sensitivity',
        'impact': 'High Clinical Impact',
        'impact_color': '#34d399',
        'trigger_conditions': ['high_bmi', 'diabetes_risk', 'sedentary']
    },
    {
        'id': 'meta_02',
        'title': 'Soluble Viscous Fiber Pre-Loading',
        'category': 'Cardiometabolic',
        'category_slug': 'cardiometabolic',
        'icon': '🥗',
        'rationale': 'Soluble dietary fibers (beta-glucan and pectin) delay gastric emptying and form an intestinal gel matrix that flattens post-meal glucose absorption.',
        'action_step': 'Consume a starter of leafy greens, chia seeds, or raw vegetables 10 minutes prior to consuming starches.',
        'target_biomarker': 'Glycemic Index & Lipid Absorption',
        'impact': 'Preventative Optimization',
        'impact_color': '#38bdf8',
        'trigger_conditions': ['high_bmi', 'general']
    },
    {
        'id': 'meta_03',
        'title': 'Circadian Insulin Timing Window',
        'category': 'Cardiometabolic',
        'category_slug': 'cardiometabolic',
        'icon': '⏰',
        'rationale': 'Peripheral tissue insulin sensitivity naturally declines in the evening as endogenous melatonin levels surge, impairing glucose disposal.',
        'action_step': 'Conclude your final meal of the day at least 3 hours prior to sleep to prevent nocturnal metabolic strain.',
        'target_biomarker': 'Fasting Insulin & Nocturnal Metabolic Rate',
        'impact': 'High Clinical Impact',
        'impact_color': '#34d399',
        'trigger_conditions': ['high_bmi', 'diabetes_risk', 'general']
    },

    # ── Vascular & Blood Pressure Regulation ────────────────────
    {
        'id': 'vasc_01',
        'title': 'Dietary Nitrate Endothelial Nitric Oxide Surge',
        'category': 'Cardiovascular',
        'category_slug': 'cardiovascular',
        'icon': '🫀',
        'rationale': 'Inorganic nitrates from beetroot and dark leafy greens enter the enterosalivary pathway, promoting systemic vasodilation and arterial elasticity.',
        'action_step': 'Integrate a portion of raw spinach, arugula, or cold-pressed beetroot into your lunch or dinner today.',
        'target_biomarker': 'Resting Systolic Blood Pressure & Endothelial Tone',
        'impact': 'High Clinical Impact',
        'impact_color': '#34d399',
        'trigger_conditions': ['hypertension_risk', 'heart_risk', 'smoker']
    },
    {
        'id': 'vasc_02',
        'title': 'Isometric Handgrip Vascular Conditioning',
        'category': 'Cardiovascular',
        'category_slug': 'cardiovascular',
        'icon': '✊',
        'rationale': 'Clinical trials demonstrate that 4 cycles of 2-minute isometric contractions trigger reactive hyperemia, lowering resting blood pressure by 5–8 mmHg.',
        'action_step': 'Perform 4 sets of 2-minute handgrip squeeze at 30% maximal effort with 1 minute rest in between.',
        'target_biomarker': 'Mean Arterial Pressure (MAP) & Baroreceptor Reflex',
        'impact': 'Preventative Optimization',
        'impact_color': '#38bdf8',
        'trigger_conditions': ['hypertension_risk', 'heart_risk']
    },
    {
        'id': 'vasc_03',
        'title': 'Potassium-to-Sodium Ratio Rebalancing',
        'category': 'Cardiovascular',
        'category_slug': 'cardiovascular',
        'icon': '🥑',
        'rationale': 'Elevated urinary sodium excretion without commensurate dietary potassium promotes fluid retention and stiffens vascular smooth muscle.',
        'action_step': 'Add potassium-dense whole foods like avocados, coconut water, or bananas while eliminating ultra-processed savory snacks.',
        'target_biomarker': 'Vascular Resistance & Renal Sodium Excretion',
        'impact': 'High Clinical Impact',
        'impact_color': '#34d399',
        'trigger_conditions': ['hypertension_risk', 'general']
    },

    # ── Renal Clearance & Cellular Hydration ───────────────────
    {
        'id': 'renal_01',
        'title': 'Glomerular Filtration Electrolyte Hydration',
        'category': 'Renal Health',
        'category_slug': 'renal',
        'icon': '💧',
        'rationale': 'Adequate fluid balance sustains renal perfusion pressure and prevents supersaturation of uric acid and calcium oxalate crystals.',
        'action_step': 'Drink 500 mL of pure water with a pinch of unrefined mineral salt upon waking before consuming caffeine.',
        'target_biomarker': 'Estimated GFR & Urinary Osmolality',
        'impact': 'Preventative Optimization',
        'impact_color': '#38bdf8',
        'trigger_conditions': ['kidney_risk', 'general', 'active']
    },
    {
        'id': 'renal_02',
        'title': 'Oxidative Renal Cortex Quenching',
        'category': 'Renal Health',
        'category_slug': 'renal',
        'icon': '🫐',
        'rationale': 'Proanthocyanidins and anthocyanins protect delicate nephron basement membranes from lipid peroxidation and systemic oxidative stress.',
        'action_step': 'Incorporate half a cup of fresh blueberries, cranberries, or pomegranate seeds into your morning routine.',
        'target_biomarker': 'Serum Creatinine & Microalbuminuria',
        'impact': 'High Clinical Impact',
        'impact_color': '#34d399',
        'trigger_conditions': ['kidney_risk', 'diabetes_risk']
    },

    # ── Neurological Resilience & Circadian Architecture ────────
    {
        'id': 'neuro_01',
        'title': 'Morning Retinal Lux Stimulation',
        'category': 'Neurological & Sleep',
        'category_slug': 'neurological',
        'icon': '☀️',
        'rationale': 'Natural morning sunlight exposure activates intrinsically photosensitive retinal ganglion cells (ipRGCs), resetting your suprachiasmatic nucleus.',
        'action_step': 'Spend 10 to 15 minutes outdoors in natural sunlight within 60 minutes of waking up without sunglasses.',
        'target_biomarker': 'Cortisol Awakening Response & Melatonin Timing',
        'impact': 'High Clinical Impact',
        'impact_color': '#34d399',
        'trigger_conditions': ['sedentary', 'general']
    },
    {
        'id': 'neuro_02',
        'title': 'Non-Sleep Deep Rest (NSDR) Neural Recovery',
        'category': 'Neurological & Sleep',
        'category_slug': 'neurological',
        'icon': '🧠',
        'rationale': '10 to 20 minutes of guided progressive physiological relaxation elevates striatal dopamine reserves and restores prefrontal executive focus.',
        'action_step': 'Conduct a 12-minute physiological sigh or Yoga Nidra session during your afternoon energy dip today.',
        'target_biomarker': 'Parasympathetic Tone (HRV) & Neuroplasticity',
        'impact': 'Preventative Optimization',
        'impact_color': '#38bdf8',
        'trigger_conditions': ['parkinsons_risk', 'general']
    },

    # ── Clinical Nutrition & Cellular Longevity ────────────────
    {
        'id': 'nutri_01',
        'title': 'Sulfur-Rich Phase-II Hepatic Support',
        'category': 'Hepatic & Detox',
        'category_slug': 'hepatic',
        'icon': '🥦',
        'rationale': 'Glucoraphanin in cruciferous vegetables converts to sulforaphane, potentizing Nrf2 transcription and glutathione synthesis.',
        'action_step': 'Consume steamed broccoli, Brussels sprouts, or garlic with lunch to stimulate hepatic detoxification enzymes.',
        'target_biomarker': 'ALT / AST Transaminases & Serum Glutathione',
        'impact': 'High Clinical Impact',
        'impact_color': '#34d399',
        'trigger_conditions': ['liver_risk', 'alcohol', 'general']
    },
    {
        'id': 'nutri_02',
        'title': 'Anti-Inflammatory Omega-3 Index Enhancement',
        'category': 'Cellular Health',
        'category_slug': 'cellular',
        'icon': '🐟',
        'rationale': 'Eicosapentaenoic acid (EPA) and docosahexaenoic acid (DHA) displace arachidonic acid in cell membranes, damping pro-inflammatory eicosanoids.',
        'action_step': 'Add wild-caught salmon, sardines, walnuts, or flaxseed meal to your nutrition plan today.',
        'target_biomarker': 'C-Reactive Protein (hs-CRP) & Cellular Fluidity',
        'impact': 'Preventative Optimization',
        'impact_color': '#38bdf8',
        'trigger_conditions': ['heart_risk', 'stroke_risk', 'general']
    },

    # ── Active Conditioning & Zone-2 Fitness ───────────────────
    {
        'id': 'act_01',
        'title': 'Zone-2 Mitochondrial Biogenesis',
        'category': 'Physical Conditioning',
        'category_slug': 'fitness',
        'icon': '⚡',
        'rationale': 'Low-intensity steady-state cardiovascular training maximizes cellular lactate clearance and increases mitochondrial density in slow-twitch fibers.',
        'action_step': 'Engage in 25 to 30 minutes of nasal-only steady-state cycling, brisk uphill walking, or jogging today.',
        'target_biomarker': 'Mitochondrial Density & VO2 Max Capacity',
        'impact': 'High Clinical Impact',
        'impact_color': '#34d399',
        'trigger_conditions': ['sedentary', 'high_bmi', 'general']
    }
]


def evaluate_user_triggers(user) -> list:
    """
    Evaluates patient profile and prediction history to determine
    tailored clinical trigger tags.
    """
    triggers = ['general']
    if not user:
        return triggers

    # Check profile attributes
    profile = getattr(user, 'profile', None)
    if profile:
        bmi = profile.bmi or 0
        if bmi >= 25.0:
            triggers.append('high_bmi')
        if getattr(profile, 'smoking_status', '') in ['Current Smoker', 'Occasional']:
            triggers.append('smoker')
        if getattr(profile, 'alcohol_status', '') in ['Regular', 'Heavy']:
            triggers.append('alcohol')
        if getattr(profile, 'activity_level', '') in ['Sedentary', 'Lightly Active']:
            triggers.append('sedentary')
        elif getattr(profile, 'activity_level', '') in ['Very Active']:
            triggers.append('active')

    # Check recent prediction history
    try:
        from database.db import PredictionHistory
        recent = PredictionHistory.query.filter_by(user_id=user.id).order_by(PredictionHistory.created_at.desc()).limit(5).all()
        for p in recent:
            dis = p.disease_name.lower()
            if 'diabet' in dis:
                triggers.append('diabetes_risk')
            if 'heart' in dis:
                triggers.append('heart_risk')
            if 'hypertens' in dis:
                triggers.append('hypertension_risk')
            if 'kidney' in dis:
                triggers.append('kidney_risk')
            if 'liver' in dis:
                triggers.append('liver_risk')
            if 'parkin' in dis:
                triggers.append('parkinsons_risk')
            if 'stroke' in dis:
                triggers.append('stroke_risk')
    except Exception:
        pass

    return list(set(triggers))


def get_personalized_ai_tip(user=None, requested_id=None, requested_category=None) -> dict:
    """
    Returns an AI personalized health tip dynamically calibrated for the user.
    """
    triggers = evaluate_user_triggers(user)

    # Filter pool
    candidates = []
    for tip in AI_TIPS_DATABASE:
        if requested_id and tip['id'] == requested_id:
            return tip
        if requested_category and tip['category_slug'] != requested_category:
            continue
        
        # Check if any trigger matches
        if any(trig in tip['trigger_conditions'] for trig in triggers):
            candidates.append(tip)

    if not candidates:
        candidates = AI_TIPS_DATABASE

    # Choose pseudo-randomly based on current day/time or random
    selected = random.choice(candidates)
    
    # Add dynamic metadata
    tip_payload = dict(selected)
    tip_payload['timestamp'] = datetime.utcnow().strftime('%I:%M %p UTC')
    tip_payload['match_reasons'] = [t.replace('_', ' ').title() for t in triggers if t in selected['trigger_conditions']]
    
    return tip_payload


def get_all_ai_tips_for_user(user=None) -> list:
    """
    Returns full list of tips prioritized for user profile.
    """
    triggers = evaluate_user_triggers(user)
    ranked = []
    
    for tip in AI_TIPS_DATABASE:
        score = sum(1 for trig in triggers if trig in tip['trigger_conditions'])
        t = dict(tip)
        t['relevance_score'] = score
        ranked.append(t)

    ranked.sort(key=lambda x: x['relevance_score'], reverse=True)
    return ranked
