#!/usr/bin/env python3
"""Prepare one Datahub study on a separate copy, with logs and hash manifests.

Runs pinned external preprocessing tools; never validates, imports, uploads,
rewrites OncoTree values, or changes the input study. See preprocessing.md.
"""
import argparse
import datetime
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys

TOOLS = (
    'cna_merge.py', 'fuse_mafs.py',
    'remove_duplicate_maf_variants.py', 'add_missing_clinical_meta.py',
    'generate_case_lists.py', 'oncotree_code_converter.py',
)
REFERENCES = ('gene_table.tsv', 'gene_alias_table.tsv', 'case_list_config.tsv', 'oncotree.json')
MAF_KEY = ('Entrez_Gene_Id', 'Chromosome', 'Start_Position', 'End_Position',
           'Variant_Classification', 'Tumor_Seq_Allele2', 'Tumor_Sample_Barcode', 'HGVSp_Short')


def sha256(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def verify_case_list_policy(tools_dir, references_dir):
    """Fail before copying/mutating study data if generation and validation differ."""
    if sha256(tools_dir / 'case_list_config.tsv') != sha256(references_dir / 'case_list_config.tsv'):
        raise ValueError('case_list_config.tsv differs from the pinned validator policy')


def snapshot(root):
    result = {}
    for path in sorted(root.rglob('*')):
        if path.is_symlink():
            raise ValueError(f'Symlinks are not supported: {path}')
        if not path.is_file():
            continue
        with path.open('rb') as stream:
            if stream.read(100).startswith(b'version https://git-lfs.github.com/spec/v1'):
                raise ValueError(f'Unmaterialized LFS pointer: {path}')
        result[str(path.relative_to(root))] = {'bytes': path.stat().st_size, 'sha256': sha256(path)}
    return result


def meta(path):
    values = {}
    for line in path.read_text().splitlines():
        if line.strip() and not line.lstrip().startswith('#') and ':' in line:
            key, value = line.split(':', 1)
            values[key.strip()] = value.strip()
    return values


def header(path):
    with path.open() as stream:
        for line in stream:
            if not line.startswith('#'):
                return line.rstrip('\r\n').split('\t')
    raise ValueError(f'No header: {path}')


def data_path(study, filename):
    path = study / filename
    if not filename or Path(filename).is_absolute() or '..' in Path(filename).parts:
        raise ValueError(f'Unsafe data_filename: {filename!r}')
    if not path.is_file() or not path.resolve().is_relative_to(study.resolve()):
        raise ValueError(f'Missing or external data file: {path}')
    return path


def metadata(study):
    return [(path, meta(path)) for path in sorted(study.glob('meta_*.txt'))]


def clinical_table(path, id_column):
    """Strict preview: avoid the upstream merger's silent last-row-wins behavior."""
    with path.open() as stream:
        lines = (line.rstrip('\r\n') for line in stream if not line.startswith('#'))
        columns = next(lines).split('\t')
        if len(columns) != len(set(columns)) or id_column not in columns:
            raise ValueError(f'Invalid clinical header: {path}')
        rows = {}
        for line in lines:
            if not line.strip():
                continue
            values = line.split('\t')
            if len(values) != len(columns):
                raise ValueError(f'Ragged clinical row: {path}')
            row = dict(zip(columns, values))
            key = row[id_column].strip()
            if not key or key in rows:
                raise ValueError(f'Blank/duplicate {id_column} {key!r}: {path}')
            rows[key] = row
    return columns, rows


def drop_generated_supplement_meta(study, existing_meta):
    """Remove meta files the gap-filler generated for supplemental clinical files.

    Supplemental clinical files are left for curators: the validator rejects a
    clinical data file that no clinical meta file references. Returns the names
    of removed meta files."""
    removed = []
    for path, values in metadata(study):
        if path not in existing_meta and re.fullmatch(r'data_clinical_supp.*\.txt', values.get('data_filename', '')):
            path.unlink()
            removed.append(path.name)
    return removed


def mutation_fusion_plan(study, explicit_same_profile=()):
    secondaries = sorted(study.glob('data_mutations_*.txt'))
    explicit = set(explicit_same_profile)
    if not explicit <= {p.name for p in secondaries}:
        raise ValueError('--same-profile-maf must name an existing secondary data_mutations_*.txt')
    if not secondaries:
        return [], []
    profiles = {}
    for path, values in metadata(study):
        if values.get('genetic_alteration_type') == 'MUTATION_EXTENDED':
            name = values.get('data_filename')
            if name in profiles:
                raise ValueError(f'Multiple mutation metadata files reference {name}')
            profiles[name] = values.get('stable_id')
    primary_profile = profiles.get('data_mutations.txt')
    merge, preserve = [], []
    for path in secondaries:
        profile = profiles.get(path.name)
        if profile and primary_profile and profile != primary_profile:
            if path.name in explicit:
                raise ValueError(f'{path.name} is an explicitly distinct mutation profile')
            preserve.append(path.name)
        elif path.name in explicit or (profile and profile == primary_profile):
            merge.append(path.name)
        else:
            raise ValueError(f'Ambiguous mutation profile for {path.name}; explicitly declare same-profile input')
    if merge:
        primary_header = header(study / 'data_mutations.txt')
        if not set(MAF_KEY) <= set(primary_header):
            raise ValueError('Primary MAF lacks the full eight-column deduplication key')
        for name in merge:
            secondary_header = header(study / name)
            if not set(MAF_KEY) <= set(secondary_header):
                raise ValueError(f'{name} lacks the full eight-column deduplication key')
            extra = set(secondary_header) - set(primary_header)
            if extra:
                raise ValueError(f'{name}: fusion would drop columns {sorted(extra)}')
            # Upstream fuse_mafs deletes metadata by filename, not data_filename.
            expected = 'meta_' + name[len('data_'):]
            for path, values in metadata(study):
                if values.get('data_filename') == name and path.name != expected:
                    raise ValueError(f'{name}: upstream fusion cannot safely remove nonstandard metadata {path.name}')
    return merge, preserve


class Runner:
    def __init__(self, args, report):
        self.args, self.report = args, report

    def run(self, label, script, *arguments):
        command = [sys.executable, str(self.args.tools_dir / script), *map(str, arguments)]
        logfile = self.args.output_dir / 'logs' / (label + '.log')
        step = {'step': label, 'command': command, 'log': str(logfile.relative_to(self.args.output_dir))}
        self.report['steps'].append(step)
        with logfile.open('w') as output:
            result = subprocess.run(command, stdout=output, stderr=subprocess.STDOUT, timeout=self.args.timeout)
        step['exit_code'] = result.returncode
        if result.returncode:
            raise RuntimeError(f'{label} failed with exit {result.returncode}; see {logfile}')
        return logfile


def preprocess(args, report):
    source, output, refs = args.study_dir, args.output_dir, args.references_dir
    if source == output or output.is_relative_to(source) or source.is_relative_to(output):
        raise ValueError('Source and output must be separate, non-nested directories')
    study_id = meta(source / 'meta_study.txt').get('cancer_study_identifier', '')
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]*', study_id):
        raise ValueError('Missing or unsafe cancer_study_identifier')
    report['study_id'] = study_id
    verify_case_list_policy(args.tools_dir, refs)
    for name in TOOLS:
        report['tools'][name] = sha256(args.tools_dir / name)
    for name in REFERENCES:
        report['references'][name] = sha256(refs / name)
    report['source_files'] = snapshot(source)
    study = output / 'study' / study_id
    shutil.copytree(source, study)
    run = Runner(args, report)
    # Resolve and check every declared path before invoking any mutating tool.
    for _, values in metadata(study):
        if 'data_filename' in values:
            data_path(study, values['data_filename'])
    cna = sorted({data_path(study, v['data_filename']) for _, v in metadata(study)
                  if v.get('genetic_alteration_type') == 'COPY_NUMBER_ALTERATION'
                  and v.get('datatype') in ('DISCRETE', 'CONTINUOUS', 'LOG2-VALUE')
                  and 'data_filename' in v})
    if cna:
        common = ['--gene-table', refs / 'gene_table.tsv', '--gene-alias', refs / 'gene_alias_table.tsv',
                  '--gene-resolution', 'validator']
        preview = output / 'cna-preview.json'
        run.run('01-cna-preview', 'cna_merge.py', *common, '--check', '--report-json', preview, *cna)
        findings = json.loads(preview.read_text())
        if any('invalid-Entrez rows' in f.get('detail', f.get('message', '')) for f in findings):
            raise ValueError('CNA preprocessing would drop invalid-Entrez rows; review cna-preview.json')
        report['cna'] = findings
        run.run('01-cna', 'cna_merge.py', *common, '--report-json', output / 'cna.json', *cna)
    else:
        report['skipped']['cna'] = 'No declared CNA matrix'
    # Supplemental clinical files are not merged; the validator flags them for curation.
    supplements = sorted(path.name for path in study.glob('data_clinical_supp*.txt'))
    if supplements:
        report['clinical_supplements_left_for_curation'] = supplements
    merge, preserve = mutation_fusion_plan(study, args.same_profile_maf)
    report['mutation_fusion'] = {'merge': merge, 'preserve_distinct_profiles': preserve}
    if merge:
        excludes = [arg for name in preserve for arg in ('--exclude', name)]
        run.run('03-maf-fusion-preview', 'fuse_mafs.py', study, *excludes, '--dry-run')
        run.run('03-maf-fusion', 'fuse_mafs.py', study, *excludes)
    else:
        report['skipped']['maf_fusion'] = 'No same-profile secondary MAFs'
    mafs = set(study.glob('data_mutations*.txt'))
    mafs.update(data_path(study, v['data_filename']) for _, v in metadata(study)
                if v.get('genetic_alteration_type') == 'MUTATION_EXTENDED' and 'data_filename' in v)
    for index, path in enumerate(sorted(mafs)):
        run.run(f'04-maf-dedup-{index:02}', 'remove_duplicate_maf_variants.py',
                '--input-maf-file', path, '--strategy', 'first', '--in-place')
    if not mafs:
        report['skipped']['maf_dedup'] = 'No mutation MAFs'
    # The upstream gap-filler accepts a parent containing study subdirectories.
    existing_meta = {path for path, _ in metadata(study)}
    run.run('05-missing-meta', 'add_missing_clinical_meta.py', study.parent)
    removed = drop_generated_supplement_meta(study, existing_meta)
    if removed:
        report['supplement_meta_not_generated'] = removed
    (study / 'case_lists').mkdir(exist_ok=True)
    run.run('06-case-lists', 'generate_case_lists.py', '--study-dir', study,
            '--case-list-dir', study / 'case_lists', '--case-list-config-file', refs / 'case_list_config.tsv',
            '--normalize-tcga-barcodes')
    # Call only the upstream read-only audit API using a pinned offline snapshot.
    spec = importlib.util.spec_from_file_location('pinned_oncotree', args.tools_dir / 'oncotree_code_converter.py')
    audit = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(audit)
    mappings = audit.extract_oncotree_code_mappings_from_oncotree_json((refs / 'oncotree.json').read_text())
    report['oncotree'] = {}
    clinical = set(study.glob('data_clinical*.txt'))
    clinical.update(data_path(study, v['data_filename']) for _, v in metadata(study)
                    if v.get('datatype') in ('SAMPLE_ATTRIBUTES', 'PATIENT_ATTRIBUTES') and 'data_filename' in v)
    with (output / 'logs' / '07-oncotree-audit.log').open('w') as log:
        for path in sorted(clinical):
            if 'ONCOTREE_CODE' not in header(path):
                report['oncotree'][path.name] = {'skipped': 'No ONCOTREE_CODE column'}
                continue
            before = sha256(path)
            findings = audit.audit_clinical_file(mappings, str(path))
            audit.report_audit_findings(findings, str(path), out=log)
            if sha256(path) != before:
                raise RuntimeError('OncoTree audit unexpectedly changed the clinical file')
            report['oncotree'][path.name] = {
                bucket: [{'key': key, 'samples': count} for key, count in entries.items()]
                for bucket, entries in findings.items()}
    for path, values in metadata(study):
        if 'data_filename' in values:
            data_path(study, values['data_filename'])
        if values.get('cancer_study_identifier', study_id) != study_id:
            raise ValueError(f'Study ID mismatch: {path}')
    report['prepared_files'] = snapshot(study)
    raw, prepared = report['source_files'], report['prepared_files']
    report['changes'] = {
        'added': sorted(set(prepared) - set(raw)), 'removed': sorted(set(raw) - set(prepared)),
        'modified': sorted(p for p in set(raw) & set(prepared) if raw[p] != prepared[p]),
    }
    if snapshot(source) != raw:
        raise RuntimeError('Source study changed during preprocessing')
    report['prepared_study'] = str(study)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('study_dir', type=Path)
    parser.add_argument('--output-dir', type=Path, required=True, help='New directory; existing paths are refused')
    parser.add_argument('--tools-dir', type=Path, required=True)
    parser.add_argument('--references-dir', type=Path, required=True)
    parser.add_argument('--same-profile-maf', action='append', default=[], help='Explicitly approve an undeclared secondary filename for fusion')
    parser.add_argument('--source-revision', default=None, help='Provenance label, not a Git checkout operation')
    parser.add_argument('--timeout', type=int, default=3600, help='Per-tool timeout in seconds')
    args = parser.parse_args(argv)
    for name in ('study_dir', 'output_dir', 'tools_dir', 'references_dir'):
        setattr(args, name, getattr(args, name).resolve())
    # Reject overlap before creating anything, including logs.
    if args.study_dir == args.output_dir or args.output_dir.is_relative_to(args.study_dir) or args.study_dir.is_relative_to(args.output_dir):
        parser.error('Source and output must be separate, non-nested directories')
    args.output_dir.mkdir(parents=True, exist_ok=False)
    (args.output_dir / 'logs').mkdir()
    report = {'status': 'running', 'source': str(args.study_dir), 'source_revision': args.source_revision,
              'started_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'wrapper_sha256': sha256(Path(__file__)), 'tools': {}, 'references': {},
              'steps': [], 'skipped': {}, 'validation': 'not_run', 'import': 'not_run'}
    try:
        preprocess(args, report)
        report['status'] = 'prepared'
    except Exception as error:
        report['status'] = 'failed'
        report['error'] = f'{type(error).__name__}: {error}'
    finally:
        report['finished_at'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        (args.output_dir / 'manifest.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'study': report.get('study_id'), 'status': report['status'],
                      'manifest': str(args.output_dir / 'manifest.json'), 'error': report.get('error')}), flush=True)
    return 0 if report['status'] == 'prepared' else 1


if __name__ == '__main__':
    sys.exit(main())
