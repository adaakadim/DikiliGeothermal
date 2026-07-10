# How to Add a New Historian Backend

Currently, the Historian writes to mock local arrays and logs. To deploy an enterprise Time-Series Database (TSDB) like InfluxDB or TimescaleDB:

## 1. Modify the Historian Class
Open `core/historian/historian.py`.

## 2. Inject the Connection Client
In the `__init__`, instantiate the external client (e.g., `influxdb_client`). Ensure you use `SystemConfig` to pass in the secure connection strings. Do NOT hardcode credentials.

## 3. Update the Flush Mechanism
Modify the `log_value` method or background flush thread to execute the bulk-insert command against the external TSDB instead of writing to local Parquet/CSV files. Ensure this operation remains fully asynchronous so it doesn't block the SCADA engine.
