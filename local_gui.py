import os
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from pymongo import MongoClient
import tkinter as tk
from tkinter import messagebox

load_dotenv()
MONGO_URI = os.getenv('MONGO_URI')
if not MONGO_URI:
    raise RuntimeError('MONGO_URI not set in .env')

client = MongoClient(MONGO_URI)
db = client['items']
raw_coll = db['raw_items']
formatted_coll = db['formatted_items']


def now_plus7_datetime():
    # Get current UTC time and add 7 hours, then mark it as UTC
    # This ensures MongoDB stores the local UTC+7 value correctly
    utc_now = datetime.now(timezone.utc)
    local_plus7 = utc_now.replace(tzinfo=None) + timedelta(hours=7)
    # Return as UTC timezone so MongoDB stores the UTC+7 value
    return local_plus7.replace(tzinfo=timezone.utc)


def format_dt_plus7(dt: datetime) -> str:
    # Return a readable UTC+7 timestamp string
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    local = dt.astimezone(timezone(timedelta(hours=7)))
    return local.strftime('%d-%m-%Y %H:%M:%S') + ' +07' 


class App:
    def __init__(self, root):
        self.root = root
        root.title('Aplikasi Pengambilan Data Lokal')

        frm = tk.Frame(root, padx=12, pady=12)
        frm.pack()

        tk.Label(frm, text='Id Barang (scan di sini):').grid(row=0, column=0, sticky='w')
        self.id_entry = tk.Entry(frm, width=60)
        self.id_entry.grid(row=0, column=1, columnspan=2, pady=4, sticky='w')
        self.id_entry.focus()

        

        # read-only fields
        self.fields = {}
        labels = ['model_pigtail','model_bearing','model_armacer','model_holder','model_produk']
        for i, name in enumerate(labels, start=1):
            tk.Label(frm, text=name.replace('_',' ').title()+':').grid(row=i, column=0, sticky='w')
            e = tk.Entry(frm, width=50, state='readonly')
            e.grid(row=i, column=1, columnspan=2, pady=2, sticky='w')
            self.fields[name] = e

        tk.Label(frm, text='Input Date (UTC+7):').grid(row=6, column=0, sticky='w')
        self.input_date = tk.Entry(frm, width=50, state='readonly')
        self.input_date.grid(row=6, column=1, columnspan=2, pady=2, sticky='w')

        tk.Label(frm, text='Lot:').grid(row=7, column=0, sticky='w')
        self.lot_entry = tk.Entry(frm, width=20)
        self.lot_entry.grid(row=7, column=1, sticky='w')

        self.tambah_btn = tk.Button(frm, text='Tambah Data', command=self.tambah_data)
        self.tambah_btn.grid(row=8, column=1, pady=8, sticky='w')

        # bind Enter to ambil
        self.id_entry.bind('<Return>', lambda e: self.ambil_data())

    def set_readonly(self, entry, text):
        entry.config(state='normal')
        entry.delete(0, 'end')
        entry.insert(0, '' if text is None else str(text))
        entry.config(state='readonly')

    def ambil_data(self):
        idv = self.id_entry.get().strip()
        if not idv:
            messagebox.showwarning('Peringatan','Masukkan id_barang terlebih dahulu')
            return

        doc = raw_coll.find_one({'id_barang': idv})
        if not doc:
            # try numeric
            try:
                doc = raw_coll.find_one({'id_barang': int(idv)})
            except Exception:
                doc = None

        if not doc:
            messagebox.showerror('Tidak ditemukan','Item tidak ditemukan di collection raw_items')
            return

        # isi fields
        for k,e in self.fields.items():
            self.set_readonly(e, doc.get(k))

        # input_date dari server lokal (UTC+7)
        self.set_readonly(self.input_date, format_dt_plus7(now_plus7_datetime()))

    def tambah_data(self):
        idv = self.id_entry.get().strip()
        if not idv:
            messagebox.showwarning('Peringatan','Id barang kosong')
            return

        # convert id_barang to int for storage
        try:
            id_int = int(idv)
        except Exception:
            messagebox.showwarning('Peringatan', 'Id barang harus berupa angka (integer)')
            return

        lotv = self.lot_entry.get().strip()
        try:
            lot_int = int(lotv)
        except Exception:
            messagebox.showwarning('Peringatan','Lot harus berupa angka (integer)')
            return

        # convert model_holder to int (required)
        mh = self.fields['model_holder'].get().strip()
        try:
            model_holder_int = int(mh)
        except Exception:
            messagebox.showwarning('Peringatan', 'Model holder harus berupa angka (integer)')
            return

        db_dt = now_plus7_datetime()

        doc = {
            'id_barang': id_int,
            'input_date': db_dt,
            'model_pigtail': self.fields['model_pigtail'].get(),
            'model_bearing': self.fields['model_bearing'].get(),
            'model_armacer': self.fields['model_armacer'].get(),
            'model_holder': model_holder_int,
            'lot': lot_int,
            'model_produk': self.fields['model_produk'].get(),
        }

        try:
            res = formatted_coll.insert_one(doc)
            messagebox.showinfo('Sukses', f'Data berhasil ditambahkan. id: {res.inserted_id}\ninput_date: {format_dt_plus7(db_dt)}')
            # clear lot
            self.lot_entry.delete(0,'end')
        except Exception as e:
            messagebox.showerror('Error', f'Gagal insert: {e}')


if __name__ == '__main__':
    root = tk.Tk()
    app = App(root)
    root.mainloop()
