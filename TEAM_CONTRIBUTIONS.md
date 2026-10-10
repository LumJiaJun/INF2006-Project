# Team Contributions

Class: EP2

Group: G014

The team confirmed the following final contribution summary for submission. The
artefact and evidence columns identify traceable examples rather than claiming
that one person worked alone on every listed file.

| Member | Role | Artefacts / commits | Test / evidence ownership | Reflection |
|--------|------|---------------------|---------------------------|------------|
| Lum Jia Jun (2500022) | Functional Testing and Cloud Deployment Support | Final function testing and cloud-deployment support; repository history includes the early project baseline and documented Azure alternative (`5206523`, `9038862`, `4e705d7`, `2f1cdaa`). | Supported final functional checks and deployment review; relevant shared evidence is in `evidence/test-functional.md` and `evidence/cloud-verification-2026-10-06.md`. | Final testing showed that a working cloud service needs both user-flow checks and deployment evidence, not configuration alone. |
| Nixon Lee Disheng (2500594) | Infrastructure, Terraform and AWS Lead | Created the diagrams, planned the infrastructure, wrote the Terraform configuration, and set up the cloud database and AWS services under `src/infrastructure/` and `evidence/`. | Led Terraform validation, deployment verification, security, monitoring, load/recovery testing and the submission preflight. | Managed services reduced server administration, but IAM, networking, cost, recovery and evidence still required deliberate design and repeated verification. |
| Madugula Adheesh (2500670) | Data and Machine Learning Lead | Cleaned the data, trained and created the machine-learning model, and tested it; related history includes `8ff78af`, `719b35e` and `77e255b`, with final reproducible artefacts under `analytics/` and `data/`. | Contributed data/model testing represented by `evidence/test-data-ai.md`, `analytics/artifacts/model_evaluation.json` and the reproducible training workflow. | Model development reinforced the need to compare against a baseline, preserve preprocessing with the model and report substantial residual error honestly. |
| Leow Yi Hao Ignatius (2501538) | Frontend and AWS Integration Contributor | Created the website frontend, linked it to AWS, and completed the independent clean-Windows review recorded on 9 October 2026. | Owned the independent reproduction and review recorded in `evidence/clean-zip-qa-2026-10-07.md` and `evidence/sanity-review-fixes-2026-10-09.md`. | Independent review caught packaging, retry, validation and report issues that were less visible to the primary implementer. |
| Wong Zhen Ho Brendan (2503427) | Documentation and Model/Frontend Contributor | Prepared documentation and made minor model/frontend changes; repository history includes navigation and test hardening in `b38dcda` and `2024589`. | Contributed frontend regression and failure-path test review represented by the automated test suite and `evidence/test-functional.md`. | The work showed that clear documentation and edge-case tests are both necessary for a usable and defensible cloud application. |
