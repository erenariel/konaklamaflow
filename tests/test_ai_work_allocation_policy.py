"""Keep the Codex allocation rule explicit in the repository."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class WorkAllocationPolicyTests(unittest.TestCase):
    def test_contribution_guide_links_to_quota_policy(self):
        guide = (ROOT / "CONTRIBUTING.md").read_text(encoding="utf-8")
        policy = (ROOT / "docs" / "AI_WORK_ALLOCATION_TR.md").read_text(encoding="utf-8")
        self.assertIn("docs/AI_WORK_ALLOCATION_TR.md", guide)
        self.assertIn("issues/62", policy)
        self.assertIn("Codex oturumu kendiliğinden başlamaz", policy)
        self.assertIn("main", policy.lower())
        self.assertIn("test", policy.lower())
        self.assertIn("gerçek otel performansı değildir", policy)


if __name__ == "__main__":
    unittest.main()
