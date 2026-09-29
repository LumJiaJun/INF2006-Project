# VM API adapter

This small standard-library HTTP service provides the local API boundary expected by the Nginx VM deployment.

It deliberately does not fabricate analytics or predictions:

- `GET /health` returns a healthy response.
- `GET /analytics` returns the generated `data/analytics-summary.json` when it exists, otherwise `503`.
- `POST /predict` uses the evaluated model artifact when it exists and returns anonymous estimates without history persistence.

The current repository does not contain the raw listings dataset or model artifact. Supply those real artifacts before enabling the corresponding endpoints. Authenticated history remains disabled on the VM because it requires the Azure identity and persistence migration.

## Run locally on the VM

```bash
cd ~/INF2006-Project
python3 src/vm_api/server.py
```

For Nginx, keep the service bound to `127.0.0.1:8000`. For a real analytics result, first upload the supplied `Listings.csv` outside Git and export its summary:

```bash
python3 analytics/export_vm_analytics.py \
	--listings "data/raw/Airbnb Data/Listings.csv" \
	--output data/analytics-summary.json
sudo systemctl restart inf2006-vm-api
```

The generated file contains the frontend response shape: an object with an `items` array and the `count`, `price_basis`, and `scope` fields.
