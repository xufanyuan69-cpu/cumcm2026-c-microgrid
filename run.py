"""Run preserved C-problem models from any working directory."""
import argparse
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
QUESTIONS = ('q1', 'q2', 'q3', 'q4_2', 'q4_3')
FILES = {
    'q1': ('附件1.xlsx',),
    'q2': ('附件1.xlsx', '附件2.xlsx'),
    'q3': ('附件1.xlsx', '附件2.xlsx', '附件3.xlsx'),
    'q4_2': ('附件1.xlsx', '附件2.xlsx', '附件4.xlsx'),
    'q4_3': ('附件1.xlsx', '附件2.xlsx', '附件3.xlsx', '附件4.xlsx'),
}
RESULTS = dict(zip(QUESTIONS, ('result1.xlsx', 'result2.xlsx', 'result3.xlsx',
                              'result4-2.xlsx', 'result4-3.xlsx')))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--question', choices=(*QUESTIONS, 'all'), default='all')
    parser.add_argument('--data-dir', type=Path, default=ROOT / 'data' / 'raw')
    parser.add_argument('--output-dir', type=Path)
    parser.add_argument('--variant', choices=('risk', 'old'), default='risk')
    parser.add_argument('--check-inputs', action='store_true')
    args = parser.parse_args()
    questions = QUESTIONS if args.question == 'all' else (args.question,)
    data = args.data_dir.resolve()
    # Separate old/risk runs so that one version never replaces the other.
    output = (args.output_dir or ROOT / 'results' /
              ('old' if args.variant == 'old' else 'risk')).resolve()
    env = os.environ.copy()
    env.update(CUMCM_DATA_DIR=str(data), CUMCM_OUTPUT_DIR=str(output),
               CUMCM_RISK_AWARE='1' if args.variant == 'risk' else '0',
               PYTHONIOENCODING='utf-8')
    sys.path.insert(0, str(ROOT / 'code'))
    from project_paths import find_template
    # Helpers use this process's configuration as well as child environments.
    os.environ.update({k: env[k] for k in
                       ('CUMCM_DATA_DIR', 'CUMCM_OUTPUT_DIR', 'CUMCM_RISK_AWARE')})
    missing = sorted({str(data / f) for q in questions for f in FILES[q]
                      if not (data / f).is_file()})
    for q in questions:
        try:
            find_template(RESULTS[q])
        except FileNotFoundError as exc:
            missing.append(str(exc))
    if missing:
        parser.exit(2, 'Missing inputs:\n' + '\n'.join(missing) +
                    '\nSee data/README.md.\n')
    print(f'Inputs: {data}\nOutputs: {output}\nVariant: {args.variant}', flush=True)
    if args.check_inputs:
        return
    for q in questions:
        subprocess.run([sys.executable, str(ROOT / 'code' / f'solve_{q}.py')],
                       cwd=ROOT, env=env, check=True)


if __name__ == '__main__':
    main()
