from pathlib import Path

default_download_location = str(
    Path(__file__).parent.with_name("Downloads").absolute()
)
