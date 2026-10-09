"""Extração com revisão humana: nenhuma importação autoriza documentos fiscais."""
import base64,io,re,zipfile,csv,shutil,subprocess,tempfile
from pathlib import Path
from xml.etree import ElementTree as ET

def extract_document(filename,content):
    try:raw=base64.b64decode(content,validate=True)
    except Exception:raise ValueError('Arquivo inválido.')
    if len(raw)>3_000_000:raise ValueError('Arquivo maior que 3 MB.')
    fields={};text='';suffix=Path(filename).suffix.lower()
    if suffix=='.pdf':
        if not raw.startswith(b'%PDF'):raise ValueError('PDF inválido.')
        try:
            from pypdf import PdfReader
            reader=PdfReader(io.BytesIO(raw))
            if len(reader.pages)>40:raise ValueError('PDF com mais de 40 páginas.')
            text='\n'.join(p.extract_text() or '' for p in reader.pages)
        except ImportError:
            if not shutil.which('pdftotext'):raise ValueError('Para importar PDF, instale o pacote opcional: python -m pip install -r requirements-optional.txt')
            with tempfile.TemporaryDirectory() as d:
                path=Path(d)/'documento.pdf';path.write_bytes(raw)
                res=subprocess.run(['pdftotext','-layout',str(path),'-'],capture_output=True,timeout=20,check=False)
                if res.returncode:raise ValueError('Não foi possível ler este PDF.')
                text=res.stdout.decode('utf-8',errors='replace')
    elif suffix=='.csv':
        text=raw.decode('utf-8-sig',errors='replace');delimiter=';' if ';' in text.splitlines()[0] else ','
        rows=list(csv.DictReader(io.StringIO(text),delimiter=delimiter))
        if rows:fields.update({k:v for k,v in rows[0].items() if k in ['produto','peso','valor_carga','ncm','contrato','ciot','pedagio_documento','pedagio_valor','contrato_valor','adiantamento','banco','agencia','conta','pix']})
    elif suffix=='.xlsx':
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            if sum(r.file_size for r in z.infolist())>15_000_000:raise ValueError('Planilha descompactada muito grande.')
            ns={'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'};strings=[]
            if 'xl/sharedStrings.xml' in z.namelist():strings=[''.join(n.itertext()) for n in ET.fromstring(z.read('xl/sharedStrings.xml')).findall('s:si',ns)]
            worksheets=sorted(n for n in z.namelist() if n.startswith('xl/worksheets/sheet') and n.endswith('.xml'))
            if not worksheets:raise ValueError('Planilha sem aba de dados.')
            sheet=ET.fromstring(z.read(worksheets[0]));rows=[]
            for row in sheet.findall('.//s:row',ns):
                cells={}
                for cell in row.findall('s:c',ns):
                    col=re.sub(r'\d','',cell.get('r',''));v=cell.find('s:v',ns);value=v.text if v is not None else ''.join(cell.itertext())
                    if cell.get('t')=='s':value=strings[int(value)]
                    cells[col]=value
                rows.append(cells)
            if len(rows)>1:
                for col,key in rows[0].items():
                    if key in ['produto','peso','valor_carga','ncm','contrato','ciot','contrato_valor','adiantamento','banco','agencia','conta','pix']:fields[key]=rows[1].get(col,'')
            text='\n'.join(' '.join(r.values()) for r in rows)
    else:raise ValueError('Use PDF, XLSX ou CSV.')
    # Identificadores fiscais de 44 dígitos; aceita espaços entre grupos na impressão.
    keys=[]
    for candidate in re.findall(r'(?:\d[ \t]*){44,}',text):
        compact=re.sub(r'\D','',candidate)
        if len(compact)==44 and compact not in keys:keys.append(compact)
    if suffix=='.pdf':
        patterns={'contrato':r'(?:contrato|contract)\s*(?:n[ºo°.]*)?\s*[:#-]?\s*(\d{4,})','ciot':r'CIOT\s*[:#-]?\s*(\d{8,})','ncm':r'NCM\s*[:#-]?\s*(\d{8})','peso':r'(?:peso bruto|peso total|peso)\s*[:#-]?\s*([\d.,]+)'}
        for k,pattern in patterns.items():
            match=re.search(pattern,text,re.I)
            if match:fields[k]=match.group(1).replace('.','').replace(',','.') if k=='peso' else match.group(1)
    if not text.strip():raise ValueError('Arquivo sem texto. PDF digitalizado requer OCR externo; não foram extraídos dados.')
    return {'fields':fields,'keys':keys,'warning':'Extração parcial. Confira as chaves e preencha os campos restantes. PDFs digitalizados não têm OCR nesta versão.','text_preview':text[:3000]}
