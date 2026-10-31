# MLflow Docker Compose (draft)

A minimal MLflow Tracking Server with its own PostgreSQL metadata database and persistent artifact storage. Intended for local testing on macOS Docker Desktop, then transfer to an air-gapped Linux environment.

## Components

- **MLflow 3.5.0**: tracking server on `http://localhost:5000` (bound to loopback by default).
- **PostgreSQL 16**: internal Compose service; not published to the host.
- **Artifacts**: host bind mount `./artifacts` (can later be a host-mounted NFS path).
- **Database data**: persistent Docker named volume `postgres_data`.

## Quick start on macOS

```bash
cp .env.example .env
# Edit .env: set POSTGRES_PASSWORD to a strong, unique value
mkdir -p artifacts
docker compose build
docker compose up -d
docker compose ps
docker compose logs -f mlflow
```

Open http://localhost:5000.

The PostgreSQL image creates the `mlflow` role and database automatically **only on first initialization of an empty volume**. You do not need to run psql or create a user manually.

To test experiment metadata and artifact uploads:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install mlflow==3.5.0
python smoke_test.py
```

Then check the `compose-smoke-test` experiment in the UI.

## Configuration

Copy `.env.example` to `.env`. Never commit the latter.

| Variable | Default | Purpose |
| --- | --- | --- |
| `POSTGRES_PASSWORD` | required | Database password; set before first start |
| `MLFLOW_PORT` | `5000` | Published host port |
| `ARTIFACTS_HOST_PATH` | `./artifacts` | Host directory for artifacts |
| `MLFLOW_EXTRA_ALLOWED_HOSTS` | `localhost:5000` | Additional MLflow host header (e.g. `mlflow.internal:5000`) |

The MLflow backend URI points to `postgres:5432` on the Compose network. Clients use `http://localhost:5000` on the Mac. With artifact serving enabled, clients upload through the tracking server, not directly to the artifact directory.

**Security:** This is a development draft without application authentication or TLS. The published MLflow port is bound to `127.0.0.1` by default. For Run:AI / remote access, plan a controlled ingress/reverse proxy with authentication, TLS, and appropriate allowed hosts; do not simply expose this unauthenticated service to an untrusted network.

## NFS artifacts in the internal environment

Mount NFS on the **Docker host** first, e.g. at `/srv/mlflow/artifacts`. Set:

```dotenv
ARTIFACTS_HOST_PATH=/srv/mlflow/artifacts
```

The directory must be writable by the MLflow container. Verify ownership, permissions, NFS export rules, and persistence. Avoid using NFS for PostgreSQL's data volume; keep PostgreSQL on suitable persistent database storage.

**Important:** Existing experiment artifact locations may retain the original URI. Keep the tracking server's artifact proxy semantics and migrate existing data carefully rather than editing old experiment paths blindly.

## Air-gapped deployment

Build on an internet-connected machine for the **target CPU architecture** (often `linux/amd64` internally; Apple Silicon Macs are typically `arm64`). Example:

```bash
docker buildx build --platform linux/amd64 --load -t mlflow-local:3.5.0 .
docker pull --platform linux/amd64 postgres:16
docker save -o mlflow-images.tar mlflow-local:3.5.0 postgres:16
```

Transfer the archive and repository source (without `.env` or artifact data) to the internal host, then:

```bash
docker load -i mlflow-images.tar
cp .env.example .env
# Set a new password and appropriate ARTIFACTS_HOST_PATH
docker compose up -d --no-build
```

For repeatable offline deployments, pin images by digest and retain the exact image archives. The supplied Dockerfile uses pinned Python package versions but not full transitive dependency hashes; freeze and mirror all Python dependencies before production use.

## Operations

```bash
docker compose ps
docker compose logs -f
docker compose down
```

`docker compose down` preserves the database volume. **Do not run `docker compose down -v` unless you intend to delete database data.** Back up PostgreSQL and the artifact directory together. Changing `POSTGRES_PASSWORD` in `.env` after the database has initialized does **not** rotate the existing database password.

## Notes

- The Compose service's database is separate from any existing PostgreSQL Docker Desktop container.
- MLflow's health endpoint is used for container health checking.
- This is a draft for local validation; verify Docker/MLflow compatibility and security controls before internal rollout.
