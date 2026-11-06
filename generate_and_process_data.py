import os
import re
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import StandardScaler

out_dir = r"c:\Users\Altorazer\Documents\Отчеты\ИТМО\Культура ИИ\Итоговый_проект"
os.makedirs(out_dir, exist_ok=True)

# Set seed for exact reproducibility
np.random.seed(42)

n_samples = 2500

industries = ["IT & SaaS", "Финансы и Банкинг", "Ритейл & E-commerce", "Производство", "Логистика & Транспорт", "Медицина & Фарма"]
industry_probs = [0.32, 0.20, 0.18, 0.14, 0.10, 0.06]

company_sizes = ["1-10", "11-50", "51-200", "201-1000", "1000+"]
size_probs = [0.25, 0.30, 0.25, 0.14, 0.06]

urgency_levels = ["Низкая (планирование)", "Средняя (1-3 месяца)", "Высокая (срочно в этот месяц)"]
urgency_probs = [0.35, 0.45, 0.20]

contact_roles = ["CEO / Генеральный директор", "CTO / IT-директор", "CMO / Директор по маркетингу", "Руководитель отдела продаж", "Менеджер проекта", "Ассистент / Секретарь"]
role_probs = [0.22, 0.25, 0.18, 0.20, 0.10, 0.05]

# Generate raw data
lead_ids = [f"LEAD-2026-{10000 + i}" for i in range(n_samples)]
company_names = [f"Компания_{np.random.choice(['Альфа', 'Бета', 'Гамма', 'Вектор', 'Сфера', 'Техно', 'Орион', 'Прогресс', 'Квазар', 'Синергия'])}_{100 + (i % 800)}" for i in range(n_samples)]
sampled_industries = np.random.choice(industries, size=n_samples, p=industry_probs)
sampled_sizes = np.random.choice(company_sizes, size=n_samples, p=size_probs)
sampled_urgencies = np.random.choice(urgency_levels, size=n_samples, p=urgency_probs)
sampled_roles = np.random.choice(contact_roles, size=n_samples, p=role_probs)

# Budgets: log-normal distribution with extreme right skew ($500 to $1,500,000)
raw_budgets = np.exp(np.random.normal(loc=9.2, scale=1.3, size=n_samples))
raw_budgets = np.round(raw_budgets, -2) # round to hundreds

# Text inquiries
templates = [
    "Требуется автоматизация обработки входящих заявок с интеграцией в CRM (Битрикс24). Планируем запуск в течение месяца. Бюджет согласован.",
    "Интересует внедрение AI-ассистента для отдела продаж. Хотим разгрузить 15 операторов и ускорить квалификацию лидов. Свяжитесь со мной.",
    "Ищем подрядчика для разработки кастомного AI-решения по скорингу B2B-клиентов. Необходим пилотный проект на 1000 обращений.",
    "Подскажите стоимость и сроки интеграции вашей системы квалификации лидов с нашей базой 1С и телефонией. Срочный проект.",
    "Здравствуйте! Хотим оптимизировать воронку продаж. Сейчас теряем до 30% лидов из-за медленного ответа операторов в нерабочее время.",
    "Нужен AI-агент, способный отвечать на типовые вопросы клиентов и собирать первичные требования перед передачей старшему менеджеру.",
    "Запрос коммерческого предложения на лицензии и внедрение для enterprise-клиента. Более 500 сотрудников, сложный контур безопасности.",
    "Добрый день! Хотим протестировать возможности AI в нашем контакт-центре. Пришлите, пожалуйста, презентацию и расчет окупаемости."
]

inquiry_texts = []
for i in range(n_samples):
    base_t = np.random.choice(templates)
    # Add noise / variations
    if np.random.rand() < 0.15:
        base_t = f"<p><b>СРОЧНО:</b> {base_t} Контактный тел: +7 (999) {np.random.randint(100, 999)}-{np.random.randint(10, 99)}-{np.random.randint(10, 99)}</p>"
    elif np.random.rand() < 0.10:
        base_t = base_t.lower() + "   "
    inquiry_texts.append(base_t)

