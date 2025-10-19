# 🏭 Inventory Optimization Project  

## 📘 Overview  
This project presents a **complete, end-to-end data analytics pipeline** for **inventory optimization** — from raw data to insights — entirely in **Python**.  
It is designed to support data-driven decision-making in supply chain management by integrating **EDA, simulation, and dashboard visualization** into one streamlined process.  

All insights are derived from real datasets and visualized using a Power BI–style **interactive dashboard** built in Jupyter Notebook.  

---

## 🎯 Key Goals  
- Understand demand and supply chain behavior using **exploratory data analysis (EDA)**.  
- Optimize **inventory ordering decisions** using EOQ and safety stock models.  
- Perform **what-if simulations** to test different supply-demand conditions.  
- Generate a **professional dashboard** summarizing all key metrics and insights.  

---

## 🧠 Complete Project Workflow  

| Step | Description | Output |
|------|--------------|--------|
| **1️⃣ Data Ingestion & Cleaning** | Load, validate, and clean raw CSV files. | Cleaned data in `data/processed/` |
| **2️⃣ Exploratory Data Analysis (EDA)** | Identify trends, SKU-level patterns, supplier & warehouse performance. | Visuals in `dashboards/eda_results/` |
| **3️⃣ Modeling & Optimization** | Compute EOQ, reorder levels, and key KPIs. | EOQ distributions, SKU analysis |
| **4️⃣ Simulation & What-if Analysis** | Simulate various demand/lead time scenarios. | Simulation visuals in `dashboards/simulation_results/` |
| **5️⃣ Dashboard Summary** | Combine all key results and visuals into a unified Power BI–style summary dashboard. | Final dashboard PNG in `dashboards/final_results/` |

---

## 🧩 Folder Structure  

```
Inventory-Optimization-Project/
│
├── data/
│   ├── raw/                     # Original datasets (optional)
│   └── processed/               # Cleaned and transformed CSVs
│
├── src/
│   ├── ingestion/               # Data ingestion and validation scripts
│   ├── cleaning/                # Data preprocessing scripts
│   ├── modeling/                # EOQ and inventory models
│   └── simulation/              # Simulation & what-if scenarios
│
├── dashboards/
│   ├── eda_results/             # PNGs generated from EDA
│   ├── simulation_results/      # PNGs from simulation step
│   ├── final_results/           # Final dashboard summary PNG
│   └── summary_dashboard.ipynb  # Interactive summary notebook
│
├── reports/                     # Optional PDF reports
├── README.md                    # Project documentation
└── requirements.txt              # Dependencies
```

---

## ⚙️ Technologies Used  

| Category | Tools / Libraries |
|-----------|-------------------|
| **Programming** | Python 3.10+ |
| **Data Handling** | pandas, numpy |
| **Visualization** | matplotlib, seaborn |
| **Dashboard & UI** | Jupyter Notebook (HTML, IPython.display) |
| **Reporting** | PIL, matplotlib for dashboard capture |
| **Version Control** | Git, GitHub |

---

## 🧮 Key Features  

- 🔍 Automated **data ingestion and cleaning** pipeline.  
- 📊 Visual **EDA summaries** for demand, inventory, and suppliers.  
- ⚙️ **EOQ** and reorder point modeling.  
- 🎲 **Simulation-based what-if analysis** for different supply-demand conditions.  
- 🖥️ **Power BI–style dashboard** summarizing all insights in one view.  
- 📸 Exports the dashboard as a **PNG snapshot** for final reporting.  

---

## 🚀 How to Run  

### 1️⃣ Clone the Repository  
```bash
git clone https://github.com/aneeshakut/Inventory-Optimization-Project.git
cd Inventory-Optimization-Project
```

### 2️⃣ Install Required Libraries  
```bash
pip install -r requirements.txt
```

### 3️⃣ Run the Project  
You can run the entire pipeline inside Jupyter Notebook:  
```
dashboards/summary_dashboard.ipynb
```
or execute the unified Python script:
```bash
python dashboards/summary_dashboard.py
```

This script automatically:  
- Loads processed data (`data/processed/`)  
- Integrates EDA visuals (`dashboards/eda_results/`)  
- Integrates simulation visuals (`dashboards/simulation_results/`)  
- Generates a **Power BI–style summary dashboard**  
- Exports the dashboard snapshot to `dashboards/final_results/dashboard_summary.png`

---

## 💡 Insights Derived  

- EOQ model shows significant ordering efficiency improvements for high-volume SKUs.  
- Lead time variability strongly impacts reorder levels and safety stock needs.  
- Simulation highlights how small demand shifts affect service levels and stockouts.  
- Dashboard consolidates EDA and simulation metrics for instant decision support.  

---

## 🧭 Future Enhancements  

- Integrate with **Power BI / Streamlit** for live dashboard interaction.  
- Add **forecasting models (ARIMA, Prophet)** for demand prediction.  
- Automate entire workflow using **Airflow or Prefect**.  
- Incorporate SQL-based data warehouse backend for scalability.  

---

## 📦 Requirements  

```txt
pandas
numpy
matplotlib
seaborn
pillow
ipython
```

---

## 🏁 Outcome  
✅ Fully automated end-to-end **Inventory Optimization System**  
✅ Real insight generation from data, without dummy values  
✅ Unified, professional-looking dashboard summarizing all findings  
✅ PNG snapshot for reporting & sharing  

---

> 🧠 *"Transforming supply chain data into strategic inventory decisions — powered by Python."*
