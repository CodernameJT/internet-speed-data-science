import datetime as dt
import json
import os

import speedtest
import sqlalchemy as sa

# Path to the SQLite database
DB_PATH = os.path.join("db", "speeds.db")

# Create an SQLAlchemy engine
engine = sa.create_engine(f"sqlite:///{DB_PATH}", future=True)


def init_db():
    """Create the speedtests table if it does not exist."""
    with engine.begin() as conn:
        conn.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS speedtests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts_utc TEXT NOT NULL,
            ping_ms REAL,
            download_mbps REAL,
            upload_mbps REAL,
            server_name TEXT,
            server_country TEXT
        )
        """))


def run_test():
    """Run a single speed test and return the results as a dict."""
    st = speedtest.Speedtest()

    # Load servers and pick the best one
    st.get_servers()
    best = st.get_best_server()

    # Run tests (results are in bits per second)
    download = st.download() / 1_000_000  # Mbps
    upload = st.upload() / 1_000_000      # Mbps
    ping = st.results.ping                # ms

    result = {
        "ts_utc": dt.datetime.utcnow().isoformat(),
        "ping_ms": float(ping),
        "download_mbps": float(download),
        "upload_mbps": float(upload),
        "server_name": best.get("name"),
        "server_country": best.get("country"),
    }

    return result


def save_result(result: dict):
    """Insert one result row into the database."""
    with engine.begin() as conn:
        conn.execute(sa.text("""
            INSERT INTO speedtests
            (ts_utc, ping_ms, download_mbps, upload_mbps, server_name, server_country)
            VALUES (:ts_utc, :ping_ms, :download_mbps, :upload_mbps, :server_name, :server_country)
        """), result)


if __name__ == "__main__":
    init_db()
    r = run_test()
    save_result(r)
    print("Saved result:")
    print(json.dumps(r, indent=2))
