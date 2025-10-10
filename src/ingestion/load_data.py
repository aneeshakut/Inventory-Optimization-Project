import pandas as pd
import os

RAW_PATH = "C:\\Users\hp\Desktop\Inventory-Optimization-Project\data\\raw"
PROCESSED_PATH = "C:\\Users\hp\Desktop\Inventory-Optimization-Project\data\processed"

def load_excel(file_name):
    path = os.path.join(RAW_PATH, file_name)
    df = pd.read_excel(path)
    print(f"✅ Loaded {file_name}: {df.shape[0]} rows, {df.shape[1]} columns")
    return df

def validate_columns(df, expected_cols, name):
    missing = set(expected_cols) - set(df.columns)
    if missing:
        print(f"⚠️ {name}: Missing columns {missing}")
    else:
        print(f"✔️ {name}: All columns validated")

def main():
    # Load all files
    products = load_excel("products.xlsx")
    suppliers = load_excel("suppliers.xlsx")
    warehouses = load_excel("warehouses.xlsx")
    sales = load_excel("sales.xlsx")
    inventory = load_excel("inventory_tx.xlsx")
    purchase = load_excel("purchase_orders.xlsx")

    # Validate schemas
    validate_columns(products, ["SKU", "Product_Name", "Category", "Unit_Cost", "Supplier_ID"], "Products")
    validate_columns(suppliers, ["Supplier_ID", "Lead_Time_Days_Avg", "Reliability_Score"], "Suppliers")
    validate_columns(warehouses, ["Warehouse_ID", "Warehouse_Name", "Location"], "Warehouses")
    validate_columns(sales, ["Sales_ID", "SKU", "Warehouse_ID", "Sale_Date", "Quantity_Sold"], "Sales")
    validate_columns(inventory, ["Transaction_ID", "SKU", "Transaction_Date", "Transaction_Type", "Quantity"], "Inventory")
    validate_columns(purchase, ["PO_ID", "SKU", "Supplier_ID", "Order_Date", "Delivery_Date", "Status"], "Purchase Orders")

    # Check for duplicates in keys
    for name, df, key in [
        ("Products", products, "SKU"),
        ("Suppliers", suppliers, "Supplier_ID"),
        ("Warehouses", warehouses, "Warehouse_ID")
    ]:
        dup = df[df.duplicated(subset=[key])]
        if not dup.empty:
            print(f"⚠️ {name}: Found duplicate {key}")
        else:
            print(f"✔️ {name}: Unique {key}")

    # Foreign key check example
    unmatched_suppliers = products[~products["Supplier_ID"].isin(suppliers["Supplier_ID"])]
    if not unmatched_suppliers.empty:
        print("⚠️ Some products have invalid Supplier_IDs")
    else:
        print("✔️ All Product Supplier_IDs valid")

    # Export clean copies
    os.makedirs(PROCESSED_PATH, exist_ok=True)
    for name, df in {
        "products": products,
        "suppliers": suppliers,
        "warehouses": warehouses,
        "sales": sales,
        "inventory_tx": inventory,
        "purchase_orders": purchase
    }.items():
        df.to_csv(os.path.join(PROCESSED_PATH, f"{name}.csv"), index=False)
        print(f"📁 Saved {name}.csv")

if __name__ == "__main__":
    main()
