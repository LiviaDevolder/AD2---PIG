import unittest
import clock

class clockTest(unittest.TestCase):
  def test_daylight(self):
    self.assertEqual(clock.clock.daylight(self), (6, 17))
    
if __name__ == '__main__':
  unittest.main()