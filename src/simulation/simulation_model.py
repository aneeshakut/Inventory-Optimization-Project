# ============================================================
# STEP 4: SIMULATION & WHAT-IF ANALYSIS (robust, no CSV dependency)
# - Rebuilds model inputs from processed data (sales, products, suppliers, inventory, purchase_orders)
# - Runs three scenarios (demand surge, lead-time delay, cost variation)
# - Saves only PNG visual outputs
# ============================================================

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from tqdm import tqdm

# -------------------------
# 1) PATH SETUP
# -------------------------
BASE_DIR = os.path.abspath(r"C:\Users\hp\Desktop\Inventory-Optimization-Project")
PROCESSED_PATH = os.path.join(BASE_DIR, "data", "processed")
OUTPUT_PATH = os.path.join(BASE_DIR, "dashboards", "simulation_results")
os.makedirs(OUTPUT_PATH, exist_ok=True)

print("Simulation outputs will be saved to:", OUTPUT_PATH)

# -------------------------
# 2) LOAD PROCESSED DATA
# -------------------------
# These should exist from Step 1 processed data
products = pd.read_csv(os.path.join(PROCESSED_PATH, "products.csv"))
suppliers = pd.read_csv(os.path.join(PROCESSED_PATH, "suppliers.csv"))
sales = pd.read_csv(os.path.join(PROCESSED_PATH, "sales.csv"))
inventory = pd.read_csv(os.path.join(PROCESSED_PATH, "inventory_tx.csv"))
purchase_orders = pd.read_csv(os.path.join(PROCESSED_PATH, "purchase_orders.csv"))

# -------------------------
# 3) PREPARE MODEL INPUTS
# -------------------------
# Convert date columns if present
if "Sale_Date" in sales.columns:
    sales['Sale_Date'] = pd.to_datetime(sales['Sale_Date'])

if "Order_Date" in purchase_orders.columns:
    purchase_orders['Order_Date'] = pd.to_datetime(purchase_orders['Order_Date'])
if "Delivery_Date" in purchase_orders.columns:
    purchase_orders['Delivery_Date'] = pd.to_datetime(purchase_orders['Delivery_Date'])

# 3.1 Weekly demand stats per SKU
sales['Week'] = sales['Sale_Date'].dt.to_period('W') if 'Sale_Date' in sales.columns else None
if sales['Week'].isnull().all():
    # fallback: aggregate by day if week can't be computed
    sku_weekly = sales.groupby('SKU')['Quantity_Sold'].sum().reset_index().rename(columns={'Quantity_Sold': 'Quantity'})
    sku_weekly['Week'] = 0
    sku_weekly = sku_weekly.groupby(['SKU','Week'])['Quantity'].sum().reset_index()
else:
    sku_weekly = sales.groupby(['SKU', 'Week'])['Quantity_Sold'].sum().reset_index()

sku_demand_stats = sku_weekly.groupby('SKU')['Quantity_Sold'].agg(['mean', 'std']).reset_index().rename(
    columns={'mean': 'Avg_Weekly_Demand', 'std': 'Std_Weekly_Demand'}
)

# 3.2 Supplier lead time: prefer purchase_orders (actual), else suppliers table
if {'Order_Date', 'Delivery_Date'}.issubset(purchase_orders.columns):
    purchase_orders['Lead_Time_Days'] = (purchase_orders['Delivery_Date'] - purchase_orders['Order_Date']).dt.days
    supplier_lead = purchase_orders.groupby('Supplier_ID')['Lead_Time_Days'].mean().reset_index().rename(
        columns={'Lead_Time_Days': 'Avg_Lead_Time_Days'}
    )
else:
    # fallback to suppliers table column names
    if 'Lead_Time_Days_Avg' in suppliers.columns:
        supplier_lead = suppliers[['Supplier_ID', 'Lead_Time_Days_Avg']].rename(
            columns={'Lead_Time_Days_Avg': 'Avg_Lead_Time_Days'}
        )
    else:
        supplier_lead = suppliers[['Supplier_ID']].copy()
        supplier_lead['Avg_Lead_Time_Days'] = 14  # default

# 3.3 Merge product-level info with demand and supplier lead times
# Ensure products has Supplier_ID and cost/order/holding fields (use defaults if missing)
if 'Ordering_Cost' not in products.columns:
    products['Ordering_Cost'] = 50
if 'Holding_Cost_Per_Unit_Per_Year' not in products.columns:
    # convert to weekly holding cost (per unit per week) later if needed
    products['Holding_Cost_Per_Unit_Per_Year'] = 2 * 52  # set a reasonable default annual cost -> weekly will be 2

model_df = products[['SKU', 'Supplier_ID', 'Unit_Cost', 'Ordering_Cost', 'Holding_Cost_Per_Unit_Per_Year']].copy()
model_df = model_df.merge(sku_demand_stats, on='SKU', how='left')
model_df = model_df.merge(supplier_lead, on='Supplier_ID', how='left')

