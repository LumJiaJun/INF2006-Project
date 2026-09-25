# Deployment — StaySphere

This document separates what's already built and automated (AUTOMATED /
CODE-GENERATED) from what requires you to act inside your AWS console
(MANUAL USER ACTION REQUIRED). You don't have an AWS account set up yet,
so start at Step 1.

Nothing here has been executed against a real AWS account yet.
Everything below is **NOT YET EXECUTED** until you run it and record the
actual result in `evidence/`.

## Local development first (do this before touching AWS)

**AUTOMATED / CODE-GENERATED** — already built, just run it:

```
git clone <your-repo-url>
cd staysphere
cp .env.example .env          # fill in JWT_SECRET locally, DATABASE_URL can stay blank for SQLite
docker compose up -d
docker compose exec backend python -m app.seed
```

Then open `http://localhost:8080` for the app and `http://localhost:8000/docs`
for the interactive API docs. Run tests with:

```
cd tests
pip install -r ../src/backend/requirements.txt
pytest -v
```

Train/retrain the price model:

```
cd analytics
pip install -r requirements.txt
python3 train_price_model.py
```

## AWS deployment

### Step 1 — MANUAL USER ACTION REQUIRED — Create AWS account and budget alert

1. **Location:** https://aws.amazon.com/ → Create a free-tier account.
2. **Click:** "Create a new AWS account", follow the signup flow.
3. **Enter:** your email, a strong root password, payment card (required
   by AWS even for free-tier usage — you will not be charged for
   free-tier-eligible resources used within limits).
4. **Why required:** only you can create and own the AWS account/billing relationship.
5. **Expected result:** access to the AWS Management Console.
6. **Security warning:** never use the root account for day-to-day work.
   Immediately create an IAM user with admin permissions for yourself and
   use that instead (Step 2).
7. **Cost implication:** free-tier eligible for 12 months on many
   services; RDS/ECS usage in this project is designed to stay within or
   close to free-tier limits, but set a budget alert regardless (below).

Then, immediately:

1. **Location:** AWS Console → Billing → Budgets.
2. **Click:** "Create budget" → "Zero spend budget" or a custom monthly
   budget (e.g. $10).
3. **Enter:** your email for alert notifications.
4. **Why required:** catches runaway costs (e.g. forgetting to shut down
   an instance) before they become a real bill.
5. **Expected result:** an email alert if spend approaches the threshold.

### Step 2 — MANUAL USER ACTION REQUIRED — Create an IAM user/role (least privilege)

