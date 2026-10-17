// SPDX-License-Identifier: Apache-2.0
// Scenario driver for C03/C04 against the pinned Index chain profile (chain/contracts/IndexProtocol.sol).
// Runs from a runner-owned copy of the pinned chain/ directory (named by SCN_INDEX_CHAIN_DIR) on a disposable
// loopback Ganache chain and prints deterministic observations as JSON (no hashes, no timestamps).
// Read-only against the pin: the pinned contract, client.mjs and reconstruct.mjs are used unmodified.
import { createRequire } from 'node:module';
import { readFileSync } from 'node:fs';
import { pathToFileURL } from 'node:url';
import path from 'node:path';

const chain = process.env.SCN_INDEX_CHAIN_DIR;
const req = createRequire(chain + path.sep);
const ganache = req('ganache'), solc = req('solc');
const { ContractFactory, JsonRpcProvider, ZeroHash } = req('ethers');
const { commitment, utf8 } = await import(pathToFileURL(path.join(chain, 'client.mjs')));
const { reconstruct } = await import(pathToFileURL(path.join(chain, 'reconstruct.mjs')));

const source = readFileSync(path.join(chain, 'contracts', 'IndexProtocol.sol'), 'utf8');
const out = JSON.parse(solc.compile(JSON.stringify({ language: 'Solidity', sources: { 'I.sol': { content: source } },
  settings: { optimizer: { enabled: true, runs: 200 }, evmVersion: 'shanghai', outputSelection: { '*': { '*': ['abi', 'evm.bytecode.object'] } } } })));
if ((out.errors ?? []).some(e => e.severity === 'error')) throw new Error(JSON.stringify(out.errors));
const art = out.contracts['I.sol'].IndexProtocol;
const b = s => commitment(utf8(s));
const ok = async f => { try { const tx = await f(); if (tx.wait) await tx.wait(); return true; } catch { return false; } };

