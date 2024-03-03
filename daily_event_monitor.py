import copy
import datetime
import json
import os
import pathlib
import typing

import requests
import pytz

TIMEZONE = pytz.timezone("US/Eastern")

DailyEventValueType = str


def time_now() -> str:
    """
    Gets the current time in the "US/Eastern" timezone formatted as "YYYY-MM-DD HH:MMAM/PM".

    :return: A string representing the current time formatted as specified.
    :rtype: str
    """
    return datetime.datetime.now(TIMEZONE).strftime("%Y-%m-%d %I:%M%p")


def today() -> typing.Tuple[int, int, int]:
    """
    Gets the current date in the "US/Eastern" timezone.

    :return: A tuple of (year, month, day) representing the current date.
    :rtype: typing.Tuple[int, int, int]
    """
    now = datetime.datetime.now(TIMEZONE)
    return (now.year, now.month, now.day)


def prev_day(
    year: int, month: int, day: int
) -> typing.Optional[typing.Tuple[int, int, int]]:
    """
    Calculates the previous day based on the input year, month, and day.

    :param year: The year of the input date.
    :type year: int
    :param month: The month of the input date.
    :type month: int
    :param day: The day of the input date.
    :type day: int
    :return: A tuple of (year, month, day) representing the previous day or None if the input date is invalid.
    :rtype: typing.Optional[typing.Tuple[int, int, int]]
    """
    try:
        date = datetime.datetime(year=year, month=month, day=day)
    except ValueError:
        return None

    date += datetime.timedelta(hours=-24)
    return (date.year, date.month, date.day)


def next_day(
    year: int, month: int, day: int
) -> typing.Optional[typing.Tuple[int, int, int]]:
    """
    Calculates the next day based on the input year, month, and day.

    :param year: The year of the input date.
    :type year: int
    :param month: The month of the input date.
    :type month: int
    :param day: The day of the input date.
    :type day: int
    :return: A tuple of (year, month, day) representing the next day or None if the input date is invalid.
    :rtype: typing.Optional[typing.Tuple[int, int, int]]
    """
    try:
        date = datetime.datetime(year=year, month=month, day=day)
    except ValueError:
        return None

    date += datetime.timedelta(hours=24)
    return (date.year, date.month, date.day)


class DailyEventMonitor:
    """
    A class to monitor and record daily events.

    Attributes:
        _data (dict): A dictionary to store event data.
        _filename (str, optional): The filename where event data is saved and loaded from.
    """

    def __init__(
        self, filename: typing.Optional[str] = None, data: typing.Optional[dict] = None
    ) -> None:
        """
        Initializes the DailyEventMonitor with optional data and filename.

        :param filename: The name of the file from which to load initial event data.
        :param data: Initial event data to be used by the monitor.
        """
        self._data = dict()
        self._filename = None

        if data is not None:
            self._data = copy.deepcopy(data)

        if filename is not None:
            self.load(filename)

    def _lookup_day(
        self, year: int, month: int, day: int
    ) -> typing.List[typing.Tuple[typing.Tuple[str, DailyEventValueType]]]:
        """
        Looks up events for a specific day.

        :param year: The year of the date to look up.
        :param month: The month of the date to look up.
        :param day: The day of the date to look up.
        :return: A list of events for the specified day.
        """
        if self._data is None:
            self._data = dict()

        key = "{}-{}-{}".format(year, month, day)
        self._data[key] = self._data.get(key, list())
        return self._data[key]

    def get(
        self, year: int, month: int, day: int
    ) -> typing.List[typing.Tuple[typing.Tuple[str, DailyEventValueType]]]:
        """
        Retrieves events for a specific day.

        :param year: The year of the date for which to retrieve events.
        :param month: The month of the date for which to retrieve events.
        :param day: The day of the date for which to retrieve events.
        :return: A list of events for the specified day.
        """
        return self._lookup_day(year=year, month=month, day=day)

    def add(
        self,
        year: int,
        month: int,
        day: int,
        value: DailyEventValueType,
        ignore_repeat: bool = True,
    ) -> bool:
        """
        Adds an event for a specific day.

        :param year: The year of the date to which to add an event.
        :param month: The month of the date to which to add an event.
        :param day: The day of the date to which to add an event.
        :param value: The value or identifier of the event to add.
        :param ignore_repeat: Whether to ignore the event if it is a repeat of the last event for that day.
        :return: True if the event was added, False otherwise (e.g., if ignored due to being a repeat).
        """
        data = self._lookup_day(year=year, month=month, day=day)

        if ignore_repeat and len(data) > 0 and data[-1][1] == value:
            return False

        # add data point
        data.append((time_now(), value))
        return True

    def add_today(self, value: DailyEventValueType, ignore_repeat: bool = True) -> bool:
        """
        Adds an event for the current day.

        :param value: The value or identifier of the event to add.
        :param ignore_repeat: Whether to ignore the event if it is a repeat of the last event for that day.
        :return: True if the event was added, False otherwise (e.g., if ignored due to being a repeat).
        """
        (year_now, month_now, day_now) = today()
        return self.add(
            year=year_now,
            month=month_now,
            day=day_now,
            value=value,
            ignore_repeat=ignore_repeat,
        )

    def load(self, filename: typing.Optional[str] = None) -> bool:
        """
        Loads event data from a file.

        :param filename: The name of the file from which to load event data. Uses the instance's filename if None.
        :return: True if the data was successfully loaded, False otherwise.
        """
        filename = filename or self._filename
        if filename is None:
            raise ValueError("no filename available!")

        self._filename = filename

        try:
            with open(filename) as f:
                try:
                    data = json.loads(f.read())
                    self._data = data
                    return True
                except:
                    return False
        except:
            return False

    def save(self, filename: typing.Optional[str] = None) -> None:
        """
        Saves the current event data to a file.

        :param filename: The name of the file to which to save event data. Uses the instance's filename if None.
        """
        filename = filename or self._filename
        if filename is None:
            raise ValueError("no filename available!")

        # ensure the folder where we output the file exists
        pathlib.Path(os.path.dirname(filename)).mkdir(parents=True, exist_ok=True)

        with open(filename, "w") as f:
            f.write(json.dumps(self._data, indent=2))
            self._filename = filename

    @property
    def file_path(self) -> typing.Optional[str]:
        """
        Returns the path to the file where event data is saved.

        :return: The path to the file where event data is saved.
        """
        return self._filename

    @property
    def data(self) -> dict:
        """
        Returns a deep copy of the event data.

        :return: A copy of the event data.
        """
        return copy.deepcopy(self._data)
