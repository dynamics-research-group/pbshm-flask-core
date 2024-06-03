from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import pytest

from pbshm.timekeeper import datetime_to_nanoseconds_since_epoch, nanoseconds_since_epoch_to_datetime, convert_nanoseconds


class TestDatetimeToNanosecondsSinceEpoch:
    def test_returns_integer(self):
        """
        Test that the function returns type 'int'.
        """
        timestamp = datetime(1995, 10, 21, 22, 11, 56, tzinfo=timezone.utc)
        nanoseconds = datetime_to_nanoseconds_since_epoch(timestamp)
        assert isinstance(nanoseconds, int)
        assert not isinstance(nanoseconds, float)

    def test_epoch_datetime(self):
        """
        Ensure that 0 is returned from epoch input.
        """
        epoch_datetime = datetime.fromtimestamp(0, timezone.utc)
        assert datetime_to_nanoseconds_since_epoch(epoch_datetime) == 0

    def test_no_timezone(self):
        """
        Testing whether an exception is raised if the timestamp has no timezone
        information.
        """
        with pytest.raises(ValueError):
            timestamp = datetime(1995, 10, 21, 22, 11, 56)
            datetime_to_nanoseconds_since_epoch(timestamp)

    def test_utc_to_utc(self):
        """
        Testing a known datetime UTC returns itself.
        """
        utc_stamp = datetime_to_nanoseconds_since_epoch(datetime(2024, 4, 23, 12, 0, 0,tzinfo=timezone.utc))
        assert utc_stamp == 1713873600000000000

    def test_timezone(self):
        """
        Test the behavior with different timezone.
        """
        known_datetime = datetime(2023, 12, 24, 12, 0, 0, tzinfo=ZoneInfo("US/Eastern"))
        expected_nanoseconds = (1703419200000 * int(1e6)) + (60 * 60 * 5 * int(1e9))  # EST to UTC conversion
        assert datetime_to_nanoseconds_since_epoch(known_datetime) == expected_nanoseconds

    def test_daylight_savings_spring_forward_same_time(self):
        """
        Test whether in local time, the times before and after daylight savings
        map to the same number of nanoseconds since epoch.
        """
        dst_datetime_0 = datetime(2024, 3, 31, 1, 0, 0, tzinfo=ZoneInfo("Europe/London"))
        dst_datetime_1 = datetime(2024, 3, 31, 2, 0, 0, tzinfo=ZoneInfo("Europe/London"))
        assert datetime_to_nanoseconds_since_epoch(dst_datetime_0) == datetime_to_nanoseconds_since_epoch(dst_datetime_1)
    
    def test_daylight_savings_fall_back_two_hours_apart(self):
        """
        Test whether in local time, the times before and after daylight savings
        ending are two hours apart.
        """
        dst_datetime_1 = datetime_to_nanoseconds_since_epoch(datetime(2024, 10, 27, 1, 0, 0, tzinfo=ZoneInfo("Europe/London")))
        dst_datetime_2 = datetime_to_nanoseconds_since_epoch(datetime(2024, 10, 27, 2, 0, 0, tzinfo=ZoneInfo("Europe/London"))) 
        assert (dst_datetime_2 - dst_datetime_1) == 2 * 60 * 60 * int(1e9)

    def test_daylight_savings_forwards_utc_consecutive(self):
        """
        Test the function's behavior during the spring daylight saving time
        transition for UTC. The nanoseconds value should be consecutive.
        """
        dst_datetime_1 = datetime_to_nanoseconds_since_epoch(datetime(2024, 3, 31, 0, 59, 59, tzinfo=timezone.utc))
        dst_datetime_2 = datetime_to_nanoseconds_since_epoch(datetime(2024, 3, 31, 1, 0, 0, tzinfo=timezone.utc))
        dst_datetime_3 = datetime_to_nanoseconds_since_epoch(datetime(2024, 3, 31, 1, 0, 1, tzinfo=timezone.utc))
        # UTC should be unaffected by daylight savings
        assert (dst_datetime_2 - dst_datetime_1) == int(1e9)  # 1 second in nanoseconds 
        assert (dst_datetime_3 - dst_datetime_2) == int(1e9)

    def test_daylight_savings_forwards_local_nonconsecutive(self):
        """
        Test the function's behavior during the spring daylight saving time
        transition for Europe/London. The nanoseconds value should not be
        consecutive.
        """       
        dst_datetime_1 = datetime_to_nanoseconds_since_epoch(datetime(2024, 3, 31, 0, 59, 59, tzinfo=ZoneInfo("Europe/London")))
        dst_datetime_2 = datetime_to_nanoseconds_since_epoch(datetime(2024, 3, 31, 1, 0, 0, tzinfo=ZoneInfo("Europe/London"))) 
        dst_datetime_3 = datetime_to_nanoseconds_since_epoch(datetime(2024, 3, 31, 2, 0, 0, tzinfo=ZoneInfo("Europe/London")))
        # This should be affected by daylight savings
        assert (dst_datetime_2 - dst_datetime_1) == int(1e9)  # 1 second in nanoseconds 
        assert (dst_datetime_3 - dst_datetime_2) == 0

    def test_daylight_savings_backwards_utc_consecutive(self):
        """
        Test the function's behavior during the autumn daylight saving time
        transition for UTC. The nanoseconds value should be consecutive.
        """
        dst_datetime_1 = datetime_to_nanoseconds_since_epoch(datetime(2024, 10, 27, 1, 59, 59, tzinfo=timezone.utc))
        dst_datetime_2 = datetime_to_nanoseconds_since_epoch(datetime(2024, 10, 27, 2, 0, 0, tzinfo=timezone.utc)) 
        dst_datetime_3 = datetime_to_nanoseconds_since_epoch(datetime(2024, 10, 27, 2, 0, 1, tzinfo=timezone.utc)) 
        # UTC should be unaffected by daylight savings
        assert (dst_datetime_2 - dst_datetime_1) == int(1e9)  # 1 second in nanoseconds 
        assert (dst_datetime_3 - dst_datetime_2) == int(1e9)

    def test_daylight_savings_backwards_local_nonconsecutive(self):
        """
        Test the function's behavior during the autumn daylight saving time
        transition for Europe/London. The nanoseconds value should not be
        consecutive.
        """
        dst_datetime_1 = datetime_to_nanoseconds_since_epoch(datetime(2024, 10, 27, 1, 59, 59, tzinfo=ZoneInfo("Europe/London"), fold=0))
        dst_datetime_2 = datetime_to_nanoseconds_since_epoch(datetime(2024, 10, 27, 2, 0, 0, tzinfo=ZoneInfo("Europe/London"), fold=0))
        dst_datetime_3 = datetime_to_nanoseconds_since_epoch(datetime(2024, 10, 27, 2, 0, 1, tzinfo=ZoneInfo("Europe/London"), fold=0))
        # This should be affected by daylight savings
        assert (dst_datetime_2 - dst_datetime_1) == (60 * 60 + 1) * int(1e9)  # 1 hour and a second in nanoseconds 
        assert (dst_datetime_3 - dst_datetime_2) == int(1e9)  # 1 second in nanoseconds

