# Build Guide — step by step in Power BI Desktop

Time needed: about 3–4 hours the first time. Follow the steps in order; every piece of code you need is in `powerbi/`.

> **Requirements:** Power BI Desktop (free, Windows; get it from the Microsoft Store). On a Mac, use a Windows VM or Parallels, or the free Power BI service in the browser for viewing only.

---

## Step 1 — Load the data with Power Query

1. Open Power BI Desktop → **Blank report**.
2. **Home → Transform data** to open the Power Query Editor.
3. Create the folder parameter: **Manage Parameters → New Parameter**
   - Name `DataFolder`, Type `Text`, Current value = full path to the repo's `data` folder **with a trailing `\`** (e.g. `C:\Users\karan\supply-chain-delivery-analytics-powerbi\data\`).
4. For each file `01_Orders.m` … `07_Inventory.m` in `powerbi/power-query/`:
   - **New Source → Blank Query**, then **Advanced Editor**, delete everything, paste the file's contents, **Done**.
   - Rename the query to the name in the file header: `Orders`, `OrderLines`, `Products`, `Customers`, `Warehouses`, `Carriers`, `Inventory`.
5. **Close & Apply.** You should see 45,766 orders and 73,530 order lines.

> Why `"en-US"` in the type steps? On German/EU Windows, Power BI reads `7.90` as 790 unless you tell it the file uses a dot as decimal separator. Worth mentioning in interviews — it's a classic real-world bug.

## Step 2 — Date table

1. **Modeling → New table**, paste `powerbi/dax/01_date_table.dax`.
2. Select the table → **Table tools → Mark as date table** → column `Date`.
3. In Data view, select `Month` → **Column tools → Sort by column → Month Number**. Same for `Day of Week` → `Day of Week Number`.
4. In Orders, sort `Delay Bucket` by `Delay Bucket Sort`.

## Step 3 — Relationships (Model view)

Delete anything Power BI auto-detected that doesn't match this, then drag to create:

| From (many side)          | To (one side)            | Cardinality | Filter direction |
|---------------------------|--------------------------|-------------|------------------|
| `OrderLines[order_id]`    | `Orders[order_id]`       | Many → One  | Single           |
| `OrderLines[product_id]`  | `Products[product_id]`   | Many → One  | Single           |
| `Orders[customer_id]`     | `Customers[customer_id]` | Many → One  | Single           |
| `Orders[warehouse_id]`    | `Warehouses[warehouse_id]` | Many → One | Single          |
| `Orders[carrier_id]`      | `Carriers[carrier_id]`   | Many → One  | Single           |
| `Orders[order_date]`      | `Date[Date]`             | Many → One  | Single           |
| `Inventory[product_id]`   | `Products[product_id]`   | Many → One  | Single           |
| `Inventory[warehouse_id]` | `Warehouses[warehouse_id]` | Many → One | Single          |
| `Inventory[week_start]`   | `Date[Date]`             | Many → One  | Single           |

Hide the ID/foreign-key columns on the fact tables (right-click → *Hide in report view*) so report users only see dimension fields.

> Note: Products filter OrderLines and Inventory, but not Orders (delivery KPIs). That's intentional — delivery happens per order, not per product. Use Category only on sales and inventory visuals.

## Step 4 — Calculated columns and measures

1. Select `Orders` → **New column** for each of the three columns in `powerbi/dax/02_calculated_columns.dax`.
2. **Home → Enter data** → name the table `_Measures` → Load. (Delete the default column after adding your first measure.)
3. Add every measure from `powerbi/dax/03_measures.dax` (**New measure**, paste one at a time). Set formats as noted in the `// [...]` comments and put each in its **Display folder** (Model view → Properties).
4. Create the what-if parameter: **Modeling → New parameter → Numeric range**: Name `Shift From CargoWay`, Decimal, 0 → 1, increment 0.05, default 0.5. Then add the What-if measures.

**Check your numbers** against `python scripts/validate_kpis.py` (all years, no filters):

| Measure | Expected |
|---|---|
| Total Orders | 45,766 |
| Net Sales | ≈ €8,035,444 |
| On-Time Delivery % | 86.3% |
| Avg Review Score | 4.18 |
| Cost of Late Delivery | ≈ €194,884 |
| Lost Sales Revenue | ≈ €1,541,994 |
| Fill Rate % | 90.9% |
| Reorder Rate 90d – Good / Bad | 80.4% / 67.1% |

## Step 5 — Theme

**View → Themes → Browse for themes** → `powerbi/urbancart_theme.json`. Set page size to 16:9 (1280 × 720).

## Step 6 — Build the 5 report pages

Keep the same layout on every page: a title bar on top, slicers (Year, Region, Season) on the left or top right, KPI cards in a row, visuals below. Use **View → Sync slicers** so Year/Region carry across pages.

