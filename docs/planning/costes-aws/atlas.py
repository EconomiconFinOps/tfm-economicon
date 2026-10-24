"""Atlas increment over the preserved 22-Oct catalog; no network or AWS calls."""
from decimal import Decimal as D
import json
from pathlib import Path
from calcular import calculate, P, FX


def scenario(cycles, hours):
    base = calculate('atlas', hours=hours, cycles=cycles)
    # One 0.5vCPU/1GiB task, one secret, two backend Cloud Map registrations,
    # 0.5 GB-month extra image retention and 0.1 GB extra logs. Existing RDS.
    increment = (D(str(hours)) * (P['cpu']/2 + P['memory'])
                 + D(str(hours))/730 * (P['secret'] + 2*P['cloudmap'])
                 + D('.5') * P['ecr'] + D('.1') * P['log_ingest']) / FX
    subtotal = D(base['total_eur']) + increment
    reserve = subtotal * D('1.21') * D('1.2')
    return dict(cycles=cycles, total_billable_hours=hours, baseline_eur=str(D(base['total_eur']).quantize(D('.01'))),
                monitoring_increment_eur=str(increment.quantize(D('.001'))),
                subtotal_eur=str(subtotal.quantize(D('.01'))),
                with_assumed_vat21_and_margin20_eur=str(reserve.quantize(D('.01'))),
                within_30_eur=reserve <= 30)


if __name__ == '__main__':
    report = dict(verified='2026-10-24', prices_verified='2026-10-22',
        reference='ffb5d307772f697cffb8b1e73e6330250e093601',
        assumptions='Existing catalog hypotheses, no credits/free tier; VAT21 is a conservative assumption, not tax advice. Billing and cleanup may exceed estimates.',
        scenarios=[scenario(1, 2), scenario(1, 4), scenario(3, 3), scenario(3, 6)])
    Path(__file__).with_name('atlas-resultados.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(report, indent=2))