1. **Location:** AWS Console → IAM → Users → "Create user".
2. **Click:** create a user for yourself with console access, attach the
   `AdministratorAccess` policy **only for initial setup** (or narrower
   policies if you're comfortable scoping them — ECS, RDS, S3, IAM-limited).
3. **Why required:** avoids using the root account, which AWS and this
   project's security controls both require.
4. **Expected result:** a new IAM user you can log in as instead of root.
5. **Security warning:** do not create or download long-lived access
   keys for this user unless you specifically need CLI access. If you
   do, store them in `aws configure`'s local credentials file, never in
   this repository.

### Step 3 — MANUAL USER ACTION REQUIRED — Create RDS PostgreSQL

1. **Location:** AWS Console → RDS → "Create database".
2. **Click:** Standard create → Engine: PostgreSQL → Templates: "Free
   tier" (or "Dev/Test" if free tier isn't available in your region).
3. **Enter:** DB instance identifier `staysphere-db`, master username
   `staysphere`, a generated strong master password (store it — do not
   commit it anywhere).
4. **Configure:** instance class `db.t3.micro` (or the smallest
   available), storage 20GB (default), **uncheck "Public access"**.
5. **Configure networking:** create/select a VPC and a security group
   that will later allow inbound port 5432 **only from the backend's
   security group** (create the backend's security group first if doing
   this in order, or come back and tighten this after Step 4).
6. **Why required:** only you can provision billed AWS resources under
   your account.
7. **Expected result:** an RDS endpoint hostname once the instance
   status shows "Available" (takes several minutes).
8. **Security warning:** never set the security group to allow
   `0.0.0.0/0` on port 5432 — this is the exact threat documented in
   `docs/THREAT_MODEL.md` item 6.
9. **Cost implication:** `db.t3.micro` is free-tier eligible for 12
   months (750 hours/month); stop or delete it after grading if outside
   the free tier window.

### Step 4 — MANUAL USER ACTION REQUIRED — Store secrets in Secrets Manager

1. **Location:** AWS Console → Secrets Manager → "Store a new secret".
2. **Click:** "Other type of secret", add key/value pairs for
   `DATABASE_URL` and `JWT_SECRET` (generate a real random value for
   the latter — see `.env.example` for the command).
3. **Why required:** avoids hardcoding secrets in the container image or task definition.
4. **Expected result:** a secret ARN you'll reference in the ECS task definition (Step 5).

### Step 5 — MANUAL USER ACTION REQUIRED — Build and push the backend image, create ECS Fargate service

1. **Location:** AWS Console → ECR → "Create repository" (name it `staysphere-backend`).
2. **Click:** "View push commands" and follow them locally:
   ```
   aws ecr get-login-password --region <region> | docker login --username AWS --password-stdin <account-id>.dkr.ecr.<region>.amazonaws.com
   docker build -t staysphere-backend ./src/backend
   docker tag staysphere-backend:latest <account-id>.dkr.ecr.<region>.amazonaws.com/staysphere-backend:latest
   docker push <account-id>.dkr.ecr.<region>.amazonaws.com/staysphere-backend:latest
   ```
3. **Location:** AWS Console → ECS → "Create cluster" (Fargate) → "Create task definition"
   referencing the pushed image, injecting `DATABASE_URL`/`JWT_SECRET` from
   the Secrets Manager ARNs (Step 4), port 8000, and a container health
   check pointing at `/api/health`.
4. **Click:** "Create service" using an Application Load Balancer, target
   group health check path `/api/health`, desired count 1–2 tasks.
5. **Why required:** only you can create billed compute resources and
   attach them to your VPC/security groups.
6. **Expected result:** an ALB DNS name that serves the API once the
   service reaches "Steady state" and the target group shows healthy.
7. **Security warning:** attach an IAM **task role** (not a hardcoded
   access key) if the backend ever needs to call other AWS services.
8. **Cost implication:** smallest Fargate task size (0.25 vCPU / 0.5GB)
   is inexpensive but not free-tier; budget a few dollars/month if left
   running, or scale desired count to 0 between grading sessions.

### Step 6 — MANUAL USER ACTION REQUIRED — Host the frontend

1. **Location:** AWS Console → S3 → "Create bucket" (e.g.
   `staysphere-frontend-<yourname>`), enable "Static website hosting" in
   bucket properties.
2. **Click:** upload `src/frontend/index.html` and `app.js`. Before
   uploading, edit `app.js`'s `API_BASE` fallback (or set
   `window.STAYSPHERE_API_BASE` in a small inline script in `index.html`)
   to point at your ALB DNS name from Step 5.
3. **Why required:** only you can create the S3 bucket under your account.
4. **Expected result:** a public S3 website URL serving the frontend.
5. **Cost implication:** effectively free at this project's scale.
6. Optional: put CloudFront in front of the S3 bucket for HTTPS on the
   frontend (the ALB already gives you a path to HTTPS on the API side
   via an ACM certificate — also manual, also optional for a class project).

### Step 7 — MANUAL USER ACTION REQUIRED — Seed the production database

Once the ECS service and RDS instance are both up:

```
# From a machine that can reach the RDS endpoint (e.g. temporarily allow
# your IP in the RDS security group, or run this as a one-off ECS task):
DATABASE_URL=postgresql://staysphere:<password>@<rds-endpoint>:5432/staysphere \
  python3 -m app.seed data/sample/dummy_listings.csv
```

Replace the CSV path with the real dataset once downloaded and validated
against `data/DATA_DICTIONARY.md`.

### Step 8 — MANUAL USER ACTION REQUIRED — Enable CloudWatch monitoring

1. **Location:** ECS task definition → Logging → confirm the `awslogs`
   driver is enabled (it is by default for Fargate task definitions
   created via the console) → CloudWatch → Log groups.
2. **Why required:** confirms logs are actually flowing before you rely on them for evidence.
3. **Expected result:** request/auth/booking log lines visible in the log group.
4. Record a sample query and screenshot, appended to `evidence/monitoring.md`.

## Shutdown / cleanup procedure (run this after grading to avoid ongoing cost)

1. ECS → Service → set desired task count to 0, then delete the service and cluster.
2. RDS → select the instance → Actions → Delete (skip final snapshot only if you're sure you don't need the data).
3. ECR → delete the repository (or just the images) once no longer needed.
4. S3 → empty and delete the frontend bucket.
5. Secrets Manager → delete the secrets (there's a mandatory recovery window, that's expected).
6. Double check Billing → Budgets shows no unexpected ongoing spend.
