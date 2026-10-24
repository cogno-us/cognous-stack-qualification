# Qualification baseline record (PREPARED by the builder; NOT ADOPTED)

Status: prepared input for the one exact Qualification baseline (target 2026-10-27). It is NOT adopted: only the Cognous operator or the delegated owner records adoption. Non-authorizing; UNQUALIFIED; release and production HOLD. Results are builder-side until independently adjudicated; NC4 remains INCOMPLETE under the original restricted-host profile.

| Item | sha256 |
|---|---|
| expectations v3 (frozen) (`process/mvp-chain/expectations.proposed.v3.json`) | `e84caab5f3628e8861094072c339b17fdb2ebe1805008f6083f2900c9be226a4` |
| expectations v6 (proposed baseline) (`process/mvp-chain/expectations.proposed.v6.json`) | `fe6ecf871d38061c8767e32ae62440c132b357c9b53b10de7412ef145651da4a` |
| expectations v7 (in force: v6 + NC7-01..03 + NC4-04) (`process/mvp-chain/expectations.proposed.v7.json`) | `0dc17a1984e1c3c153f3cb6e3f7fdd4dad87cdc4414728a20df0f8174e402f6b` |
| mandatory battery (`process/mvp-acceptance/mandatory-battery.proposed.v1.json`) | `a520e9e92534f196a48d4229d984231abbb71c23dfe63b573d919d2285bcdb16` |
| candidate identity (tuple + composite) (`process/mvp-acceptance/candidate-identity.inputs.json`) | `e7484a0afa1758b3925801ae6cf70a718f676eaa593addb9c20d739b9654c7fb` |
| gate (`tools/mvp_acceptance_gate.py`) | `532c90684c46115eb69ce7bca527f357418a2863f004b5bd92a1001b76969e20` |
| acceptance workflow (`.github/workflows/mvp-acceptance.yml`) | `f17f55ea8840c6c45ba87ed863c03e7470c069ec4fde47a15fb1d4f9f60067ba` |
| environment profile (original, unchanged) (`process/mvp-acceptance/environment-profile.proposed.v1.json`) | `78518a9fa49e372203bb902e5ff59ec9dd5296234930c68d2cc6b5a42f4f9207` |
| successor profile (proposal) (`process/mvp-acceptance/environment-profile.trusted-host-successor.proposed.v1.json`) | `a8d7e526dd3d8488a399434651439f2c87d8c627e7995c20a421291eab0f1ea5` |
| harness: _ingress.py (`suites/mvp-chain/_ingress.py`) | `c0ef3fcd688578dfbc261d9feb95572f55c46eb698db127a5af789623e3566fe` |
| harness: _chain.py (`suites/mvp-chain/_chain.py`) | `8899fa24b7389d46e345aed76cbc031e1481f7ea7ff345ab71c97dea8b2396b5` |
| harness: _kwflow.py (`suites/mvp-chain/_kwflow.py`) | `ce84b3d299c033944b2bf12a2bf739edfc56e738beb13d92d77fe70f650ce70b` |
| harness: verdict.py (`suites/mvp-chain/verdict.py`) | `6fd42002ccc2f7836a512888f871a9a71f7f7aee7ed12c0e6242d3c83cc6b0e4` |

Candidate tuple (candidate-identity.inputs.json): Control Plane 7a4bcd40, Runtime c5e97e87, Replay 40012b8c, Evidence Pack 7b9511f2, ODES 1a5e1d30, Verifier c0b8ba1f, Action Manifest fa170815, hub c897266b (git tree ids in the composite block).

Candidate commitment (`candidate-commitment.proposed.v4.json`): its sha256 cannot be written into any committed file (it would change the commitment); it is REPORTED in the PR comment of the head that carries this record and supplied from outside the checkout.

Adoption record (blank, for the owner): adopted by ______ on ______, Qualification commit ______, commitment sha256 ______.