# Fill NA defaults
model_df['Avg_Weekly_Demand'] = model_df['Avg_Weekly_Demand'].fillna(0)
model_df['Std_Weekly_Demand'] = model_df['Std_Weekly_Demand'].fillna(0)
model_df['Avg_Lead_Time_Days'] = model_df['Avg_Lead_Time_Days'].fillna(14)  # default two weeks

# Convert lead time to weeks
model_df['Avg_Lead_Time_Weeks'] = model_df['Avg_Lead_Time_Days'] / 7.0

# Current inventory per SKU (sum of inventory transactions)
if 'Quantity' in inventory.columns:
    current_inv = inventory.groupby('SKU')['Quantity'].sum().reset_index().rename(columns={'Quantity': 'Current_Stock'})
else:
    current_inv = pd.DataFrame({'SKU': model_df['SKU'], 'Current_Stock': 0})

model_df = model_df.merge(current_inv, on='SKU', how='left')
model_df['Current_Stock'] = model_df['Current_Stock'].fillna(0)

# -------------------------
# 4) CALCULATE EOQ, SAFETY STOCK, ROP
# -------------------------
# EOQ: use ordering cost S and holding cost H (annual)
# If Holding_Cost_Per_Unit_Per_Year is present use it; else derive approx
model_df['Annual_Demand'] = model_df['Avg_Weekly_Demand'] * 52

# Set parameters and safe defaults
model_df['Ordering_Cost'] = model_df['Ordering_Cost'].fillna(50)
model_df['Holding_Cost_Per_Unit_Per_Year'] = model_df['Holding_Cost_Per_Unit_Per_Year'].fillna(2 * 52)

# EOQ formula (avoid zero division)
model_df['EOQ'] = np.sqrt((2 * model_df['Annual_Demand'] * model_df['Ordering_Cost']) / model_df['Holding_Cost_Per_Unit_Per_Year'])
model_df['EOQ'] = model_df['EOQ'].replace([np.inf, -np.inf], 0).fillna(0)

# Safety stock & ROP: choose service level
Z = 1.65  # ~95%
model_df['Demand_SD_LeadTime'] = model_df['Std_Weekly_Demand'] * np.sqrt(model_df['Avg_Lead_Time_Weeks'].replace(0, 1e-6))
model_df['Safety_Stock'] = Z * model_df['Demand_SD_LeadTime']
model_df['Demand_During_Lead'] = model_df['Avg_Weekly_Demand'] * model_df['Avg_Lead_Time_Weeks']
model_df['ROP'] = model_df['Demand_During_Lead'] + model_df['Safety_Stock']

# Add ABC proxy if not available (top terciles by annual demand)
model_df['ABC_Category'] = pd.qcut(model_df['Annual_Demand'].rank(method='first'), q=3, labels=['C','B','A'])

# -------------------------
# 5) HELPER FUNCTIONS FOR SIMULATION
# -------------------------
def simulate_demand_once(base_weekly, surge_factor):
    """Return a simulated weekly demand value (normal around base)."""
    if base_weekly == 0:
        return 0.0
    sd = max(base_weekly * 0.3, 1.0)  # baseline variability if std not reliable
    return max(0.0, np.random.normal(loc=base_weekly * (1 + surge_factor * np.random.uniform(-0.2, 1.0)), scale=sd))

def simulate_leadtime_once(base_days, delay_factor):
    """Return simulated lead time in days (base +/- noise)."""
    if np.isnan(base_days) or base_days <= 0:
        base_days = 14
    sd = max(base_days * 0.3, 1.0)
    return max(1.0, np.random.normal(loc=base_days * (1 + delay_factor * np.random.uniform(0.0, 1.0)), scale=sd))

def total_cost_for_sku(eoq, annual_demand, ordering_cost, holding_cost_annual):
    """Simple total annual cost: ordering + holding."""
    if eoq <= 0 or annual_demand <= 0:
        return np.nan
    orders_per_year = annual_demand / eoq
    return orders_per_year * ordering_cost + (holding_cost_annual * eoq / 2.0)

