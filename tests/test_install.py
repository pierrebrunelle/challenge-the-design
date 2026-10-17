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


class ValidateTests(unittest.TestCase):
    def copy_package(self, destination: Path) -> Path:
        import shutil
        target = destination / 'pkg'
        shutil.copytree(ROOT, target, ignore=shutil.ignore_patterns('.git', '__pycache__'))
        return target

    def test_validate_rejects_version_description_keyword_and_security_drift(self) -> None:
        import json
        import sys
        sys.path.insert(0, str(ROOT / 'scripts'))
        from validate_plugin import validate

        self.assertEqual(validate(ROOT), [])
        with tempfile.TemporaryDirectory() as temporary:
            pkg = self.copy_package(Path(temporary))
            pkg_json = json.loads((pkg / 'package.json').read_text(encoding='utf-8'))
            pkg_json['version'] = '0.9.9'
            pkg_json['keywords'] = ['pi-package']
            (pkg / 'package.json').write_text(json.dumps(pkg_json), encoding='utf-8')
            cursor_json = json.loads((pkg / '.cursor-plugin/plugin.json').read_text(encoding='utf-8'))
            cursor_json['description'] = 'stale description'
            (pkg / '.cursor-plugin/plugin.json').write_text(json.dumps(cursor_json), encoding='utf-8')
            (pkg / 'SECURITY.md').write_text('Version 0.1.x is the current supported series.\n', encoding='utf-8')
            errors = validate(pkg)
            self.assertIn('package.json: inconsistent version', errors)
            self.assertIn('package.json: inconsistent keywords', errors)
            self.assertIn('.cursor-plugin/plugin.json: inconsistent description', errors)
            self.assertIn('SECURITY.md: supported version series differs', errors)

    def test_validate_handles_missing_or_commented_metadata_and_malformed_evals(self) -> None:
        import json
        import sys
        sys.path.insert(0, str(ROOT / 'scripts'))
        from validate_plugin import validate

        with tempfile.TemporaryDirectory() as temporary:
            pkg = self.copy_package(Path(temporary))
            (pkg / 'skills/challenge-the-design/agents/openai.yaml').unlink()
            errors = validate(pkg)
            self.assertIn('skill metadata: missing path: skills/challenge-the-design/agents/openai.yaml', errors)

        with tempfile.TemporaryDirectory() as temporary:
            pkg = self.copy_package(Path(temporary))
            (pkg / 'commands/review-design.md').write_text(
                '---\n# description: commented out\n---\nbody\n',
                encoding='utf-8',
            )
            (pkg / 'skills/challenge-the-design/agents/openai.yaml').write_text(
                '# display_name: "x"\n# short_description: "y"\n# $challenge-the-design\n',
                encoding='utf-8',
            )
            (pkg / 'evals/evals.json').write_text(
                json.dumps({'skill_name': 'challenge-the-design', 'evals': [{'prompt': 'p', 'criteria': ['']}]}),
                encoding='utf-8',
            )
            errors = validate(pkg)
            self.assertIn('commands/review-design.md: command description missing', errors)
            self.assertIn('skill metadata missing display_name', errors)
            self.assertIn('skill metadata missing short_description', errors)
            self.assertIn('skill default prompt must name the skill', errors)
            self.assertIn('evaluation IDs must be unique integers', errors)
            self.assertIn('evaluation needs name, input prompt, and non-empty grading criteria list', errors)


if __name__ == '__main__':
    unittest.main()
