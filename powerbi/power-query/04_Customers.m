// Query: Customers
let
    Source  = Csv.Document(File.Contents(DataFolder & "customers.csv"), [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),
    Headers = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),
    Typed   = Table.TransformColumnTypes(Headers, {
                  {"customer_id", type text}, {"city", type text}, {"state", type text},
                  {"region", type text}, {"segment", type text}, {"signup_date", type date}}, "en-US"),
    // Helps the map visual geocode correctly
    MapLocation = Table.AddColumn(Typed, "Map Location", each [city] & ", Germany", type text)
in
    MapLocation
