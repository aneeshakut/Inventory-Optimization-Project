# ============================================================
# Step 3: Inventory Optimization Modeling
# ============================================================

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# ------------------------------------------------------------
# 1️⃣ PATH SETUP
# ------------------------------------------------------------
BASE_DIR = os.path.abspath(r"C:\\Users\\hp\\Desktop\\Inventory-Optimization-Project")
EDA_RESULTS = os.path.join(BASE_DIR, "dashboards/eda_results/plots")   # only for visual review
PROCESSED_PATH = os.path.join(BASE_DIR, "data/processed")
OUTPUT_DIR = os.path.join(BASE_DIR, "dashboards/optimization_results/plots")
os.makedirs(OUTPUT_DIR, exist_ok=True)

print(f"📂 Saving optimization plots to: {OUTPUT_DIR}")

# ------------------------------------------------------------
# 2️⃣ LOAD DATA
# ------------------------------------------------------------
# We re-use cleaned processed data from earlier steps
products = pd.read_csv(os.path.join(PROCESSED_PATH, "products.csv"))
suppliers = pd.read_csv(os.path.join(PROCESSED_PATH, "suppliers.csv"))
warehouses = pd.read_csv(os.path.join(PROCESSED_PATH, "warehouses.csv"))
sales = pd.read_csv(os.path.join(PROCESSED_PATH, "sales.csv"))
inventory = pd.read_csv(os.path.join(PROCESSED_PATH, "inventory_tx.csv"))
purchase_orders = pd.read_csv(os.path.join(PROCESSED_PATH, "purchase_orders.csv"))

# ------------------------------------------------------------
# 3️⃣ PREPARE BASE DATAFRAME
# ------------------------------------------------------------
# Aggregate sales demand stats per SKU
sales['Sale_Date'] = pd.to_datetime(sales['Sale_Date'])
sku_demand = (
    sales.groupby('SKU')['Quantity_Sold']
    .agg(['mean', 'std'])
    .rename(columns={'mean': 'Avg_Weekly_Demand', 'std': 'Std_Weekly_Demand'})
    .reset_index()
)

# Average supplier lead time per SKU (join via Supplier_ID if available)
purchase_orders['Order_Date'] = pd.to_datetime(purchase_orders['Order_Date'])
purchase_orders['Delivery_Date'] = pd.to_datetime(purchase_orders['Delivery_Date'])
purchase_orders['Lead_Time_Days'] = (purchase_orders['Delivery_Date'] - purchase_orders['Order_Date']).dt.days
lead_times = (
    purchase_orders.groupby('Supplier_ID')['Lead_Time_Days']
    .mean()
    .reset_index()
    .rename(columns={'Lead_Time_Days': 'Avg_Lead_Time'})
)

# Merge supplier lead times with product SKUs
model_df = pd.merge(products, lead_times, on='Supplier_ID', how='left')
model_df = pd.merge(model_df, sku_demand, on='SKU', how='left')

# Fill missing with safe defaults
model_df.fillna({'Avg_Weekly_Demand': 0, 'Std_Weekly_Demand': 0, 'Avg_Lead_Time': 7}, inplace=True)

# ------------------------------------------------------------
# 4️⃣ SAFETY STOCK & ROP CALCULATION
# ------------------------------------------------------------
service_level = 0.95
Z = 1.65   # z-score for 95% service level

# Convert lead time to weeks (approx)
model_df['Lead_Time_Weeks'] = model_df['Avg_Lead_Time'] / 7

# Safety stock = Z * std_demand * sqrt(lead_time_weeks)
model_df['Safety_Stock'] = Z * model_df['Std_Weekly_Demand'] * np.sqrt(model_df['Lead_Time_Weeks'])

# ROP = demand during lead time + safety stock
model_df['ROP'] = (model_df['Avg_Weekly_Demand'] * model_df['Lead_Time_Weeks']) + model_df['Safety_Stock']

# ------------------------------------------------------------
# 5️⃣ EOQ CALCULATION (ECONOMIC ORDER QUANTITY)
# ------------------------------------------------------------
# Assume ordering & holding cost constants for illustration
ordering_cost = 50
holding_cost = 2