# Inject real-world data flaws:
# 1. Missing values in budget (12%)
budget_with_nans = raw_budgets.copy()
nan_budget_idx = np.random.choice(n_samples, size=int(n_samples * 0.12), replace=False)
budget_with_nans[nan_budget_idx] = np.nan

# 2. Missing values in industry (5%)
industry_with_nans = sampled_industries.copy()
nan_ind_idx = np.random.choice(n_samples, size=int(n_samples * 0.05), replace=False)
industry_with_nans[nan_ind_idx] = None

# 3. Create DataFrame
df_raw = pd.DataFrame({
    "lead_id": lead_ids,
    "company_name": company_names,
    "industry": industry_with_nans,
    "company_size": sampled_sizes,
    "contact_role": sampled_roles,
    "urgency": sampled_urgencies,
    "budget_rub": budget_with_nans,
    "inquiry_text": inquiry_texts
})

# Add duplicates (30 duplicate rows to simulate repeated submissions)
dup_rows = df_raw.iloc[:30].copy()
df_raw = pd.concat([df_raw, dup_rows], ignore_index=True)

raw_path = os.path.join(out_dir, "raw_leads_dataset.csv")
df_raw.to_csv(raw_path, index=False, encoding="utf-8")
print(f"Raw dataset saved: {df_raw.shape[0]} rows, {df_raw.shape[1]} cols")

# --- DATA CLEANING & PREPARATION ---
df = df_raw.copy()

# Step 1: Deduplication
initial_count = len(df)
df = df.drop_duplicates(subset=["lead_id"])
dups_removed = initial_count - len(df)
print(f"Duplicates removed: {dups_removed}")

# Step 2: Missing values handling
# Industry: fill missing with 'Не указано'
df["industry"] = df["industry"].fillna("Не указано")

# Budget: impute missing with median by company_size group
median_by_size = df.groupby("company_size")["budget_rub"].transform("median")
df["budget_imputed_flag"] = df["budget_rub"].isna().astype(int)
df["budget_rub"] = df["budget_rub"].fillna(median_by_size).fillna(df["budget_rub"].median())

# Step 3: Text cleaning and feature extraction
def clean_text(text):
    if not isinstance(text, str):
        return ""
    # strip HTML tags
    clean = re.sub(r"<[^>]+>", " ", text)
    # normalize whitespace
    clean = re.sub(r"\s+", " ", clean).strip()
    return clean

df["clean_inquiry"] = df["inquiry_text"].apply(clean_text)
df["inquiry_length"] = df["clean_inquiry"].apply(len)
df["has_phone"] = df["clean_inquiry"].str.contains(r"\+7|\b8\s?\(?\d{3}\)?", regex=True).astype(int)

# Step 4: Rule-based Initial Lead Scoring (for ML / Routing)
# 0 to 100 score based on size, role, urgency, budget
size_score_map = {"1-10": 10, "11-50": 30, "51-200": 60, "201-1000": 85, "1000+": 100}
urgency_score_map = {"Низкая (планирование)": 15, "Средняя (1-3 месяца)": 50, "Высокая (срочно в этот месяц)": 90}
role_score_map = {
    "CEO / Генеральный директор": 95,
    "CTO / IT-директор": 90,
    "CMO / Директор по маркетингу": 85,
    "Руководитель отдела продаж": 80,
    "Менеджер проекта": 45,
    "Ассистент / Секретарь": 20
}

df["size_score"] = df["company_size"].map(size_score_map)
df["urgency_score"] = df["urgency"].map(urgency_score_map)
df["role_score"] = df["contact_role"].map(role_score_map)

# Budget score: percentile rank
df["budget_score"] = pd.qcut(df["budget_rub"], q=10, labels=False, duplicates="drop") * 10

# Blended Lead Score (0 - 100)
df["lead_score"] = (
    0.35 * df["budget_score"] +
    0.25 * df["role_score"] +
    0.25 * df["size_score"] +
    0.15 * df["urgency_score"]
).round(1)

# Step 5: Feature transformations
# Log transformation for skewed budget and inquiry_length
df["log_budget"] = np.log1p(df["budget_rub"])
df["log_inquiry_length"] = np.log1p(df["inquiry_length"])

# Scaling
scaler = StandardScaler()
df[["scaled_log_budget", "scaled_lead_score"]] = scaler.fit_transform(df[["log_budget", "lead_score"]])

