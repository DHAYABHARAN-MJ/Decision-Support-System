# dss/tests.py
from django.test import TestCase, Client
import json
from .engine import DSSEngine
from .validators import validate_params


BEST_CASE = dict(
    slope_angle=5, elevation='low', landslide_risk='low', soil_type='rock',
    bearing_capacity=350, moisture_content='low', num_floors=1,
    foundation_type='pile', building_load='light', material='concrete',
    wall_type='reinforced', retaining_wall='yes', drainage='yes',
    seismic_zone=1, usage='residential'
)

WORST_CASE = dict(
    slope_angle=70, elevation='high', landslide_risk='high', soil_type='sandy',
    bearing_capacity=30, moisture_content='high', num_floors=8,
    foundation_type='shallow', building_load='heavy', material='wood',
    wall_type='lightweight', retaining_wall='no', drainage='no',
    seismic_zone=5, usage='commercial'
)

CONDITIONAL = dict(
    slope_angle=45, elevation='medium', landslide_risk='medium', soil_type='clay',
    bearing_capacity=100, moisture_content='medium', num_floors=5,
    foundation_type='raft', building_load='medium', material='concrete',
    wall_type='reinforced', retaining_wall='yes', drainage='yes',
    seismic_zone=4, usage='residential'
)


class EngineTests(TestCase):

    def test_best_case_feasible(self):
        r = DSSEngine.assess(BEST_CASE)
        self.assertGreaterEqual(r['score'], 75)
        self.assertEqual(r['verdict']['verdict'], 'Feasible')

    def test_worst_case_not_recommended(self):
        r = DSSEngine.assess(WORST_CASE)
        self.assertEqual(r['score'], 0)
        self.assertEqual(r['verdict']['verdict'], 'Not recommended')

    def test_conditional_case(self):
        r = DSSEngine.assess(CONDITIONAL)
        self.assertGreaterEqual(r['score'], 50)
        self.assertLess(r['score'], 75)

    def test_score_clamped_0_100(self):
        r = DSSEngine.assess(WORST_CASE)
        self.assertGreaterEqual(r['score'], 0)
        self.assertLessEqual(r['score'], 100)

    def test_compound_rules_triggered(self):
        bad = dict(WORST_CASE)
        r = DSSEngine.assess(bad)
        rules = [c['rule'] for c in r['compound_rules_triggered']]
        self.assertIn('Heavy load + Sandy soil', rules)
        self.assertIn('High moisture + No drainage', rules)

    def test_bonus_compound_triggered(self):
        r = DSSEngine.assess(BEST_CASE)
        rules = [c['rule'] for c in r['compound_rules_triggered']]
        self.assertIn('Pile foundation + Rock soil', rules)
        self.assertIn('Concrete material + Reinforced walls', rules)

    def test_individual_results_all_15(self):
        r = DSSEngine.assess(BEST_CASE)
        self.assertEqual(len(r['individual_results']), 15)

    def test_flags_only_non_ok(self):
        r = DSSEngine.assess(WORST_CASE)
        for key, val in r['flags'].items():
            self.assertIn(val['status'], ('warn', 'danger'))


class ValidatorTests(TestCase):

    def test_valid_input_passes(self):
        _, errors = validate_params(BEST_CASE)
        self.assertEqual(errors, {})

    def test_missing_field_caught(self):
        data = dict(BEST_CASE)
        del data['slope_angle']
        _, errors = validate_params(data)
        self.assertIn('slope_angle', errors)

    def test_slope_out_of_range(self):
        data = dict(BEST_CASE, slope_angle=95)
        _, errors = validate_params(data)
        self.assertIn('slope_angle', errors)

    def test_invalid_elevation_value(self):
        data = dict(BEST_CASE, elevation='extreme')
        _, errors = validate_params(data)
        self.assertIn('elevation', errors)

    def test_invalid_seismic_zone(self):
        data = dict(BEST_CASE, seismic_zone=6)
        _, errors = validate_params(data)
        self.assertIn('seismic_zone', errors)

    def test_bearing_capacity_coerced(self):
        data = dict(BEST_CASE, bearing_capacity='200')
        cleaned, errors = validate_params(data)
        self.assertEqual(errors, {})
        self.assertEqual(cleaned['bearing_capacity'], 200.0)

    def test_string_values_lowercased(self):
        data = dict(BEST_CASE, elevation='LOW', soil_type='ROCK')
        cleaned, errors = validate_params(data)
        self.assertEqual(errors, {})
        self.assertEqual(cleaned['elevation'], 'low')
        self.assertEqual(cleaned['soil_type'], 'rock')


class APITests(TestCase):

    def setUp(self):
        self.client = Client()

    def test_assess_endpoint_200(self):
        res = self.client.post(
            '/api/dss/assess/',
            data=json.dumps(BEST_CASE),
            content_type='application/json'
        )
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.content)
        self.assertIn('score', data)
        self.assertIn('verdict', data)
        self.assertIn('individual_results', data)

    def test_assess_invalid_input_422(self):
        bad = dict(BEST_CASE, slope_angle=999)
        res = self.client.post(
            '/api/dss/assess/',
            data=json.dumps(bad),
            content_type='application/json'
        )
        self.assertEqual(res.status_code, 422)

    def test_score_endpoint(self):
        res = self.client.post(
            '/api/dss/score/',
            data=json.dumps(BEST_CASE),
            content_type='application/json'
        )
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.content)
        self.assertIn('score', data)
        self.assertIn('verdict', data)

    def test_flags_endpoint(self):
        res = self.client.post(
            '/api/dss/flags/',
            data=json.dumps(WORST_CASE),
            content_type='application/json'
        )
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.content)
        self.assertIn('individual_flags', data)
        self.assertIn('compound_flags', data)

    def test_rules_endpoint_get(self):
        res = self.client.get('/api/dss/rules/')
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.content)
        self.assertEqual(data['total_parameters'], 15)

    def test_compound_rules_endpoint_get(self):
        res = self.client.get('/api/dss/compound-rules/')
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.content)
        self.assertEqual(data['total_compound_rules'], 14)

    def test_bad_json_body(self):
        res = self.client.post(
            '/api/dss/assess/',
            data='not json',
            content_type='application/json'
        )
        self.assertEqual(res.status_code, 400)
