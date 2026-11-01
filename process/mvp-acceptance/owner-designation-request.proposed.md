# Request to the repository owner: designate the independent Qualification reviewer (DRAFT text)

Status: draft prepared by the builder. Not posted anywhere (not on issue #218). Non-authorizing.

To the owner of `cogno-us/cognous-stack-qualification`:

The MVP candidate testing is complete or partially complete on the builder side; independent adjudication is pending because no authorized independent Qualification owner is recorded. Qualification must own the oracle and every verdict; the builder only prepares inputs and does not merge.

Please:
1. Designate the independent Qualification reviewer(s) (a person or an organization separate from the builder and from the Runtime/Control Plane authors), naming the role the designation grants (review of PRs #226, #223, #225 in that merge order; adjudication of the oracle rows; decision on the trusted-host successor profile; authority to accept or reject a gate verdict).
2. Record the identity and delegation in this repository, for example `process/qualification-owner.md`, with: legal or account identity, date, the scope and time limit of the delegation, who delegated it, how a later change is made, and a statement that the builder's own agents cannot approve their own work.
3. Decide, as operator, the scope change: no Yama host will be provisioned; the original restricted-host profile and its INCOMPLETE NC4 host requirements stay unchanged; the successor profile `environment-profile.trusted-host-successor.proposed.v1.json` is only a proposal until you and the designated reviewer approve it.
4. Confirm the target date for the oracle baseline and which tuple (`candidate-identity.inputs.json`, composite identity) is the candidate.

Until then every result is labelled: **Candidate testing complete or partially complete; independent adjudication pending.** Release and production stay HOLD.
