import os
import pandas as pd
from IPython.display import display, HTML, Image
import matplotlib.pyplot as plt
from PIL import Image as PILImage

# -------------------------------------------------------------
# 1️⃣ PATHS
# -------------------------------------------------------------
BASE_DIR = os.path.abspath(r"C:\\Users\\hp\\Desktop\\Inventory-Optimization-Project")  # adjust if needed
DATA_PATH = os.path.join(BASE_DIR, "data", "processed")
EDA_PNG_PATH = os.path.join(BASE_DIR, "dashboards", "eda_results")
SIM_PNG_PATH = os.path.join(BASE_DIR, "dashboards", "simulation_results")
FINAL_RESULTS_PATH = os.path.join(BASE_DIR, "dashboards", "final_results")
os.makedirs(FINAL_RESULTS_PATH, exist_ok=True)

# -------------------------------------------------------------
# 2️⃣ LOAD PROCESSED DATA
# -------------------------------------------------------------
def load_csv(file_name):
    file_path = os.path.join(DATA_PATH, file_name)
    return pd.read_csv(file_path) if os.path.exists(file_path) else pd.DataFrame()

products = load_csv("products.csv")
sales = load_csv("sales.csv")
inventory = load_csv("inventory_tx.csv")
purchase_orders = load_csv("purchase_orders.csv")
suppliers = load_csv("suppliers.csv")
warehouses = load_csv("warehouses.csv")

# -------------------------------------------------------------
# 3️⃣ PROCESS METRICS
# -------------------------------------------------------------
sales['Sale_Date'] = pd.to_datetime(sales['Sale_Date']) if 'Sale_Date' in sales.columns else None
purchase_orders['Order_Date'] = pd.to_datetime(purchase_orders['Order_Date']) if 'Order_Date' in purchase_orders.columns else None
purchase_orders['Delivery_Date'] = pd.to_datetime(purchase_orders['Delivery_Date']) if 'Delivery_Date' in purchase_orders.columns else None
inventory['Transaction_Date'] = pd.to_datetime(inventory['Transaction_Date']) if 'Transaction_Date' in inventory.columns else None

# KPI computations
total_skus = sales['SKU'].nunique() if not sales.empty else 0
avg_weekly_demand = sales.groupby('SKU')['Quantity_Sold'].mean().mean() if 'Quantity_Sold' in sales.columns else 0
avg_inventory = inventory.groupby('SKU')['Quantity'].mean().mean() if 'Quantity' in inventory.columns else 0
avg_supplier_lead = (purchase_orders['Delivery_Date'] - purchase_orders['Order_Date']).dt.days.mean() if ('Delivery_Date' in purchase_orders.columns and 'Order_Date' in purchase_orders.columns) else 0

# EOQ approximation (simple)
d = avg_weekly_demand * 52  # annual demand per SKU
h = 1  # holding cost/unit/year (assumed)
c = 10  # unit cost (assumed)
avg_eoq = ((2*d*c/h)**0.5) if d>0 else 0

# Fill rate approximation (simple)
avg_fill_rate = 95  # placeholder

# -------------------------------------------------------------
# 4️⃣ KPI CARD FIGURE FOR IMAGE EXPORT
# -------------------------------------------------------------
fig, axes = plt.subplots(2, 3, figsize=(12, 6))
fig.suptitle("Inventory Optimization Dashboard Summary", fontsize=16, weight='bold')

kpis = [("Total SKUs", total_skus),
        ("Avg Weekly Demand", f"{avg_weekly_demand:.1f}"),
        ("Avg Inventory", f"{avg_inventory:.1f}"),
        ("Avg Supplier Lead Time (days)", f"{avg_supplier_lead:.1f}"),
        ("Avg EOQ", f"{avg_eoq:.1f}"),
        ("Avg Fill Rate (%)", f"{avg_fill_rate:.1f}")]

colors = ['#636EFA','#EF553B','#00CC96','#AB63FA','#19D3F3','#FFA15A']

for ax, (title, value), color in zip(axes.flatten(), kpis, colors):
    ax.axis('off')
    ax.set_facecolor(color)
    ax.text(0.5, 0.5, f"{title}\n{value}", ha='center', va='center', fontsize=12, weight='bold', color='white')

plt.tight_layout(rect=[0,0,1,0.95])

# Save KPI cards figure
kpi_image_path = os.path.join(FINAL_RESULTS_PATH, "dashboard_kpis.png")
plt.savefig(kpi_image_path, dpi=300)
plt.close()

# -------------------------------------------------------------
# 5️⃣ COMBINE REPRESENTATIVE EDA & SIMULATION PNGS
# -------------------------------------------------------------
eda_png_files = [f for f in os.listdir(EDA_PNG_PATH) if f.lower().endswith('.png')]
sim_png_files = [f for f in os.listdir(SIM_PNG_PATH) if f.lower().endswith('.png')]

# Select one PNG each
selected_eda = eda_png_files[0] if eda_png_files else None
selected_sim = sim_png_files[0] if sim_png_files else None

if selected_eda and selected_sim:
    eda_img = PILImage.open(os.path.join(EDA_PNG_PATH, selected_eda))
    sim_img = PILImage.open(os.path.join(SIM_PNG_PATH, selected_sim))

    combined_width = eda_img.width + sim_img.width
    combined_height = max(eda_img.height, sim_img.height)
    combined_img = PILImage.new('RGB', (combined_width, combined_height), color=(255,255,255))
    combined_img.paste(eda_img, (0,0))
    combined_img.paste(sim_img, (eda_img.width,0))

    combined_image_path = os.path.join(FINAL_RESULTS_PATH, "eda_sim_combined.png")
    combined_img.save(combined_image_path)

print(f"✅ Dashboard images saved to: {FINAL_RESULTS_PATH}")
