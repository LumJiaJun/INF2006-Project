# tests/

Automated tests, API collection or repeatable test scripts.

At least four tests are required (see report Section 6 and evidence/):
1. Functional workflow test
2. Security control test
3. Data / AI validation test
4. Scalability, resilience or recovery test

## How to run

```bash
python -m unittest discover -s tests -p "test_*.py" -v
```
