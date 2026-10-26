import importlib.util
from pathlib import Path
import sys
import threading
import time
import unittest
from concurrent.futures import ThreadPoolExecutor

spec = importlib.util.spec_from_file_location('demo_pipeline', Path(__file__).parents[1]/'examples/demo_pipeline.py')
demo = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = demo
spec.loader.exec_module(demo)

class DemoTests(unittest.TestCase):
    def test_mock_is_explicit(self):
        result = demo.LocalDispatcher(['p'], demo.MockAdapter()).run(demo.Task('demo', 'deepseek', 'p'))
        self.assertTrue(result['mock'])
        self.assertEqual(result['status'], 'demo_completed')
        self.assertEqual(result['screenshots'], [])

    def test_same_device_never_overlaps(self):
        class CheckingAdapter:
            active = 0
            maximum = 0
            guard = threading.Lock()
            def collect(self, task):
                with self.guard:
                    self.active += 1
                    self.maximum = max(self.maximum, self.active)
                time.sleep(0.01)
                with self.guard: self.active -= 1
                return {'answer': 'mock'}
        adapter = CheckingAdapter()
        dispatch = demo.LocalDispatcher(['p'], adapter)
        with ThreadPoolExecutor(max_workers=4) as pool:
            list(pool.map(dispatch.run, [demo.Task('q', 'demo', 'p') for _ in range(8)]))
        self.assertEqual(adapter.maximum, 1)

    def test_failure_is_not_success(self):
        class Broken:
            def collect(self, task): raise RuntimeError('demo failure')
        result = demo.LocalDispatcher(['p'], Broken()).run(demo.Task('q', 'demo', 'p'))
        self.assertEqual(result['status'], 'demo_failed')
        self.assertEqual(result['error'], 'demo failure')

if __name__ == '__main__': unittest.main()
