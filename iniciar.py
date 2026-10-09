"""Inicializa o sistema e abre o navegador local."""
import os,runpy,threading,webbrowser
from pathlib import Path
root=Path(__file__).resolve().parent
os.chdir(root)
port=os.environ.get('DG_PORT','8080')
if os.environ.get('DG_NO_BROWSER')!='1':threading.Timer(1.5,lambda:webbrowser.open('http://127.0.0.1:'+port)).start()
runpy.run_path(str(root/'server.py'),run_name='__main__')
