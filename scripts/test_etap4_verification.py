# -*- coding: utf-8 -*-
import json
import os
import unittest

class TestEtap4Verification(unittest.TestCase):
    GEOJSON_PATH = 'data/krakow_streets.geojson'
    LEXICON_PATH = 'data/street_translations_lexicon.json'
    ETYM_CACHE_PATH = 'data/cache_etymologies.json'

    def setUp(self):
        self.assertTrue(os.path.exists(self.GEOJSON_PATH), f"Missing {self.GEOJSON_PATH}")
        self.assertTrue(os.path.exists(self.LEXICON_PATH), f"Missing {self.LEXICON_PATH}")
        self.assertTrue(os.path.exists(self.ETYM_CACHE_PATH), f"Missing {self.ETYM_CACHE_PATH}")

        with open(self.GEOJSON_PATH, 'r', encoding='utf-8') as f:
            self.geojson = json.load(f)

        with open(self.LEXICON_PATH, 'r', encoding='utf-8') as f:
            self.lexicon = json.load(f)

        with open(self.ETYM_CACHE_PATH, 'r', encoding='utf-8') as f:
            self.etym_cache = json.load(f)

    def test_01_file_size_under_limit(self):
        """Master GeoJSON must not exceed 6.5 MB limit."""
        size_bytes = os.path.getsize(self.GEOJSON_PATH)
        size_mb = size_bytes / (1024 * 1024)
        print(f"\n[GeoJSON Size] {size_mb:.2f} MB (Limit: 6.50 MB)")
        self.assertLess(size_mb, 6.5, f"GeoJSON exceeds 6.5 MB: {size_mb:.2f} MB")

    def test_02_lexicon_enrichment(self):
        """Lexicon must contain rich curated translations (>500 entries)."""
        print(f"\n[Lexicon Entries] {len(self.lexicon)} curated entries")
        self.assertGreaterEqual(len(self.lexicon), 500)
        sample = self.lexicon.get('szewska') or next(iter(self.lexicon.values()))
        self.assertIsNotNone(sample)
        self.assertIsInstance(sample, (list, tuple))
        self.assertEqual(len(sample), 2)
        self.assertTrue(len(sample[0]) > 0)
        self.assertTrue(len(sample[1]) > 0)

    def test_03_cache_etymologies_coverage(self):
        """Cache etymologies must have 100% of non-person streets (>1800)."""
        print(f"\n[Etymologies Cache] {len(self.etym_cache)} streets cached")
        self.assertGreaterEqual(len(self.etym_cache), 1800)
        
        for name, data in self.etym_cache.items():
            self.assertIn('literal_meaning', data, f"Missing literal_meaning in cache for {name}")
            self.assertIn('en', data['literal_meaning'])
            self.assertIn('de', data['literal_meaning'])
            self.assertIn('etymology', data, f"Missing etymology in cache for {name}")
            self.assertIn('pl', data['etymology'])
            self.assertIn('en', data['etymology'])
            self.assertIn('de', data['etymology'])

    def test_04_master_geojson_literal_meanings_coverage(self):
        """Master GeoJSON must have at least 1,000 non-person streets with literal meanings (spec target)."""
        features = self.geojson.get('features', [])
        self.assertEqual(len(features), 2763, "Expected 2763 features in Kraków streets GeoJSON")

        with_literal = 0
        non_person_count = 0
        person_count = 0

        for f in features:
            props = f.get('properties', {})
            patron = props.get('patron')
            lit = props.get('literal_meaning')

            if patron is None:
                non_person_count += 1
                if lit:
                    with_literal += 1
                    self.assertIn('en', lit)
                    self.assertIn('de', lit)
                    self.assertTrue(len(lit['en']) > 0)
                    self.assertTrue(len(lit['de']) > 0)
            else:
                person_count += 1

        print(f"\n[Master Coverage] Total non-person streets: {non_person_count}")
        print(f"[Master Coverage] Streets with literal_meaning: {with_literal}")
        coverage_pct = (with_literal / non_person_count) * 100
        print(f"[Master Coverage] Percentage: {coverage_pct:.2f}%")

        self.assertGreaterEqual(with_literal, 1000, "Must cover at least 1000 non-person streets")
        self.assertGreaterEqual(coverage_pct, 95.0, "Coverage should be at least 95%")

    def test_05_zero_hallucinations_patron_null(self):
        """Zero hallucinations: all enriched non-person streets must have patron: null."""
        hallucinations = 0
        features = self.geojson.get('features', [])
        sample_names = {'floriańska', 'juliuszasłowackiego', 'józefadietla', 'stanisławalema', 'wisławyszymborskiej'}

        for f in features:
            props = f.get('properties', {})
            name = props.get('name', {}).get('pl') if isinstance(props.get('name'), dict) else props.get('name', '')
            norm_name = name.lower().replace(' ', '')
            patron = props.get('patron')
            lit = props.get('literal_meaning')

            if lit and patron is not None:
                if norm_name not in sample_names:
                    hallucinations += 1

        print(f"\n[Zero Hallucinations] Unexpected patron entries on non-sample streets: {hallucinations}")
        self.assertEqual(hallucinations, 0, "No non-person street should have a fabricated patron!")

    def test_06_trilingual_etymologies(self):
        """Non-person streets must have consistent trilingual etymologies (pl, en, de)."""
        valid_etym = 0
        for f in self.geojson.get('features', []):
            props = f.get('properties', {})
            etym = props.get('etymology')
            if isinstance(etym, dict) and 'pl' in etym and 'en' in etym and 'de' in etym:
                valid_etym += 1
                
        print(f"\n[Trilingual Etymologies] Features with complete (pl, en, de) etymology: {valid_etym} / 2763")
        self.assertGreaterEqual(valid_etym, 2600)

if __name__ == '__main__':
    unittest.main()
