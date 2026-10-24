"""
Generate the UrbanCart GmbH supply chain dataset (2024-2025).

UrbanCart is a fictional German online retailer shipping from 5 warehouses
with 4 carrier partners. The data is synthetic but built around realistic
operational patterns so the Power BI analysis has real problems to find:

  1. One low-cost carrier is late far more often than the others.
  2. The Leipzig warehouse collapses under peak-season (Nov-Dec) volume.
  3. Late deliveries drive cancellations, returns, bad reviews and lower
     repeat purchasing.
  4. Electronics reorder points were set using outdated supplier lead times,
     so they stock out repeatedly and lose sales.

Run:  python scripts/generate_data.py
Output: CSV files in ./data
"""
from pathlib import Path
import numpy as np
import pandas as pd

SEED = 42
rng = np.random.default_rng(SEED)
OUT = Path(__file__).resolve().parents[1] / "data"
OUT.mkdir(exist_ok=True)

START, END = pd.Timestamp("2024-01-01"), pd.Timestamp("2025-12-31")

# --------------------------------------------------------------------------
# Warehouses
# --------------------------------------------------------------------------
warehouses = pd.DataFrame([
    ("WH-BER", "Berlin",    "Berlin",                 "East",  1400),
    ("WH-HAM", "Hamburg",   "Hamburg",                "North", 1300),
    ("WH-MUC", "Munich",    "Bavaria",                "South", 1350),
    ("WH-FRA", "Frankfurt", "Hesse",                  "West",  1450),
    ("WH-LEJ", "Leipzig",   "Saxony",                 "East",   700),
], columns=["warehouse_id", "warehouse_city", "warehouse_state", "service_region",
            "daily_capacity_orders"])

# --------------------------------------------------------------------------
# Carriers (fictional names)
# --------------------------------------------------------------------------
carriers = pd.DataFrame([
    ("CR-01", "SwiftFreight", "Premium",  2, 7.90, 0.05),
    ("CR-02", "NordLogistik", "Standard", 3, 5.40, 0.08),
    ("CR-03", "ExpressLine",  "Standard", 3, 5.10, 0.10),
    ("CR-04", "CargoWay",     "Economy",  4, 3.60, 0.23),
], columns=["carrier_id", "carrier_name", "service_level", "promised_transit_days",
            "avg_cost_per_shipment_eur", "_base_late_rate"])
carrier_share = np.array([0.18, 0.30, 0.24, 0.28])  # CargoWay is cheap -> heavily used

# --------------------------------------------------------------------------
# Products
# --------------------------------------------------------------------------
cat_spec = {
    #  category        n   price range     margin  lead time (d)  assumed lead (d)
    "Electronics":    (22, (39, 899),      0.22,   (24, 38),      9),
    "Home & Kitchen": (24, (12, 249),      0.38,   (6, 12),       9),
    "Fashion":        (26, (15, 159),      0.52,   (7, 14),      11),
    "Beauty":         (18, (6, 69),        0.55,   (5, 10),       8),
    "Sports":         (16, (14, 329),      0.40,   (8, 15),      12),
    "Books & Media":  (14, (8, 49),        0.30,   (4, 8),        6),
}
suppliers = {
    "Electronics": ["Shenzhen TechSource", "EuroComponents BV"],
    "Home & Kitchen": ["HausWerk GmbH", "Nordic Living AB"],
    "Fashion": ["Istanbul Textiles", "Porto Apparel Lda"],
    "Beauty": ["Lyon Cosmetique", "Alpine Care AG"],
    "Sports": ["ActiveGear Poland", "Taipei Sports Mfg"],
    "Books & Media": ["Leipziger Verlagsvertrieb"],
}
rows, pid = [], 1
for cat, (n, (lo, hi), margin, (lt_lo, lt_hi), assumed) in cat_spec.items():
    for i in range(n):
        price = round(float(np.exp(rng.uniform(np.log(lo), np.log(hi)))), 2) - 0.01
        cost = round(price * (1 - margin + rng.normal(0, 0.04)), 2)
        rows.append({
            "product_id": f"P{pid:04d}",
            "product_name": f"{cat.split(' ')[0]} Item {i + 1:02d}",
            "category": cat,
            "supplier": rng.choice(suppliers[cat]),
            "unit_price_eur": round(price, 2),
            "unit_cost_eur": cost,
            "actual_supplier_lead_time_days": int(rng.integers(lt_lo, lt_hi + 1)),
            "planning_lead_time_days": assumed,  # what the ERP assumes
            "_popularity": rng.gamma(1.4, 1.0) * (1.6 if cat in ("Fashion", "Beauty") else 1.0)
                           / (1 + price / 300),
        })
        pid += 1
