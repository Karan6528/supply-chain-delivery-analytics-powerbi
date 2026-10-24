// Query: Warehouses
let
    Source  = Csv.Document(File.Contents(DataFolder & "warehouses.csv"), [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),
    Headers = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),
    Typed   = Table.TransformColumnTypes(Headers, {
                  {"warehouse_id", type text}, {"warehouse_city", type text}, {"warehouse_state", type text},
                  {"service_region", type text}, {"daily_capacity_orders", Int64.Type}}, "en-US")
in
    Typed
