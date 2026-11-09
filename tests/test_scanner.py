import unittest
from unittest.mock import patch
from scanner import Page,candidates,validate_url,UnsafeUrl
class ScannerTests(unittest.TestCase):
 def test_no_script_in_evidence(self):
  p=Page();p.feed('<h1>Financial assistance</h1><script>400% fabrication</script><p>Call our office</p><a href="app.pdf">Application</a>')
  self.assertNotIn('fabrication',p.text());self.assertEqual(len(candidates(p.text(),'https://example.org')),0);self.assertEqual(p.links[0]['href'],'app.pdf')
 def test_candidate_is_source_substring_not_compliance_verdict(self):
  text='Patients with income up to 400% of the federal poverty level may apply.'
  found=candidates(text,'https://example.org/policy.pdf',3)
  self.assertTrue(found);self.assertIn(found[0]['quote'],text);self.assertEqual(found[0]['page'],3);self.assertNotIn('compliant',found[0])
 def test_http_and_offhost_sources_rejected(self):
  for url in ['http://example.org','https://evil.example','https://user:pass@example.org','https://example.org:8443']:
   with self.assertRaises(UnsafeUrl):validate_url(url,{'example.org'})
 def test_dns_private_addresses_rejected(self):
  with patch('socket.getaddrinfo',return_value=[(2,1,6,'',('127.0.0.1',443))]):
   with self.assertRaises(UnsafeUrl):validate_url('https://example.org',{'example.org'})
 def test_public_source_allowed(self):
  with patch('socket.getaddrinfo',return_value=[(2,1,6,'',('93.184.216.34',443))]):self.assertEqual(validate_url('https://example.org',{'example.org'}),'https://example.org')
if __name__=='__main__':unittest.main()

class RetentionTests(unittest.TestCase):
 def test_failure_keeps_last_good_evidence_and_date(self):
  from state import retain_evidence
  old={'contentHash':'abc','checkedAt':'old','candidates':[{'quote':'Public quote'}],'documents':[]}
  result,changed=retain_evidence(old,{'error':'HTTP 404','candidates':[]},'new')
  self.assertEqual(result['lastGoodEvidence']['candidates'],old['candidates']);self.assertEqual(result['lastSuccessfulAt'],'old');self.assertFalse(changed)
 def test_change_after_failure_still_keeps_before_and_after(self):
  from state import retain_evidence
  original={'contentHash':'abc','checkedAt':'old','candidates':[{'quote':'Before'}]}
  failed,_=retain_evidence(original,{'error':'HTTP 403'},'failed')
  current,changed=retain_evidence(failed,{'contentHash':'def','candidates':[{'quote':'After'}]},'new')
  self.assertTrue(changed);self.assertEqual(current['previousEvidence']['candidates'][0]['quote'],'Before');self.assertEqual(current['candidates'][0]['quote'],'After')
 def test_parser_upgrade_does_not_masquerade_as_policy_change(self):
  from state import retain_evidence
  old={'contentHash':'old','checkedAt':'old'}
  result,changed=retain_evidence(old,{'contentHash':'new','contentHashVersion':2,'candidates':[]},'new')
  self.assertFalse(changed);self.assertIn('comparisonReset',result)
