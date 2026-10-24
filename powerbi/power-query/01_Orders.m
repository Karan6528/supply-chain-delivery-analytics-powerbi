// Query: Orders  (one row per order / shipment)
// Culture "en-US" is set on type changes so decimals parse correctly on German/EU Windows locales.
let
    Source   = Csv.Document(File.Contents(DataFolder & "orders.csv"), [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),
    Headers  = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),
    Blanks   = Table.ReplaceValue(Headers, "", null, Replacer.ReplaceValue,
                   {"ship_date", "actual_delivery_date", "review_score"}),
    Typed    = Table.TransformColumnTypes(Blanks, {
                   {"order_id", type text}, {"order_date", type date}, {"customer_id", type text},
                   {"warehouse_id", type text}, {"carrier_id", type text}, {"ship_date", type date},
                   {"promised_delivery_date", type date}, {"actual_delivery_date", type date},
                   {"order_status", type text}, {"shipping_cost_eur", type number},
                   {"late_compensation_eur", type number}, {"review_score", Int64.Type}}, "en-US"),

    // Days late vs. promise (negative = early, null = cancelled / never delivered)
    DelayDays = Table.AddColumn(Typed, "Delay Days", each
                   if [actual_delivery_date] = null then null
                   else Duration.Days([actual_delivery_date] - [promised_delivery_date]), Int64.Type),

    DeliveryDays = Table.AddColumn(DelayDays, "Delivery Days", each
                   if [actual_delivery_date] = null then null
                   else Duration.Days([actual_delivery_date] - [order_date]), Int64.Type),

    DeliveryStatus = Table.AddColumn(DeliveryDays, "Delivery Status", each
                   if [order_status] = "Cancelled" then "Cancelled"
                   else if [Delay Days] <= 0 then "On Time" else "Late", type text),

    IsLateOrCancelled = Table.AddColumn(DeliveryStatus, "Is Late Or Cancelled", each
                   [Delivery Status] <> "On Time", type logical),

    DelayBucket = Table.AddColumn(IsLateOrCancelled, "Delay Bucket", each
                   if [order_status] = "Cancelled" then "Cancelled"
                   else if [Delay Days] <= 0 then "On time"
                   else if [Delay Days] <= 2 then "1-2 days late"
                   else if [Delay Days] <= 4 then "3-4 days late"
                   else "5+ days late", type text),

    // Numeric sort key for the bucket (Column tools > Sort by column)
    DelaySortKey = Table.AddColumn(DelayBucket, "Delay Bucket Sort", each
                   List.PositionOf({"On time", "1-2 days late", "3-4 days late", "5+ days late", "Cancelled"}, [Delay Bucket]),
                   Int64.Type),

    Experience = Table.AddColumn(DelaySortKey, "Experience Group", each
                   if [order_status] = "Cancelled" or ([Delay Days] <> null and [Delay Days] >= 3)
                   then "3+ days late or cancelled" else "Good experience", type text)
in
    Experience