# -------------------------
# 6) SIMULATION SCENARIOS
# -------------------------
def simulate_demand_surge(df, surge_factor=0.3, runs=500):
    """Monte Carlo: random demand surges for A SKUs and compute stockout rate per run."""
    results = []
    df = df.copy()
    for _ in tqdm(range(runs), desc="Demand Surge sims"):
        # Simulate demand for each SKU
        df['Sim_Weekly_Demand'] = df['Avg_Weekly_Demand'].apply(lambda x: simulate_demand_once(x, surge_factor))
        # Simple rule: stockout if Sim_Weekly_Demand > (Current_Stock + EOQ) (very simplified)
        df['Stockout_Flag'] = np.where(df['Sim_Weekly_Demand'] > (df['Current_Stock'] + df['EOQ']), 1, 0)
        results.append(df['Stockout_Flag'].mean())
    # Plot distribution of stockout probabilities
    plt.figure(figsize=(8,4))
    sns.histplot(results, bins=30, kde=True, color='orange')
    plt.title("Stockout Probability Distribution (Demand Surge)")
    plt.xlabel("Stockout Probability")
    plt.ylabel("Frequency")
    plt.tight_layout()
    out = os.path.join(OUTPUT_PATH, "demand_surge_simulation.png")
    plt.savefig(out, dpi=150)
    plt.close()
    print("Saved:", out)

def simulate_leadtime_delay(df, delay_factor=0.3, runs=500):
    """Monte Carlo: random lead-time delays and measure average required safety stock."""
    avg_extra = []
    df = df.copy()
    for _ in tqdm(range(runs), desc="Lead Time Delay sims"):
        df['Sim_Lead_Days'] = df['Avg_Lead_Time_Days'].apply(lambda x: simulate_leadtime_once(x, delay_factor))
        df['Sim_Lead_Weeks'] = df['Sim_Lead_Days'] / 7.0
        df['New_Safety'] = Z * df['Std_Weekly_Demand'] * np.sqrt(df['Sim_Lead_Weeks'].replace(0,1e-6))
        avg_extra.append(df['New_Safety'].mean())
    plt.figure(figsize=(8,4))
    sns.histplot(avg_extra, bins=30, kde=True, color='steelblue')
    plt.title("Average Safety Stock Required under Lead Time Delays")
    plt.xlabel("Avg Safety Stock Units")
    plt.ylabel("Frequency")
    plt.tight_layout()
    out = os.path.join(OUTPUT_PATH, "lead_time_delay_simulation.png")
    plt.savefig(out, dpi=150)
    plt.close()
    print("Saved:", out)

def simulate_cost_variation(df, cost_factor=0.1, runs=500):
    """Monte Carlo: vary unit cost and compute average total annual cost."""
    avg_costs = []
    df = df.copy()
    for _ in tqdm(range(runs), desc="Cost Variation sims"):
        df['Sim_Unit_Cost'] = df['Unit_Cost'] * np.random.uniform(1-cost_factor, 1+cost_factor, size=len(df))
        df['Sim_Total_Cost'] = df.apply(lambda r: total_cost_for_sku(
            eoq=r['EOQ'],
            annual_demand=r['Annual_Demand'],
            ordering_cost=r['Ordering_Cost'],
            holding_cost_annual=r['Holding_Cost_Per_Unit_Per_Year']
        ), axis=1)
        avg_costs.append(df['Sim_Total_Cost'].mean())
    plt.figure(figsize=(8,4))
    sns.histplot(avg_costs, bins=30, kde=True, color='green')
    plt.title("Average Annual Total Cost under Unit Cost Variation")
    plt.xlabel("Average Annual Cost")
    plt.ylabel("Frequency")
    plt.tight_layout()
    out = os.path.join(OUTPUT_PATH, "cost_variation_simulation.png")
    plt.savefig(out, dpi=150)
    plt.close()
    print("Saved:", out)

# -------------------------
# 7) RUN SIMULATIONS
# -------------------------
if __name__ == "__main__":
    # Check model_df for required columns
    required_cols = ['SKU', 'Avg_Weekly_Demand', 'Std_Weekly_Demand', 'Avg_Lead_Time_Days',
                     'Avg_Lead_Time_Weeks', 'EOQ', 'Safety_Stock', 'ROP', 'Current_Stock', 'Unit_Cost',
                     'Ordering_Cost', 'Holding_Cost_Per_Unit_Per_Year', 'Annual_Demand']
    missing = [c for c in required_cols if c not in model_df.columns]
    if missing:
        print("Warning: some expected columns are missing and will be filled with defaults:", missing)
        # Attempt to add defaults
        for c in missing:
            if c == 'Unit_Cost':
                model_df[c] = products.get('Unit_Cost', 1).fillna(1)
            elif c == 'Ordering_Cost':
                model_df[c] = model_df.get('Ordering_Cost', 50)
            elif c == 'Holding_Cost_Per_Unit_Per_Year':
                model_df[c] = model_df.get('Holding_Cost_Per_Unit_Per_Year', 2*52)
            else:
                model_df[c] = 0

    # Run scenarios
    simulate_demand_surge(model_df, surge_factor=0.3, runs=300)
    simulate_leadtime_delay(model_df, delay_factor=0.3, runs=300)
    simulate_cost_variation(model_df, cost_factor=0.1, runs=300)

    print("✅ All simulations complete. Check PNGs in:", OUTPUT_PATH)