# Demand D per year (weekly * 52)
model_df['Annual_Demand'] = model_df['Avg_Weekly_Demand'] * 52

# EOQ = sqrt((2 * D * S) / H)
model_df['EOQ'] = np.sqrt((2 * model_df['Annual_Demand'] * ordering_cost) / holding_cost)

# ------------------------------------------------------------
# 6️⃣ ABC CLASSIFICATION ADJUSTMENT (from products)
# ------------------------------------------------------------
# If ABC info is in another table, merge it here; else use a proxy
model_df['ABC_Category'] = pd.qcut(
    model_df['Annual_Demand'].rank(method='first'), q=3, labels=['C', 'B', 'A']
)

# Adjust safety stock by category priority
adj = {'A': 1.0, 'B': 0.8, 'C': 0.6}
model_df['Safety_Stock_Adjusted'] = model_df.apply(
    lambda x: x['Safety_Stock'] * adj.get(x['ABC_Category'], 1.0), axis=1
)

# ------------------------------------------------------------
# 7️⃣ RECOMMENDED ORDER QUANTITY
# ------------------------------------------------------------
# Current inventory per SKU (from inventory_tx)
current_inv = inventory.groupby('SKU')['Quantity'].sum().reset_index().rename(columns={'Quantity': 'Current_Stock'})
model_df = pd.merge(model_df, current_inv, on='SKU', how='left').fillna({'Current_Stock': 0})

# Recommended order = max(ROP - Current, 0)
model_df['Recommended_Order_Qty'] = np.maximum(model_df['ROP'] - model_df['Current_Stock'], 0)

# ------------------------------------------------------------
# 8️⃣ VISUALIZATIONS
# ------------------------------------------------------------

# --- Safety Stock by SKU ---
plt.figure(figsize=(10,5))
sns.barplot(data=model_df.sort_values('Safety_Stock', ascending=False).head(30),
            x='SKU', y='Safety_Stock', hue='ABC_Category', dodge=False)
plt.title('Top 30 SKUs by Safety Stock')
plt.xlabel('SKU')
plt.ylabel('Safety Stock Units')
plt.xticks(rotation=90)
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, "top30_safety_stock.png"))
plt.close()

# --- ROP vs Current Inventory ---
plt.figure(figsize=(8,6))
sns.scatterplot(data=model_df, x='ROP', y='Current_Stock', hue='ABC_Category', alpha=0.7)
plt.title("Reorder Point vs Current Inventory")
plt.xlabel("Reorder Point (ROP)")
plt.ylabel("Current Stock")
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, "rop_vs_current_stock.png"))
plt.close()

# --- EOQ Distribution by Category (Improved) ---
plt.figure(figsize=(10,5))
sns.kdeplot(data=model_df, x='EOQ', hue='ABC_Category', fill=True, common_norm=False, alpha=0.4)
plt.title("EOQ Distribution by ABC Category")
plt.xlabel("Economic Order Quantity (EOQ)")
plt.ylabel("Density")
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, "eoq_distribution_by_category.png"))
plt.close()

# --- Top 30 SKUs by EOQ (Improved) ---
top_eoq = model_df.sort_values('EOQ', ascending=False).head(30)
plt.figure(figsize=(12,6))
sns.barplot(data=top_eoq, x='SKU', y='EOQ', hue='ABC_Category', dodge=False)
plt.title("Top 30 SKUs by EOQ")
plt.xlabel("SKU")
plt.ylabel("EOQ")
plt.xticks(rotation=90)
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, "top30_eoq_by_sku.png"))
plt.close()

# --- Recommended Order Quantities ---
plt.figure(figsize=(10,5))
sns.histplot(model_df['Recommended_Order_Qty'], bins=30, color='teal', kde=True)
plt.title('Distribution of Recommended Order Quantities')
plt.xlabel('Recommended Order Quantity')
plt.ylabel('Frequency')
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, "recommended_order_qty_distribution.png"))
plt.close()

print("✅ Optimization plots successfully saved in:", OUTPUT_DIR)