products = pd.DataFrame(rows)
products["product_name"] = products["category"].map({
    "Electronics": "Electronics", "Home & Kitchen": "Home", "Fashion": "Fashion",
    "Beauty": "Beauty", "Sports": "Sports", "Books & Media": "Media"}) + " SKU " + \
    products["product_id"].str[1:]
pop = products["_popularity"].to_numpy()
pop = pop / pop.sum()

# --------------------------------------------------------------------------
# Customers
# --------------------------------------------------------------------------
cities = pd.DataFrame([
    ("Berlin", "Berlin", "East", 0.14), ("Potsdam", "Brandenburg", "East", 0.03),
    ("Dresden", "Saxony", "East", 0.04), ("Leipzig", "Saxony", "East", 0.05),
    ("Erfurt", "Thuringia", "East", 0.02), ("Magdeburg", "Saxony-Anhalt", "East", 0.02),
    ("Hamburg", "Hamburg", "North", 0.09), ("Bremen", "Bremen", "North", 0.03),
    ("Hanover", "Lower Saxony", "North", 0.04), ("Kiel", "Schleswig-Holstein", "North", 0.02),
    ("Rostock", "Mecklenburg-Vorpommern", "North", 0.02),
    ("Munich", "Bavaria", "South", 0.10), ("Nuremberg", "Bavaria", "South", 0.04),
    ("Stuttgart", "Baden-Wuerttemberg", "South", 0.06), ("Freiburg", "Baden-Wuerttemberg", "South", 0.02),
    ("Frankfurt", "Hesse", "West", 0.07), ("Cologne", "North Rhine-Westphalia", "West", 0.07),
    ("Dusseldorf", "North Rhine-Westphalia", "West", 0.04), ("Dortmund", "North Rhine-Westphalia", "West", 0.04),
    ("Mainz", "Rhineland-Palatinate", "West", 0.02), ("Saarbrucken", "Saarland", "West", 0.02),
], columns=["city", "state", "region", "weight"])
cities["weight"] /= cities["weight"].sum()

N_CUST = 6000
ci = rng.choice(len(cities), N_CUST, p=cities["weight"])
customers = pd.DataFrame({
    "customer_id": [f"C{i:05d}" for i in range(1, N_CUST + 1)],
    "city": cities["city"].to_numpy()[ci],
    "state": cities["state"].to_numpy()[ci],
    "region": cities["region"].to_numpy()[ci],
    "segment": rng.choice(["Consumer", "Small Business"], N_CUST, p=[0.86, 0.14]),
    "signup_date": START + pd.to_timedelta(rng.integers(-400, 650, N_CUST), unit="D"),
})
customers.loc[customers["signup_date"] < pd.Timestamp("2023-01-01"), "signup_date"] = pd.Timestamp("2023-01-01")
propensity = rng.gamma(1.1, 1.0, N_CUST) * np.where(customers["segment"] == "Small Business", 2.2, 1.0)
signup = customers["signup_date"].to_numpy()

# Warehouse routing: region -> warehouse(s). East is split Berlin/Leipzig.
region_wh = {"North": (["WH-HAM"], [1.0]), "South": (["WH-MUC"], [1.0]),
             "West": (["WH-FRA"], [1.0]), "East": (["WH-BER", "WH-LEJ"], [0.52, 0.48])}

# --------------------------------------------------------------------------
# Orders (simulated day by day so experience affects repeat behaviour)
# --------------------------------------------------------------------------
days = pd.date_range(START, END, freq="D")
order_rows, line_rows = [], []
oid = 1
carrier_late = carriers["_base_late_rate"].to_numpy()
carrier_transit = carriers["promised_transit_days"].to_numpy()
carrier_cost = carriers["avg_cost_per_shipment_eur"].to_numpy()

