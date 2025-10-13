# ============================================================
# Exploratory Data Analysis (EDA) for Inventory Optimization
# ============================================================

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# ------------------------------------------------------------
# 1️⃣  PATH SETUP
# ------------------------------------------------------------
BASE_DIR = os.path.abspath(r"C:\Users\hp\Desktop\Inventory-Optimization-Project")
PROCESSED_PATH = os.path.join(BASE_DIR, "data/processed")
OUTPUT_DIR = os.path.join(BASE_DIR, "dashboards/eda_results")
PLOT_DIR = OUTPUT_DIR
os.makedirs(PLOT_DIR, exist_ok=True)

print(f"📂 Using data from: {PROCESSED_PATH}")
print(f"📂 Plots will be saved to: {PLOT_DIR}")

# ------------------------------------------------------------
# 2️⃣  LOAD DATA
# ------------------------------------------------------------
products = pd.read_csv(os.path.join(PROCESSED_PATH, "products.csv"))
suppliers = pd.read_csv(os.path.join(PROCESSED_PATH, "suppliers.csv"))
warehouses = pd.read_csv(os.path.join(PROCESSED_PATH, "warehouses.csv"))
sales = pd.read_csv(os.path.join(PROCESSED_PATH, "sales.csv"))
inventory = pd.read_csv(os.path.join(PROCESSED_PATH, "inventory_tx.csv"))
purchase_orders = pd.read_csv(os.path.join(PROCESSED_PATH, "purchase_orders.csv"))

# ------------------------------------------------------------
# 3️⃣  BASIC DATA OVERVIEW
# ------------------------------------------------------------
print("\n--- Data Overview ---")
print("Products:", products.shape)
print("Suppliers:", suppliers.shape)
print("Sales:", sales.shape)
print("Inventory:", inventory.shape)
print("Purchase Orders:", purchase_orders.shape)

print("\nSales columns:", sales.columns.tolist())
print("\nSample data:")
print(sales.head())

# Convert dates
sales['Sale_Date'] = pd.to_datetime(sales['Sale_Date'])
purchase_orders['Order_Date'] = pd.to_datetime(purchase_orders['Order_Date'])
purchase_orders['Delivery_Date'] = pd.to_datetime(purchase_orders['Delivery_Date'])
inventory['Transaction_Date'] = pd.to_datetime(inventory['Transaction_Date'])

# ------------------------------------------------------------
# 4️⃣  DEMAND ANALYSIS PER SKU
# ------------------------------------------------------------
sales['Week'] = sales['Sale_Date'].dt.to_period('W')
sku_weekly = sales.groupby(['SKU', 'Week'])['Quantity_Sold'].sum().reset_index()

sku_demand_stats = sku_weekly.groupby('SKU')['Quantity_Sold'].agg(['mean', 'std', 'count']).reset_index()
sku_demand_stats.rename(columns={'mean': 'Avg_Weekly_Demand', 'std': 'Std_Weekly_Demand'}, inplace=True)
sku_demand_stats['CV'] = sku_demand_stats['Std_Weekly_Demand'] / sku_demand_stats['Avg_Weekly_Demand'].replace(0, np.nan)

print("\n--- SKU Demand Variability ---")
print(sku_demand_stats.head())

# Visualization: demand variability histogram
plt.figure(figsize=(8,5))
sns.histplot(sku_demand_stats['CV'], bins=30, kde=True, color='skyblue')
plt.title("Demand Variability Across SKUs (Coefficient of Variation)")
plt.xlabel("CV (Std / Mean of Weekly Demand)")
plt.ylabel("Count of SKUs")
plt.tight_layout()
plt.savefig(os.path.join(PLOT_DIR, "demand_cv_hist.png"))
plt.show()

# ------------------------------------------------------------
# 5️⃣  INVENTORY ANALYSIS
# ------------------------------------------------------------
inv_summary = inventory.groupby('SKU')['Quantity'].agg(['mean', 'std', 'min', 'max']).reset_index()
inv_summary.rename(columns={'mean':'Avg_On_Hand','std':'Std_On_Hand'}, inplace=True)

# Visualize the distribution of average on-hand inventory
plt.figure(figsize=(8,4))
sns.histplot(inv_summary['Avg_On_Hand'], bins=30, color='orange', edgecolor='black')
plt.title('Average On-Hand Inventory Distribution (per SKU)')
plt.xlabel('Average Quantity on Hand')
plt.ylabel('Count of SKUs')
plt.tight_layout()
plt.savefig(os.path.join(PLOT_DIR, "avg_on_hand_inventory_hist.png"))
plt.show()

