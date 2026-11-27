let
    Source = #table({"Events", "Users", "PV", "Browsers", "FavoriteUsers", "CartUsers", "Buyers", "BuyLogs"}, {
      {100095231,987991,89660688,984105,389823,738996,672404,2015839}
    }),
    Typed = Table.TransformColumnTypes(Source, {{"Events", Int64.Type}, {"Users", Int64.Type}, {"PV", Int64.Type}, {"Browsers", Int64.Type}, {"FavoriteUsers", Int64.Type}, {"CartUsers", Int64.Type}, {"Buyers", Int64.Type}, {"BuyLogs", Int64.Type}}, "en-US")
in
    Typed