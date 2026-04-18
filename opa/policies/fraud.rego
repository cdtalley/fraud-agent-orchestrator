package fraud

# Rule: fraud/result — POST /v1/data/fraud/result  body: {"input": {...}}

result = x {
  xs := [msg | deny[msg]]
  count(xs) == 0
  x := {"allow": true, "deny_reasons": []}
}

result = x {
  xs := [msg | deny[msg]]
  count(xs) > 0
  x := {"allow": false, "deny_reasons": xs}
}

deny[msg] {
  input.alert.country == "KP"
  msg := "opa_blocked_country_kp"
}