# Lead Category for Routing: Standard, Priority, Enterprise VIP
def categorize_lead(row):
    if row["lead_score"] >= 75 and row["company_size"] in ["201-1000", "1000+"]:
        return "Enterprise VIP (Эскалация)"
    elif row["lead_score"] >= 50:
        return "Priority (Старший менеджер)"
    else:
        return "Standard (Авто-квалификация)"

df["routing_category"] = df.apply(categorize_lead, axis=1)

processed_path = os.path.join(out_dir, "processed_leads_dataset.csv")
df.to_csv(processed_path, index=False, encoding="utf-8")
print(f"Clean processed dataset saved: {df.shape[0]} rows, {df.shape[1]} cols")

# --- PLOTTING PUBLICATION-QUALITY CHARTS ---
plt.rcParams["font.sans-serif"] = ["Arial", "DejaVu Sans"]
plt.rcParams["font.family"] = "sans-serif"
sns.set_theme(style="whitegrid")

# Chart 1: Distributions Before vs After Log Transform
fig, axes = plt.subplots(1, 2, figsize=(13, 5))

# Before (Raw Budget)
sns.histplot(df["budget_rub"] / 1000, bins=35, kde=True, ax=axes[0], color="#C44E52")
axes[0].set_title(f"Исходное распределение бюджета\n(Асимметрия: skew = {df['budget_rub'].skew():.2f})", fontsize=12, fontweight="bold")
axes[0].set_xlabel("Бюджет заявки (тыс. руб.)", fontsize=11)
axes[0].set_ylabel("Плотность / Частота", fontsize=11)

# After (Log-transformed Budget)
sns.histplot(df["log_budget"], bins=35, kde=True, ax=axes[1], color="#4C72B0")
axes[1].set_title(f"Распределение после log1p-трансформации\n(Асимметрия: skew = {df['log_budget'].skew():.2f})", fontsize=12, fontweight="bold")
axes[1].set_xlabel("Логарифм бюджета: ln(1 + budget)", fontsize=11)
axes[1].set_ylabel("Плотность / Частота", fontsize=11)

plt.tight_layout()
dist_chart_path = os.path.join(out_dir, "distributions_before_after.png")
plt.savefig(dist_chart_path, dpi=200)
plt.close()
print("Saved:", dist_chart_path)

# Chart 2: Category Breakdown and Routing Distribution
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Industries breakdown
ind_order = df["industry"].value_counts().index
sns.countplot(data=df, y="industry", order=ind_order, palette="Blues_r", ax=axes[0])
axes[0].set_title("Распределение входящих лидов по отраслям", fontsize=12, fontweight="bold")
axes[0].set_xlabel("Количество обращений", fontsize=11)
axes[0].set_ylabel("Отрасль бизнеса", fontsize=11)

# Routing categories breakdown
cat_counts = df["routing_category"].value_counts()
colors = ["#55A868", "#4C72B0", "#C44E52"]
axes[1].pie(cat_counts, labels=cat_counts.index, autopct="%1.1f%%", startangle=140, colors=colors, textprops={"fontsize": 10})
axes[1].set_title("Структура маршрутизации обращений (Lead Routing)", fontsize=12, fontweight="bold")

plt.tight_layout()
cat_chart_path = os.path.join(out_dir, "categories_breakdown.png")
plt.savefig(cat_chart_path, dpi=200)
plt.close()
print("Saved:", cat_chart_path)

# Print Summary Stats
print("\n--- STATISTICAL SUMMARY ---")
print(f"Total raw leads: {initial_count}")
print(f"Total unique processed leads: {len(df)}")
print(f"Raw Budget: Mean={df['budget_rub'].mean():.1f}, Median={df['budget_rub'].median():.1f}, Skew={df['budget_rub'].skew():.2f}")
print(f"Log Budget: Mean={df['log_budget'].mean():.2f}, Median={df['log_budget'].median():.2f}, Skew={df['log_budget'].skew():.2f}")
print(f"Lead Score: Mean={df['lead_score'].mean():.1f}, Median={df['lead_score'].median():.1f}")
print(f"Routing counts:\n{df['routing_category'].value_counts()}")
