import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "skills" / "upthink" / "scripts" / "subtitle_tools.py"
spec = importlib.util.spec_from_file_location("subtitle_tools", SCRIPT)
tools = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tools)


class SubtitleTests(unittest.TestCase):
    def test_punctuation_and_no_content_loss(self):
        self.assertEqual(tools.reconcile("经济数据增长", "经济数据，增长。"), "经济数据，增长。")
        output = tools.reconcile("经济数据增长", "经济数字下降。")
        self.assertEqual("".join(c for c in output if not tools.punctuation_or_space(c)), "经济数据增长")

    def test_original_punctuation_is_preserved(self):
        self.assertEqual(tools.reconcile("甲，乙", "甲乙。"), "甲，乙。")

    def test_cross_segment_search_and_timing(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "s.json"
            path.write_text(json.dumps({"body": [
                {"from": 1.0, "to": 2.0, "content": "经济"},
                {"from": 2.1, "to": 3.2, "content": "数据增长"}]}), encoding="utf-8")
            result = subprocess.run([sys.executable, str(SCRIPT), "find", str(path), "经济数据"],
                                    capture_output=True, text=True, encoding="utf-8", check=True)
            self.assertEqual([(r["from"], r["to"]) for r in json.loads(result.stdout)], [(1.0, 3.2)])

    def test_invalid_timestamps_fail(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "s.json"
            path.write_text('{"body":[{"from":3,"to":2,"content":"x"}]}', encoding="utf-8")
            with self.assertRaises(ValueError):
                tools.load_subtitles(path)


if __name__ == "__main__":
    unittest.main()
