let
    Source = #table({"Behavior", "Eligible", "Converted", "Censored", "NotConverted"}, {
      {"加购",4639111,183827,747473,4455284},
      {"收藏",2481639,85661,388338,2395978},
      {"浏览",61713539,735437,9301653,60978102}
    }),
    Typed = Table.TransformColumnTypes(Source, {{"Behavior", type text}, {"Eligible", Int64.Type}, {"Converted", Int64.Type}, {"Censored", Int64.Type}, {"NotConverted", Int64.Type}}, "en-US")
in
    Typed