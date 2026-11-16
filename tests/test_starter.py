import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import ifcopenshell
import ifcopenshell.guid

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from main import analyse
from runall import save_result


class StarterTests(unittest.TestCase):
    def test_runner_uses_python_settings_and_allows_argument_override(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            capability = root / "capability"
            shutil.copytree(ROOT / "src", capability / "src")
            source = capability / "building with spaces.ifc"
            model = ifcopenshell.file(schema="IFC4")
            model.create_entity("IfcWindow", GlobalId=ifcopenshell.guid.new())
            model.write(str(source))
            settings = capability / "src" / "settings.py"
            settings.write_text(f"MODEL_PATH = {source.name!r}\n", encoding="utf-8")
            command = [sys.executable, "-B", str(capability / "src" / "runall.py")]
            process = subprocess.run(command, cwd=root, capture_output=True, text=True)
            self.assertEqual(process.returncode, 0, process.stderr)
            output = next((capability / "results").glob("run-*/result.json"))
            self.assertEqual(json.loads(output.read_text()), {"window_count": 1})
            settings.write_text("MODEL_PATH = ''\n", encoding="utf-8")
            failed = subprocess.run(command, cwd=root, capture_output=True, text=True)
            self.assertNotEqual(failed.returncode, 0)
            self.assertIn("Set MODEL_PATH", failed.stderr)
            override = subprocess.run(command + [str(source)], capture_output=True, text=True)
            self.assertEqual(override.returncode, 0, override.stderr)
            self.assertEqual(len(list((capability / "results").iterdir())), 2)

    def test_analysis_accepts_a_model_and_distinguishes_zero(self):
        model = ifcopenshell.file(schema="IFC4")
        self.assertEqual(analyse(model), {"window_count": 0})
        model.create_entity("IfcWindow", GlobalId=ifcopenshell.guid.new())
        self.assertEqual(analyse(model), {"window_count": 1})

    def test_runner_preserves_input_and_previous_results(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "example.ifc"
            model = ifcopenshell.file(schema="IFC4")
            model.create_entity("IfcWindow", GlobalId=ifcopenshell.guid.new())
            model.write(str(source))
            original = source.read_bytes()
            results = root / "results"
            for _ in range(2):
                process = subprocess.run(
                    [sys.executable, str(ROOT / "src" / "runall.py"),
                     str(source), "--results-dir", str(results)],
                    capture_output=True, text=True,
                )
                self.assertEqual(process.returncode, 0, process.stderr)
                self.assertIn("Result saved to:", process.stdout)
            outputs = list(results.glob("run-*/result.json"))
            self.assertEqual(len(outputs), 2)
            for output in outputs:
                self.assertEqual(json.loads(output.read_text()), {"window_count": 1})
            self.assertEqual(source.read_bytes(), original)
            source.write_text("not an IFC", encoding="utf-8")
            failed = subprocess.run(
                [sys.executable, str(ROOT / "src" / "runall.py"),
                 str(source), "--results-dir", str(results)],
                capture_output=True, text=True,
            )
            self.assertNotEqual(failed.returncode, 0)
            self.assertEqual(len(list(results.iterdir())), 2)

    def test_import_has_no_model_loading_or_output_side_effects(self):
        with tempfile.TemporaryDirectory() as directory:
            process = subprocess.run(
                [sys.executable, "-c",
                 f"import sys; sys.path.insert(0, {str(ROOT / 'src')!r}); import main, runall"],
                cwd=directory, capture_output=True, text=True,
            )
            self.assertEqual(process.returncode, 0, process.stderr)
            self.assertEqual(process.stdout, "")
            self.assertEqual(list(Path(directory).iterdir()), [])

    def test_invalid_result_is_not_written(self):
        with tempfile.TemporaryDirectory() as directory:
            results = Path(directory) / "results"
            for invalid in [object(), {"count": float("nan")}]:
                with self.assertRaises((TypeError, ValueError)):
                    save_result(invalid, results)
            self.assertFalse(results.exists())


if __name__ == "__main__":
    unittest.main()
