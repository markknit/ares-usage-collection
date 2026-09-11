import json
import pathlib
import subprocess
import tempfile
import unittest

SCRIPT = pathlib.Path(__file__).resolve().parents[1] / 'central-monitoring' / 'process_incoming.py'


class ProcessorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        root = pathlib.Path(self.temp.name)
        self.incoming = root / 'incoming'
        self.archive = root / 'archive'
        self.rejected = root / 'rejected'
        self.state = root / 'state.json'
        self.incoming.mkdir()

    def tearDown(self):
        self.temp.cleanup()

    def run_processor(self, extra=None):
        cmd = [
            'python3', str(SCRIPT),
            '--incoming', str(self.incoming),
            '--archive', str(self.archive),
            '--state', str(self.state),
            '--rejected', str(self.rejected),
        ]
        if extra:
            cmd.extend(extra)
        return subprocess.run(cmd, text=True, capture_output=True)

    def write_valid(self, name, body='kind,value\nquarter,3\n'):
        (self.incoming / name).write_text(body, encoding='utf-8')

    def test_accepts_and_archives_valid_file(self):
        name = 'ARES_USAGE_ARES-S0001_2026-Q3-MID_2026-09-10_09-30-00.csv'
        self.write_valid(name)
        result = self.run_processor()
        self.assertEqual(result.returncode, 0, result.stderr)
        summary = json.loads(result.stdout)
        self.assertEqual(summary['processed'], [name])
        self.assertTrue((self.archive / '2026-Q3-MID' / 'ARES-S0001' / name).exists())
        self.assertFalse((self.incoming / name).exists())
        state = json.loads(self.state.read_text())
        self.assertEqual(len(state['sha256']), 1)

    def test_discards_exact_content_duplicate(self):
        first = 'ARES_USAGE_ARES-S0001_2026-Q3-MID_2026-09-10_09-30-00.csv'
        second = 'ARES_USAGE_ARES-S0001_2026-Q3-MID_2026-09-10_09-31-00.csv'
        self.write_valid(first)
        self.assertEqual(self.run_processor().returncode, 0)
        self.write_valid(second)
        result = self.run_processor()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['duplicates'], [second])
        self.assertFalse((self.incoming / second).exists())

    def test_quarantines_invalid_filename(self):
        bad = self.incoming / 'prepare_due_usage_upload.php'
        bad.write_text('not csv', encoding='utf-8')
        result = self.run_processor()
        self.assertEqual(result.returncode, 2)
        summary = json.loads(result.stdout)
        self.assertEqual(summary['rejected'][0]['reason'], 'invalid filename')
        self.assertTrue((self.rejected / 'prepare_due_usage_upload.php').exists())

    def test_quarantines_malformed_csv(self):
        name = 'ARES_USAGE_ARES-S0001_2026-Q3-MID_2026-09-10_09-30-00.csv'
        (self.incoming / name).write_text('not-a-csv', encoding='utf-8')
        result = self.run_processor()
        self.assertEqual(result.returncode, 2)
        self.assertEqual(json.loads(result.stdout)['rejected'][0]['reason'], 'not a plausible CSV')
        self.assertTrue((self.rejected / name).exists())

    def test_quarantines_archive_name_conflict(self):
        name = 'ARES_USAGE_ARES-S0001_2026-Q3-MID_2026-09-10_09-30-00.csv'
        dest = self.archive / '2026-Q3-MID' / 'ARES-S0001' / name
        dest.parent.mkdir(parents=True)
        dest.write_text('kind,value\nquarter,old\n', encoding='utf-8')
        self.write_valid(name, 'kind,value\nquarter,new\n')
        result = self.run_processor()
        self.assertEqual(result.returncode, 2)
        self.assertEqual(json.loads(result.stdout)['rejected'][0]['reason'], 'archive filename conflict')
        self.assertTrue((self.rejected / name).exists())

    def test_runs_report_command_once_when_processed(self):
        marker = pathlib.Path(self.temp.name) / 'report-ran'
        name = 'ARES_USAGE_ARES-S0001_AUTO_2026-09-10_09-30-00.csv'
        self.write_valid(name)
        result = self.run_processor(['--report-command', f'touch {marker}'])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(marker.exists())


if __name__ == '__main__':
    unittest.main()
