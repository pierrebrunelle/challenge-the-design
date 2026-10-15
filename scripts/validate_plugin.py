#!/usr/bin/env python3
"""Validate this skills-only package's metadata and local paths using the stdlib.

Native host validation and installer/discovery smoke checks remain separate.
Behavioral cases describe agent evaluations; this script does not execute them.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
NAME = 'challenge-the-design'
MANIFESTS = (
    'plugin.json', '.plugin/plugin.json', '.cursor-plugin/plugin.json',
    '.claude-plugin/plugin.json', '.claude-plugin/marketplace.json',
    '.codex-plugin/plugin.json', '.agents/plugins/marketplace.json', 'package.json',
)


def validate() -> list[str]:
    errors: list[str] = []

    def check(condition: bool, message: str) -> None:
        if not condition:
            errors.append(message)

    def load(relative: str) -> dict[str, Any]:
        try:
            data = json.loads((ROOT / relative).read_text(encoding='utf-8'))
            if not isinstance(data, dict):
                raise ValueError('expected an object')
            return data
        except (OSError, ValueError) as exc:
            errors.append(f'{relative}: {exc}')
            return {}

    def local_path(value: Any, location: str, *, directory: bool = False) -> None:
        if not isinstance(value, str):
            errors.append(f'{location}: expected a local path')
            return
        path = (ROOT / value).resolve()
        check(path.is_relative_to(ROOT), f'{location}: path escapes package: {value}')
        check(path.is_dir() if directory else path.is_file(), f'{location}: missing path: {value}')

    parsed = {relative: load(relative) for relative in MANIFESTS}
    portable = parsed['plugin.json']
    version = portable.get('version')
    check(isinstance(version, str) and bool(re.fullmatch(r'\d+\.\d+\.\d+', version)), 'plugin.json: invalid version')
    check(portable.get('$schema') == 'https://agent-plugins.org/schemas/1.0.0/plugin.schema.json',
          'plugin.json: missing portable schema')

    for relative, data in parsed.items():
        check(data.get('name') == NAME, f'{relative}: inconsistent package name')
        if relative == '.claude-plugin/marketplace.json':
            current = (data.get('metadata') or {}).get('version')
        else:
            current = data.get('version')
        if relative != '.agents/plugins/marketplace.json':
            check(current == version, f'{relative}: inconsistent version')
        if relative in ('plugin.json', '.codex-plugin/plugin.json'):
            check(not data.get('mcpServers'), f'{relative}: this package has no MCP server')

    codex = parsed['.codex-plugin/plugin.json']
    check(portable.get('extensions', {}).get('com.openai', {}).get('interface') == codex.get('interface'),
          'portable and Codex interfaces differ')
    check(codex.get('skills') == './skills/', 'Codex skills path must be ./skills/')
    local_path(codex.get('skills'), 'Codex skills', directory=True)
    for relative in ('.plugin/plugin.json', '.cursor-plugin/plugin.json'):
        for component in ('skills', 'commands'):
            local_path(parsed[relative].get(component), f'{relative}: {component}', directory=True)
    for command in parsed['.claude-plugin/plugin.json'].get('commands', []):
        local_path(command, 'Claude command')

    for relative in ('.agents/plugins/marketplace.json', '.claude-plugin/marketplace.json'):
        entries = parsed[relative].get('plugins', [])
        check(len(entries) == 1 and entries[0].get('name') == NAME, f'{relative}: expected this plugin only')
        if not entries:
            continue
        source = entries[0].get('source')
        if relative.startswith('.agents'):
            check(isinstance(source, dict) and source.get('source') == 'local', f'{relative}: expected local source')
            source = source.get('path') if isinstance(source, dict) else None
        check(source == './', f'{relative}: source must be the package root')

    skill_files = list((ROOT / 'skills').glob('*/SKILL.md'))
    check(len(skill_files) == 1, 'expected exactly one skill')
    for skill_file in skill_files:
        content = skill_file.read_text(encoding='utf-8')
        match = re.match(r'\A---\n(.*?)\n---\n', content, re.DOTALL)
        check(match is not None, 'skill frontmatter missing')
        matter = match.group(1) if match else ''
        check(bool(re.search(rf'^name: {NAME}$', matter, re.MULTILINE)), 'skill name differs')
        check(bool(re.search(r'^description:', matter, re.MULTILINE)), 'skill description missing')
        check(bool(re.search(rf'^  version: {re.escape(str(version))}$', matter, re.MULTILINE)), 'skill version differs')
        check(len(content.splitlines()) < 500, 'skill must stay under 500 lines')
        check('[TODO:' not in content, 'skill has unfinished scaffold content')
        local_path(str(skill_file.parent.relative_to(ROOT) / 'agents/openai.yaml'), 'skill metadata')
        metadata = (skill_file.parent / 'agents/openai.yaml').read_text(encoding='utf-8')
        check(f'${NAME}' in metadata, 'skill default prompt must name the skill')

    for document in ROOT.rglob('*.md'):
        if any(part.startswith('.') for part in document.relative_to(ROOT).parts):
            continue
        for target in re.findall(r'\[[^\]]*\]\(([^)]+)\)', document.read_text(encoding='utf-8')):
            if '://' in target or target.startswith('#'):
                continue
            path = (document.parent / target.split('#')[0]).resolve()
            check(path.is_relative_to(ROOT) and path.exists(),
                  f'{document.relative_to(ROOT)}: unresolved local link {target}')

    evaluations = load('evals/evals.json')
    check(evaluations.get('skill_name') == NAME, 'evaluation skill name differs')
    cases = evaluations.get('evals', [])
    check(bool(cases), 'behavioral evaluation cases missing')
    check(len({case['id'] for case in cases}) == len(cases), 'evaluation IDs must be unique')
    for case in cases:
        check(bool(case.get('prompt')) and bool(case.get('criteria')), 'evaluation needs input and grading criteria')
    return errors


if __name__ == '__main__':
    failures = validate()
    if failures:
        print('\n'.join(f'FAIL: {failure}' for failure in failures), file=sys.stderr)
        raise SystemExit(1)
    print('OK: manifests, versions, component paths, skill metadata, links, and evaluation structure.')
