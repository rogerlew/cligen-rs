from __future__ import annotations

import unittest
from datetime import date, datetime, timedelta

from research.a9c.data import EventState, advance_event, daymet_date


class DaymetCalendarTests(unittest.TestCase):
    def test_leap_mapping_retains_feb29_and_omits_dec31(self) -> None:
        self.assertEqual(daymet_date(2024, 60), date(2024, 2, 29))
        self.assertEqual(daymet_date(2024, 365), date(2024, 12, 30))


class EventTests(unittest.TestCase):
    def test_event_support_and_earliest_peak(self) -> None:
        state = EventState()
        start = datetime(2020, 1, 1)
        for index in range(72):
            self.assertIsNone(
                advance_event(state, start, 0.0, (1.0, 2.0, 3.0, 4.0), "s", "g")
            )
            start += timedelta(minutes=5)
        self.assertIsNone(advance_event(state, start, 2.0, (1.0, 2.0, 3.0, 4.0), "s", "g"))
        start += timedelta(minutes=5)
        self.assertIsNone(advance_event(state, start, 2.0, (1.0, 2.0, 3.0, 4.0), "s", "g"))
        for _ in range(71):
            start += timedelta(minutes=5)
            self.assertIsNone(advance_event(state, start, 0.0, (1.0, 2.0, 3.0, 4.0), "s", "g"))
        start += timedelta(minutes=5)
        result = advance_event(state, start, 0.0, (1.0, 2.0, 3.0, 4.0), "s", "g")
        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result["duration_min"], 10.0)
        self.assertEqual(result["peak_ratio"], 1.0)
        self.assertEqual(result["time_to_peak_fraction"], 0.25)


if __name__ == "__main__":
    unittest.main()
