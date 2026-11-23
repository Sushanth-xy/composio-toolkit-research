"""Comprehensive verification tests for Composio Toolkit Research audit fixes."""

import unittest
import json
import csv
from pathlib import Path

from analysis.accuracy import compute_all_accuracies, score_field, HOLD_OUT_IDS, SCORED_FIELDS
from analysis.patterns import load_records, analyze_patterns


class TestAuditRequirements(unittest.TestCase):

    def setUp(self):
        self.root = Path(__file__).parent.parent

    def test_holdout_gold_template(self):
        """Task 9: Verify blank hold-out gold labeling sheet for 18 hold-out apps."""
        gold_path = self.root / "data" / "gold_holdout.csv"
        self.assertTrue(gold_path.exists(), "data/gold_holdout.csv must exist")

        with open(gold_path, "r", encoding="utf-8") as f:
            reader = list(csv.DictReader(f))

        self.assertEqual(len(reader), 18, "Hold-out sheet must contain exactly 18 apps")
        row_ids = {int(r["id"]) for r in reader}
        self.assertEqual(row_ids, HOLD_OUT_IDS, "Must match the 18 stratified hold-out app IDs")

        for row in reader:
            for field in SCORED_FIELDS:
                self.assertEqual(row[field].strip(), "", f"Field {field} for app {row['id']} must be blank")

    def test_accuracy_script_pending_and_eval(self):
        """Task 9: Verify accuracy script reports pending when blank, and calculates only from filled."""
        rep = compute_all_accuracies("data/gold_holdout.csv")
        self.assertEqual(rep["status"], "pending_human_labeling")
        self.assertEqual(rep["labeled_holdout_count"], 0)
        self.assertEqual(rep["progression"]["final"]["hold_out_accuracy"], "Pending human gold labeling")
        self.assertIn("0.0% accuracy movement", rep["verification_loop_note"])

        # Test field scoring logic
        self.assertEqual(score_field("oauth2", "oauth2", "auth_methods"), "correct")
        self.assertEqual(score_field("oauth2, api_key", "oauth2", "auth_methods"), "partial")
        self.assertEqual(score_field("api_key", "oauth2", "auth_methods"), "wrong")
        self.assertEqual(score_field("green", "", "buildability"), "unsupported")

    def test_patterns_exclude_none_blocker(self):
        """Task 7: Verify 'none' is excluded when ranking blockers, and headlines are valid."""
        records = load_records("data/results_final.jsonl")
        patterns = analyze_patterns(records)

        ranked = patterns["ranked_real_blockers"]
        self.assertNotIn("none", [b[0] for b in ranked], "'none' must be excluded from ranked_real_blockers")
        self.assertGreater(patterns["none_blocker_count"], 50, "Unblocked 'none' count must be tracked separately")

        # Headlines must not say top blocker is none
        for h in patterns["headlines"]:
            self.assertNotIn("'none'", h)

        # Check easy wins and needs outreach
        self.assertGreater(len(patterns["easy_wins"]), 0)
        self.assertGreater(len(patterns["needs_outreach"]), 0)
        self.assertEqual(patterns["easy_wins_count"], len(patterns["easy_wins"]))
        self.assertEqual(patterns["needs_outreach_count"], len(patterns["needs_outreach"]))

    def test_re_sourced_evidence_vendor_domains(self):
        """Task 4, 5, 6: Verify evidence URLs are on vendor primary domains and correctly classified."""
        records = {r.id: r for r in load_records("data/results_final.jsonl")}

        # 1. Salesforce (ID 1)
        r1 = records[1]
        self.assertIn("developer.salesforce.com", r1.auth_methods.evidence_url)
        self.assertIn("developer.salesforce.com", r1.access_model.evidence_url)
        self.assertNotIn("unified.to", r1.access_model.evidence_url)
        self.assertNotIn("getknit.dev", r1.auth_methods.evidence_url)
        self.assertEqual(r1.buildability.value, "green")

        # 2. Twilio (ID 22)
        r22 = records[22]
        self.assertIn("twilio.com", r22.auth_methods.evidence_url)
        self.assertNotIn("mindcloud.co", r22.auth_methods.evidence_url)
        self.assertIn("basic", r22.auth_methods.value)

        # 3. LiveAgent (ID 16)
        r16 = records[16]
        self.assertIn("liveagent.com", r16.auth_methods.evidence_url)
        self.assertEqual(r16.existing_mcp.value, "official")
        self.assertIn("QualityUnit/liveagent-mcp-server", r16.existing_mcp.mcp_url)

        # 4. Meta Ads (ID 32)
        r32 = records[32]
        self.assertIn("developers.facebook.com", r32.auth_methods.evidence_url)
        self.assertIn("developers.facebook.com", r32.access_model.evidence_url)
        self.assertNotIn("prismatic.io", r32.auth_methods.evidence_url)
        self.assertEqual(r32.main_blocker.value, "app_review")

        # 5. Sherlock (ID 58)
        r58 = records[58]
        self.assertIn("github.com/sherlock-project/sherlock", r58.auth_methods.evidence_url)
        self.assertEqual(r58.buildability.value, "yellow")
        self.assertEqual(r58.main_blocker.value, "cli_or_local_only")

        # 6. Mermaid CLI (ID 98)
        r98 = records[98]
        self.assertIn("github.com/mermaid-js/mermaid-cli", r98.auth_methods.evidence_url)
        self.assertEqual(r98.buildability.value, "yellow")
        self.assertEqual(r98.main_blocker.value, "cli_or_local_only")

        # 7. higgsfield (ID 97)
        r97 = records[97]
        self.assertIn("docs.higgsfield.ai", r97.auth_methods.evidence_url)
        self.assertEqual(r97.buildability.value, "green")
        self.assertEqual(r97.existing_mcp.value, "official")

        # 8. iPayX (ID 85)
        r85 = records[85]
        self.assertEqual(r85.name, "iPayX")
        self.assertIn("ipayx.ai", r85.one_liner.evidence_url)
        self.assertIn("iPAYX-Technologies/mcp-fx-audit", r85.auth_methods.evidence_url)
        self.assertEqual(r85.buildability.value, "green")
        self.assertEqual(r85.existing_mcp.value, "official")
        self.assertEqual(r85.main_blocker.value, "none")

        # 9. Plaid (ID 82)
        r82 = records[82]
        self.assertEqual(r82.existing_mcp.value, "official")
        self.assertEqual(r82.buildability.value, "yellow")
        self.assertEqual(r82.main_blocker.value, "app_review")
        self.assertIn("developer/sandbox tooling", r82.reasoning)
        self.assertIn("production banking data", r82.reasoning)

    def test_site_html_integrity(self):
        """Task 2, 3, 8: Verify static HTML table, no fake accuracy, human interventions match LOG.md."""
        site_path = self.root / "site" / "index.html"
        self.assertTrue(site_path.exists())

        with open(site_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Task 2: No fake accuracy numbers
        for fake_num in ["61.1%", "83.3%", "94.4%", "96.7%"]:
            self.assertNotIn(fake_num, content, f"Fake accuracy number {fake_num} must not appear on page")
        self.assertNotIn("<th>Ground Truth</th>", content)
        self.assertNotIn("Representative Hits & Misses Analysis", content)

        # Task 8: 100 static HTML rows renderable without JS
        for i in range(1, 101):
            self.assertIn(f'id="row-{i}"', content, f"Static row {i} must be rendered in HTML")
        self.assertIn('id="data"', content, "#data embedded JSON script tag must exist")

        # Task 3: Human interventions match LOG.md
        self.assertIn("Exactly 20 flagged rows were routed to the review queue", content)
        self.assertIn("Confirmed Human-Corrected Errors (Exactly 2)", content)
        self.assertIn("Fathom (ID 93)", content)
        self.assertIn("Xero (ID 87)", content)


if __name__ == "__main__":
    unittest.main()
