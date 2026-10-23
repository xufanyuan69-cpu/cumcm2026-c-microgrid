"""Validate NPZ SOC/nonnegativity and report costs against frozen references."""
import argparse
import csv
import json
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output-dir', type=Path, default=ROOT / 'results' / 'risk')
    p.add_argument('--variant', choices=('risk', 'old'), default='risk')
    p.add_argument('--report', type=Path, help='Write a machine-readable validation report.')
    args = p.parse_args()
    directory = args.output_dir.resolve() / 'analysis_outputs'
    if not directory.is_dir():
        p.error(f'Missing {directory}; run the solvers first.')
    found = 0
    report = []
    refs = {r['model']: r for r in csv.DictReader(
        (ROOT / 'reference_results' / 'model_summary.csv').open(encoding='utf-8-sig'))}
    for name, model, emergency in [('q2', 'Q2', 'emergency_cost'),
                                    ('q3', 'Q3-risk', 'em_cost'),
                                    ('q4_2', 'Q4-2', 'emergency_cost'),
                                    ('q4_3', 'Q4-3-risk', 'em_cost')]:
        path = directory / f'{name}_results.npz'
        if not path.is_file():
            continue
        if args.variant == 'old':
            model = model.replace('-risk', '-old')
        found += 1
        with np.load(path) as a:
            for key in a.files:
                if a[key].dtype.kind in 'fiu' and not np.isfinite(a[key]).all():
                    raise AssertionError(f'{name}: non-finite {key}')
            s, c, d = a['S'], a['C'], a['D']
            assert s.min() >= 1200 - 1e-5 and s.max() <= 10800 + 1e-5, name
            prev = np.concatenate([np.full((len(s), 1), 6000.), s[:, :-1]], axis=1)
            residual = float(np.max(np.abs(s - prev - .9*c + d/.9)))
            assert residual < 1e-5, (name, residual)
            assert np.max(np.abs(s[:, -1] - 6000)) < 1e-5, name
            for key in ('P', 'C', 'D', 'E'):
                assert a[key].min() >= -1e-6, (name, key)
            total = a['plan_cost'] + a[emergency]
            if 'adj_cost' in a:
                total = total + a['adj_cost']
            ref = float(refs[model]['total_cost_mean_yuan_per_day'])
            print(f'{model}: days={len(s)}, total/day={total.mean():.4f}, '
                  f'reference={ref:.4f}, delta={total.mean()-ref:+.4f}, '
                  f'SOC residual={residual:.3g}')
            report.append({'model': model, 'days': len(s),
                           'total_cost_mean_yuan_per_day': float(total.mean()),
                           'reference_total_cost': ref,
                           'cost_delta': float(total.mean()) - ref,
                           'emergency_energy_mean_kWh_per_day': float(a['E'].sum(axis=1).mean()),
                           'emergency_days': int((a['E'].sum(axis=1) > 1e-6).sum()),
                           'soc_residual_max_kWh': residual})
    if not found:
        p.error('No yearly result arrays found.')
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n',
                               encoding='utf-8')
    # A cost difference is reported rather than hidden: degenerate optima and
    # solver versions can change the chosen plan without violating constraints.


if __name__ == '__main__':
    main()
