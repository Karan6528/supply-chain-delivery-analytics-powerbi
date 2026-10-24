// Query: OrderLines  (one row per product in an order)
let
    Source  = Csv.Document(File.Contents(DataFolder & "order_lines.csv"), [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),
    Headers = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),
    Typed   = Table.TransformColumnTypes(Headers, {
                  {"order_id", type text}, {"line_number", Int64.Type}, {"product_id", type text},
                  {"quantity", Int64.Type}, {"unit_price_eur", type number},
                  {"discount_pct", type number}, {"unit_cost_eur", type number}}, "en-US"),
    NetSales = Table.AddColumn(Typed, "Line Net Sales", each
                  [quantity] * [unit_price_eur] * (1 - [discount_pct]), Currency.Type),
    Cogs     = Table.AddColumn(NetSales, "Line COGS", each [quantity] * [unit_cost_eur], Currency.Type)
in
    Cogs
