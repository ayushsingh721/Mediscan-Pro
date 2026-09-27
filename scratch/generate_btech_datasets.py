import os
import numpy as np
import pandas as pd

np.random.seed(42)
os.makedirs('datasets', exist_ok=True)

# 1. Diabetes (PIMA Indian format - 768 samples)
n = 768
preg = np.random.poisson(3.8, n).clip(0, 17)
glu = np.random.normal(120, 32, n).clip(44, 199).astype(int)
bp = np.random.normal(69, 19, n).clip(24, 122).astype(int)
skin = np.random.normal(20, 15, n).clip(0, 99).astype(int)
ins = np.random.normal(79, 115, n).clip(0, 846).astype(int)
bmi = np.round(np.random.normal(32.0, 7.8, n).clip(18.2, 67.1), 1)
ped = np.round(np.random.normal(0.47, 0.33, n).clip(0.08, 2.42), 3)
age = np.random.normal(33, 11.7, n).clip(21, 81).astype(int)
score = 0.03*glu + 0.04*bmi + 0.02*age + 0.5*ped - 4.2
prob = 1 / (1 + np.exp(-score))
outcome = (np.random.rand(n) < prob).astype(int)
df_diab = pd.DataFrame({
    'pregnancies': preg, 'glucose': glu, 'blood_pressure': bp,
    'skin_thickness': skin, 'insulin': ins, 'bmi': bmi,
    'diabetes_pedigree': ped, 'age': age, 'outcome': outcome
})
df_diab.to_csv('datasets/diabetes.csv', index=False)
print('Generated diabetes.csv:', len(df_diab))

# 2. Heart Disease (Cleveland format - 303 samples)
n = 303
age = np.random.normal(54.4, 9.0, n).clip(29, 77).astype(int)
sex = np.random.choice([0, 1], n, p=[0.32, 0.68])
cp = np.random.choice([0, 1, 2, 3], n, p=[0.47, 0.17, 0.28, 0.08])
trestbps = np.random.normal(131.6, 17.5, n).clip(94, 200).astype(int)
chol = np.random.normal(246.3, 51.8, n).clip(126, 564).astype(int)
fbs = np.random.choice([0, 1], n, p=[0.85, 0.15])
restecg = np.random.choice([0, 1, 2], n, p=[0.48, 0.50, 0.02])
thalach = np.random.normal(149.6, 22.9, n).clip(71, 202).astype(int)
exang = np.random.choice([0, 1], n, p=[0.67, 0.33])
oldpeak = np.round(np.random.exponential(1.0, n).clip(0.0, 6.2), 1)
slope = np.random.choice([0, 1, 2], n, p=[0.07, 0.46, 0.47])
ca = np.random.choice([0, 1, 2, 3, 4], n, p=[0.58, 0.22, 0.13, 0.05, 0.02])
thal = np.random.choice([0, 1, 2, 3], n, p=[0.01, 0.06, 0.55, 0.38])
score = 0.03*trestbps + 0.005*chol - 0.025*thalach + 0.6*exang + 0.4*oldpeak + 0.5*ca - 2.5
prob = 1 / (1 + np.exp(-score))
target = (np.random.rand(n) < prob).astype(int)
df_heart = pd.DataFrame({
    'age': age, 'sex': sex, 'cp': cp, 'trestbps': trestbps,
    'chol': chol, 'fbs': fbs, 'restecg': restecg, 'thalach': thalach,
    'exang': exang, 'oldpeak': oldpeak, 'slope': slope, 'ca': ca,
    'thal': thal, 'target': target
})
df_heart.to_csv('datasets/heart.csv', index=False)
print('Generated heart.csv:', len(df_heart))

# 3. Kidney Disease (CKD format - 400 samples)
n = 400
age = np.random.normal(51.5, 17.0, n).clip(2, 90).astype(int)
bp = np.random.choice([60, 70, 80, 90, 100, 110, 120], n)
sg = np.random.choice([1.005, 1.010, 1.015, 1.020, 1.025], n)
al = np.random.choice([0, 1, 2, 3, 4, 5], n, p=[0.5, 0.15, 0.15, 0.1, 0.05, 0.05])
bgr = np.random.normal(148, 79, n).clip(22, 490).astype(int)
bu = np.random.normal(57, 50, n).clip(1.5, 391).astype(int)
sc = np.round(np.random.exponential(1.5, n).clip(0.4, 76.0), 2)
hemo = np.round(np.random.normal(12.5, 2.9, n).clip(3.1, 17.8), 1)
pcv = np.random.normal(38.8, 8.9, n).clip(9, 54).astype(int)
wbcc = np.random.normal(8406, 2944, n).clip(2200, 26400).astype(int)
rbcc = np.round(np.random.normal(4.7, 1.0, n).clip(2.1, 8.0), 1)
htn = (bp >= 90).astype(int)
score = 0.8*sc + 0.01*bu - 0.3*hemo + 0.5*al - 1.0
prob = 1 / (1 + np.exp(-score))
outcome = (np.random.rand(n) < prob).astype(int)
df_kidney = pd.DataFrame({
    'age': age, 'blood_pressure': bp, 'specific_gravity': sg, 'albumin': al,
    'blood_glucose_random': bgr, 'blood_urea': bu, 'serum_creatinine': sc,
    'haemoglobin': hemo, 'packed_cell_volume': pcv, 'white_blood_cell_count': wbcc,
    'red_blood_cell_count': rbcc, 'hypertension': htn, 'outcome': outcome
})
df_kidney.to_csv('datasets/kidney.csv', index=False)
print('Generated kidney.csv:', len(df_kidney))

