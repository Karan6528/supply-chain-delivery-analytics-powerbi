"""
Recompute the headline KPIs in pandas so you can check your DAX measures
return the same numbers in Power BI (a good habit for any BI project).

Run:  python scripts/validate_kpis.py
"""
from pathlib import Path
import pandas as pd
pd.set_option("display.width", 200)
pd.set_option("display.max_columns", 20)

D = Path(__file__).resolve().parents[1] / "data"
o = pd.read_csv(D / "orders.csv", parse_dates=["order_date", "ship_date",
                "promised_delivery_date", "actual_delivery_date"])
l = pd.read_csv(D / "order_lines.csv")
p = pd.read_csv(D / "products.csv")
c = pd.read_csv(D / "carriers.csv")
w = pd.read_csv(D / "warehouses.csv")
inv = pd.read_csv(D / "inventory_weekly.csv", parse_dates=["week_start"])

l["net_sales"] = l.quantity * l.unit_price_eur * (1 - l.discount_pct)
l["cogs"] = l.quantity * l.unit_cost_eur
o = o.merge(l.groupby("order_id")[["net_sales", "cogs"]].sum(), on="order_id")
o["year"] = o.order_date.dt.year

dl = o[o.order_status != "Cancelled"].copy()
dl["delay_days"] = (dl.actual_delivery_date - dl.promised_delivery_date).dt.days
dl["on_time"] = dl.delay_days <= 0
o = o.merge(dl[["order_id", "delay_days", "on_time"]], on="order_id", how="left")

def pct(x): return f"{x:.1%}"
def eur(x): return f"EUR {x:,.0f}"

print("=" * 64, "\nHEADLINE KPIs (all years)\n" + "=" * 64)
print("Orders                    ", f"{len(o):,}")
print("Net sales                 ", eur(o.net_sales.sum()))
print("On-time delivery rate     ", pct(dl.on_time.mean()))
print("Avg delay (late orders)   ", f"{dl.loc[~dl.on_time, 'delay_days'].mean():.2f} days")
print("Cancellation rate         ", pct((o.order_status == 'Cancelled').mean()))
print("Return rate               ", pct((o.order_status == 'Returned').mean()))
print("Avg review score          ", f"{o.review_score.mean():.2f}")

# Cost of late deliveries
late = o[(o.delay_days > 0) | ((o.order_status == "Cancelled"))]
refund_late = o.loc[(o.order_status.isin(["Cancelled", "Returned"])) & ((o.delay_days > 0) | (o.order_status == "Cancelled")), "net_sales"].sum()
comp = o.late_compensation_eur.sum()
print("Revenue lost to late-related cancels/returns", eur(refund_late))
print("Late compensation vouchers", eur(comp))

print("\n--- By year")
print(o.groupby("year").agg(orders=("order_id", "size"), net_sales=("net_sales", "sum"),
                            on_time=("on_time", "mean")).round(3))

print("\n--- By carrier")
cc = o.merge(c, on="carrier_id").groupby("carrier_name").agg(
    orders=("order_id", "size"), on_time=("on_time", "mean"),
    cost_per_ship=("shipping_cost_eur", "mean"), cancel=("order_status", lambda s: (s == "Cancelled").mean()),
    review=("review_score", "mean"), compensation=("late_compensation_eur", "sum"))
print(cc.round(3))

print("\n--- By warehouse x peak season")
o["peak"] = o.order_date.dt.month.isin([11, 12]).map({True: "Nov-Dec", False: "Jan-Oct"})
print(o.pivot_table(index="warehouse_id", columns="peak", values="on_time", aggfunc="mean").round(3))

print("\n--- Review score & return rate by delay bucket")
b = pd.cut(o.delay_days, [-10, 0, 2, 4, 20], labels=["On time", "1-2 d late", "3-4 d late", "5+ d late"])
print(o.groupby(b, observed=True).agg(orders=("order_id", "size"), review=("review_score", "mean"),
      returns=("order_status", lambda s: (s == "Returned").mean())).round(3))

print("\n--- Customer reorders within 90 days, by delivery experience")
# Mirrors the DAX column 'Next Order Date' = next order on a LATER date
o = o.sort_values(["customer_id", "order_date"])
nxt = (o[["customer_id", "order_date"]].drop_duplicates()
       .assign(next_date=lambda t: t.groupby("customer_id").order_date.shift(-1)))
o = o.merge(nxt, on=["customer_id", "order_date"], how="left")
o["bad_exp"] = (o.delay_days >= 3) | (o.order_status == "Cancelled")
x = o[o.order_date <= "2025-10-02"]   # leave 90 days to observe
x = x.assign(reordered=(x.next_date - x.order_date).dt.days <= 90)
print(x.groupby(x.bad_exp.map({True: "3+ days late or cancelled", False: "Good experience"}))
       .reordered.mean().round(3))

print("\n--- Inventory: stockouts & lost sales by category")
inv = inv.merge(p[["product_id", "category", "unit_price_eur", "actual_supplier_lead_time_days",
                   "planning_lead_time_days"]], on="product_id")
inv["lost_rev"] = inv.lost_sales_units * inv.unit_price_eur
cat = inv.groupby("category").agg(stockout_rate=("stockout_flag", "mean"), lost_units=("lost_sales_units", "sum"),
                                  lost_revenue=("lost_rev", "sum"))
lt = p.groupby("category")[["actual_supplier_lead_time_days", "planning_lead_time_days"]].mean()
print(cat.join(lt).sort_values("lost_revenue", ascending=False).round(3))
print("Total lost revenue from stockouts", eur(inv.lost_rev.sum()))
