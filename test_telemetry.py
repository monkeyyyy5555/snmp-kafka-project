import unittest
from unittest.mock import AsyncMock, patch
from rates import Rates, MOD
import collector

class RateTests(unittest.TestCase):
    def setUp(self):
        self.r = Rates()
    def sample(self, counters, t, up=1000, disc=0, speed=100_000_000):
        return self.r.sample("r", counters, t, up, disc, speed)
    def test_first(self):
        self.assertEqual(self.sample((100,200),0), (0,0))
    def test_actual_elapsed(self):
        self.sample((0,0),0)
        self.assertEqual(self.sample((1_000_000,2_000_000),4), (2,4))
    def test_wrap(self):
        self.sample((MOD-100,MOD-200),0)
        self.assertEqual(self.sample((100,200),5), (0.00032,0.00064))
    def test_reset(self):
        self.sample((10000,10000),0)
        self.assertEqual(self.sample((10,10),5), (0,0))
    def test_reboot(self):
        self.sample((0,0),0,up=1000)
        self.assertEqual(self.sample((100,100),5,up=20), (0,0))
    def test_discontinuity(self):
        self.sample((0,0),0)
        self.assertEqual(self.sample((100,100),5,disc=10), (0,0))
    def test_long_gap(self):
        self.sample((0,0),0)
        self.assertEqual(self.sample((100,100),400), (0,0))
    def test_zero_elapsed(self):
        self.sample((0,0),0)
        self.assertEqual(self.sample((100,100),0), (0,0))
    def test_timeout_rebaseline(self):
        self.sample((0,0),0)
        self.r.reset("r")
        self.assertEqual(self.sample((100,100),5), (0,0))

class FailureTests(unittest.IsolatedAsyncioTestCase):
    async def test_failed_router_isolated(self):
        with patch.object(collector, "poll", AsyncMock(side_effect=TimeoutError)):
            ok = await collector.collect_one(None, {}, None, Rates(), "test", 3, "test")
        self.assertFalse(ok)

if __name__ == "__main__":
    unittest.main()
