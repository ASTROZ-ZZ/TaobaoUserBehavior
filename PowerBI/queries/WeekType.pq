let
    Source = #table({"DayType", "Days", "PV", "ActiveUserDays", "BuyerUserDays"}, {
      {"工作日",5,46172898,3609009,719098},
      {"周末",4,43487790,3359535,616382}
    }),
    Typed = Table.TransformColumnTypes(Source, {{"DayType", type text}, {"Days", Int64.Type}, {"PV", Int64.Type}, {"ActiveUserDays", Int64.Type}, {"BuyerUserDays", Int64.Type}}, "en-US")
in
    Typed