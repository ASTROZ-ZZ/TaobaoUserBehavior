let
    Source = #table({"Behavior", "HistoryGroup", "Eligible", "Converted"}, {
      {"加购","prior_active_0to2",2176095,93062},
      {"加购","prior_active_3plus",2463016,90765},
      {"收藏","prior_active_0to2",1157761,41134},
      {"收藏","prior_active_3plus",1323878,44527},
      {"浏览","prior_active_0to2",29694345,381567},
      {"浏览","prior_active_3plus",32019194,353870}
    }),
    Typed = Table.TransformColumnTypes(Source, {{"Behavior", type text}, {"HistoryGroup", type text}, {"Eligible", Int64.Type}, {"Converted", Int64.Type}}, "en-US")
in
    Typed