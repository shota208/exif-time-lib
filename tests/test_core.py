import datetime as _dt
import unittest

from exif_time_lib import ExifTimeError, normalize_exif_datetime, parse_exif_datetime


class ParseExifDatetimeTests(unittest.TestCase):
    def test_canonical_colon_form(self):
        self.assertEqual(
            parse_exif_datetime("2020:01:02 03:04:05"),
            _dt.datetime(2020, 1, 2, 3, 4, 5),
        )

    def test_iso_style_date_with_t_separator(self):
        self.assertEqual(
            parse_exif_datetime("2020-01-02T03:04:05"),
            _dt.datetime(2020, 1, 2, 3, 4, 5),
        )

    def test_underscore_separator(self):
        self.assertEqual(
            parse_exif_datetime("2020:01:02_03:04:05"),
            _dt.datetime(2020, 1, 2, 3, 4, 5),
        )

    def test_leading_whitespace_stripped(self):
        self.assertEqual(
            parse_exif_datetime("  2020:01:02 03:04:05  "),
            _dt.datetime(2020, 1, 2, 3, 4, 5),
        )

    def test_empty_string_rejected(self):
        with self.assertRaises(ExifTimeError):
            parse_exif_datetime("")

    def test_non_string_rejected(self):
        with self.assertRaises(ExifTimeError):
            parse_exif_datetime(20200102)  # type: ignore[arg-type]

    def test_subsecond_rejected(self):
        with self.assertRaises(ExifTimeError):
            parse_exif_datetime("2020:01:02 03:04:05.123")

    def test_timezone_rejected(self):
        with self.assertRaises(ExifTimeError):
            parse_exif_datetime("2020:01:02T03:04:05Z")

    def test_mixed_date_delimiters_rejected(self):
        with self.assertRaises(ExifTimeError):
            parse_exif_datetime("2020:01-02 03:04:05")

    def test_multiple_separators_rejected(self):
        with self.assertRaises(ExifTimeError):
            parse_exif_datetime("2020:01:02 03:04:05T06:07:08")

    def test_invalid_month_rejected(self):
        with self.assertRaises(ExifTimeError):
            parse_exif_datetime("2020:13:01 00:00:00")

    def test_invalid_day_rejected(self):
        with self.assertRaises(ExifTimeError):
            parse_exif_datetime("2020:01:32 00:00:00")

    def test_unpadded_year_rejected(self):
        with self.assertRaises(ExifTimeError):
            parse_exif_datetime("20:01:02 00:00:00")

    def test_unpadded_month_rejected(self):
        with self.assertRaises(ExifTimeError):
            parse_exif_datetime("2020:1:02 00:00:00")

    def test_exif_error_is_value_error(self):
        try:
            parse_exif_datetime("bad")
        except ExifTimeError:
            pass
        except ValueError:
            self.fail("should raise ExifTimeError, not plain ValueError")
        else:
            self.fail("expected ExifTimeError")


class NormalizeExifDatetimeTests(unittest.TestCase):
    def test_canonical_unchanged(self):
        self.assertEqual(
            normalize_exif_datetime("2020:01:02 03:04:05"),
            "2020:01:02 03:04:05",
        )

    def test_iso_style_normalized_to_colon(self):
        self.assertEqual(
            normalize_exif_datetime("2020-01-02T03:04:05"),
            "2020:01:02 03:04:05",
        )

    def test_underscore_normalized_to_space(self):
        self.assertEqual(
            normalize_exif_datetime("2020:01:02_03:04:05"),
            "2020:01:02 03:04:05",
        )

    def test_invalid_input_rejected(self):
        with self.assertRaises(ExifTimeError):
            normalize_exif_datetime("2020:01:02 03:04:05.1")


if __name__ == "__main__":
    unittest.main()