# 4. Liver Disease (ILPD format - 583 samples)
n = 583
age = np.random.normal(44.7, 16.2, n).clip(4, 90).astype(int)
gender = np.random.choice([0, 1], n, p=[0.24, 0.76])
tb = np.round(np.random.exponential(2.5, n).clip(0.4, 75.0), 1)
db = np.round((tb * np.random.uniform(0.3, 0.7, n)).clip(0.1, 19.7), 1)
alp = np.random.normal(290, 242, n).clip(63, 2110).astype(int)
alt = np.random.normal(80, 182, n).clip(10, 2000).astype(int)
ast = np.random.normal(109, 288, n).clip(10, 4929).astype(int)
tp = np.round(np.random.normal(6.5, 1.1, n).clip(2.7, 9.6), 1)
alb = np.round(np.random.normal(3.1, 0.8, n).clip(0.9, 5.5), 1)
agr = np.round((alb / (tp - alb + 0.001)).clip(0.3, 2.8), 2)
score = 0.05*tb + 0.005*alt + 0.003*ast - 0.4*alb - 0.5
prob = 1 / (1 + np.exp(-score))
outcome = (np.random.rand(n) < prob).astype(int)
df_liver = pd.DataFrame({
    'age': age, 'gender': gender, 'total_bilirubin': tb, 'direct_bilirubin': db,
    'alkaline_phosphotase': alp, 'alamine_aminotransferase': alt,
    'aspartate_aminotransferase': ast, 'total_proteins': tp, 'albumin': alb,
    'albumin_and_globulin_ratio': agr, 'outcome': outcome
})
df_liver.to_csv('datasets/liver.csv', index=False)
print('Generated liver.csv:', len(df_liver))

# 5. Parkinson's (Oxford format - 195 samples)
n = 195
fo = np.round(np.random.normal(154.2, 41.4, n).clip(88.3, 260.1), 3)
fhi = np.round(fo * np.random.uniform(1.1, 1.8, n), 3)
flo = np.round(fo * np.random.uniform(0.6, 0.95, n), 3)
jit = np.round(np.random.normal(0.006, 0.005, n).clip(0.001, 0.033), 5)
shim = np.round(np.random.normal(0.029, 0.019, n).clip(0.009, 0.119), 5)
nhr = np.round(np.random.normal(0.024, 0.040, n).clip(0.0006, 0.314), 5)
hnr = np.round(np.random.normal(21.8, 4.4, n).clip(8.4, 33.0), 3)
rpde = np.round(np.random.normal(0.49, 0.10, n).clip(0.25, 0.68), 5)
dfa = np.round(np.random.normal(0.71, 0.05, n).clip(0.57, 0.82), 5)
sp1 = np.round(np.random.normal(-5.68, 1.09, n).clip(-7.96, -2.43), 4)
sp2 = np.round(np.random.normal(0.22, 0.08, n).clip(0.006, 0.45), 4)
d2 = np.round(np.random.normal(2.38, 0.38, n).clip(1.42, 3.67), 4)
score = 80*jit + 20*shim - 0.1*hnr + 1.2*sp2 - 0.5
prob = 1 / (1 + np.exp(-score))
status = (np.random.rand(n) < prob).astype(int)
df_park = pd.DataFrame({
    'mdvp_fo': fo, 'mdvp_fhi': fhi, 'mdvp_flo': flo, 'mdvp_jitter': jit,
    'mdvp_shimmer': shim, 'nhr': nhr, 'hnr': hnr, 'rpde': rpde,
    'dfa': dfa, 'spread1': sp1, 'spread2': sp2, 'd2': d2, 'status': status
})
df_park.to_csv('datasets/parkinsons.csv', index=False)
print('Generated parkinsons.csv:', len(df_park))

