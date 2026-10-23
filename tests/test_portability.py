import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'code'))
from dispatch_execution import execute_fixed_plan
from project_paths import prepare_result, output_directory


class PortabilityTests(unittest.TestCase):
    def test_dispatch_balances_and_terminal(self):
        plan = np.array([10., 10., 10.])
        load = np.array([90., 60., 30.])
        pv = np.zeros(3)
        c, d, e, r, s = execute_fixed_plan(plan, load, pv, np.ones(3),
                                          6000., target_soc=6000.)
        np.testing.assert_allclose(plan + pv/6 + d + e, load/6 + c + r,
                                   atol=1e-7)
        np.testing.assert_allclose(s, np.r_[6000., s[:-1]] + .9*c - d/.9,
                                   atol=1e-7)
        self.assertAlmostEqual(s[-1], 6000.)

    def test_template_is_copied_not_modified(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            template = root / 'inputs' / '附件5' / 'synthetic.xlsx'
            template.parent.mkdir(parents=True)
            template.write_bytes(b'unchanged template')
            with patch.dict(os.environ, CUMCM_DATA_DIR=str(root / 'inputs'),
                            CUMCM_OUTPUT_DIR=str(root / 'outputs')):
                result = prepare_result('synthetic.xlsx')
                result.write_bytes(b'generated result')
                self.assertEqual(template.read_bytes(), b'unchanged template')
                self.assertEqual(result.parent, root / 'outputs')

    def test_output_must_not_write_into_inputs(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with patch.dict(os.environ, CUMCM_DATA_DIR=str(root),
                            CUMCM_OUTPUT_DIR=str(root / 'nested')):
                with self.assertRaises(ValueError):
                    output_directory()


if __name__ == '__main__':
    unittest.main()
