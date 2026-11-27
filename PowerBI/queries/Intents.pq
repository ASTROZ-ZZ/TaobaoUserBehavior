let
    Source = #table({"Segment", "Intent", "Users"}, {
      {"高活跃＋低购买","仅浏览及其他",19135},
      {"高活跃＋低购买","单日购买",185159},
      {"高活跃＋低购买","未购但加购",117340},
      {"高活跃＋低购买","未购未加购但收藏",25238}
    }),
    Typed = Table.TransformColumnTypes(Source, {{"Segment", type text}, {"Intent", type text}, {"Users", Int64.Type}}, "en-US")
in
    Typed