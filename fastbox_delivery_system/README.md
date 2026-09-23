# FastBox Mystery Delivery System

Python implementation of the **FastBox Mystery Delivery System** assignment from Nexgensis Technologies.

## Requirements

- Python 3.10+
- No third-party runtime dependencies
- `pytest` is only needed to run the automated tests

## Project structure

```text
fastbox-delivery-system/
├── data/
│   ├── base_case.json
│   └── test_cases/
│       ├── test_case_1.json
│       ├── ...
│       └── test_case_10.json
├── src/
│   ├── __init__.py
│   ├── delivery_system.py
│   └── main.py
├── tests/
│   └── test_delivery_system.py
├── report.json
├── requirements.txt
├── .gitignore
└── README.md
```

## Approach

1. Parse the JSON using Python's standard `json` module.
2. Normalize both JSON formats supplied with the assignment:
   - entity lists such as `{ "id": "W1", "location": [0, 0] }`
   - entity dictionaries such as `{ "W1": [0, 0] }`
3. Calculate Euclidean distance with `math.hypot`.
4. Assign every package to the nearest agent based on the agent's **initial position to the package's warehouse**.
5. Simulate packages in input order. For each package, the agent travels:

   `current agent position -> warehouse -> package destination`

6. Update the agent's position to the delivered package's destination.
7. Report the number of packages, total distance and average distance per package (`efficiency`) for each agent.
8. Select the best agent using the lowest efficiency among agents that delivered at least one package.
9. Save the final report as JSON.
10. Optionally export the top performer to CSV as a bonus feature.

## Assumptions and ambiguity decisions

The assignment does not define a routing order or tie-breaking rule. The following deterministic assumptions are documented explicitly:

- **Assignment basis:** package assignment uses each agent's initial location, as stated in the requirement.
- **Delivery order:** packages assigned to an agent are processed in the same order in which they appear in the input JSON.
- **Agent movement:** after delivering a package, an agent remains at that destination. Therefore, the next delivery starts from that destination.
- **No final return:** an agent does not return to its previous location or depot after its final delivery.
- **Tie-breaking:** if multiple agents are exactly equally close to a warehouse, the lexicographically smaller agent ID is selected.
- **Best agent:** efficiency means average distance per delivered package. Agents with zero deliveries are excluded; ties are resolved by agent ID.
- **Rounding:** distance and efficiency are rounded to two decimal places in the generated report.

These choices keep the simulation deterministic and avoid silently inventing an additional depot/return trip that is not specified by the assignment.

## Run the simulator

From the repository root:

```bash
python src/main.py data/base_case.json
```

This creates `report.json` in the current directory.

You can choose another output path:

```bash
python src/main.py data/test_cases/test_case_1.json -o test_case_1_report.json
```

## Run tests

Install pytest if necessary:

```bash
pip install pytest
```

Then run:

```bash
pytest -q
```

The test suite checks the distance calculation, package assignment, base-case report, all 10 supplied test cases, support for both input formats, deterministic tie-breaking, and the CSV bonus.

## Complexity

For `P` packages, `A` agents and `W` warehouses:

- Assignment: `O(P * A)`
- Simulation: `O(P)` after assignment
- Space: `O(P + A + W)`

The implementation intentionally uses only the Python standard library for the application itself.

## Bonus: top performer CSV

The implementation includes an optional CSV export for the selected top performer:

```bash
python src/main.py data/base_case.json --top-performer-csv top_performer.csv
```
