"""Extract signed 100-parcel and 14-ROI signals using bounded inverse chunks."""
import runpy
import sys
from pathlib import Path

if __name__ == "__main__":
    if "--include-parcels" not in sys.argv:
        sys.argv.append("--include-parcels")
    runpy.run_path(str(Path(__file__).with_name("03_extract_14roi_timeseries.py")),
                  run_name="__main__")
