from pathlib import Path
import json
from playwright.sync_api import sync_playwright,expect
ROOT=Path(__file__).resolve().parents[1]
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
 page=b.new_page(viewport={'width':1440,'height':1000});errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 page.goto('http://127.0.0.1:5173',wait_until='networkidle')
 expect(page.get_by_role('heading',name='Current monitoring health')).to_be_visible()
 expect(page.get_by_text('For demonstration only. Not medical advice. Public hospital-policy data; no patient data.')).to_be_visible()
 page.get_by_role('button',name='Español',exact=True).click();expect(page.get_by_text('Solo para demostración.',exact=False)).to_be_visible();page.get_by_role('button',name='English',exact=True).click()
 page.get_by_role('button',name='Hospital directory',exact=True).click();page.get_by_role('textbox',name='Search hospitals').fill('Bertrand')
 page.get_by_role('button',name='Bertrand Chaffee Hospital',exact=True).click();page.get_by_role('button',name='Current evidence',exact=True).click()
 expect(page.get_by_text('Last successful retrieval',exact=True)).to_be_visible()
 card=page.locator('.evidence-card').first;card.locator('summary').click();card.get_by_label('Review check',exact=True).select_option('maxFpl');card.get_by_label('Reviewer alias (no personal details)',exact=True).fill('SYN-Reviewer-01');card.get_by_label('Reason and follow-up',exact=True).fill('Synthetic workflow test on a public source. Further review required.');card.get_by_role('button',name='Save evidence decision').click();expect(card.get_by_text('Decision saved.',exact=False)).to_be_visible()
 page.keyboard.press('Escape');page.locator('nav button').filter(has_text='Evidence & review').click()
 with page.expect_download() as d:page.get_by_role('button',name='Export reviews',exact=False).click()
 d.value.save_as(str(ROOT/'.local/test-review-export.json'));export=json.load(open(ROOT/'.local/test-review-export.json'));assert export['records'];assert export['records'][0]['baselineUnchanged']
 page.get_by_label('Import review records').set_input_files(str(ROOT/'.local/test-review-export.json'));expect(page.get_by_text('validated review records.',exact=False)).to_be_visible()
 page.get_by_role('button',name='Needs attention',exact=True).click();assert page.locator('.source-list>button').count()>0
 page.screenshot(path=str(ROOT/'v2-review.png'),full_page=True,animations='disabled')
 page.locator('nav button').filter(has_text='AI evidence lab').click();expect(page.get_by_role('button',name='Extract cited evidence')).to_be_disabled()
 page.get_by_role('button',name='Methodology',exact=True).click();expect(page.get_by_role('heading',name='Current-law rubric: partner approval required')).to_be_visible()
 page.set_viewport_size({'width':390,'height':844});page.get_by_role('button',name='Open navigation').click();page.get_by_role('button',name='Hospital directory',exact=True).click();page.get_by_role('textbox',name='Search hospitals').fill('Albany Medical Center');expect(page.locator('tbody tr')).to_have_count(2)
 assert page.evaluate('document.documentElement.scrollWidth<=innerWidth');page.screenshot(path=str(ROOT/'v2-mobile.png'),full_page=True,animations='disabled')
 assert not errors,errors
 print('V2 browser checks passed: health, bilingual safety notice, cited decisions, export/import, attention queue, AI off by default, rubric gate, mobile cards; no runtime errors.')
 b.close()
