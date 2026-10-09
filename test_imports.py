import unittest,sys,base64,io,zipfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from imports import extract_document
class Imports(unittest.TestCase):
 def test_csv_preview_separates_cargo_and_freight(self):
  text='produto;peso;valor_carga;contrato_valor;chave\nCarga;500;20000;10000;'+('1'*44)+'\n'
  result=extract_document('dados.csv',base64.b64encode(text.encode()).decode())
  self.assertEqual(result['fields']['valor_carga'],'20000');self.assertEqual(result['fields']['contrato_valor'],'10000');self.assertEqual(result['keys'],['1'*44])
 def test_xlsx_reads_headers_without_excel(self):
  raw=io.BytesIO()
  with zipfile.ZipFile(raw,'w') as z:z.writestr('xl/worksheets/sheet1.xml','<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData><row r="1"><c r="A1" t="inlineStr"><is><t>produto</t></is></c><c r="B1" t="inlineStr"><is><t>peso</t></is></c></row><row r="2"><c r="A2" t="inlineStr"><is><t>Teste</t></is></c><c r="B2"><v>500</v></c></row></sheetData></worksheet>')
  r=extract_document('a.xlsx',base64.b64encode(raw.getvalue()).decode());self.assertEqual(r['fields']['produto'],'Teste');self.assertEqual(r['fields']['peso'],'500')
 def test_invalid_file(self):
  with self.assertRaises(ValueError):extract_document('a.pdf',base64.b64encode(b'not pdf').decode())
if __name__=='__main__':unittest.main()
