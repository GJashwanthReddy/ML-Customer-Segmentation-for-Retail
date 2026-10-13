"""
Data Loader Module
Handles downloading, caching, and loading the UCI Online Retail dataset.
"""

import os
import urllib.request
import zipfile
import pandas as pd


DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
CSV_PATH = os.path.join(DATA_DIR, "online_retail.csv")
XLSX_PATH = os.path.join(DATA_DIR, "Online Retail.xlsx")
ZIP_PATH = os.path.join(DATA_DIR, "online_retail.zip")
UCI_ZIP_URL = "https://archive.ics.uci.edu/static/public/352/online+retail.zip"


def ensure_dataset_exists() -> str:
    """
    Checks if the dataset exists locally. If not, downloads and extracts it from UCI.
    Returns path to the best available dataset file (prefers CSV, then XLSX).
    """
    os.makedirs(DATA_DIR, exist_ok=True)

    if os.path.exists(CSV_PATH):
        return CSV_PATH

    if os.path.exists(XLSX_PATH):
        # Convert to CSV for faster future loads
        print(f"Converting {XLSX_PATH} to CSV for high-performance caching...")
        df = pd.read_excel(XLSX_PATH)
        df.to_csv(CSV_PATH, index=False)
        return CSV_PATH

    # If neither exists, download from UCI
    print(f"Downloading UCI Online Retail dataset from {UCI_ZIP_URL}...")
    opener = urllib.request.build_opener()
    opener.addheaders = [("User-Agent", "Mozilla/5.0")]
    urllib.request.install_opener(opener)
    urllib.request.urlretrieve(UCI_ZIP_URL, ZIP_PATH)

    with zipfile.ZipFile(ZIP_PATH, "r") as z:
        z.extractall(DATA_DIR)

    # Convert to CSV
    if os.path.exists(XLSX_PATH):
        df = pd.read_excel(XLSX_PATH)
        df.to_csv(CSV_PATH, index=False)
        return CSV_PATH

    return CSV_PATH


def load_raw_data(file_source=None, nrows: int = None) -> pd.DataFrame:
    """
    Loads the Online Retail dataset.
    Args:
        file_source: Optional file path, URL, or uploaded file buffer.
        nrows: Optional row limit for fast preview.
    Returns:
        pd.DataFrame: Raw transactions dataset.
    """
    if file_source is not None:
        if isinstance(file_source, str) and file_source.endswith(".xlsx"):
            return pd.read_excel(file_source, nrows=nrows)
        elif isinstance(file_source, str) and file_source.endswith(".csv"):
            return pd.read_csv(file_source, nrows=nrows)
        else:
            # Could be a Streamlit UploadedFile object or buffer
            try:
                return pd.read_csv(file_source, nrows=nrows)
            except Exception:
                file_source.seek(0)
                return pd.read_excel(file_source, nrows=nrows)

    # Use default local path
    dataset_path = ensure_dataset_exists()
    return pd.read_csv(dataset_path, nrows=nrows)
