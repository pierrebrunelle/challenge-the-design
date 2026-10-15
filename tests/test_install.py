"""Exercise the actual standalone installer in temporary destinations."""

from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / 'skills/challenge-the-design'


class InstallTests(unittest.TestCase):
    def run_installer(self, *arguments: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(['bash', str(ROOT / 'install.sh'), *arguments], capture_output=True, text=True, check=False)

    def test_complete_skill_is_copied_to_a_destination_with_spaces(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            for platform in ('codex-skill', 'cursor-skill', 'claude-code', 'antigravity'):
                with self.subTest(platform=platform):
                    destination = Path(temporary) / 'path with spaces' / platform
                    result = self.run_installer('--platform', platform, '--destination', str(destination))
                    self.assertEqual(result.returncode, 0, result.stderr)
                    source_files = {p.relative_to(SOURCE): p.read_bytes() for p in SOURCE.rglob('*') if p.is_file()}
                    installed = {p.relative_to(destination): p.read_bytes() for p in destination.rglob('*') if p.is_file()}
                    self.assertEqual(installed, source_files)

    def test_existing_installation_is_left_untouched(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary) / 'skill'
            destination.mkdir()
            marker = destination / 'my-local-change.md'
            marker.write_text('keep this')
            result = self.run_installer('--platform', 'codex-skill', '--destination', str(destination))
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(list(destination.iterdir()), [marker])
            self.assertEqual(marker.read_text(), 'keep this')

    def test_symlink_destination_is_not_followed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / 'unrelated'
            target.mkdir()
            destination = Path(temporary) / 'skill'
            destination.symlink_to(target, target_is_directory=True)
            result = self.run_installer('--platform', 'codex-skill', '--destination', str(destination))
            self.assertNotEqual(result.returncode, 0)
            self.assertTrue(destination.is_symlink())
            self.assertEqual(list(target.iterdir()), [])

    def test_invalid_arguments_do_not_create_a_destination(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary) / 'skill'
            for arguments in (
                ('--platform', 'unknown', '--destination', str(destination)),
                ('--platform',), ('--destination',), ('--typo',),
            ):
                with self.subTest(arguments=arguments):
                    result = self.run_installer(*arguments)
                    self.assertEqual(result.returncode, 2)
                    self.assertFalse(destination.exists())


if __name__ == '__main__':
    unittest.main()
