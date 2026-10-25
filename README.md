# exif-time-lib

Parses and normalizes EXIF date-time strings from image metadata into Python `datetime` objects and canonical `YYYY:MM:DD HH:MM:SS` strings.

```python
from exif_time_lib import parse_exif_datetime, normalize_exif_datetime, ExifTimeError

dt = parse_exif_datetime("2020:01:02 03:04:05")  # datetime.datetime(2020, 1, 2, 3, 4, 5)
canonical = normalize_exif_datetime("2020-01-02T03:04:05")  # "2020:01:02 03:04:05"

try:
    parse_exif_datetime("2020:01:02 03:04:05.500")  # sub-seconds not supported
except ExifTimeError:
    pass
```

## Why this exists

EXIF stores capture time as `YYYY:MM:DD HH:MM:SS` — colons in the date, a space, colons in the time. It is neither ISO 8601 nor XMP. Most parsers either hand the raw string around untouched or run it through `datetime.strptime` and silently accept things EXIF never intended to carry, like fractional seconds and time-zone offsets, then drop that information on the floor.

This library accepts the classic EXIF colon form plus the two single-separator variants that genuinely appear in real files (`T` separator with ISO-style hyphen dates, and `_` separator from filename-derived metadata) and nothing else. It rejects sub-second fractions, timezone suffixes, and mixed delimiters rather than guessing, because a timestamp guessed wrong is worse than a timestamp that fails loudly.

## Edge you will hit

The `datetime` objects returned are timezone-naive. EXIF's classic form carries no timezone, so there is nothing to attach. If you need to sort photos taken across timezones you must supply the offset yourself from a separate source — do not infer it from the EXIF timestamp.

The parser also rejects unpadded fields (e.g. `2020:1:2 ...`) and non-4-digit years, even though `datetime` itself would accept them, because EXIF mandates fixed-width fields and a lax parse would mask the kind of corrupt sensor clock that produces `2020:00:00`.

## Scope decisions

Standard library only, no dependencies. Sub-second EXIF (the `SubSecTime` tags), timezone offsets, and XMP's ISO 8601 form are intentionally out of scope. Use a different tool for those — this one will raise `ExifTimeError` rather than drop precision.
