# Qualification baseline record (PREPARED by the builder; NOT ADOPTED)

Status: prepared input for the one exact Qualification baseline (target 2026-10-27). It is NOT adopted: only the Cognous operator or the delegated owner records adoption. Non-authorizing; UNQUALIFIED; release and production HOLD. Results are builder-side until independently adjudicated; NC4 remains INCOMPLETE under the original restricted-host profile.

| Item | sha256 |
|---|---|
| expectations v3 (frozen) (`process/mvp-chain/expectations.proposed.v3.json`) | `e84caab5f3628e8861094072c339b17fdb2ebe1805008f6083f2900c9be226a4` |
| expectations v6 (proposed baseline) (`process/mvp-chain/expectations.proposed.v6.json`) | `fe6ecf871d38061c8767e32ae62440c132b357c9b53b10de7412ef145651da4a` |
| expectations v7 (historical, unchanged: 42 rows) (`process/mvp-chain/expectations.proposed.v7.json`) | `0dc17a1984e1c3c153f3cb6e3f7fdd4dad87cdc4414728a20df0f8174e402f6b` |
| expectations v8 (in force: v7 + NC2-07, NC3-04, NC4-03a..d; NC4-03 rescoped) (`process/mvp-chain/expectations.proposed.v8.json`) | `498efc12fc1f608fb6fb53738ef61776cb576a70573f0644eb42a0f3e35f359c` |
| mandatory battery v1 (historical, unchanged) (`process/mvp-acceptance/mandatory-battery.proposed.v1.json`) | `a520e9e92534f196a48d4229d984231abbb71c23dfe63b573d919d2285bcdb16` |
| mandatory battery v2 (in force) (`process/mvp-acceptance/mandatory-battery.proposed.v2.json`) | `61228fad3d28aa9188e528ec8dbea3952308bdc8ad750d7d1628755f46e4d262` |
| candidate identity (tuple + composite) (`process/mvp-acceptance/candidate-identity.inputs.json`) | `f806d42ddd814df1c6efe7d2c9989a0c60dda82332e5ace5a67d9acb091ae897` |
| gate (`tools/mvp_acceptance_gate.py`) | `9400eba1562d989764e09b962d5f9fce8dec13203c25984eb7d33723f778958f` |
| acceptance workflow (`.github/workflows/mvp-acceptance.yml`) | `c5fdb04ce4a66e98c9cf6d7cf1b5f2e250b9740d5071ac050abce76012bc5e53` |
| environment profile (original, unchanged) (`process/mvp-acceptance/environment-profile.proposed.v1.json`) | `78518a9fa49e372203bb902e5ff59ec9dd5296234930c68d2cc6b5a42f4f9207` |
| environment profile v2 (in force; QGATE-05 host annotations) (`process/mvp-acceptance/environment-profile.proposed.v2.json`) | `4ca8f1756adc8135681114f8805b73a00f0081610a9b4c1d4e7b457f889f0d91` |
| successor profile (proposal) (`process/mvp-acceptance/environment-profile.trusted-host-successor.proposed.v1.json`) | `a8d7e526dd3d8488a399434651439f2c87d8c627e7995c20a421291eab0f1ea5` |
| harness: _ingress.py (`suites/mvp-chain/_ingress.py`) | `9667d46dbda473c32de48dc8fa173fab2f083cd6b37ae25e0f21132de1ee4031` |
| harness: _chain.py (`suites/mvp-chain/_chain.py`) | `552c5608a7469ac0d08097bdb14dc1c3a46a4725d49cdccf5383b8614b7c5ca7` |
| harness: _kwflow.py (`suites/mvp-chain/_kwflow.py`) | `ce84b3d299c033944b2bf12a2bf739edfc56e738beb13d92d77fe70f650ce70b` |
| harness: verdict.py (`suites/mvp-chain/verdict.py`) | `6fd42002ccc2f7836a512888f871a9a71f7f7aee7ed12c0e6242d3c83cc6b0e4` |

Candidate tuple (candidate-identity.inputs.json): Control Plane 7a4bcd40, Runtime c5e97e87, Replay 40012b8c, Evidence Pack 7b9511f2, ODES 1a5e1d30, Verifier c0b8ba1f, Action Manifest fa170815, hub c897266b (git tree ids in the composite block).

Candidate commitment (`candidate-commitment.proposed.v4.json`): its sha256 cannot be written into any committed file (it would change the commitment); it is REPORTED in the PR comment of the head that carries this record and supplied from outside the checkout.

Adoption record (blank, for the owner): adopted by ______ on ______, Qualification commit ______, commitment sha256 ______.