class TestNanosecondsSinceEpochToDatetime:
    def test_error_if_not_int(self):
        """
        Test if noninteger arguments raise errors.
        """
        with pytest.raises(TypeError):
            nanoseconds_since_epoch_to_datetime("1")
        
        with pytest.raises(ValueError):
            nanoseconds_since_epoch_to_datetime(1.1)

    def test_epoch(self):
        """
        Test zero seconds from epoch is epoch datetime.
        """
        epoch_datetime = datetime.fromtimestamp(0, timezone.utc)
        assert nanoseconds_since_epoch_to_datetime(0) == epoch_datetime

    def test_known_nanoseconds(self):
        """
        Test against a predetermined know number of nanoseconds since epoch.
        """
        expected_datetime = datetime(1995, 10, 21, 22, 11, 56, tzinfo=timezone.utc)
        assert nanoseconds_since_epoch_to_datetime(814313516000000000) == expected_datetime

    def test_one_oclock_twice_daylight_savings(self):
        """
        Test whether a local time that happens twice due to day light savings
        time do not equate (fold=0 and fold=1).
        """
        nanos1 = 1729987200000000000 # datetime(2024, 10, 27, 1, 0, 0, tzinfo=ZoneInfo("Europe/London"), fold=0)
        nanos2 = 1729990800000000000 # datetime(2024, 10, 27, 1, 0, 0, tzinfo=ZoneInfo("Europe/London"), fold=1)
        assert nanoseconds_since_epoch_to_datetime(nanos1) != nanoseconds_since_epoch_to_datetime(nanos2) 


class TestConvertNanoseconds:
    def test_float_input(self):
        """
        Test if an error is raised if non integer is passed as an argument.
        """
        with pytest.raises(ValueError):
            convert_nanoseconds(10.9, "microseconds")

    def test_microseconds(self):
        """
        Test correct conversion on known value from microseconds.
        """
        assert convert_nanoseconds(int(1e9), "microseconds") == "1000000"

    def test_milliseconds(self):
        """
        Test correct conversion on known value from milliseconds.
        """
        assert convert_nanoseconds(int(1e6), "milliseconds") == '1'

    def test_seconds(self):
        """
        Test correct conversion on known value from seconds.
        """
        assert convert_nanoseconds(int(1e9), "seconds") == '1'

    def test_datetimeutc(self):
        """
        Test correct conversion on known nanosecond value to datetime UTC.
        """
        assert convert_nanoseconds(814313516000000000, "datetimeutc") == "1995-10-21 22:11:56"

    def test_unsupported_unit(self):
        """
        Test raises error with unsupported units.
        """
        with pytest.raises(Exception) as exc_info:
            convert_nanoseconds(int(1e9), "invalid")
        assert str(exc_info.value) == "Unsupported unit"