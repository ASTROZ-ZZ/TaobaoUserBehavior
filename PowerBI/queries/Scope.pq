let
    Source = #table({"AllProducts", "EligibleProducts", "TrafficThreshold", "RateThreshold", "HighActiveLowBuyUsers", "HighActiveNeverBuyCartUsers", "MultiBuyDayUsers", "AllBuyers", "PeakPVHour", "PeakBuyHour", "PeakOnsetHour", "PrioritySKU"}, {
      {4161138,110545,344,0.0067567568,346872,117340,370274,672404,21,21,10,"812879"}
    }),
    Typed = Table.TransformColumnTypes(Source, {{"AllProducts", Int64.Type}, {"EligibleProducts", Int64.Type}, {"TrafficThreshold", Int64.Type}, {"RateThreshold", type number}, {"HighActiveLowBuyUsers", Int64.Type}, {"HighActiveNeverBuyCartUsers", Int64.Type}, {"MultiBuyDayUsers", Int64.Type}, {"AllBuyers", Int64.Type}, {"PeakPVHour", Int64.Type}, {"PeakBuyHour", Int64.Type}, {"PeakOnsetHour", Int64.Type}, {"PrioritySKU", type text}}, "en-US")
in
    Typed