import os
import sys
import types
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

insightface_stub = types.ModuleType("insightface")
insightface_stub.app = types.SimpleNamespace(FaceAnalysis=lambda *args, **kwargs: None)
insightface_stub.model_zoo = types.SimpleNamespace(get_model=lambda *args, **kwargs: None)
sys.modules.setdefault("insightface", insightface_stub)

import services.models as models


class TestSystemStatus(unittest.TestCase):
    def test_get_system_status_returns_warming_without_loading_models(self):
        original_loaded = models._models_loaded
        original_face_app = models._face_app
        original_swapper = models._swapper
        original_names = models._synthetic_names
        original_loading_flag = models._model_load_in_progress

        try:
            models._models_loaded = False
            models._model_load_in_progress = False
            models._face_app = None
            models._swapper = None
            models._synthetic_names = []

            with patch.object(models, "load_system", side_effect=AssertionError("load_system should not be called here")):
                status = models.get_system_status()

            self.assertEqual(status["status"], "warming")
            self.assertFalse(status["face_detection"])
            self.assertFalse(status["inswapper"])
            self.assertIn("Loading AI models", status["message"])
        finally:
            models._models_loaded = original_loaded
            models._model_load_in_progress = original_loading_flag
            models._face_app = original_face_app
            models._swapper = original_swapper
            models._synthetic_names = original_names

    def test_get_models_starts_background_warmup_and_does_not_block(self):
        original_loaded = models._models_loaded
        original_face_app = models._face_app
        original_swapper = models._swapper
        original_loading_flag = models._model_load_in_progress

        try:
            models._models_loaded = False
            models._model_load_in_progress = False
            models._face_app = None
            models._swapper = None

            with patch.object(models, "load_system", side_effect=AssertionError("load_system should not be called synchronously")):
                result = models.get_models()

            self.assertEqual(result, (None, None, {}, []))
            self.assertTrue(models._model_load_in_progress)
        finally:
            models._models_loaded = original_loaded
            models._model_load_in_progress = original_loading_flag
            models._face_app = original_face_app
            models._swapper = original_swapper


if __name__ == "__main__":
    unittest.main()
