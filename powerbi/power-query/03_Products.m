// Query: Products
let
    Source  = Csv.Document(File.Contents(DataFolder & "products.csv"), [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),
    Headers = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),
    Typed   = Table.TransformColumnTypes(Headers, {
                  {"product_id", type text}, {"product_name", type text}, {"category", type text},
                  {"supplier", type text}, {"unit_price_eur", type number}, {"unit_cost_eur", type number},
                  {"actual_supplier_lead_time_days", Int64.Type}, {"planning_lead_time_days", Int64.Type}}, "en-US"),
    LeadGap = Table.AddColumn(Typed, "Lead Time Gap Days", each
                  [actual_supplier_lead_time_days] - [planning_lead_time_days], Int64.Type)
in
    LeadGap