for d in days:
    month, dow = d.month, d.dayofweek
    season = {11: 1.55, 12: 1.75, 1: 0.85, 2: 0.85, 7: 0.92, 8: 0.92}.get(month, 1.0)
    if month == 11 and d.day >= 24:          # Black Friday / Cyber week
        season *= 1.6
    growth = 1.0 + 0.20 * ((d - START).days / 730)
    weekday = [1.05, 1.0, 1.0, 1.02, 0.95, 0.85, 1.12][dow]
    n_orders = rng.poisson(52 * season * growth * weekday)

    active = signup <= np.datetime64(d)
    w = propensity * active
    if w.sum() == 0:
        continue
    custs = rng.choice(N_CUST, n_orders, p=w / w.sum())

    wh_load = {}
    for c in custs:
        region = customers.at[c, "region"]
        whs, wp = region_wh[region]
        wh = whs[rng.choice(len(whs), p=wp)] if len(whs) > 1 else whs[0]
        wh_load[wh] = wh_load.get(wh, 0) + 1
        k = rng.choice(4, p=carrier_share)

        late_p = carrier_late[k]
        if month in (11, 12):
            late_p += 0.05
            if wh == "WH-LEJ":
                late_p += 0.22                # Leipzig peak-season capacity crunch
        late_p = min(late_p, 0.85)

        handling = 1
        promised = handling + carrier_transit[k]
        is_late = rng.random() < late_p
        delay = int(rng.choice([1, 2, 3, 4, 5, 6, 8], p=[.30, .24, .17, .12, .08, .06, .03])) if is_late else 0
        if not is_late and rng.random() < 0.35:
            delay = -1                        # some arrive a day early
        ship_lag = handling + (1 if (is_late and rng.random() < 0.5) else 0)
        actual_days = promised + delay

        order_date = d
        promised_date = order_date + pd.Timedelta(days=int(promised))

        # Outcome model
        status = "Delivered"
        if delay >= 4 and rng.random() < 0.18:
            status = "Cancelled"
        elif rng.random() < (0.05 + (0.09 if delay >= 2 else 0.0)):
            status = "Returned"

        if status == "Cancelled":
            ship_date = pd.NaT if rng.random() < 0.3 else order_date + pd.Timedelta(days=int(ship_lag))
            delivered_date = pd.NaT
            review = np.nan
        else:
            ship_date = order_date + pd.Timedelta(days=int(ship_lag))
            delivered_date = order_date + pd.Timedelta(days=int(actual_days))
            base = 4.45 if delay <= 0 else 3.6 - 0.22 * delay
            review = np.nan if rng.random() < 0.45 else int(np.clip(np.rint(rng.normal(base, 0.75)), 1, 5))

        # Bad experience lowers future purchase propensity (churn effect)
        if delay >= 3 or status == "Cancelled":
            propensity[c] *= 0.55
        elif delay <= 0:
            propensity[c] *= 1.03

        # Lines
        n_lines = rng.choice([1, 2, 3, 4], p=[0.58, 0.27, 0.11, 0.04])
        prods = rng.choice(len(products), n_lines, replace=False, p=pop)
        gross = 0.0
        for ln, p in enumerate(prods, 1):
            qty = int(rng.choice([1, 1, 1, 2, 2, 3]))
            price = products.at[p, "unit_price_eur"]
            disc = 0.0
            if month == 11 and d.day >= 24:
                disc = rng.choice([0.1, 0.15, 0.2, 0.25])
            elif rng.random() < 0.15:
                disc = rng.choice([0.05, 0.1])
            line_rows.append({
                "order_id": f"O{oid:06d}", "line_number": ln,
                "product_id": products.at[p, "product_id"], "quantity": qty,
                "unit_price_eur": price, "discount_pct": disc,
                "unit_cost_eur": products.at[p, "unit_cost_eur"],
            })
            gross += qty * price * (1 - disc)

        shipping_cost = round(carrier_cost[k] * rng.uniform(0.85, 1.2) * (1 + 0.15 * (n_lines - 1)), 2)
        compensation = 5.0 if (delay >= 3 and status != "Cancelled") else 0.0

        order_rows.append({
            "order_id": f"O{oid:06d}",
            "order_date": order_date.date(),
            "customer_id": customers.at[c, "customer_id"],
            "warehouse_id": wh,
            "carrier_id": carriers.at[k, "carrier_id"],
            "ship_date": ship_date.date() if pd.notna(ship_date) else None,
            "promised_delivery_date": promised_date.date(),
            "actual_delivery_date": delivered_date.date() if pd.notna(delivered_date) else None,
            "order_status": status,
            "shipping_cost_eur": shipping_cost,
            "late_compensation_eur": compensation,
            "review_score": review,
        })
        oid += 1