### Page 1 — Executive Overview
*Question: how is the business doing, and what is lateness costing us?*
- **KPI cards (row of 6):** Net Sales (+ Net Sales YoY % as reference label), Total Orders, On-Time Delivery %, Avg Review Score, Cost of Late Delivery, Lost Sales Revenue.
- **Line chart:** X = `Date[Year Month]`, Y = On-Time Delivery %, add constant line at 0.92 (Analytics pane) labelled *Target*. The Nov–Dec dips are the story.
- **Column chart:** Net Sales by `Date[Year Month]`.
- **Bar chart:** Cost of Late Delivery by `Carriers[carrier_name]`.
- **Text box:** 3 bullet key findings (copy from the README once you've confirmed them).

### Page 2 — Delivery Performance
*Question: where do late deliveries come from?*
- **Clustered bar:** On-Time Delivery % by carrier; conditional formatting on bar colour → Field value → `OTD Color`.
- **Matrix heatmap:** Rows = `Warehouses[warehouse_city]`, Columns = `Date[Year Month]`, Values = On-Time Delivery %; conditional formatting → background colour scale (red → green). Leipzig in Nov/Dec will jump out.
- **Clustered column:** Regular Season OTD % vs Peak Season OTD % by warehouse.
- **100% stacked bar:** Total Orders by carrier, legend = `Orders[Delay Bucket]`.
- **Card:** `Dynamic Title - Delivery`.

### Page 3 — Cost & Carrier Economics
*Question: is the cheapest carrier actually cheapest?*
- **Table:** carrier_name, Shipping Cost per Order, Late Cost per Order, True Cost per Order, On-Time Delivery %, Cancellation Rate %. Data bars on True Cost per Order.
- **Scatter:** X = Shipping Cost per Order, Y = Late Delivery %, Size = Total Orders, Details = carrier_name.
- **Stacked column:** Shipping Cost per Order + Late Cost per Order by carrier (shows CargoWay's hidden cost).
- **What-if panel:** `Shift From CargoWay` slicer + cards for Projected Annual Savings and Projected Late Orders Avoided per Year.

### Page 4 — Customer Impact
*Question: do late deliveries hurt customers and future revenue?*
- **Column chart:** Avg Review Score by `Orders[Delay Bucket]`.
- **Line + column combo:** Total Orders (column) and Return Rate % (line) by Delay Bucket.
- **Clustered bar:** Reorder Rate 90d by `Orders[Experience Group]` + card for Reorder Gap (pp).
- **Map (or filled map):** Location = `Customers[Map Location]`, bubble size = Total Orders, colour = Late Delivery %. *(Enable maps in File → Options → Security if prompted.)*

### Page 5 — Inventory & Stockouts
*Question: where are we losing sales because items are out of stock, and why?*
- **KPI cards:** Fill Rate %, Lost Sales Revenue, Stockout Week %, Lead Time Gap (days).
- **Bar chart:** Lost Sales Revenue by `Products[category]`.
- **Clustered bar:** Avg Actual Lead Time vs Avg Planning Lead Time by category — the root cause.
- **Line chart:** Lost Sales Revenue by `Date[Week Start]`, legend = category (filter to top 3).
- **Table:** Top 10 products by Lost Sales Revenue (product_name, category, supplier, Fill Rate %, Lost Sales Revenue) using Top N filter.

### Finishing touches (these make it portfolio-grade)
- A **tooltip page** (Page settings → Allow use as tooltip) showing OTD % trend and Avg Review Score, assigned to the carrier and warehouse visuals.
- A **drill-through page** on carrier_name with that carrier's monthly OTD and warehouse breakdown.
- **Bookmarks + buttons** for a "Show recommendations" panel on Page 1.
- Consistent titles phrased as insights ("Leipzig misses 37% of deliveries in peak season"), not labels ("OTD by warehouse").

## Step 7 — Save for GitHub

1. **File → Save as** → `powerbi/UrbanCart_SupplyChain.pbix`.
2. *(Recommended)* Also **File → Save as → Power BI project (.pbip)** into `powerbi/pbip/`. The .pbip format saves the model and report as text files, so GitHub shows real diffs of your DAX — a strong signal to reviewers. (If the option is missing: File → Options → Preview features → *Power BI Project (.pbip) save option*.)
3. **File → Export → Export to PDF** → `docs/UrbanCart_Dashboard.pdf`.
4. Take a screenshot of each page (Windows: `Win + Shift + S`) and save them in `images/` as `01_overview.png` … `05_inventory.png`. The README already points to these names.
5. *(Optional)* Record a 30–60s GIF walking through the slicers (ScreenToGif is free) → `images/demo.gif`.
