from pathlib import Path
import json

from meetings.authenticate import google_credentials
from meetings.request import calendar_service, get_events


if __name__ == '__main__':
    events_json = Path("events.json")

    if not events_json.exists():
        creds = google_credentials()
        service = calendar_service(creds)
        events = get_events(service)
        json.dump(events_json.open("w"), events)


    import datetime
    import altair as alt
    from dateutil import parser
    import pandas as pd

    def _transform(row):
        if "dateTime" in row:
            return parser.parse(row["dateTime"])
        elif "date" in row:
            return parser.parse(row["date"])
        return None

    df = pd.read_json(events_json)
    df["start_time"] = df["start"].apply(_transform)
    df["end_time"] = df["end"].apply(_transform)
    df["duration"] = df["end_time"] - df["start_time"]
    df["date"] = df["start_time"].apply(lambda row: row.date())
    # df["week"] = df["date"].apply(lambda row: row.strftime("%V"))
    df["iso_week"] = df["date"].apply(lambda row: row.isocalendar()[1])
    df["iso_year"] = df["date"].apply(lambda row: row.isocalendar()[0])
    df["month"] = df["date"].apply(lambda row: row.strftime("%m"))
    df["year"] = df["date"].apply(lambda row: row.strftime("%Y"))

    df = df[["summary", "date", "iso_week", "month", "iso_year", "duration"]]
    df = df[df["duration"] < datetime.timedelta(hours=10)]

    exclude_list = {*[
        keyword.lower()
        for keyword in [
            "Emily School Zoom", "Coffee break", "Meditation", "meditation", "out of office",
            "Lunchtime catch up", "holiday", "School Collection", "home school"
        ]
    ]}

    def _filter(summary):
        for keyword in exclude_list:
            if keyword in summary.lower():
                return False
        return True

    ix = df["summary"].apply(_filter)
    df = df[ix]

    results = pd.DataFrame(
        data=[
            (year, week, x["duration"].sum())
            for (year, week), x in df.sort_values(by="date").groupby(by=["iso_year", "iso_week"])
        ],
        columns=["year", "week", "total"]
    )
    results["hours"] = results["total"].apply(lambda row: row.total_seconds() / (60 * 60))
    results["year-week"] = results["year"].astype(str) + "-" + results["week"].astype(str)
    results["hours-mean"] = results["hours"].rolling(4).mean()
    results = results.drop(labels="total", axis=1)

    # results = results[results["year"] != "2021"]

    chart = alt.Chart(results).mark_area(opacity=0.3).encode(
        x="week",
        y="hours-mean:Q",
        # y=alt.Y("hours-mean:Q", stack=None),
        row="year:N",
        color="year:N",
    ).properties(
        height=100,
        width=800
    )

    chart.save('filename.html')