orders = pd.DataFrame(order_rows)
lines = pd.DataFrame(line_rows)
orders["review_score"] = orders["review_score"].astype("Int64")

# --------------------------------------------------------------------------
# Weekly inventory simulation per product x warehouse
# --------------------------------------------------------------------------
lw = lines.merge(orders[["order_id", "order_date", "warehouse_id"]], on="order_id")
lw["week_start"] = pd.to_datetime(lw["order_date"]) - pd.to_timedelta(pd.to_datetime(lw["order_date"]).dt.dayofweek, unit="D")
demand = lw.groupby(["product_id", "warehouse_id", "week_start"])["quantity"].sum()
weeks = pd.date_range(START - pd.Timedelta(days=START.dayofweek), END, freq="W-MON")

inv_rows = []
for _, prod in products.iterrows():
    for wh in warehouses["warehouse_id"]:
        try:
            dem = demand.loc[(prod.product_id, wh)].reindex(weeks, fill_value=0).to_numpy()
        except KeyError:
            dem = np.zeros(len(weeks), dtype=int)
        # True demand is a bit higher than fulfilled orders (unseen lost demand)
        true_dem = np.rint(dem * 1.0 + rng.poisson(0.3, len(weeks))).astype(int)
        avg_w = max(true_dem[:8].mean(), 0.5)
        plan_lt_w = prod.planning_lead_time_days / 7
        act_lt_w = int(np.ceil(prod.actual_supplier_lead_time_days / 7))
        safety = int(np.ceil(avg_w * 0.8))
        rop = int(np.ceil(avg_w * plan_lt_w + safety))
        order_qty = int(np.ceil(avg_w * 4))
        on_hand = rop + order_qty
        pipeline = []  # (arrival_week_idx, qty)
        for wi, wk in enumerate(weeks):
            received = sum(q for a, q in pipeline if a == wi)
            pipeline = [(a, q) for a, q in pipeline if a != wi]
            on_hand += received
            opening = on_hand
            sold = min(on_hand, true_dem[wi])
            lost = true_dem[wi] - sold
            on_hand -= sold
            in_transit = sum(q for _, q in pipeline)
            po = 0
            if on_hand + in_transit <= rop:
                po = order_qty
                pipeline.append((wi + max(act_lt_w, 1), po))
            # rolling re-estimate of demand for growth/seasonality (planners do update this)
            if wi % 8 == 7:
                avg_w = max(true_dem[max(0, wi - 7):wi + 1].mean(), 0.5)
                safety = int(np.ceil(avg_w * 0.8))
                rop = int(np.ceil(avg_w * plan_lt_w + safety))
                order_qty = int(np.ceil(avg_w * 4))
            inv_rows.append({
                "week_start": wk.date(), "product_id": prod.product_id, "warehouse_id": wh,
                "opening_stock_units": opening - received, "units_received": received,
                "demand_units": int(true_dem[wi]), "units_fulfilled": int(sold),
                "lost_sales_units": int(lost), "closing_stock_units": int(on_hand),
                "reorder_point_units": rop, "purchase_order_units": po,
                "stockout_flag": int(lost > 0),
            })
inventory = pd.DataFrame(inv_rows)
inventory = inventory[(pd.to_datetime(inventory["week_start"]) >= START - pd.Timedelta(days=6))]

# --------------------------------------------------------------------------
# Write
# --------------------------------------------------------------------------
products.drop(columns="_popularity").to_csv(OUT / "products.csv", index=False)
carriers.drop(columns="_base_late_rate").to_csv(OUT / "carriers.csv", index=False)
warehouses.to_csv(OUT / "warehouses.csv", index=False)
customers.assign(signup_date=customers["signup_date"].dt.date).to_csv(OUT / "customers.csv", index=False)
orders.to_csv(OUT / "orders.csv", index=False)
lines.to_csv(OUT / "order_lines.csv", index=False)
inventory.to_csv(OUT / "inventory_weekly.csv", index=False)

for f in sorted(OUT.glob("*.csv")):
    print(f"{f.name:24s} {sum(1 for _ in open(f)) - 1:>8,d} rows")