# ------------------------------------------------------------
# 6️⃣  SUPPLIER PERFORMANCE ANALYSIS
# ------------------------------------------------------------
purchase_orders['Actual_Lead_Time'] = (purchase_orders['Delivery_Date'] - purchase_orders['Order_Date']).dt.days
supplier_perf = purchase_orders.groupby('Supplier_ID')['Actual_Lead_Time'].agg(['mean','std','count']).reset_index()
supplier_perf.rename(columns={'mean':'Avg_Lead_Time','std':'Std_Lead_Time'}, inplace=True)

supplier_perf = pd.merge(supplier_perf, suppliers[['Supplier_ID','Supplier_Name','Lead_Time_Days_Avg']], on='Supplier_ID', how='left')
supplier_perf['Lead_Time_Diff'] = supplier_perf['Avg_Lead_Time'] - supplier_perf['Lead_Time_Days_Avg']

print("\n--- Supplier Performance ---")
print(supplier_perf.head())

plt.figure(figsize=(8,5))
sns.histplot(supplier_perf['Lead_Time_Diff'], bins=20, kde=True, color='green')
plt.title("Supplier Lead Time Difference (Actual vs Promised)")
plt.xlabel("Lead Time Difference (days)")
plt.ylabel("Count of Suppliers")
plt.tight_layout()
plt.savefig(os.path.join(PLOT_DIR, "supplier_lead_time_diff_hist.png"))
plt.show()

# ------------------------------------------------------------
# 7️⃣  ABC CLASSIFICATION
# ------------------------------------------------------------
# Merge unit cost from products table
sales_value = pd.merge(sales, products[['SKU', 'Unit_Cost']], on='SKU', how='left')

# Calculate total sales value per row
sales_value['Sales_Value'] = sales_value['Quantity_Sold'] * sales_value['Unit_Cost']

# Aggregate to SKU level
sku_value = (
    sales_value.groupby('SKU', as_index=False)['Sales_Value']
    .sum()
    .rename(columns={'Sales_Value': 'Annual_Value'})
)

# Sort descending by annual value
sku_value = sku_value.sort_values('Annual_Value', ascending=False).reset_index(drop=True)

# Compute cumulative percentage
sku_value['Cumulative_%'] = sku_value['Annual_Value'].cumsum() / sku_value['Annual_Value'].sum() * 100

# Assign ABC category
sku_value['Category'] = pd.cut(
    sku_value['Cumulative_%'],
    bins=[0, 80, 95, 100],
    labels=['A', 'B', 'C']
)

# Plot top 20 SKUs
top20 = sku_value.head(20)
plt.figure(figsize=(10,6))
plt.barh(top20['SKU'], top20['Annual_Value'], color='skyblue')
plt.xlabel('Annual Sales Value')
plt.ylabel('SKU')
plt.title('Top 20 SKUs by Annual Sales Value (ABC Classification)')
plt.gca().invert_yaxis()  # highest value on top
plt.tight_layout()
plt.savefig(os.path.join(PLOT_DIR, "abc_top20_skus.png"))
plt.show()

print(sku_value.head())

# ------------------------------------------------------------
# 8️⃣  WAREHOUSE-LEVEL INVENTORY ANALYSIS
# ------------------------------------------------------------
# Compute storage capacity and current inventory per warehouse
wh_capacity = warehouses.groupby('Warehouse_ID')['Storage_Capacity_Units'].mean().reset_index()
wh_current = inventory.groupby('Warehouse_ID')['Quantity'].sum().reset_index()
wh_plot = pd.merge(wh_capacity, wh_current, on='Warehouse_ID', how='left')
wh_plot = pd.merge(wh_plot, warehouses[['Warehouse_ID','Location']], on='Warehouse_ID', how='left')

# Plot capacity vs current stock
plt.figure(figsize=(10,6))
bar_width = 0.4
x = np.arange(len(wh_plot['Warehouse_ID']))
plt.bar(x - bar_width/2, wh_plot['Storage_Capacity_Units'], width=bar_width, label='Capacity', color='skyblue')
plt.bar(x + bar_width/2, wh_plot['Quantity'], width=bar_width, label='Current Inventory', color='orange')
plt.xticks(x, wh_plot['Warehouse_ID'])
plt.xlabel('Warehouse ID')
plt.ylabel('Units')
plt.title('Warehouse Capacity vs Current Inventory')
plt.legend()
plt.tight_layout()
plt.savefig(os.path.join(PLOT_DIR, "warehouse_capacity_vs_inventory.png"))
plt.show()
