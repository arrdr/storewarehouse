import os
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()
# Configure MongoDB URI here (or set MONGO_URI in .env or environment variable).
# Example in .env: MONGO_URI=mongodb://user:pass@host:27017
MONGO_URI = os.getenv('MONGO_URI') or 'PUT_YOUR_MONGO_URI_HERE'
if MONGO_URI == 'PUT_YOUR_MONGO_URI_HERE':
    raise RuntimeError('Please set MONGO_URI in generate_table.py, .env, or environment variable')

client = MongoClient(MONGO_URI)
db = client['items']
coll = db['formatted_items']


def format_date(dt):
    if dt is None:
        return ''
    try:
        # if datetime has timezone info, format it in that timezone; otherwise assume UTC
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.strftime('%d-%m-%Y %H:%M:%S')
    except Exception:
        return str(dt)


def generate_html(rows):
    header = '''<!doctype html>
<html lang="id">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width,initial-scale=1" />
    <title>Daftar Formatted Items</title>
    <style>
      body{font-family:Arial,Helvetica,sans-serif;padding:20px}
      table{border-collapse:collapse;width:100%;max-width:1200px}
      th,td{border:1px solid #ccc;padding:8px;text-align:left}
      th{background:#f0f0f0}
    </style>
  </head>
  <body>
    <h2>Daftar Formatted Items</h2>
    <table>
      <thead>
        <tr>
          <th>Id Barang</th>
          <th>Model Pigtail</th>
          <th>Model Bearing</th>
          <th>Model Armacer</th>
          <th>Model Holder</th>
          <th>Model Produk</th>
          <th>Lot</th>
          <th>Tanggal Input</th>
        </tr>
      </thead>
      <tbody>'''

    rows_html = []
    for r in rows:
        idb = r.get('id_barang', '')
        mp = r.get('model_pigtail', '') or ''
        mb = r.get('model_bearing', '') or ''
        ma = r.get('model_armacer', '') or ''
        mh = r.get('model_holder', '')
        prod = r.get('model_produk', '') or ''
        lot = r.get('lot', '')
        dt = r.get('input_date')
        dt_s = format_date(dt)
        rows_html.append(f"<tr><td>{idb}</td><td>{mp}</td><td>{mb}</td><td>{ma}</td><td>{mh}</td><td>{prod}</td><td>{lot}</td><td>{dt_s}</td></tr>")

    footer = '''      </tbody>
    </table>
  </body>
</html>'''

    return header + '\n'.join(rows_html) + '\n' + footer


def main():
    cursor = coll.find({}, sort=[('input_date', -1)])
    rows = list(cursor)
    html = generate_html(rows)
    out = os.path.join(os.path.dirname(__file__), 'web_form.html')
    with open(out, 'w', encoding='utf-8') as f:
        f.write(html)
    print('Wrote', out, 'with', len(rows), 'rows')

    # try to open in default browser/file viewer
    try:
        if os.name == 'nt':
            os.startfile(out)
        else:
            import webbrowser
            webbrowser.open('file://' + os.path.abspath(out))
    except Exception:
        pass


if __name__ == '__main__':
    main()
