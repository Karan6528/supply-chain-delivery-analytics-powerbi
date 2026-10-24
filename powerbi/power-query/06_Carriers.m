// Query: Carriers
let
    Source  = Csv.Document(File.Contents(DataFolder & "carriers.csv"), [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),
    Headers = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),
    Typed   = Table.TransformColumnTypes(Headers, {
                  {"carrier_id", type text}, {"carrier_name", type text}, {"service_level", type text},
                  {"promised_transit_days", Int64.Type}, {"avg_cost_per_shipment_eur", type number}}, "en-US")
in
    Typed
