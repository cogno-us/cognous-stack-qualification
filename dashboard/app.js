/* SPDX-License-Identifier: Apache-2.0 */
'use strict';
const data = JSON.parse(document.getElementById('qualification-data').textContent);
const repo = 'https://github.com/cogno-us/cognous-stack-qualification';
const $ = id => document.getElementById(id);
function el(tag, text, className) { const n=document.createElement(tag); if(text!==undefined)n.textContent=text; if(className)n.className=className; return n; }
function link(text, url) { const n=el('a',text); n.href=url; return n; }
function badge(text) { return el('span',text,'badge '+text.toLowerCase().replaceAll(' ','-')); }
function details(row) {
  $('dialog-id').textContent = row.scenario_id+' / '+row.mapping_status+' / NOT RUN';
  $('dialog-title').textContent=row.title;
  const body=$('dialog-content'); body.replaceChildren();
  for(const [heading,text] of [['Stimulus',row.stimulus],['Required observation',row.required_observation],['Remaining gap',row.gaps.join(' ')]] ) {body.append(el('h3',heading),el('p',text));}
  body.append(el('h3','Supporting test references'));
  if(!row.tests.length)body.append(el('p','No migrated test association has been established.'));
  for(const test of row.tests){const block=el('div',undefined,'test-ref'); block.append(link(test.symbol,`${repo}/blob/${test.suite_commit}/${test.path}`),el('code',test.path),el('code','SHA-256 '+test.sha256),el('p',test.relation),link('Original source · '+test.license,test.source_url));body.append(block);}
  body.append(el('h3','Scenario provenance'),el('p',row.scenario_provenance.source_id+' / '+row.scenario_provenance.source_section),el('code',row.scenario_provenance.document_sha256),el('p','Scenario license: '+row.scenario_license));
  $('case-dialog').showModal();
}
function cases() {
  const query=$('search').value.toLowerCase().trim(), mapping=$('mapping-filter').value, suite=$('suite-filter').value;
  const rows=data.scenarios.filter(r=>(!mapping||r.mapping_status===mapping)&&(!suite||r.suite===suite)&&(!query||JSON.stringify(r).toLowerCase().includes(query)));
  $('case-rows').replaceChildren();
  for(const r of rows){const tr=el('tr'), name=el('td'); name.append(el('span',r.scenario_id,'case-id'),el('strong',r.title));tr.append(name,el('td',r.suite,'muted'));const m=el('td');m.append(badge(r.mapping_status));const status=el('td');status.append(badge('NOT RUN'));const boundary=el('td');const button=el('button',`${r.tests.length} references · inspect gap`,'inspect');button.addEventListener('click',()=>details(r));boundary.append(button);tr.append(m,status,boundary);$('case-rows').append(tr);}
  $('visible-count').textContent=rows.length+' of '+data.scenarios.length+' cases';$('no-matches').hidden=rows.length!==0;
}
function runs(){const outcome=$('outcome-filter').value, rows=data.runs.filter(r=>!outcome||r.execution.outcome===outcome);$('run-rows').replaceChildren();for(const r of rows){const tr=el('tr'),name=el('td');name.append(link(r.execution.name||r.run_id,r.execution.url),el('small',r.source.repository));const verdict=el('td');verdict.append(badge(r.execution.outcome));const source=el('td');source.append(link(r.source.commit.slice(0,12),`https://github.com/${r.source.repository}/commit/${r.source.commit}`));source.title=r.source.commit;const record=el('td');record.append(link('Manifest ↗',`${repo}/blob/main/${r.manifest_path}`));tr.append(name,verdict,source,el('td',r.observed_at||'Not recorded','muted'),record);$('run-rows').append(tr);}$('no-runs').hidden=rows.length!==0;}
for(const tab of ['cases','runs','sources']){$('tab-'+tab).addEventListener('click',()=>{for(const name of ['cases','runs','sources']){const selected=name===tab;$('tab-'+name).classList.toggle('active',selected);$('tab-'+name).setAttribute('aria-pressed',String(selected));$(name+'-panel').hidden=!selected;}});}
for(const suite of [...new Set(data.scenarios.map(r=>r.suite))].sort()){$('suite-filter').append(el('option',suite));}
$('case-count').textContent=data.scenarios.length;$('partial-count').textContent=data.mapping_counts.PARTIAL||0;$('run-count').textContent=data.runs.length;$('run-tab-count').textContent=data.runs.length;$('wiki-count').textContent=data.wiki_specifications;
$('migration-summary').textContent=`${data.migration.moved_files} migrated files · ${data.migration.workflows} delegated workflows · ${data.migration.public_repositories} public repositories inventoried`;
$('search').addEventListener('input',cases);$('mapping-filter').addEventListener('change',cases);$('suite-filter').addEventListener('change',cases);$('outcome-filter').addEventListener('change',runs);$('close-dialog').addEventListener('click',()=>$('case-dialog').close());
cases();runs();
