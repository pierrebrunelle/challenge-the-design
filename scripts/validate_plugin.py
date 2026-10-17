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


def _unquote(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
        return value[1:-1].strip()
    return value.split(' #', 1)[0].strip()


def _parse_yaml_mapping(text: str) -> dict[str, Any]:
    result: dict[str, Any] = {}
    lines = text.splitlines()
    index = 0
    while index < len(lines):
        raw = lines[index]
        stripped = raw.strip()
        if not stripped or stripped.startswith('#'):
            index += 1
            continue
        match = re.match(r'^([A-Za-z0-9_-]+):(?:\s*(.*))?$', raw)
        if not match:
            index += 1
            continue
        key, rest = match.group(1), (match.group(2) or '').strip()
        if rest.startswith('#'):
            rest = ''
        if rest in ('>', '|', '>-', '|-'):
            block: list[str] = []
            index += 1
            while index < len(lines):
                sub = lines[index]
                if not sub.strip():
                    index += 1
                    continue
                if not sub.startswith('  ') or sub.lstrip().startswith('#'):
                    if sub.lstrip().startswith('#'):
                        index += 1
                        continue
                    break
                block.append(sub.strip())
                index += 1
            result[key] = ' '.join(block).strip()
        elif not rest:
            nested: dict[str, str] = {}
            index += 1
            while index < len(lines):
                sub = lines[index]
                if not sub.strip() or sub.lstrip().startswith('#'):
                    index += 1
                    continue
                sub_match = re.match(r'^  ([A-Za-z0-9_-]+):(?:\s*(.*))?$', sub)
                if not sub_match:
                    break
                sub_val = (sub_match.group(2) or '').strip()
                if sub_val.startswith('#'):
                    sub_val = ''
                nested[sub_match.group(1)] = _unquote(sub_val)
                index += 1
            result[key] = nested
        else:
            result[key] = _unquote(rest)
            index += 1
    return result


def validate(root: Path = ROOT) -> list[str]:
    root = root.resolve()
    errors: list[str] = []

    def check(condition: bool, message: str) -> None:
        if not condition:
            errors.append(message)

    def load(relative: str) -> dict[str, Any]:
        try:
            data = json.loads((root / relative).read_text(encoding='utf-8'))
            if not isinstance(data, dict):
                raise ValueError('expected an object')
            return data
        except (OSError, ValueError) as exc:
            errors.append(f'{relative}: {exc}')
            return {}

    def local_path(value: Any, location: str, *, directory: bool = False) -> bool:
        if not isinstance(value, str):
            errors.append(f'{location}: expected a local path')
            return False
        path = (root / value).resolve()
        in_root = path.is_relative_to(root)
        exists = path.is_dir() if directory else path.is_file()
        check(in_root, f'{location}: path escapes package: {value}')
        check(exists, f'{location}: missing path: {value}')
        return in_root and exists

    parsed = {relative: load(relative) for relative in MANIFESTS}
    portable = parsed['plugin.json']
    version = portable.get('version')
    check(isinstance(version, str) and bool(re.fullmatch(r'\d+\.\d+\.\d+', version)), 'plugin.json: invalid version')
    description = portable.get('description')
    check(isinstance(description, str) and bool(description.strip()), 'plugin.json: missing description')
    keywords = portable.get('keywords')
    check(isinstance(keywords, list) and bool(keywords) and all(isinstance(k, str) and k for k in keywords),
          'plugin.json: invalid keywords')
    check(portable.get('$schema') == 'https://agent-plugins.org/schemas/1.0.0/plugin.schema.json',
          'plugin.json: missing portable schema')

    for relative, data in parsed.items():
        check(data.get('name') == NAME, f'{relative}: inconsistent package name')
        if relative == '.claude-plugin/marketplace.json':
            meta = data.get('metadata') if isinstance(data.get('metadata'), dict) else {}
            current = meta.get('version')
            check(meta.get('description') == description, f'{relative}: inconsistent description')
            plugins = data.get('plugins') if isinstance(data.get('plugins'), list) else []
            if plugins and isinstance(plugins[0], dict):
                check(plugins[0].get('description') == description, f'{relative}: inconsistent plugin description')
        else:
            current = data.get('version')
            if relative != '.agents/plugins/marketplace.json':
                check(data.get('description') == description, f'{relative}: inconsistent description')
        if relative != '.agents/plugins/marketplace.json':
            check(current == version, f'{relative}: inconsistent version')
        if relative in ('.plugin/plugin.json', '.cursor-plugin/plugin.json', '.claude-plugin/plugin.json', '.codex-plugin/plugin.json'):
            check(data.get('keywords') == keywords, f'{relative}: inconsistent keywords')
        if relative == 'package.json' and isinstance(keywords, list):
            check(data.get('keywords') == ['pi-package', *keywords], 'package.json: inconsistent keywords')
        if relative in ('plugin.json', '.codex-plugin/plugin.json'):
            check(not data.get('mcpServers'), f'{relative}: this package has no MCP server')

    if isinstance(version, str) and re.fullmatch(r'\d+\.\d+\.\d+', version):
        series = '.'.join(version.split('.')[:2]) + '.x'
        security_path = root / 'SECURITY.md'
        if security_path.is_file():
            check(f'Version {series} is the current supported series.' in security_path.read_text(encoding='utf-8'),
                  'SECURITY.md: supported version series differs')

    codex = parsed['.codex-plugin/plugin.json']
    extensions = portable.get('extensions') if isinstance(portable.get('extensions'), dict) else {}
    openai_ext = extensions.get('com.openai') if isinstance(extensions.get('com.openai'), dict) else {}
    openai_iface = openai_ext.get('interface') if isinstance(openai_ext.get('interface'), dict) else {}
    check(openai_iface == codex.get('interface'), 'portable and Codex interfaces differ')
    starter_prompts = openai_iface.get('defaultPrompt')
    check(
        isinstance(starter_prompts, list) and bool(starter_prompts)
        and all(isinstance(p, str) and f'${NAME}' in p and len(p) <= 80 for p in starter_prompts),
        'plugin.json: defaultPrompt must be concise starter prompts naming the skill',
    )
    check(codex.get('skills') == './skills/', 'Codex skills path must be ./skills/')
    local_path(codex.get('skills'), 'Codex skills', directory=True)
    for relative in ('.plugin/plugin.json', '.cursor-plugin/plugin.json'):
        for component in ('skills', 'commands'):
            local_path(parsed[relative].get(component), f'{relative}: {component}', directory=True)
    claude_commands = parsed['.claude-plugin/plugin.json'].get('commands')
    check(isinstance(claude_commands, list) and bool(claude_commands), '.claude-plugin/plugin.json: missing commands')
    for command in claude_commands if isinstance(claude_commands, list) else []:
        local_path(command, 'Claude command')

    for relative in ('.agents/plugins/marketplace.json', '.claude-plugin/marketplace.json'):
        entries = parsed[relative].get('plugins')
        valid_entries = isinstance(entries, list) and len(entries) == 1 and isinstance(entries[0], dict)
        check(valid_entries and entries[0].get('name') == NAME, f'{relative}: expected this plugin only')
        if not valid_entries:
            continue
        source = entries[0].get('source')
        if relative.startswith('.agents'):
            check(isinstance(source, dict) and source.get('source') == 'local', f'{relative}: expected local source')
            source = source.get('path') if isinstance(source, dict) else None
        check(source == './', f'{relative}: source must be the package root')

    skill_files = list((root / 'skills').glob('*/SKILL.md'))
    check(len(skill_files) == 1, 'expected exactly one skill')
    for skill_file in skill_files:
        content = skill_file.read_text(encoding='utf-8')
        match = re.match(r'\A---\n(.*?)\n---\n', content, re.DOTALL)
        check(match is not None, 'skill frontmatter missing')
        matter = _parse_yaml_mapping(match.group(1)) if match else {}
        check(matter.get('name') == NAME, 'skill name differs')
        check(isinstance(matter.get('description'), str) and bool(matter['description']), 'skill description missing')
        skill_meta = matter.get('metadata') if isinstance(matter.get('metadata'), dict) else {}
        check(skill_meta.get('version') == str(version), 'skill version differs')
        check(len(content.splitlines()) < 500, 'skill must stay under 500 lines')
        check('[TODO:' not in content, 'skill has unfinished scaffold content')
        yaml_rel = str(skill_file.parent.relative_to(root) / 'agents/openai.yaml')
        if local_path(yaml_rel, 'skill metadata'):
            metadata = _parse_yaml_mapping((root / yaml_rel).read_text(encoding='utf-8'))
            interface = metadata.get('interface') if isinstance(metadata.get('interface'), dict) else {}
            check(bool(interface.get('display_name')), 'skill metadata missing display_name')
            check(bool(interface.get('short_description')), 'skill metadata missing short_description')
            prompt = interface.get('default_prompt', '')
            check(
                isinstance(prompt, str) and f'${NAME}' in prompt and len(prompt) <= 80,
                'skill default prompt must concisely name the skill',
            )

    command_files = list((root / 'commands').glob('*.md'))
    check(bool(command_files), 'commands: expected at least one command file')
    for command_file in command_files:
        command_text = command_file.read_text(encoding='utf-8')
        command_match = re.match(r'\A---\n(.*?)\n---\n', command_text, re.DOTALL)
        command_matter = _parse_yaml_mapping(command_match.group(1)) if command_match else {}
        check(isinstance(command_matter.get('description'), str) and bool(command_matter['description']),
              f'{command_file.relative_to(root)}: command description missing')

    readme_path = root / 'README.md'
    if readme_path.is_file():
        readme_text = readme_path.read_text(encoding='utf-8')
        check('/review-design' in readme_text and f'${NAME}' in readme_text,
              'README.md: must document /review-design and $challenge-the-design invocations')

    for document in root.rglob('*.md'):
        if any(part.startswith('.') for part in document.relative_to(root).parts):
            continue
        for target in re.findall(r'\[[^\]]*\]\(([^)]+)\)', document.read_text(encoding='utf-8')):
            if '://' in target or target.startswith('#'):
                continue
            path = (document.parent / target.split('#')[0]).resolve()
            check(path.is_relative_to(root) and path.exists(),
                  f'{document.relative_to(root)}: unresolved local link {target}')

    evaluations = load('evals/evals.json')
    check(evaluations.get('skill_name') == NAME, 'evaluation skill name differs')
    cases = evaluations.get('evals')
    check(isinstance(cases, list) and bool(cases), 'behavioral evaluation cases missing')
    if isinstance(cases, list) and cases:
        ids = [
            case.get('id')
            for case in cases
            if isinstance(case, dict) and isinstance(case.get('id'), int) and not isinstance(case.get('id'), bool)
        ]
        check(len(ids) == len(cases) and len(set(ids)) == len(cases), 'evaluation IDs must be unique integers')
        for case in cases:
            valid_case = (
                isinstance(case, dict)
                and isinstance(case.get('name'), str) and bool(case['name'].strip())
                and isinstance(case.get('prompt'), str) and bool(case['prompt'].strip())
                and isinstance(case.get('criteria'), list) and bool(case['criteria'])
                and all(isinstance(item, str) and bool(item.strip()) for item in case['criteria'])
            )
            check(valid_case, 'evaluation needs name, input prompt, and non-empty grading criteria list')
    return errors


if __name__ == '__main__':
    failures = validate()
    if failures:
        print('\n'.join(f'FAIL: {failure}' for failure in failures), file=sys.stderr)
        raise SystemExit(1)
    print('OK: manifests, versions, component paths, skill metadata, links, and evaluation structure.')
