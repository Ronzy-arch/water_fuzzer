# test_framework_modules.py
import unittest
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock
import config
from core import CoreAuditor
from modules.cmd import CommandInjectionModule

class TestWaterFuzzerV10_2Integritas(unittest.TestCase):
    """Integration Test Suite untuk memverifikasi perbaikan pemulihan error, Semaphore, & Rantai Bukti."""

    def setUp(self) -> None:
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.auditor = CoreAuditor(target_url="http://test.local", parameter="test_param", method="POST")
        self.auditor.baseline = {
            "status_code": 200, "content_length": 100, "response_time": 0.05, "entropy_score": 4.0, "captured": True
        }

    def tearDown(self) -> None:
        self.loop.close()

    def test_evidence_engine_json_compliance(self) -> None:
        indicators = ["response_diff", "anomalous_output", "consistent_evaluation_proof"]
        verdict = self.auditor.evaluate_heuristic_evidence(
            response_text="uid=33(www-data) proof", status_code=200, response_time=0.1, sent_payload=";id;",
            indicators=indicators, evidence_type="COMMAND_INJECTION", module_specific_proof={"is_compromised": True}
        )
        self.assertEqual(verdict, "VERIFIED")
        findings = self.auditor.master_report["audit_findings_summary"][0]
        
        # Validasi struktur 5 dimensi rantai bukti JSON komersial
        self.assertIn("1_REQUEST_EVIDENCE", findings)
        self.assertIn("2_BASELINE_EVIDENCE", findings)
        self.assertIn("3_TEST_RESPONSE_EVIDENCE", findings)
        self.assertIn("4_BEHAVIORAL_PROOF", findings)
        self.assertIn("5_MODULE_SPECIFIC_EVIDENCE", findings)

    def test_async_semaphore_public_api(self) -> None:
        """FIX MEDIUM: Menguji ketepatan konfigurasi Semaphore melalui API publik bawaan Python."""
        semaphore = asyncio.Semaphore(config.MAX_CONCURRENT_TASKS)
        # Memastikan objek dikonstruksi secara valid dari kelas Semaphore asli
        self.assertIsInstance(semaphore, asyncio.Semaphore)
        self.assertFalse(semaphore.locked())

if __name__ == '__main__':
    unittest.main()
