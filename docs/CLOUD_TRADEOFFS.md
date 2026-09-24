# Cloud Service Trade-offs — StaySphere

## Compute: ECS Fargate vs EC2 vs Elastic Beanstalk

| Criterion | ECS Fargate (chosen) | EC2 | Elastic Beanstalk |
|---|---|---|---|
| Cost | Pay per task-second; no idle VM cost when scaled to 0 | Pay for the instance whether busy or idle; cheaper at sustained high utilization | Runs on EC2 underneath, similar cost profile to EC2 plus no extra EB charge |
| Scalability | Native horizontal scaling (desired task count / auto scaling policies) | Manual, or requires an Auto Scaling Group set up separately | Built-in auto scaling, similar ease to Fargate |
| Complexity | Moderate — task definitions, services, ALB target groups | Higher — OS patching, process management (systemd/supervisor), manual scaling setup | Lowest to get started, but abstracts away resources, making it harder to point to explicit evidence of what's provisioned |
| Operational overhead | Low — no OS to patch | High — team is responsible for OS updates, security patches | Low, but debugging "magic" failures can be harder |
| Suitability for this project | Good fit: stateless container, small team, short timeline | Overkill operational burden for the project's scope | Good fit functionally, but weaker for producing clear "here's exactly what we provisioned" evidence for grading |
| Team skill requirement | Some Docker/ECS familiarity | Linux sysadmin skills | Lowest — mostly console clicks |

**Why ECS Fargate:** the backend is already containerized (Dockerfile
exists), the team is small and time-constrained, and Fargate removes
OS-patching responsibility entirely while still giving explicit,
inspectable resources (task definitions, services) to cite as evidence —
unlike Elastic Beanstalk, which manages more on our behalf but is harder
to point to precisely in a report.

## Data layer: RDS PostgreSQL vs DynamoDB

| Criterion | RDS PostgreSQL (chosen) | DynamoDB |
|---|---|---|
| Cost | `db.t3.micro` free-tier eligible for 12 months | Pay-per-request or provisioned throughput; can be cheaper at massive scale, but this project is nowhere near that scale |
| Scalability | Vertical scaling (bigger instance) is simple; horizontal read scaling via read replicas is available but not needed here | Scales horizontally by design, better suited to very high-throughput key-value workloads |
| Complexity | Familiar SQL, joins, and multi-column filtering/sorting map directly onto the search requirement | Requires designing access patterns around partition/sort keys upfront; multi-attribute filtering (city + price range + rating + room type simultaneously) is awkward and usually needs a secondary index per query shape |
| Suitability | Listings have many filterable/sortable numeric and categorical columns, and bookings have a clear relational structure (users -> bookings -> listings) — this is a textbook relational workload | Better suited to simple, high-volume lookups by a known key, which doesn't match this project's search-heavy access pattern |
| Team skill requirement | SQL is the team's existing background | Would require learning DynamoDB's data modeling approach from scratch |

**Why RDS PostgreSQL:** the core feature of this application is
multi-filter, multi-sort search over listings — exactly what relational
indexes and `WHERE`/`ORDER BY` are built for. Modeling that well in
DynamoDB would require several secondary indexes and still not match SQL's
flexibility for ad hoc filter combinations, for no performance benefit at
this project's scale.

## Frontend hosting: S3 static site vs Amplify vs a server-rendered app

Not selected as the primary comparison, but noted: Amplify would add
CI/CD and hosting convenience at the cost of more moving parts than this
project's plain-HTML/JS frontend needs. A static S3 site keeps the
frontend deployment simple and cheap, matching the "avoid unnecessary
managed services" cost-control guidance in the project brief.
