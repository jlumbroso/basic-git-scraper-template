import copy
import datetime
import json
import os
import pathlib
import typing

import requests
import pytz

ETIX_TIME_SEARCHED_API = "https://www.etix.com/ticket/online/timedEntrySearch.do"
ETIX_TIME_SEARCHED_METHOD = "specifiedTimedEntryData"

HOPEWELL_QUARRY_EVENT_ID = "1026877"
HOPEWELL_QUARRY_MAX_OPEN = 300
HOPEWELL_QUARRY_TIMEZONE = pytz.timezone("US/Eastern")

OptionalNumber = typing.Optional[typing.Union[str, int]]


# class EtixEventInfo(typing.TypedDict):
#     id: int
#     open: int
#     date: datetime.date

EtixEventInfo = typing.Dict


def time_now():
    return datetime.datetime.now(HOPEWELL_QUARRY_TIMEZONE).strftime("%I:%M%p")


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


class EventMonitor:

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

    def add(
        self,
        year: int,
        month: int,
        day: int,
        value: int,
    ) -> bool:

        data = self._lookup_day(year=year, month=month, day=day)

        # ignore repeated value
        if len(data) > 0 and data[-1][1] == value:
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
        pathlib.Path(os.path.dirname(filename)).mkdir(parents=True, exist_ok=True)

        with open(filename, "w") as f:
            f.write(json.dumps(self._data, indent=2))
            self._filename = filename

    @property
    def data(self):
        return copy.deepcopy(self._data)


def lookup_etix_event(
    event_id,
    day: OptionalNumber = None,
    month: OptionalNumber = None,
    year: OptionalNumber = None,
) -> EtixEventInfo:

    # defaults
    now = datetime.datetime.now()
    year = year or now.year
    month = month or now.month
    day = day or now.day

    try:
        response = requests.get(
            url=ETIX_TIME_SEARCHED_API,
            params={
                "method": ETIX_TIME_SEARCHED_METHOD,
                "event_id": event_id,
                "year": year,
                "month": month,
                "day": day,
            },
            headers={
                "Accept": "application/json, text/javascript, */*; q=0.01",
                "Accept-Language": "en-US,en",
                "Connection": "keep-alive",
                "Referer": "https://www.etix.com/ticket/e/1026877/hopewell-quarry-day-passes-hopewell-hopewell-quarry",
                "Sec-Fetch-Dest": "empty",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Site": "same-origin",
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.64 Safari/537.36",
                "X-Requested-With": "XMLHttpRequest",
                "Sec-Ch-Ua": "\" Not A;Brand\";v=\"99\", \"Chromium\";v=\"101\", \"Google Chrome\";v=\"101\"",
                "Sec-Ch-Ua-Mobile": "?0",
                "Sec-Ch-Ua-Platform": "\"macOS\"",
                "Accept-Encoding": "gzip",
            },
        )

    except requests.exceptions.RequestException:
        return

    # response.json() =
    # [{'compoundTime': 'Jun 04, 2022', 'id': '7495057', 'open': '294'}]
    data = response.json()

    if len(data) == 0:
        return

    # should only be one element
    assert(len(data) == 1)
    data = data[0]

    # clean up
    data["id"] = int(data["id"])
    data["open"] = int(data["open"])
    data["date"] = datetime.date(year=year, month=month, day=day)

    return data


def lookup_hopewell_quarry(
    day: OptionalNumber = None,
    month: OptionalNumber = None,
    year: OptionalNumber = None,
) -> EtixEventInfo:

    return lookup_etix_event(
        event_id=HOPEWELL_QUARRY_EVENT_ID,
        year=year,
        month=month,
        day=day,
    )


def update_hopewell_quarry_data(data):

    # start today
    today = datetime.datetime.now()
    year = today.year
    month = today.month
    day = today.day

    #
    contiguous_unbooked = 0

    while contiguous_unbooked < 2:
        query = lookup_hopewell_quarry(day=day, month=month, year=year)
        if query is None:
            (year, month, day) = next_day(year=year, month=month, day=day)
            continue

        query_open = query["open"]
        if query_open == HOPEWELL_QUARRY_MAX_OPEN:
            contiguous_unbooked += 1

        data.add(year=year, month=month, day=day, value=query_open)

        (year, month, day) = next_day(year=year, month=month, day=day)

    return data


hopewell_quarry_data = EventMonitor("data/hopewell_quarry_data.json")
hopewell_quarry_data = update_hopewell_quarry_data(hopewell_quarry_data)
hopewell_quarry_data.save()
