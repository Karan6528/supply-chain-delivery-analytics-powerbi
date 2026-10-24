# Data dictionary

All files are in `data/`, UTF-8 CSV with a dot as the decimal separator. Dates are `YYYY-MM-DD`. Money is in euros.

## orders.csv — one row per order (45,766 rows)

| Column | Meaning |
|---|---|
| order_id | Unique order ID |
| order_date | Day the customer placed the order |
| customer_id | Links to customers.csv |
| warehouse_id | Warehouse that shipped it |
| carrier_id | Delivery partner used |
| ship_date | Day it left the warehouse (blank if cancelled before shipping) |
| promised_delivery_date | Date shown to the customer at checkout |
| actual_delivery_date | Day it arrived (blank if cancelled) |
| order_status | Delivered, Returned or Cancelled |
| shipping_cost_eur | What UrbanCart paid the carrier |
| late_compensation_eur | €5 apology voucher given when an order was 3+ days late |
| review_score | 1–5 stars; blank if the customer didn't leave a review |

## order_lines.csv — one row per product in an order (73,530 rows)

| Column | Meaning |
|---|---|
| order_id, line_number | Which order and which line in it |
| product_id | Links to products.csv |
| quantity | Units bought |
| unit_price_eur | List price per unit |
| discount_pct | Discount applied (0.10 = 10%) |
| unit_cost_eur | What UrbanCart paid per unit |

## products.csv (120 rows)

| Column | Meaning |
|---|---|
| product_id, product_name, category, supplier | Product details |
| unit_price_eur, unit_cost_eur | Selling price and purchase cost |
| actual_supplier_lead_time_days | How long the supplier really takes to deliver stock |
| planning_lead_time_days | What the stock planning system assumes |

## customers.csv (6,000 rows)

| Column | Meaning |
|---|---|
| customer_id | Unique ID |
| city, state, region | Where they live (region = North / South / East / West) |
| segment | Consumer or Small Business |
| signup_date | When they created an account |

## warehouses.csv (5 rows)

| Column | Meaning |
|---|---|
| warehouse_id, warehouse_city, warehouse_state | Location |
| service_region | Region it ships to (Berlin and Leipzig share East) |
| daily_capacity_orders | Roughly how many orders a day it can handle comfortably |

## carriers.csv (4 rows)

| Column | Meaning |
|---|---|
| carrier_id, carrier_name | Delivery partner (fictional names) |
| service_level | Premium, Standard or Economy |
| promised_transit_days | Days in transit promised to the customer |
| avg_cost_per_shipment_eur | Contract price per parcel |

## inventory_weekly.csv — one row per product, warehouse and week (63,000 rows)

| Column | Meaning |
|---|---|
| week_start | Monday of the week |
| product_id, warehouse_id | Which item where |
| opening_stock_units | Stock at the start of the week |
| units_received | Stock that arrived from the supplier that week |
| demand_units | How many units customers wanted |
| units_fulfilled | How many we could actually sell from stock |
| lost_sales_units | Demand we couldn't serve because we ran out |
| closing_stock_units | Stock at the end of the week |
| reorder_point_units | Stock level that triggers a new purchase order |
| purchase_order_units | Units ordered from the supplier that week (0 if none) |
| stockout_flag | 1 if we ran out at any point that week |

## Columns added in Power BI

| Table | Column | How it's made |
|---|---|---|
| Orders | Delay Days | actual − promised delivery date (negative = early) |
| Orders | Delivery Days | actual delivery − order date |
| Orders | Delivery Status | On Time / Late / Cancelled |
| Orders | Delay Bucket | On time, 1–2, 3–4, 5+ days late, Cancelled |
| Orders | Experience Group | "3+ days late or cancelled" vs "Good experience" |
| Orders | Next Order Date, Days To Next Order | DAX, used for the 90-day reorder rate |
| OrderLines | Line Net Sales, Line COGS | quantity × price × (1 − discount), quantity × cost |
| Products | Lead Time Gap Days | actual − planning lead time |
