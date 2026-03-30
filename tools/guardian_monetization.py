#!/usr/bin/env python3
"""Simple monetization model for Guardian Layer.

Usage:
  python tools/guardian_monetization.py --scenario conservative
  python tools/guardian_monetization.py --scenario base
  python tools/guardian_monetization.py --scenario aggressive
"""

import argparse
from dataclasses import dataclass


@dataclass(frozen=True)
class Scenario:
    customers: int
    arpa_monthly_usd: float
    gross_margin: float
    churn_annual: float
    cogs_monthly_fixed_usd: float
    sales_marketing_monthly_usd: float


SCENARIOS = {
    "conservative": Scenario(
        customers=12,
        arpa_monthly_usd=800,
        gross_margin=0.72,
        churn_annual=0.18,
        cogs_monthly_fixed_usd=2200,
        sales_marketing_monthly_usd=4500,
    ),
    "base": Scenario(
        customers=30,
        arpa_monthly_usd=1500,
        gross_margin=0.78,
        churn_annual=0.12,
        cogs_monthly_fixed_usd=4000,
        sales_marketing_monthly_usd=9000,
    ),
    "aggressive": Scenario(
        customers=70,
        arpa_monthly_usd=2200,
        gross_margin=0.82,
        churn_annual=0.10,
        cogs_monthly_fixed_usd=9000,
        sales_marketing_monthly_usd=18000,
    ),
}


def calc(s: Scenario) -> dict[str, float]:
    mrr = s.customers * s.arpa_monthly_usd
    arr = mrr * 12

    gross_profit_monthly = mrr * s.gross_margin
    gross_profit_annual = gross_profit_monthly * 12

    opex_monthly = s.cogs_monthly_fixed_usd + s.sales_marketing_monthly_usd
    opex_annual = opex_monthly * 12

    annual_net_before_rnd = gross_profit_annual - opex_annual

    ltv = (s.arpa_monthly_usd * s.gross_margin * 12) / max(s.churn_annual, 0.001)

    break_even_customers = opex_monthly / max(s.arpa_monthly_usd * s.gross_margin, 1)

    return {
        "mrr": mrr,
        "arr": arr,
        "gross_profit_annual": gross_profit_annual,
        "opex_annual": opex_annual,
        "annual_net_before_rnd": annual_net_before_rnd,
        "ltv": ltv,
        "break_even_customers": break_even_customers,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenario", choices=SCENARIOS.keys(), default="base")
    args = parser.parse_args()

    s = SCENARIOS[args.scenario]
    result = calc(s)

    print(f"Scenario: {args.scenario}")
    print(f"Customers: {s.customers}")
    print(f"ARPA (monthly): ${s.arpa_monthly_usd:,.0f}")
    print(f"MRR: ${result['mrr']:,.0f}")
    print(f"ARR: ${result['arr']:,.0f}")
    print(f"Gross profit (annual): ${result['gross_profit_annual']:,.0f}")
    print(f"Operating costs (annual): ${result['opex_annual']:,.0f}")
    print(f"Annual net before R&D/headcount: ${result['annual_net_before_rnd']:,.0f}")
    print(f"Indicative LTV: ${result['ltv']:,.0f}")
    print(f"Break-even customers: {result['break_even_customers']:.1f}")


if __name__ == "__main__":
    main()
