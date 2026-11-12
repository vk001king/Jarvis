import unittest
from unittest.mock import patch

from core import observatory_data


class ObservatoryDataTests(unittest.TestCase):
    def test_iss_position_is_returned_as_bounded_orbital_telemetry(self):
        with patch.object(observatory_data, "_read_json", return_value={
            "latitude": 51.5,
            "longitude": -0.1,
            "altitude": 420.0,
            "velocity": 27500.0,
            "footprint": 4500.0,
            "visibility": "daylight",
            "timestamp": 1_700_000_000,
        }):
            position = observatory_data.fetch_iss_position()

        self.assertEqual(position["latitude"], 51.5)
        self.assertEqual(position["longitude"], -0.1)
        self.assertEqual(position["altitude_km"], 420.0)
        self.assertEqual(position["visibility"], "daylight")

    def test_iss_position_rejects_out_of_range_coordinates(self):
        with patch.object(observatory_data, "_read_json", return_value={
            "latitude": 91,
            "longitude": 0,
            "altitude": 420,
            "velocity": 27_500,
            "footprint": 4500,
            "timestamp": 1_700_000_000,
        }):
            with self.assertRaisesRegex(ValueError, "out-of-range"):
                observatory_data.fetch_iss_position()

    def test_noaa_kp_uses_newest_reading(self):
        with patch.object(observatory_data, "_read_json", return_value=[
            {"time_tag": "2026-01-01T00:01:00", "estimated_kp": 2.0},
            {"time_tag": "2026-01-01T00:02:00", "estimated_kp": 3.5},
        ]):
            reading = observatory_data.fetch_kp_index()

        self.assertEqual(reading, {
            "index": 3.5,
            "time": "2026-01-01T00:02:00",
        })

    def test_goes_xray_flux_is_classified_from_the_long_wave_channel(self):
        with patch.object(observatory_data, "_read_json", return_value=[
            {"time_tag": "2026-01-01T00:02:00Z", "energy": "0.05-0.4nm",
             "flux": 1e-4},
            {"time_tag": "2026-01-01T00:02:00Z", "energy": "0.1-0.8nm",
             "flux": 6.9e-7},
        ]):
            reading = observatory_data.fetch_xray_flux()

        self.assertEqual(reading["class"], "B6.9")
        self.assertEqual(reading["flux"], 6.9e-7)

    def test_market_chart_parses_prices_and_uses_quoted_symbol(self):
        response = {
            "chart": {
                "result": [{
                    "meta": {
                        "shortName": "S&P 500",
                        "currency": "USD",
                        "regularMarketPrice": 123.5,
                        "regularMarketChangePercent": 1.2,
                        "chartPreviousClose": 122.0,
                        "regularMarketDayHigh": None,
                        "regularMarketDayLow": None,
                    },
                    "indicators": {
                        "quote": [{
                            "close": [121.0, None, 123.5],
                            "volume": [10, 20, 30],
                        }],
                    },
                }],
                "error": None,
            },
        }
        with patch.object(
            observatory_data, "_read_json", return_value=response
        ) as read_json:
            data = observatory_data.fetch_market_history("^GSPC")

        self.assertEqual(data["history"], [121.0, 123.5])
        self.assertEqual(data["high"], 123.5)
        self.assertEqual(data["low"], 121.0)
        self.assertEqual(data["change_pct"], 1.2)
        self.assertIn("%5EGSPC", read_json.call_args.args[0])

    def test_market_chart_rejects_url_injection_before_fetching(self):
        with patch.object(observatory_data, "_read_json") as read_json:
            with self.assertRaisesRegex(ValueError, "ticker"):
                observatory_data.fetch_market_history("^GSPC&interval=1d")

        read_json.assert_not_called()

    def test_market_quote_falls_back_to_last_candle_when_live_price_is_missing(self):
        response = {
            "chart": {
                "result": [{
                    "meta": {"currency": "USD"},
                    "indicators": {
                        "quote": [{"close": [10.0, 10.5], "volume": [1, 2]}],
                    },
                }],
            },
        }
        with patch.object(observatory_data, "_read_json", return_value=response):
            data = observatory_data.fetch_market_history("AAPL")

        self.assertEqual(data["price"], 10.5)
        self.assertEqual(data["high"], 10.5)
        self.assertEqual(data["low"], 10.0)


if __name__ == "__main__":
    unittest.main()
