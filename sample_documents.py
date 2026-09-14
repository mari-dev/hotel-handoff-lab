"""Produce actual synthetic PDF/EML files, not valid accounting invoices."""
from email.message import EmailMessage
from email.utils import formatdate,make_msgid
from pathlib import Path
import hashlib

def simple_pdf(guest,stay):
    lines=['INVOICE - SYNTHETIC DEMO / NOT VALID FOR ACCOUNTING',
           'Guest: '+guest,'Stay: '+stay,'Invoice: DEMO-001','Total: EUR 100.00']
    commands=['BT /F1 11 Tf 45 790 Td']
    for line in lines:
        safe=line.replace('\\','\\\\').replace('(','\\(').replace(')','\\)')
        commands.append('('+safe+') Tj 0 -22 Td')
    commands.append('ET')
    stream='\n'.join(commands).encode('cp1252',errors='replace')
    objects=[b'<< /Type /Catalog /Pages 2 0 R >>',
             b'<< /Type /Pages /Kids [3 0 R] /Count 1 >>',
             b'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>',
             b'<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>',
             b'<< /Length '+str(len(stream)).encode()+b' >>\nstream\n'+stream+b'\nendstream']
    data=bytearray(b'%PDF-1.4\n');offsets=[0]
    for index,obj in enumerate(objects,1):
        offsets.append(len(data));data.extend(f'{index} 0 obj\n'.encode()+obj+b'\nendobj\n')
    start=len(data);data.extend(f'xref\n0 {len(objects)+1}\n0000000000 65535 f \n'.encode())
    for offset in offsets[1:]: data.extend(f'{offset:010d} 00000 n \n'.encode())
    data.extend(f'trailer\n<< /Size {len(objects)+1} /Root 1 0 R >>\nstartxref\n{start}\n%%EOF\n'.encode())
    return bytes(data)

def sent_email(pdf):
    message=EmailMessage()
    message['From']='reception@example.invalid';message['To']='guest@example.invalid'
    message['Date']=formatdate(localtime=False);message['Message-ID']=make_msgid(domain='example.invalid')
    message['Subject']='Synthetic invoice demo - never sent'
    message.set_content('Synthetic exported Sent email fixture. No SMTP delivery occurred.')
    message.add_attachment(pdf,maintype='application',subtype='pdf',filename='invoice-demo.pdf')
    return message.as_bytes()

def place_demo_file(folder,request,kind):
    folder=Path(folder)
    if not request['stay'].strip(): raise ValueError('Enter the stay to create a sample file')
    pdf=simple_pdf(request['guest'],request['stay']);digest=hashlib.sha256(pdf).hexdigest()[:16]
    if kind=='pdf': path=folder/'pdfs'/f'demo-{digest}.pdf';data=pdf
    elif kind=='eml': path=folder/'sent'/f'demo-{digest}.eml';data=sent_email(pdf)
    else: raise ValueError('Invalid file type')
    if not path.exists():
        temp=path.with_suffix('.partial');temp.write_bytes(data);temp.replace(path)
    return path.name
