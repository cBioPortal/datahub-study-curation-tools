import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('preprocess', Path(__file__).with_name('preprocess_datahub_study.py'))
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)


class PreprocessTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.study = self.root / 'raw'
        self.study.mkdir()

    def write(self, name, content):
        path = self.study / name
        path.parent.mkdir(exist_ok=True, parents=True)
        path.write_text(content)
        return path

    def maf(self, name, extra=()):
        columns = list(p.MAF_KEY) + list(extra)
        row = ['1', '1', '10', '10', 'Missense_Mutation', 'T', 'S1', 'p.A1V'] + ['x'] * len(extra)
        return self.write(name, '\t'.join(columns) + '\n' + ('\t'.join(row) + '\n') * 2)

    def mutation_meta(self, name, stable):
        self.write('meta_' + name[5:], f'genetic_alteration_type: MUTATION_EXTENDED\nstable_id: {stable}\ndata_filename: {name}\n')

    def clinical(self, name, columns, rows):
        self.write(name, ('#' + '\t'.join(columns) + '\n') * 4 + '\t'.join(columns) + '\n' +
                   ''.join('\t'.join(row) + '\n' for row in rows))

    def test_rejects_lfs_pointer(self):
        self.write('data.txt', 'version https://git-lfs.github.com/spec/v1\noid sha256:abc\nsize 1\n')
        with self.assertRaisesRegex(ValueError, 'LFS'):
            p.snapshot(self.study)

    def test_case_list_policy_must_match_pinned_validator(self):
        tools = self.root / 'tools'
        refs = self.root / 'references'
        tools.mkdir()
        refs.mkdir()
        (tools / 'case_list_config.tsv').write_text('candidate rules')
        (refs / 'case_list_config.tsv').write_text('old EC2 rules')
        with self.assertRaisesRegex(ValueError, 'pinned validator'):
            p.verify_case_list_policy(tools, refs)
        (refs / 'case_list_config.tsv').write_text('candidate rules')
        p.verify_case_list_policy(tools, refs)

    def test_rejects_symlink(self):
        (self.study / 'link').symlink_to('/etc/hosts')
        with self.assertRaisesRegex(ValueError, 'Symlinks'):
            p.snapshot(self.study)

    def test_paths_cannot_escape(self):
        for name in ('../file', '/etc/hosts', ''):
            with self.subTest(name=name), self.assertRaises(ValueError):
                p.data_path(self.study, name)

    def test_distinct_mutation_profiles_preserved(self):
        self.maf('data_mutations.txt')
        self.maf('data_mutations_germline.txt')
        self.mutation_meta('data_mutations.txt', 'mutations')
        self.mutation_meta('data_mutations_germline.txt', 'germline')
        self.assertEqual(p.mutation_fusion_plan(self.study), ([], ['data_mutations_germline.txt']))
        with self.assertRaisesRegex(ValueError, 'distinct'):
            p.mutation_fusion_plan(self.study, ['data_mutations_germline.txt'])

    def test_ambiguous_maf_requires_explicit_choice(self):
        self.maf('data_mutations.txt')
        self.maf('data_mutations_extra.txt')
        with self.assertRaisesRegex(ValueError, 'Ambiguous'):
            p.mutation_fusion_plan(self.study)
        self.assertEqual(p.mutation_fusion_plan(self.study, ['data_mutations_extra.txt'])[0], ['data_mutations_extra.txt'])

    def test_fusion_refuses_column_loss(self):
        self.maf('data_mutations.txt')
        self.maf('data_mutations_extra.txt', ['IMPORTANT'])
        with self.assertRaisesRegex(ValueError, 'drop columns'):
            p.mutation_fusion_plan(self.study, ['data_mutations_extra.txt'])

    def test_generated_supplement_meta_is_dropped(self):
        self.write('meta_timeline_a.txt', 'datatype: TIMELINE\ndata_filename: data_timeline_a.txt\n')
        self.write('meta_clinical_supp_curated.txt', 'datatype: SAMPLE_ATTRIBUTES\ndata_filename: data_clinical_supp_curated.txt\n')
        existing = {path for path, _ in p.metadata(self.study)}
        # what the gap-filler would add: one timeline meta and one supp meta
        self.write('meta_timeline_b.txt', 'datatype: TIMELINE\ndata_filename: data_timeline_b.txt\n')
        self.write('meta_clinical_supp.txt', 'datatype: SAMPLE_ATTRIBUTES\ndata_filename: data_clinical_supp.txt\n')
        self.assertEqual(p.drop_generated_supplement_meta(self.study, existing), ['meta_clinical_supp.txt'])
        self.assertTrue((self.study / 'meta_timeline_b.txt').exists())
        # a supp meta that was already in the study is the curator's and stays
        self.assertTrue((self.study / 'meta_clinical_supp_curated.txt').exists())
        self.assertFalse((self.study / 'meta_clinical_supp.txt').exists())

    def test_output_overlap_refused_before_creation(self):
        with self.assertRaises(SystemExit):
            p.main([str(self.study), '--output-dir', str(self.study / 'nested'),
                    '--tools-dir', str(self.root), '--references-dir', str(self.root)])
        self.assertFalse((self.study / 'nested').exists())

    @unittest.skipUnless(os.environ.get('PREPROCESS_TOOLS_DIR'), 'Set PREPROCESS_TOOLS_DIR for pinned-tool integration test')
    def test_all_seven_steps_and_source_preservation(self):
        self.write('meta_study.txt', 'cancer_study_identifier: fixture\n')
        self.maf('data_mutations.txt')
        self.maf('data_mutations_extra.txt')
        self.mutation_meta('data_mutations.txt', 'mutations')
        self.mutation_meta('data_mutations_extra.txt', 'mutations')
        self.clinical('data_clinical_sample.txt', ['SAMPLE_ID', 'PATIENT_ID', 'ONCOTREE_CODE', 'CANCER_TYPE', 'CANCER_TYPE_DETAILED'],
                      [['S1', 'P1', 'OLD_CODE', 'unchanged', 'unchanged detail']])
        self.clinical('data_clinical_supp.txt', ['SAMPLE_ID', 'VALUE'], [['S1', 'x']])
        self.write('data_timeline_test.txt', 'PATIENT_ID\tSTART_DATE\tEVENT_TYPE\nP1\t0\tTEST\n')
        self.write('data_cna.txt', 'Hugo_Symbol\tEntrez_Gene_Id\tS1\nGENE\t1\t0\nALIAS\t1\t2\n')
        self.write('meta_cna.txt', 'genetic_alteration_type: COPY_NUMBER_ALTERATION\ndatatype: DISCRETE\ndata_filename: data_cna.txt\n')
        refs = self.root / 'refs'
        refs.mkdir()
        (refs / 'gene_table.tsv').write_text('1\tGENE\n')
        (refs / 'gene_alias_table.tsv').write_text('1\tALIAS\n')
        (refs / 'oncotree.json').write_text('[{"code":"NEW_CODE","mainType":"New","name":"New"}]')
        # Use the same pinned validator policy for generation and validation.
        (refs / 'case_list_config.tsv').write_bytes(Path(os.environ['PREPROCESS_CASE_CONFIG']).read_bytes())
        before = p.snapshot(self.study)
        out = self.root / 'out'
        result = p.main([str(self.study), '--output-dir', str(out), '--tools-dir', os.environ['PREPROCESS_TOOLS_DIR'],
                         '--references-dir', str(refs)])
        report = json.loads((out / 'manifest.json').read_text())
        self.assertEqual(result, 0, report.get('error'))
        for step in report['steps']:
            if step['step'] in ('01-cna-preview', '01-cna'):
                self.assertIn('--gene-resolution', step['command'])
                self.assertEqual('validator', step['command'][step['command'].index('--gene-resolution') + 1])
        self.assertEqual(p.snapshot(self.study), before)
        prepared = Path(report['prepared_study'])
        self.assertFalse((prepared / 'data_mutations_extra.txt').exists())
        # supplemental clinical data is left untouched, without a meta file, for the validator to flag
        self.assertEqual((prepared / 'data_clinical_supp.txt').read_bytes(), (self.study / 'data_clinical_supp.txt').read_bytes())
        self.assertFalse((prepared / 'meta_clinical_supp.txt').exists())
        self.assertEqual(report['clinical_supplements_left_for_curation'], ['data_clinical_supp.txt'])
        self.assertTrue((prepared / 'meta_timeline_test.txt').exists())
        self.assertNotIn('VALUE', p.header(prepared / 'data_clinical_sample.txt'))
        self.assertIn('OLD_CODE', (prepared / 'data_clinical_sample.txt').read_text())
        _, clinical_rows = p.clinical_table(prepared / 'data_clinical_sample.txt', 'SAMPLE_ID')
        self.assertEqual({name: clinical_rows['S1'][name] for name in
                          ('ONCOTREE_CODE', 'CANCER_TYPE', 'CANCER_TYPE_DETAILED')},
                         {'ONCOTREE_CODE': 'OLD_CODE', 'CANCER_TYPE': 'unchanged',
                          'CANCER_TYPE_DETAILED': 'unchanged detail'})
        self.assertEqual(len((prepared / 'data_mutations.txt').read_text().splitlines()), 2)
        self.assertEqual(len((prepared / 'data_cna.txt').read_text().splitlines()), 2)
        self.assertTrue(list((prepared / 'case_lists').glob('*')))
        self.assertEqual(report['validation'], 'not_run')
        self.assertTrue(report['oncotree']['data_clinical_sample.txt']['stale_codes'])
        with self.assertRaises(FileExistsError):
            p.main([str(self.study), '--output-dir', str(out), '--tools-dir', str(refs), '--references-dir', str(refs)])


if __name__ == '__main__':
    unittest.main()
