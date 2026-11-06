import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

out_dir = r"c:\Users\Altorazer\Documents\Отчеты\ИТМО\Культура ИИ\Итоговый_проект"
os.makedirs(out_dir, exist_ok=True)

plt.rcParams["font.sans-serif"] = ["Arial", "DejaVu Sans"]
plt.rcParams["font.family"] = "sans-serif"

# 1. PARAMETERS & FORMULAS
input_tokens_per_call = 2900
output_tokens_per_call = 440

p_in_per_million = 0.15   # $0.15 / 1M tokens
p_out_per_million = 0.60  # $0.60 / 1M tokens

usd_rub = 95.0

# Formula strictly from ITMO assignment:
# Стоимость вызова = ((входные токены * цена входа за 1M) + (выходные токены * цена выхода за 1M)) / 1 000 000
cost_call_usd = ((input_tokens_per_call * p_in_per_million) + (output_tokens_per_call * p_out_per_million)) / 1000000
cost_call_rub = cost_call_usd * usd_rub

# Additional micro-services
c_rag_usd = 0.000300
c_guard_usd = 0.000200
total_unit_cost_usd = cost_call_usd + c_rag_usd + c_guard_usd
total_unit_cost_rub = total_unit_cost_usd * usd_rub

# Manual processing baseline
sdr_salary_net = 80000
tax_overhead = 0.302
workplace_overhead = 10000
sdr_total_monthly = sdr_salary_net * (1 + tax_overhead) + workplace_overhead
sdr_monthly_leads = 1320 # 60 leads/day * 22 days
manual_cost_per_lead_rub = sdr_total_monthly / sdr_monthly_leads
manual_cost_per_lead_usd = manual_cost_per_lead_rub / usd_rub

delta_savings_per_lead_rub = manual_cost_per_lead_rub - total_unit_cost_rub

# Fixed & Capital Costs
capex_rub = 650000 # Development, prompt engineering, integration
opex_fixed_monthly_rub = 100000 # Server VPS, PostgreSQL, Redis, maintenance

# Break-Even Points
bep_monthly_leads = opex_fixed_monthly_rub / delta_savings_per_lead_rub
bep_capex_leads = capex_rub / delta_savings_per_lead_rub

# Monthly volume
monthly_leads = 30000 # 1000 leads / day
monthly_savings_rub = (monthly_leads * delta_savings_per_lead_rub) - opex_fixed_monthly_rub
annual_net_benefit_rub = (monthly_savings_rub * 12) - capex_rub
roi_first_year = (annual_net_benefit_rub / capex_rub) * 100

print(f"Token Call Cost (USD): ${cost_call_usd:.6f} ({cost_call_rub:.4f} RUB)")
print(f"Total AI Unit Cost (RUB): {total_unit_cost_rub:.4f} RUB")
print(f"Manual Lead Cost (RUB): {manual_cost_per_lead_rub:.2f} RUB")
print(f"Savings per Lead (RUB): {delta_savings_per_lead_rub:.2f} RUB")
print(f"BEP Operating Monthly: {bep_monthly_leads:.0f} leads")
print(f"BEP CapEx Total: {bep_capex_leads:.0f} leads (~{bep_capex_leads/1000:.1f} days at 1000 leads/day)")
print(f"Net Annual Benefit: {annual_net_benefit_rub:,.0f} RUB, ROI: {roi_first_year:.1f}%")

# --- PLOT 1: BREAK-EVEN ANALYSIS ---
leads_range = np.linspace(0, 15000, 300)
manual_total_cost = (leads_range * manual_cost_per_lead_rub) / 1000 # in thousands RUB
ai_total_cost = (capex_rub + (opex_fixed_monthly_rub / 2) + leads_range * total_unit_cost_rub) / 1000

plt.figure(figsize=(9, 5.2))
plt.plot(leads_range, manual_total_cost, label="Ручная обработка (23 менеджера SDR)", color="#C44E52", linewidth=2.5)
plt.plot(leads_range, ai_total_cost, label="AI-система (CapEx + OpEx + API)", color="#4C72B0", linewidth=2.5)
plt.axvline(bep_capex_leads, color="#55A868", linestyle="--", linewidth=1.8, label=f"Точка безубыточности: {int(bep_capex_leads)} лидов")
plt.scatter([bep_capex_leads], [(bep_capex_leads * manual_cost_per_lead_rub) / 1000], color="#55A868", s=130, zorder=5)

plt.annotate(
    f"BEP = {int(bep_capex_leads)} обращений\n(~{bep_capex_leads/1000:.1f} дней потока)",
    xy=(bep_capex_leads, (bep_capex_leads * manual_cost_per_lead_rub) / 1000),
    xytext=(bep_capex_leads + 1200, (bep_capex_leads * manual_cost_per_lead_rub) / 1000 - 150),
    arrowprops=dict(facecolor="black", shrink=0.08, width=1.5, headwidth=7),
    fontsize=11, fontweight="bold", backgroundcolor="white"
)

plt.title("Анализ точки окупаемости AI-решения (Break-Even Analysis)", fontsize=13, fontweight="bold", pad=12)
plt.xlabel("Количество обработанных входящих обращений (лидов)", fontsize=11)
plt.ylabel("Совокупные затраты (тыс. руб.)", fontsize=11)
plt.grid(True, linestyle="--", alpha=0.6)
plt.legend(loc="upper left", fontsize=10)
plt.tight_layout()
bep_chart_path = os.path.join(out_dir, "economic_break_even.png")
plt.savefig(bep_chart_path, dpi=200)
plt.close()
print("Saved:", bep_chart_path)

# --- PLOT 2: COST PER LEAD COMPARISON ---
plt.figure(figsize=(8, 4.5))
categories = ["Ручной разбор (SDR)", "AI-агент (Полный стек)"]
costs = [manual_cost_per_lead_rub, total_unit_cost_rub]
colors = ["#C44E52", "#55A868"]

bars = plt.bar(categories, costs, color=colors, width=0.45)
plt.title("Сравнение себестоимости обработки одного обращения", fontsize=12, fontweight="bold", pad=12)
plt.ylabel("Стоимость обработки 1 лида (руб.)", fontsize=11)
plt.yscale("log") # log scale because of huge difference

for bar in bars:
    yval = bar.get_height()
    plt.text(bar.get_x() + bar.get_width()/2.0, yval * 1.3, f"{yval:.2f} руб.", ha="center", va="bottom", fontsize=11, fontweight="bold")

plt.grid(True, linestyle="--", alpha=0.5, axis="y")
plt.tight_layout()
cost_comp_path = os.path.join(out_dir, "cost_comparison_chart.png")
plt.savefig(cost_comp_path, dpi=200)
plt.close()
print("Saved:", cost_comp_path)