# 6. Breast Cancer (Wisconsin WDBC format - 569 samples)
n = 569
rm = np.round(np.random.normal(14.1, 3.5, n).clip(6.9, 28.1), 2)
tm = np.round(np.random.normal(19.3, 4.3, n).clip(9.7, 39.2), 2)
pm = np.round(rm * 2 * np.pi * np.random.uniform(0.9, 1.1, n), 2)
am = np.round(np.pi * (rm ** 2) * np.random.uniform(0.9, 1.1, n), 1)
sm = np.round(np.random.normal(0.096, 0.014, n).clip(0.05, 0.16), 4)
cm = np.round(np.random.normal(0.104, 0.052, n).clip(0.019, 0.345), 4)
conc = np.round(np.random.normal(0.088, 0.079, n).clip(0.0, 0.426), 4)
cp = np.round(np.random.normal(0.048, 0.038, n).clip(0.0, 0.201), 4)
sym = np.round(np.random.normal(0.181, 0.027, n).clip(0.106, 0.304), 4)
fd = np.round(np.random.normal(0.062, 0.007, n).clip(0.049, 0.097), 4)
score = 0.4*rm + 0.08*tm + 15.0*conc + 20.0*cp - 8.5
prob = 1 / (1 + np.exp(-score))
diagnosis = (np.random.rand(n) < prob).astype(int)
df_bc = pd.DataFrame({
    'radius_mean': rm, 'texture_mean': tm, 'perimeter_mean': pm, 'area_mean': am,
    'smoothness_mean': sm, 'compactness_mean': cm, 'concavity_mean': conc,
    'concave_points_mean': cp, 'symmetry_mean': sym, 'fractal_dimension_mean': fd,
    'diagnosis': diagnosis
})
df_bc.to_csv('datasets/breast_cancer.csv', index=False)
print('Generated breast_cancer.csv:', len(df_bc))

# 7. Hypertension (500 samples)
n = 500
age = np.random.normal(52, 14, n).clip(20, 85).astype(int)
sex = np.random.choice([0, 1], n, p=[0.45, 0.55])
cp = np.random.choice([0, 1, 2, 3], n, p=[0.4, 0.2, 0.25, 0.15])
trestbps = np.random.normal(135, 18, n).clip(90, 200).astype(int)
chol = np.random.normal(230, 45, n).clip(120, 450).astype(int)
fbs = np.random.choice([0, 1], n, p=[0.8, 0.2])
restecg = np.random.choice([0, 1, 2], n, p=[0.5, 0.48, 0.02])
thalach = np.random.normal(145, 20, n).clip(75, 195).astype(int)
exang = np.random.choice([0, 1], n, p=[0.65, 0.35])
oldpeak = np.round(np.random.exponential(1.1, n).clip(0.0, 5.0), 1)
slope = np.random.choice([0, 1, 2], n, p=[0.1, 0.45, 0.45])
ca = np.random.choice([0, 1, 2, 3], n, p=[0.6, 0.2, 0.15, 0.05])
thal = np.random.choice([1, 2, 3], n, p=[0.05, 0.55, 0.4])
score = 0.05*trestbps + 0.015*age + 0.005*chol - 8.0
prob = 1 / (1 + np.exp(-score))
target = (np.random.rand(n) < prob).astype(int)
df_hyp = pd.DataFrame({
    'age': age, 'sex': sex, 'cp': cp, 'trestbps': trestbps,
    'chol': chol, 'fbs': fbs, 'restecg': restecg, 'thalach': thalach,
    'exang': exang, 'oldpeak': oldpeak, 'slope': slope, 'ca': ca,
    'thal': thal, 'target': target
})
df_hyp.to_csv('datasets/hypertension.csv', index=False)
print('Generated hypertension.csv:', len(df_hyp))

# 8. Stroke (1000 samples)
n = 1000
gender = np.random.choice([0, 1], n, p=[0.58, 0.42])
age = np.random.normal(48.5, 21.0, n).clip(10, 82).astype(int)
htn = (np.random.rand(n) < (0.05 + 0.003*age)).astype(int)
hd = (np.random.rand(n) < (0.02 + 0.002*age)).astype(int)
ever_married = (age > 24).astype(int)
work_type = np.random.choice([0, 1, 2, 3, 4], n, p=[0.55, 0.16, 0.14, 0.13, 0.02])
residence_type = np.random.choice([0, 1], n, p=[0.51, 0.49])
agl = np.round(np.random.normal(106, 45, n).clip(55, 271), 2)
bmi = np.round(np.random.normal(28.8, 7.8, n).clip(10.3, 97.6), 1)
smoking_status = np.random.choice([0, 1, 2, 3], n, p=[0.37, 0.17, 0.15, 0.31])
score = 0.05*age + 1.2*htn + 1.1*hd + 0.01*agl + 0.02*bmi - 6.2
prob = 1 / (1 + np.exp(-score))
stroke = (np.random.rand(n) < prob).astype(int)
df_stroke = pd.DataFrame({
    'gender': gender, 'age': age, 'hypertension': htn, 'heart_disease': hd,
    'ever_married': ever_married, 'work_type': work_type,
    'residence_type': residence_type, 'avg_glucose_level': agl, 'bmi': bmi,
    'smoking_status': smoking_status, 'stroke': stroke
})
df_stroke.to_csv('datasets/stroke.csv', index=False)
print('Generated stroke.csv:', len(df_stroke))
print('ALL 8 DATASETS GENERATED SUCCESSFULLY!')
