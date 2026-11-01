// Drives the pinned Index lifecycle contract (chain/contracts/IndexProtocol.sol) on a disposable loopback Ganache chain
// and prints observations as JSON. Read-only against the pin: dependencies come from the pin's own node_modules.
import { createRequire } from 'node:module';
import { readFileSync } from 'node:fs';
import { pathToFileURL } from 'node:url';
import path from 'node:path';

const chain = path.join(process.env.PROBE_INDEX_DIR, 'chain');
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
const w = new JsonRpcProvider(url, undefined, { cacheTimeout: -1 }), r = new JsonRpcProvider(url, undefined, { cacheTimeout: -1 });
w.pollingInterval = 10; r.pollingInterval = 10;
const obs = {};
try {
  const alice = await w.getSigner(0), bob = await w.getSigner(1);
  const c = await new ContractFactory(art.abi, art.evm.bytecode.object, alice).deploy();
  await c.waitForDeployment();
  const D = await c.DOMAIN(), addr = await c.getAddress();
  const v1 = b('probe claim v1'), v2 = b('probe claim v2'), v3 = b('probe claim v3');
  const id1 = await c.claimId(await alice.getAddress(), v1, ZeroHash);
  const id2 = await c.claimId(await alice.getAddress(), v2, id1);
  const id3 = await c.claimId(await alice.getAddress(), v3, ZeroHash);
  await (await c.register(D, v1, ZeroHash)).wait();
  await (await c.register(D, v2, id1)).wait();
  await (await c.register(D, v3, ZeroHash)).wait();
  await (await c.connect(bob).submitEvidence(D, id1, b('early challenge'), b('m'), ZeroHash, 2)).wait();
  obs.before = { lifecycle: Number((await c.claims(id1)).lifecycle) };
  obs.third_party_supersede = await ok(() => c.connect(bob).supersede(D, id1, id2, b('x')));
  obs.unrelated_successor = await ok(() => c.supersede(D, id1, id3, b('x')));
  obs.self_successor = await ok(() => c.supersede(D, id1, id1, b('x')));
  obs.empty_reason = await ok(() => c.supersede(D, id1, id2, ZeroHash));
  obs.supersede_ok = await ok(() => c.supersede(D, id1, id2, b('correction')));
  const o = await c.claims(id1), n = await c.claims(id2);
  obs.original = { content_preserved: o.content === v1, lifecycle: Number(o.lifecycle), successor_is_revision: o.successor === id2, author_preserved: o.author === await alice.getAddress() };
  obs.revision = { content: n.content === v2, lifecycle: Number(n.lifecycle), parent_is_original: n.parent === id1 };
  obs.withdraw_after_supersede = await ok(() => c.withdraw(D, id1, b('x')));
  obs.supersede_twice = await ok(() => c.supersede(D, id1, id2, b('x')));
  obs.evidence_after_supersede = await ok(() => c.connect(bob).submitEvidence(D, id1, b('late challenge'), b('m'), ZeroHash, 2));
  const st = await reconstruct(r, addr, art.abi);
  obs.reconstructed_original = st.claims[id1] && { content_preserved: st.claims[id1].content === v1, lifecycle: st.claims[id1].lifecycle, successor_is_revision: st.claims[id1].successor === id2 };
  obs.history = st.history.filter(h => h.id === id1 || h.id === id2).map(h => `${h.event}:${h.id === id1 ? 'v1' : 'v2'}${h.lifecycle ? ':' + h.lifecycle : ''}`);
  obs.evidence_count_on_original = Object.values(st.evidence).filter(e => e.claim === id1).length;
} finally {
  await server.close();
}
process.stdout.write(JSON.stringify(obs));
