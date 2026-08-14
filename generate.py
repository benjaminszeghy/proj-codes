from pyproj import CRS
from pyproj.database import query_crs_info
from pyproj.exceptions import CRSError
import json
import csv

def build_crs_dict():
    crs_list = query_crs_info(
        auth_name="EPSG",
        pj_types=None,
        allow_deprecated=False,
    )

    crs_dict = {}
    for crs in crs_list:
        try:
            proj4string = CRS.from_authority(crs.auth_name, crs.code).to_proj4()
        except CRSError:
            continue  # skips codes that can't be used in proj4js
        crs_dict[f"{crs.auth_name}:{crs.code}"] = {
            "auth_name": crs.auth_name,
            "code": crs.code,
            "name": crs.name,
            "proj4string": proj4string
        }
    return crs_dict


def to_columnar(crs_dict):
    """Reshape the CRS dict into columns.

    Row i is (auth_dict[auth_index[i]], code[i], name[i], proj4string[i]).
    The authority column is dictionary encoded: it repeats across every row,
    so we store each distinct value once and keep a column of indices into it.
    """
    auth_dict = []
    auth_ids = {}
    auth_index = []

    for crs in crs_dict.values():
        if crs["auth_name"] not in auth_ids:
            auth_ids[crs["auth_name"]] = len(auth_dict)
            auth_dict.append(crs["auth_name"])
        auth_index.append(auth_ids[crs["auth_name"]])

    return {
        "cols": {
            "auth": {"dict": auth_dict, "index": auth_index},
            "code": [crs["code"] for crs in crs_dict.values()],
            "name": [crs["name"] for crs in crs_dict.values()],
            "proj4string": [crs["proj4string"] for crs in crs_dict.values()],
        }
    }


def main():
    crs_dict = build_crs_dict()

    with open("proj-codes.json", "w") as f:
        json.dump(to_columnar(crs_dict), f, separators=(",", ":"))

    with open("proj-codes.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["auth_name", "code", "name"])
        for crs in crs_dict.values():
            writer.writerow([crs["auth_name"], crs["code"], crs["name"]])


if __name__ == "__main__":
    main()