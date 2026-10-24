"""Core parser for EXIF date-time strings.

EXIF stores capture time in the tags DateTimeOriginal (0x9003), DateTime
(0x0132), and DateTimeDigitized (0x9004). The on-disk format is almost always
``YYYY:MM:DD HH:MM:SS`` — colons in the date, a space separator, colons in the
time. This is distinct from ISO 8601 and from XMP, which uses ISO 8601.

This module deliberately handles only the classic EXIF colon form plus the two
legitimate single-separator variants seen in real files (``T`` separator and
space-with-hyphen-date). Sub-second fractions, time zones, and non-Gregorian
calendars are out of scope and rejected, not silently truncated: silently
dropping precision from a timestamp is the kind of bug that makes a whole
photo pipeline sort images into the wrong month.
"""

from __future__ import annotations

import datetime as _dt


class ExifTimeError(ValueError):
    """Raised when an EXIF date-time string cannot be parsed unambiguously.

    Subclass of ValueError so callers that already catch ValueError for input
    validation get sensible behaviour for free, while those that want to
    distinguish a parse failure can catch this directly.
    """


# Accepted separators between date and time. The EXIF spec mandates a single
# space, but real-world files also use 'T' (from tools that normalize toward
# ISO 8601) and an underscore (common in filenames that were then stored back
# into EXIF by batch tools). Anything else is almost certainly corruption or a
# format we should not guess at.
_DATE_TIME_SEPARATORS = (" ", "T", "_")

# EXIF uses ':' in both date and time positions. ISO-style '-' in the date and
# ':' in the time also appears in the wild. We accept exactly these two date
# delimiters rather than treating any non-digit as a delimiter, because a
# string like '2020-01-02T03:04:05Z' is structurally different and should be
# handled by an ISO parser, not quietly accepted here.
_DATE_DELIMITERS = (":", "-")


def _split_parts(value: str, delimiters: tuple[str, ...]) -> list[str]:
    """Split *value* on the first delimiter that occurs.

    Returns the pieces. Raises ExifTimeError if no delimiter is present or if
    different delimiters are mixed within the same field (e.g.
    ``2020:01-02``), which would be ambiguous.
    """
    found = None
    for d in delimiters:
        if d in value:
            if found is not None and found != d:
                raise ExifTimeError(
                    f"mixed delimiters in EXIF date/time field: {value!r}"
                )
            found = d
    if found is None:
        raise ExifTimeError(f"no delimiter found in EXIF date/time field: {value!r}")
    return value.split(found)


def _find_separator(value: str, separators: tuple[str, ...]) -> str:
    """Return the date/time separator actually present in *value*."""
    present = [s for s in separators if s in value]
    if len(present) != 1:
        raise ExifTimeError(
            f"expected exactly one date/time separator, found {len(present)} in {value!r}"
        )
    return present[0]


def parse_exif_datetime(value: str) -> _dt.datetime:
    """Parse an EXIF date-time string into a timezone-naive datetime.

    Accepted forms (date delimiters ':' or '-', date/time separator in
    {space, T, _}, time delimiter ':'):

        2020:01:02 03:04:05
        2020-01-02T03:04:05
        2020:01:02_03:04:05

    Each component must be zero-padded to width 2 (date) or 2 (time) and
    represent a valid calendar date and valid wall-clock time. Out-of-range
    values raise ExifTimeError rather than wrapping or clamping: a timestamp
    of ``2020:13:01 ...`` is almost certainly a corrupt sensor clock and should
    not be interpreted as January of the following year.
    """
    if not isinstance(value, str):
        raise ExifTimeError(f"expected str, got {type(value).__name__}")

    stripped = value.strip()
    if not stripped:
        raise ExifTimeError("empty EXIF date-time string")

    sep = _find_separator(stripped, _DATE_TIME_SEPARATORS)
    date_part, time_part = stripped.split(sep, 1)

    if not date_part or not time_part:
        raise ExifTimeError(f"missing date or time component in {value!r}")

    date_pieces = _split_parts(date_part, _DATE_DELIMITERS)
    if len(date_pieces) != 3:
        raise ExifTimeError(
            f"expected YYYY:MM:DD, got {date_part!r} with {len(date_pieces)} components"
        )

    time_pieces = _split_parts(time_part, (":",))
    if len(time_pieces) != 3:
        raise ExifTimeError(
            f"expected HH:MM:SS, got {time_part!r} with {len(time_pieces)} components"
        )

    try:
        year, month, day = (int(p) for p in date_pieces)
        hour, minute, second = (int(p) for p in time_pieces)
    except ValueError as exc:
        raise ExifTimeError(f"non-integer component in {value!r}") from exc

    # Reject sub-second or timezone suffixes explicitly. datetime.fromisoformat
    # and strptime-with-%f would accept them, but accepting them would silently
    # discard precision we promised not to touch.
    for piece in (*date_pieces, *time_pieces):
        if len(piece) != 2 and piece is not date_pieces[0]:
            raise ExifTimeError(
                f"component {piece!r} in {value!r} must be exactly 2 digits"
            )
    if len(date_pieces[0]) != 4:
        raise ExifTimeError(
            f"year {date_pieces[0]!r} in {value!r} must be exactly 4 digits"
        )

    try:
        return _dt.datetime(year, month, day, hour, minute, second)
    except ValueError as exc:
        raise ExifTimeError(f"invalid date/time in {value!r}: {exc}") from exc


def normalize_exif_datetime(value: str) -> str:
    """Normalize an EXIF date-time string to canonical ``YYYY:MM:DD HH:MM:SS``.

    Canonical here means: colons in the date, a single space separator, colons
    in the time, zero-padded two-digit fields. This is the form the EXIF spec
    mandates and the form most downstream tools expect. Normalization is useful
    when writing EXIF back into an image or when indexing from mixed sources.

    The value is parsed first and then reformatted, so anything that
    :func:`parse_exif_datetime` rejects is rejected here too.
    """
    dt = parse_exif_datetime(value)
    return dt.strftime("%Y:%m:%d %H:%M:%S")
