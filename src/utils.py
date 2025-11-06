import pandas as pd
import xml.etree.ElementTree as et


def get_average_travel_time(path_tripinfo):
    xtree = et.parse(path_tripinfo)
    xroot = xtree.getroot()

    rows = []
    for node in xroot:
        travel_time = node.attrib.get("duration")
        rows.append({"travel_time": travel_time})

    columns = ["travel_time"]
    travel_time = pd.DataFrame(rows, columns=columns).astype("float64")
    return travel_time["travel_time"].mean()
