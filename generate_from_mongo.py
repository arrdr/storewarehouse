import os
import re
import sys
import argparse
from typing import Optional, Union
from dotenv import load_dotenv
from pymongo import MongoClient
import treepoem  # Menggantikan 'barcode' (python-barcode)

def _sanitize_filename(name: str) -> str:
    return re.sub(r'[^A-Za-z0-9._-]', '_', name)

def generate_barcode(id_value: Union[int, str], output_path: Optional[str] = None) -> str:
    if not isinstance(id_value, (int, str)):
        raise TypeError("id_value must be int or str")

    data = str(id_value)

    # Default output: folder 'barcode' and filename '<id>.png'
    if output_path is None:
        out_dir = 'barcode'
        filename = f"{_sanitize_filename(data)}.png"
        output_path = os.path.join(out_dir, filename)
    else:
        out_dir = os.path.dirname(output_path)
        if not out_dir:
            # no dir specified, place into default barcode folder
            out_dir = 'barcode'
            output_path = os.path.join(out_dir, output_path)

    if out_dir and not os.path.exists(out_dir):
        os.makedirs(out_dir, exist_ok=True)

    # Prepare data for EAN-13: need 12 digits (checksum computed automatically)
    def _digits_only(s: str) -> str:
        return re.sub(r"\D", "", s)

    def _ean13_checksum(d12: str) -> int:
        s_odd = sum(int(d12[i]) for i in range(0, 12, 2))
        s_even = sum(int(d12[i]) for i in range(1, 12, 2))
        total = s_odd + s_even * 3
        return (10 - (total % 10)) % 10

    digits = _digits_only(data)

    if len(digits) == 12:
        base_digits = digits
    elif len(digits) == 13:
        # validate checksum of provided 13th digit
        chk = _ean13_checksum(digits[:12])
        if chk == int(digits[12]):
            base_digits = digits[:12]
        else:
            # fallback: use last 12 digits
            base_digits = digits[-12:]
    elif len(digits) > 13:
        base_digits = digits[-12:]
    else:
        # pad left with zeros to reach 12 digits
        base_digits = digits.zfill(12)

    # --- Proses pembuatan barcode menggunakan treepoem ---
    # Opsi includetext=True memastikan teks angka muncul sesuai standar EAN-13
    image = treepoem.generate_barcode(
        barcode_type='ean13',
        data=base_digits,
        options={"includetext": True}
    )

    # Konversi gambar ke format hitam-putih (1-bit pixels) dan simpan sebagai PNG
    image.convert('1').save(output_path)
    return output_path

def sanitize_filename(name: str) -> str:
    # keep safe chars only
    return re.sub(r'[^A-Za-z0-9._-]', '_', name)

def main(limit: int | None, output_dir: str):
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    load_dotenv(env_path)

    uri = os.getenv('MONGO_URI')
    if not uri:
        print('MONGO_URI not found in .env', file=sys.stderr)
        sys.exit(1)

    client = MongoClient(uri)
    db = client['items']
    coll = db['raw_items']

    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    cursor = coll.find({}, {'id_barang': 1})
    count = 0
    for doc in cursor:
        if limit is not None and count >= limit:
            break
        id_barang = doc.get('id_barang')
        if not id_barang:
            continue
        safe = sanitize_filename(str(id_barang))
        out_path = os.path.join(output_dir, f"{safe}.png")
        try:
            path = generate_barcode(id_barang, out_path)
            print('Generated:', path)
            count += 1
        except Exception as e:
            print('Error generating for', id_barang, '-', e, file=sys.stderr)

    client.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate barcodes from MongoDB items.raw_items')
    parser.add_argument('-n', '--limit', type=int, help='Limit number of items to process')
    parser.add_argument('-o', '--output-dir', default='barcode', help='Output directory')
    parser.add_argument('--id', help='Single id to generate (skip MongoDB)')
    args = parser.parse_args()

    if args.id:
        # generate single barcode
        path = generate_barcode(args.id, os.path.join(args.output_dir, f"{_sanitize_filename(args.id)}.png"))
        print('Generated:', path)
    else:
        main(args.limit, args.output_dir)