import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Add scripts directory to path
scripts_dir = Path(__file__).resolve().parent.parent / "skills" / "latest" / "scripts"
sys.path.insert(0, str(scripts_dir))

import stable_version  # noqa: E402


class TestStableVersionHelpers(unittest.TestCase):
    def test_order(self):
        self.assertGreater(stable_version.order("1.10.0"), stable_version.order("1.2.0"))
        self.assertGreater(stable_version.order("v7.0.1"), stable_version.order("v6.9.9"))
        self.assertEqual(stable_version.order("1.0.0"), (1, 0, 0))

    def test_split_line(self):
        self.assertEqual(stable_version.split_line("pkg@5.2"), ("pkg", "5.2"))
        self.assertEqual(stable_version.split_line("@scoped/pkg@24"), ("@scoped/pkg", "24"))
        self.assertEqual(stable_version.split_line("@scoped/pkg"), ("@scoped/pkg", None))
        self.assertEqual(stable_version.split_line("pkg"), ("pkg", None))

    def test_in_line(self):
        self.assertTrue(stable_version.in_line("24.2.0", "24"))
        self.assertTrue(stable_version.in_line("24.2.0", "24.2"))
        self.assertTrue(stable_version.in_line("24.2.0", None))
        self.assertFalse(stable_version.in_line("25.0.0", "24"))

    def test_when(self):
        stamp = stable_version.when("2026-10-01T12:00:00Z")
        self.assertEqual(stamp.tzinfo, timezone.utc)
        self.assertEqual(stamp.year, 2026)
        self.assertEqual(stamp.month, 10)
        self.assertEqual(stamp.day, 1)

    def test_quiet_note(self):
        now = datetime.now(timezone.utc)
        releases_recent = {"1.0.0": now - timedelta(days=30)}
        self.assertIsNone(stable_version.quiet_note(releases_recent))

        releases_quiet = {"1.0.0": now - timedelta(days=400)}
        note = stable_version.quiet_note(releases_quiet)
        self.assertIsNotNone(note)
        self.assertIn("NOTE: no release for", note)

    def test_docker_missing_tag(self):
        res = stable_version.docker("node", 7)
        self.assertIn("ERROR", res)
        self.assertIn("tag required", res)

    def test_choose_cutoff_filtering(self):
        now = datetime.now(timezone.utc)
        # 1.0.0 is 2 days old (inside the 7 day wait), 0.9.0 is 10 days old (outside wait)
        releases = {
            "1.0.0": now - timedelta(days=2),
            "0.9.0": now - timedelta(days=10),
        }
        pick, skipped = stable_version.choose(releases, 7)
        self.assertEqual(pick, "0.9.0")
        self.assertEqual(skipped, ["1.0.0"])

    def test_choose_ceiling(self):
        now = datetime.now(timezone.utc)
        releases = {
            "2.0.0": now - timedelta(days=10),
            "1.9.0": now - timedelta(days=12),
        }
        pick, skipped = stable_version.choose(releases, 7, ceiling="1.9.0")
        self.assertEqual(pick, "1.9.0")
        self.assertEqual(skipped, [])


if __name__ == "__main__":
    unittest.main()
