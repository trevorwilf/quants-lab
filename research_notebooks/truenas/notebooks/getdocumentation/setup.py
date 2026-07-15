pip install --update pip
pip install -r requirements-exchange-docs.txt
python -m playwright install chromium
pip install "scrapling[fetchers]"
scrapling install  
from scrapling.cli import install