const server = ganache.server({ logging: { quiet: true }, chain: { chainId: 31337, hardfork: 'shanghai' }, wallet: { deterministic: true } });
await server.listen(0, '127.0.0.1');
const url = `http://127.0.0.1:${server.address().port}`;
const w = new JsonRpcProvider(url, undefined, { cacheTimeout: -1 });
const r1 = new JsonRpcProvider(url, undefined, { cacheTimeout: -1 });
const r2 = new JsonRpcProvider(url, undefined, { cacheTimeout: -1 });
for (const p of [w, r1, r2]) p.pollingInterval = 10;
const obs = {};
try {
  const alice = await w.getSigner(0), bob = await w.getSigner(1), carol = await w.getSigner(2);
  const aliceAddr = await alice.getAddress();
  const c = await new ContractFactory(art.abi, art.evm.bytecode.object, alice).deploy();
  await c.waitForDeployment();
  const D = await c.DOMAIN(), addr = await c.getAddress();
  const v1 = b('c04 claim v1'), v2 = b('c04 claim v2'), v3 = b('c04 unrelated claim');
  const id1 = await c.claimId(aliceAddr, v1, ZeroHash);
  const id2 = await c.claimId(aliceAddr, v2, id1);
  const id3 = await c.claimId(aliceAddr, v3, ZeroHash);
  await (await c.register(D, v1, ZeroHash)).wait();
  await (await c.register(D, v2, id1)).wait();
  await (await c.register(D, v3, ZeroHash)).wait();
  await (await c.connect(bob).submitEvidence(D, id1, b('early challenge'), b('m'), ZeroHash, 2)).wait();

  // ---------------- C04: supersession preserves history; status recomputes from the logs
  const sup = {};
  sup.third_party_supersede_refused = !(await ok(() => c.connect(bob).supersede(D, id1, id2, b('x'))));
  sup.unrelated_successor_refused = !(await ok(() => c.supersede(D, id1, id3, b('x'))));
  sup.self_successor_refused = !(await ok(() => c.supersede(D, id1, id1, b('x'))));
  sup.empty_reason_refused = !(await ok(() => c.supersede(D, id1, id2, ZeroHash)));
  sup.supersede_by_author_accepted = await ok(() => c.supersede(D, id1, id2, b('correction')));
  const o = await c.claims(id1), n = await c.claims(id2);
  sup.original = { content_preserved: o.content === v1, lifecycle: Number(o.lifecycle), successor_is_revision: o.successor === id2, author_preserved: o.author === aliceAddr };
  sup.revision = { content_preserved: n.content === v2, lifecycle: Number(n.lifecycle), parent_is_original: n.parent === id1 };
  sup.withdraw_after_supersede_refused = !(await ok(() => c.withdraw(D, id1, b('x'))));
  sup.supersede_twice_refused = !(await ok(() => c.supersede(D, id1, id2, b('x'))));
  sup.later_criticism_of_superseded_claim_recorded = await ok(() => c.connect(carol).submitEvidence(D, id1, b('late challenge'), b('m2'), ZeroHash, 2));
  obs.supersession = sup;

  const s1 = await reconstruct(r1, addr, art.abi);
  const s2 = await reconstruct(r2, addr, art.abi);
  const label = h => `${h.event}:${h.id === id1 ? 'v1' : h.id === id2 ? 'v2' : h.id === id3 ? 'v3' : 'other'}${h.lifecycle ? ':' + h.lifecycle : ''}`;
  const direct = {};
  for (const [name, id] of [['v1', id1], ['v2', id2], ['v3', id3]]) {
    const d = await c.claims(id);
    direct[name] = { lifecycle: Number(d.lifecycle), successor_is_v2: d.successor === id2, content_equals_commitment: true };
  }
  const recon = {};
  for (const [name, id] of [['v1', id1], ['v2', id2], ['v3', id3]]) {
    const d = s1.claims[id];
    recon[name] = { lifecycle: d.lifecycle, successor_is_v2: d.successor === id2, content_equals_commitment: true };
  }
  const stable = st => JSON.stringify({ claims: st.claims, evidence: st.evidence });
  obs.reconstruction = {
    from_logs_equals_direct_reads: JSON.stringify(direct) === JSON.stringify(recon),
    two_independent_readers_agree: stable(s1) === stable(s2),
    history_order: s1.history.map(label),
    history_has_registered_before_lifecycle_change: s1.history.findIndex(h => h.event === 'Registered') < s1.history.findIndex(h => h.event === 'LifecycleChanged'),
    original_content_reconstructed: s1.claims[id1].content === v1,
    evidence_on_original_after_supersession: Object.values(s1.evidence).filter(e => e.claim === id1).length,
    reconstructed_lifecycles: recon,
    finality: s1.finality,
  };

  // ---------------- C04: copied / dependent evidence
  const cid = await c.claimId(aliceAddr, b('c04 corroboration claim'), ZeroHash);
  await (await c.register(D, b('c04 corroboration claim'), ZeroHash)).wait();
  const original = b('one original measurement');
  const man = b('manifest: source lineage S1');
  const cp = {};
  cp.original_support_accepted = await ok(() => c.submitEvidence(D, cid, original, man, ZeroHash, 1));
  cp.exact_duplicate_refused = !(await ok(() => c.submitEvidence(D, cid, original, man, ZeroHash, 1)));
  cp.same_wallet_copy_with_other_manifest_accepted = await ok(() => c.submitEvidence(D, cid, original, b('manifest: re-hosted copy 1'), ZeroHash, 1));
  cp.other_wallet_copy_accepted = await ok(() => c.connect(bob).submitEvidence(D, cid, original, man, ZeroHash, 1));
  cp.third_wallet_copy_accepted = await ok(() => c.connect(carol).submitEvidence(D, cid, original, b('manifest: re-hosted copy 2'), ZeroHash, 1));
  const independent = b('a genuinely different measurement');
  cp.independent_support_accepted = await ok(() => c.connect(bob).submitEvidence(D, cid, independent, b('manifest: source lineage S2'), ZeroHash, 1));
  const s3 = await reconstruct(r1, addr, art.abi);
  const ev = Object.values(s3.evidence).filter(e => e.claim === cid);
  const distinct = new Set(ev.map(e => e.content));
  const copies = ev.filter(e => e.content === original);
  cp.evidence_records_on_claim = ev.length;
  cp.distinct_content_commitments = distinct.size;
  cp.records_sharing_the_original_content_commitment = copies.length;
  cp.copies_are_visible_not_merged = copies.length === 4;
  cp.fields_exposed = Object.keys(ev[0]).sort();
  cp.contract_computes_no_corroboration_or_independence_value = !art.abi.some(f => /independ|corrob|score|weight/i.test(f.name ?? ''));
  obs.copied_evidence = cp;

  // ---------------- C03: a statement commitment is recorded, never verified
  const sc = {};
  const forged = commitment(utf8('a forged statement digest nobody verified'));
  const cid2 = await c.claimId(aliceAddr, b('c03 claim'), ZeroHash);
  await (await c.register(D, b('c03 claim'), ZeroHash)).wait();
  sc.forged_statement_commitment_stored = await ok(() => c.connect(bob).submitEvidence(D, cid2, b('c03 evidence'), b('c03 manifest'), forged, 1));
  const s4 = await reconstruct(r2, addr, art.abi);
  const e4 = Object.values(s4.evidence).filter(e => e.claim === cid2)[0];
  sc.evidence_record_fields = Object.keys(e4).sort();
  sc.verified_flag_present = Object.keys(e4).some(k => /verif|assur|trust|valid/i.test(k));
  sc.reconstructed_statement_equals_commitment = e4.statement === forged;
  sc.abi_has_verification_entry = art.abi.some(f => /verif|assur/i.test(f.name ?? ''));
  obs.statement_commitment = sc;
} finally {
  await server.close();
}
process.stdout.write(JSON.stringify(obs));
