"""Synthetic normalized fixtures and frozen evidence spans, no providers or product writes."""
import hashlib
import json
from pathlib import Path

root=Path(__file__).parent
cases=[]
def add(name,fmt,text,blocks,questions,method='synthetic-normalized'):
    document={'schema_version':1,'document_id':'evaluation-'+name,'tenant_id':'tenant-rag2-evaluation',
        'original_format':fmt,'origin':{'source':'synthetic-evaluation','uploaded_by':'synthetic-operator','tenant_id':'tenant-rag2-evaluation','content_hash':hashlib.sha256(text.encode()).hexdigest()},
        'text':text,'blocks':blocks,'file_metadata':{},'warnings':[], 'extraction_method':method,'result':'extracted'}
    references=[]
    for query,evidence,page in questions:
        start=text.index(evidence)
        assert text.find(evidence,start+1)==-1, 'Ground truth must be unambiguous'
        references.append({'query':query,'document_id':document['document_id'],'evidence':evidence,
            'normalized_span':[start,start+len(evidence)],'page':page})
    cases.append({'name':name,'fixture_kind':'synthetic normalized input, not a claim of file extraction','document':document,'questions':references})

rule='relative_delta > 20 % AND absolute_delta > 100 EUR/day'
clarification='Ambos límites son estrictos: un valor exactamente igual no supera el umbral.'
md='# Operación FinOps\n\n## Anomalías\n\nLas anomalías diarias se rigen por la siguiente condición conjunta.\n\n```text\n'+rule+'\n```\n\n'+clarification+'\n\n## Etiquetas\n\nLa etiqueta owner identifica al responsable operativo.\n'
add('markdown','md',md,[{'kind':'heading','level':1,'text':'Operación FinOps','source_lines':[1,1]},
    {'kind':'heading','level':2,'text':'Anomalías','source_lines':[3,3]},
    {'kind':'code','language':'text','text':rule,'source_lines':[7,9]},
    {'kind':'paragraph','text':clarification,'source_lines':[11,11]}],
    [('¿Qué dos condiciones deben cumplirse para detectar la anomalía diaria?',rule,None),('¿Qué ocurre al alcanzar exactamente el límite de anomalía?',clarification,None)])

paragraphs=['La política de soporte mantiene un presupuesto de emergencia separado.']+[f'La nota operativa {i} conserva trazabilidad y responsable para decisiones de soporte.' for i in range(70)]
paragraphs.insert(35,'El presupuesto de emergencia del equipo Boreal es de 450 EUR por mes.')
paragraphs.append('La revisión de consumo de Boreal se celebra el martes a las 09:30 UTC.')
txt='\n\n'.join(paragraphs)
add('plain-text','txt',txt,[{'kind':'text','text':txt,'source_lines':[1,len(txt.splitlines())]}],
    [('¿Cuánto presupuesto mensual de emergencia tiene Boreal?','El presupuesto de emergencia del equipo Boreal es de 450 EUR por mes.',None),('¿Cuándo revisa Boreal su consumo?','La revisión de consumo de Boreal se celebra el martes a las 09:30 UTC.',None)])

page1='Informe de activos\nProyecto Álamo\nRecurso Coste Responsable\nvm-alamo-01 120 EUR Lucía\nvm-alamo-02 85 EUR Víctor'
page2='Condiciones operativas\nEl proyecto Álamo archiva instantáneas los viernes.\nLa retención máxima de instantáneas es de 18 días.'
pdf=page1+'\n\n'+page2
pdfblocks=[{'kind':'text','text':line,'page':page,'bbox':[10,10+i*12,500,20+i*12],'coordinate_system':'pdf_points'}
    for page,body in [(1,page1),(2,page2)] for i,line in enumerate(body.splitlines())]
pdfblocks.insert(len(page1.splitlines()),{'kind':'table','page':1,'bbox':[10,34,500,70],'coordinate_system':'pdf_points','rows':[['Recurso','Coste','Responsable'],['vm-alamo-01','120 EUR','Lucía'],['vm-alamo-02','85 EUR','Víctor']]})
add('digital-pdf','pdf',pdf,pdfblocks,[('¿Qué coste y responsable tiene vm-alamo-02?','vm-alamo-02 85 EUR Víctor',1),('¿Cuántos días se conservan las instantáneas de Álamo?','La retención máxima de instantáneas es de 18 días.',2)])

ocr1='Registro escaneado de continuidad\nEl simulacro de recuperación del equipo Cobalto se realiza en noviembre.'
ocr2='El objetivo de recuperación de Cobalto es de 45 minutos.\nConservar el acta de cada simulacro.'
ocr=ocr1+'\n\n'+ocr2
ocrblocks=[{'kind':'text','method':'ocr','text':line,'page':page,'bbox':[8,8+i*24,900,24+i*24],'coordinate_system':'render_pixels'}
    for page,body in [(1,ocr1),(2,ocr2)] for i,line in enumerate(body.splitlines())]
add('scanned-pdf','pdf',ocr,ocrblocks,[('¿En qué mes se realiza el simulacro de Cobalto?','El simulacro de recuperación del equipo Cobalto se realiza en noviembre.',1),('¿Cuál es el objetivo de recuperación de Cobalto?','El objetivo de recuperación de Cobalto es de 45 minutos.',2)],method='synthetic-ocr-normalized')

for name,fmt,team,budget,day in [('word-modern','docx','Dalia','720','jueves'),('word-legacy','doc','Encina','930','lunes')]:
    first={'kind':'heading','level':1,'text':'Plan del equipo '+team}
    intro={'kind':'paragraph','text':f'El equipo {team} dispone de {budget} EUR para pruebas trimestrales.'}
    rows=[]
    for i in range(35):
        rows.append([[{'kind':'paragraph','text':f'Actividad {i}'}], [{'kind':'paragraph','text':f'Responsable de servicio {team} {i}'}]])
    table={'kind':'table','rows':rows}
    last={'kind':'list_item','text':f'La aprobación del equipo {team} se registra cada {day}.'}
    text='\n'.join([first['text'],intro['text']]+['\t'.join(cell[0]['text'] for cell in row) for row in rows]+[last['text']])
    add(name,fmt,text,[first,intro,table,last],[(f'¿Cuál es el presupuesto trimestral de pruebas de {team}?',intro['text'],None),(f'¿Cuándo registra {team} su aprobación?',last['text'],None)])

payload={'schema_version':1,'policy':'synthetic only; fixed documents/questions/evidence before comparing; no private corpus; references independent of chunk IDs','cases':cases}
raw=json.dumps(payload,ensure_ascii=False,sort_keys=True,indent=2).encode('utf-8')
target=root/'evaluation-corpus-frozen-v2.json'
assert not target.exists(),'Do not replace frozen ground truth'
target.write_bytes(raw)
(root/'evaluation-corpus-freeze-v2.json').write_text(json.dumps({'sha256':hashlib.sha256(raw).hexdigest(),'documents':len(cases),'questions':sum(len(case['questions']) for case in cases),'characters':sum(len(case['document']['text']) for case in cases),'source':'principal synthetic fixture preparation before implementation','data_classification':'no private data','preliminary_v1':'Preserved; invalid Word fixture cell shape found before any comparison/test, corrected to actual lists-of-blocks. Text/questions/evidence unchanged.'},indent=2),encoding='utf-8')
print((root/'evaluation-corpus-freeze-v2.json').read_text())
