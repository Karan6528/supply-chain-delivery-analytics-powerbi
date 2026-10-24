// Query: Inventory  (weekly snapshot per product x warehouse)
let
    Source  = Csv.Document(File.Contents(DataFolder & "inventory_weekly.csv"), [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),
    Headers = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),
    Typed   = Table.TransformColumnTypes(Headers, {
                  {"week_start", type date}, {"product_id", type text}, {"warehouse_id", type text},
                  {"opening_stock_units", Int64.Type}, {"units_received", Int64.Type},
                  {"demand_units", Int64.Type}, {"units_fulfilled", Int64.Type},
                  {"lost_sales_units", Int64.Type}, {"closing_stock_units", Int64.Type},
                  {"reorder_point_units", Int64.Type}, {"purchase_order_units", Int64.Type},
                  {"stockout_flag", Int64.Type}}, "en-US")
in
    Typed
