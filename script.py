import copy
import datetime
import json
import os
import pathlib
import typing

import requests
import pytz

TIMEZONE = pytz.timezone("US/Eastern")


def time_now():
    return datetime.datetime.now(TIMEZONE).strftime("%Y-%m-%d %I:%M%p")


def prev_day(year, month, day):

    try:
        date = datetime.datetime(year=year, month=month, day=day)
    except ValueError:
        return

    date += datetime.timedelta(hours=-24)
    return (date.year, date.month, date.day)


def next_day(year, month, day):

    try:
        date = datetime.datetime(year=year, month=month, day=day)
    except ValueError:
        return

    date += datetime.timedelta(hours=24)
    return (date.year, date.month, date.day)


class DailyEventMonitor:

    def __init__(self, filename=None, data=None):
        self._data = dict()
        self._filename = None

        if data is not None:
            self._data = copy.deepcopy(data)

        if filename is not None:
            self.load(filename)

    def _lookup_day(
        self,
        year: int,
        month: int,
        day: int
    ) -> typing.List[typing.Tuple[typing.Tuple[str, int]]]:
        if self._data is None:
            self._data = dict()

        key = "{}-{}-{}".format(year, month, day)

        self._data[key] = self._data.get(key, list())
        return self._data[key]

    def get(
        self,
        year: int,
        month: int,
        day: int
    ) -> typing.List[typing.Tuple[typing.Tuple[str, int]]]:
        return self._lookup_day(year=year, month=month, day=day)

    def add(
        self,
        year: int,
        month: int,
        day: int,
        value: int,
        ignore_repeat: bool = True,
    ) -> bool:

        data = self._lookup_day(year=year, month=month, day=day)

        # ignore repeated value
        if ignore_repeat and len(data) > 0 and data[-1][1] == value:
            return False

        # add data point
        data.append((time_now(), value))
        return True

    def load(self, filename=None):
        filename = filename or self._filename
        if filename is None:
            raise ValueError("no filename available!")

        self._filename = filename

        try:
            with open(filename) as f:
                try:
                    data = json.loads(f.read())
                    self._data = data
                    self._filename = filename
                    return True
                except:
                    return False
        except:
            return False

    def save(self, filename=None):
        filename = filename or self._filename
        if filename is None:
            raise ValueError("no filename available!")

        # ensure the folder where we output the file exists
        pathlib.Path(os.path.dirname(filename)).mkdir(
            parents=True, exist_ok=True)

        with open(filename, "w") as f:
            f.write(json.dumps(self._data, indent=2))
            self._filename = filename

    @property
    def data(self):
        return copy.deepcopy(self._data)


# output something in "./data"
