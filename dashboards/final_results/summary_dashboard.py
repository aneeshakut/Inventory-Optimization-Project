import os
import pandas as pd
from IPython.display import display, HTML, Image
import ipywidgets as widgets

# -------------------------------------------------------------
# 1️⃣ PATHS
# -------------------------------------------------------------
BASE_DIR = os.path.abspath(r"C:\\Users\\hp\\Desktop\\Inventory-Optimization-Project")
DATA_PATH = os.path.join(BASE_DIR, "data", "processed")
EDA_PNG_PATH = os.path.join(BASE_DIR, "dashboards", "eda_results")
SIM_PNG_PATH = os.path.join(BASE_DIR, "dashboards", "simulation_results")

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

total_skus = sales['SKU'].nunique() if not sales.empty else 0
avg_weekly_demand = sales.groupby('SKU')['Quantity_Sold'].mean().mean() if 'Quantity_Sold' in sales.columns else 0
avg_inventory = inventory.groupby('SKU')['Quantity'].mean().mean() if 'Quantity' in inventory.columns else 0
avg_supplier_lead = (purchase_orders['Delivery_Date'] - purchase_orders['Order_Date']).dt.days.mean() if ('Delivery_Date' in purchase_orders.columns and 'Order_Date' in purchase_orders.columns) else 0

d = avg_weekly_demand * 52
h = 1
c = 10
avg_eoq = ((2*d*c/h)**0.5) if d>0 else 0
avg_fill_rate = 95

# -------------------------------------------------------------
# 4️⃣ KPI CARDS 
# -------------------------------------------------------------
def kpi_card(title, value, color):
    return f"""
    <div style="
        background-color:{color};
        border-radius:10px;
        padding:15px;
        margin:10px;
        flex:1;
        text-align:center;
        color:white;
        font-family:sans-serif;
        min-width:180px;
        box-shadow:0 3px 6px rgba(0,0,0,0.1);">
        <h4 style="margin:5px 0;">{title}</h4>
        <h2 style="margin:0;">{value}</h2>
    </div>
    """

cards_html = f"""
<div style="display:flex;flex-wrap:wrap;justify-content:space-around;">
{ kpi_card('📦 Total SKUs', f'{total_skus:,}', '#636EFA') }
{ kpi_card('📊 Avg Weekly Demand', f'{avg_weekly_demand:.1f}', '#EF553B') }
{ kpi_card('⚙️ Avg Inventory', f'{avg_inventory:.1f}', '#00CC96') }
{ kpi_card('⏱️ Avg Supplier Lead Time', f'{avg_supplier_lead:.1f} days', '#AB63FA') }
{ kpi_card('⚙️ Avg EOQ', f'{avg_eoq:.1f}', '#19D3F3') }
{ kpi_card('📈 Avg Fill Rate', f'{avg_fill_rate:.1f}%', '#FFA15A') }
</div>
"""

display(HTML("<h2 style='color:#007acc;'>📊 Inventory Optimization Dashboard</h2>"))
display(HTML(cards_html))

# -------------------------------------------------------------
# 5️⃣ & 6️⃣ EDA and SIMULATION PNG SELECTION 
# -------------------------------------------------------------

eda_png_files = [f for f in os.listdir(EDA_PNG_PATH) if f.lower().endswith('.png')]
sim_png_files = [f for f in os.listdir(SIM_PNG_PATH) if f.lower().endswith('.png')]

# Manually select which PNG to display
selected_eda = eda_png_files[0]  
selected_sim = sim_png_files[2]  

display(HTML("<h3>🔹 Selected EDA Result</h3>"))
display(Image(filename=os.path.join(EDA_PNG_PATH, selected_eda)))

display(HTML("<h3>🔹 Selected Simulation Result</h3>"))
display(Image(filename=os.path.join(SIM_PNG_PATH, selected_sim)))

print("✅ Dashboard with selectable plots generated successfully!")
