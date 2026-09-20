import tempfile
import unittest
import logging
import os
import sys
from pathlib import Path

import cna_merge as cna


class ValidatorResolutionTests(unittest.TestCase):
    def maps(self, genes=None, aliases=None):
        return cna.build_gene_maps(genes or [('PIH1D1', 55011)],
                                   aliases or [(55011, 'Pih1')], resolution='validator')

    def test_alias_case_collision_resolves_in_both_paths(self):
        _, lookup = self.maps()
        for resolve in (cna.resolve_entrez_strict, cna.resolve_entrez_fallback):
            self.assertEqual(55011, resolve(['PIH1', ''], 1, 0, lookup))
            self.assertEqual(55011, resolve(['PIH1D1', '55011'], 1, 0, lookup))

    def test_ambiguous_alias_is_not_arbitrarily_assigned(self):
        _, lookup = self.maps([('ONE', 1), ('TWO', 2)], [(1, 'Alias'), (2, 'ALIAS')])
        self.assertIsNone(cna.resolve_entrez_fallback(['alias', ''], 1, 0, lookup))

    def test_canonical_symbol_precedes_alias(self):
        _, lookup = self.maps([('ONE', 1), ('TWO', 2)], [(2, 'one')])
        self.assertEqual(1, cna.resolve_entrez_strict(['one', ''], 1, 0, lookup))

    def test_unknown_numeric_id_is_preserved_as_unresolved(self):
        _, lookup = self.maps()
        self.assertIsNone(cna.resolve_entrez_fallback(['PIH1D1', '999'], 1, 0, lookup))

    def test_symbol_trimming_pipe_suffix_and_integer_normalization(self):
        _, lookup = self.maps()
        for resolve in (cna.resolve_entrez_strict, cna.resolve_entrez_fallback):
            self.assertEqual(55011, resolve([' pih1|annotation ', ''], 1, 0, lookup))
            self.assertEqual(55011, resolve(['PIH1D1', '055011'], 1, 0, lookup))

    def test_malformed_identifier_still_enters_reported_invalid_row_path(self):
        _, lookup = self.maps()
        for value in ('NA', '0', '-1', '2147483648'):
            with self.subTest(value=value):
                with self.assertRaises(cna.MergeAbort):
                    cna.resolve_entrez_strict(['PIH1D1', value], 1, 0, lookup)
                self.assertIs(cna.DROP_LINE, cna.resolve_entrez_fallback(['PIH1D1', value], 1, 0, lookup))

    def test_merge_and_conflicting_fallback_remove_case_alias_duplicate(self):
        symbols, lookup = self.maps()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'data_cna.txt'
            for values, status in [(('0', '2'), 'merged'), (('-2', '-1'), 'fallback')]:
                with self.subTest(status=status):
                    original = 'Hugo_Symbol\tEntrez_Gene_Id\tS1\nPIH1\t\t' + values[0] + '\nPIH1D1\t55011\t' + values[1] + '\n'
                    path.write_text(original)
                    self.assertEqual(status, cna.merge_file(path, symbols, lookup, True)[0])
                    self.assertEqual(original, path.read_text())
                    self.assertEqual(status, cna.merge_file(path, symbols, lookup, False)[0])
                    self.assertEqual(2, len(path.read_text().splitlines()))
                    once = path.read_bytes()
                    self.assertEqual('clean', cna.merge_file(path, symbols, lookup, False)[0])
                    self.assertEqual(once, path.read_bytes())

    def test_unknown_and_ambiguous_rows_are_not_removed(self):
        symbols, lookup = self.maps([('ONE', 1), ('TWO', 2)], [(1, 'Alias'), (2, 'ALIAS')])
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'data_cna.txt'
            original = 'Hugo_Symbol\tEntrez_Gene_Id\tS1\nAlias\t\t0\nALIAS\t\t2\nUNKNOWN\t\t0\n'
            path.write_text(original)
            self.assertEqual('clean', cna.merge_file(path, symbols, lookup, False)[0])
            self.assertEqual(original, path.read_text())

    def test_default_jar_policy_remains_unchanged(self):
        _, lookup = cna.build_gene_maps([('PIH1D1', 55011)], [(55011, 'Pih1')])
        self.assertIsNone(cna.resolve_entrez_fallback(['PIH1', ''], 1, 0, lookup))

    @unittest.skipUnless(os.environ.get('CBIOPORTAL_SCRIPTS_DIR'), 'Core validator not supplied')
    def test_resolution_matches_actual_core_validator(self):
        sys.path.insert(0, os.environ['CBIOPORTAL_SCRIPTS_DIR'])
        from importer import validateData
        genes = [('PIH1D1', 55011), ('ONE', 1), ('TWO', 2)]
        aliases = [(55011, 'Pih1'), (1, 'Alias'), (2, 'ALIAS'), (2, 'one')]
        _, lookup = self.maps(genes, aliases)
        gene_json = [dict(hugoGeneSymbol=s, entrezGeneId=i) for s, i in genes]
        alias_json = [dict(alias=s, entrezGeneId=i) for i, s in aliases]
        portal = validateData.PortalInstance(None, None,
            validateData.transform_symbol_entrez_map(gene_json),
            validateData.transform_symbol_entrez_map(alias_json, id_field='alias'), None, None, None)
        logger = logging.getLogger('cna-parity')
        logger.addHandler(logging.NullHandler())
        validator = validateData.CNADiscreteValidator('.', {'data_filename': 'unused'}, portal, logger, False, False)
        for symbol, entrez in [('PIH1', ''), ('PIH1D1', '55011'), ('one', ''),
                               ('alias', ''), ('UNKNOWN', ''), ('PIH1D1', '999'),
                               ('pih1|annotation', ''), ('PIH1D1', '055011')]:
            with self.subTest(symbol=symbol, entrez=entrez):
                expected = validator.checkGeneIdentification(symbol, entrez or None)
                expected = int(expected) if expected is not None else None
                for resolve in (cna.resolve_entrez_strict, cna.resolve_entrez_fallback):
                    self.assertEqual(expected, resolve([symbol, entrez], 1, 0, lookup))


if __name__ == '__main__':
    unittest.main()
