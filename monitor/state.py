"""Pure evidence retention logic; preserves historical grades elsewhere."""
EVIDENCE_KEYS=('candidates','documents','skippedDocuments','checkedAt','lastSuccessfulAt','evidenceAt','contentHash','contentHashVersion','lastModified','textLength')
def evidence_view(source):return {k:source[k] for k in EVIDENCE_KEYS if k in source}
def retain_evidence(old,result,at):
 result=dict(result);result['checkedAt']=at
 last=old.get('lastGoodEvidence') if old.get('error') else evidence_view(old)
 old_hash=old.get('contentHash') or (last or {}).get('contentHash')
 migrated=bool(not result.get('error') and old_hash and old.get('contentHashVersion',(last or {}).get('contentHashVersion',1))!=result.get('contentHashVersion',1))
 changed=bool(not result.get('error') and not migrated and old_hash and old_hash!=result.get('contentHash'))
 if migrated:result['comparisonReset']='Extraction rules updated; new comparison baseline, not a detected policy change'
 result['changed']=changed or bool(old.get('changed'))
 if changed:
  result['changedAt']=at;result['previousEvidence']=last
 elif old.get('previousEvidence'):result['previousEvidence']=old['previousEvidence']
 if not changed and old.get('changedAt'):result['changedAt']=old['changedAt']
 if result.get('error'):
  if last and last.get('contentHash'):
   result['lastGoodEvidence']=last;result['contentHash']=last['contentHash'];result['contentHashVersion']=last.get('contentHashVersion',1);result['lastSuccessfulAt']=last.get('lastSuccessfulAt',last.get('checkedAt'))
 else:result['lastSuccessfulAt']=at;result['evidenceAt']=at
 return result,changed
