from pathlib import Path

BASE_DIR = Path('SMK_MART_4_ROLE')

BASE_DIR.mkdir(parents=True, exist_ok=True)
print(f"Folder database dan struk: {BASE_DIR}")

import hashlib
import hmac
import json
import os
from pathlib import Path
import secrets
from datetime import datetime

LOKASI = BASE_DIR
FILE_DATA = LOKASI / "smk_mart_data.json"
FOLDER_STRUK = LOKASI / "struk_smk_mart"
ROLE = ("admin", "gudang", "kasir", "manager")


def rupiah(nilai):
    return "Rp" + f"{nilai:,}".replace(",", ".")


def input_wajib(pesan):
    while True:
        hasil = input(pesan).strip()
        if hasil:
            return hasil
        print("[ERROR] Input tidak boleh kosong.")


def input_angka(pesan, minimum=0):
    while True:
        try:
            angka = int(input(pesan).strip())
            if angka < minimum:
                print(f"[ERROR] Angka minimal {minimum}.")
                continue
            return angka
        except ValueError:
            print("[ERROR] Masukkan bilangan bulat yang valid.")


def buat_hash_password(password):
    salt = secrets.token_hex(16)
    hasil = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), 150_000)
    return f"{salt}${hasil.hex()}"


def cek_password(password, password_hash):
    try:
        salt, nilai = password_hash.split("$", 1)
        hasil = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), 150_000)
        return hmac.compare_digest(hasil, bytes.fromhex(nilai))
    except (ValueError, TypeError):
        return False


def input_password():
    while True:
        sandi = input_wajib("Password (minimal 4 karakter): ")
        if len(sandi) < 4:
            print("[ERROR] Password terlalu pendek.")
            continue
        ulang = input_wajib("Ulangi password: ")
        if sandi == ulang:
            return buat_hash_password(sandi)
        print("[ERROR] Kedua password tidak sama.")


def muat_data():
    if not FILE_DATA.exists():
        return {"pengguna": {}, "barang": {}, "transaksi": [], "nomor_berikutnya": 1}
    try:
        with FILE_DATA.open("r", encoding="utf-8") as f:
            hasil = json.load(f)
        if not all(k in hasil for k in ("pengguna", "barang", "transaksi", "nomor_berikutnya")):
            raise ValueError("Format database tidak sesuai")
        return hasil
    except (OSError, ValueError, TypeError) as error:
        raise SystemExit(f"[ERROR] Tidak dapat membaca {FILE_DATA.name}: {error}")


def simpan_data(data_baru=None):
    """Simpan file secara atomik agar data lama tidak tertimpa separuh."""
    isi = db if data_baru is None else data_baru
    sementara = FILE_DATA.with_suffix(".json.tmp")
    try:
        with sementara.open("w", encoding="utf-8") as f:
            json.dump(isi, f, indent=2, ensure_ascii=False)
        os.replace(sementara, FILE_DATA)
        return True
    except OSError as error:
        print(f"[ERROR] Gagal menyimpan database: {error}")
        return False


def username_terpakai(username, kecuali_id=None):
    return any(p["username"] == username and id_p != kecuali_id
               for id_p, p in db["pengguna"].items())


def setup_pertama():
    """Buat empat akun awal, masing-masing untuk satu role."""
    if db["pengguna"]:
        return

    print("\n=== REGISTRASI AWAL 4 ROLE SMK MART ===")
    print("Daftarkan satu Admin, satu Gudang, satu Kasir, dan satu Manager.")
    akun_awal = (
        ("ADM001", "admin", "ADMIN"),
        ("GUD001", "gudang", "GUDANG"),
        ("KSR001", "kasir", "KASIR"),
        ("MGR001", "manager", "MANAGER"),
    )
    pengguna_baru = {}
    username_dipakai = set()
    for id_p, role, label in akun_awal:
        print(f"\n--- BUAT AKUN {label} ---")
        nama = input_wajib(f"Nama {role}: ")
        while True:
            username = input_wajib(f"Username {role}: ").lower()
            if username in username_dipakai:
                print("[ERROR] Username sudah digunakan. Pilih username berbeda.")
                continue
            break
        username_dipakai.add(username)
        pengguna_baru[id_p] = {
            "nama": nama, "username": username,
            "password": input_password(), "role": role
        }

    db["pengguna"].update(pengguna_baru)
    if not simpan_data():
        db["pengguna"].clear()
        raise SystemExit("Setup tidak berhasil disimpan. Cek izin akses folder.")
    print("\n[SUKSES] Keempat akun dibuat! Sekarang silakan login.")


def tampilkan_data_pengguna():
    print("\n--- TAMPILKAN DATA PENGGUNA ---")
    if not db["pengguna"]:
        print("Belum ada data pengguna yang ditambahkan.")
    else:
        for id_pengguna, info in db["pengguna"].items():
            # Password asli tidak ditampilkan demi keamanan sistem hash Code 2
            print(f"ID Pengguna: {id_pengguna} | Nama: {info['nama']} | Username: {info.get('username', '-')} | Role: {info['role']}")


def tambah_pengguna():
    print("\n--- TAMBAH DATA PENGGUNA ---")
    id_pengguna = input("silahkan masukkan id pengguna anda : ").strip().upper()
    
    if id_pengguna in db["pengguna"]:
        print("[ERROR] ID pengguna sudah ada.")
        return
        
    nama = input("silahkan masukkan nama anda : ").strip()
    username = input("masukkan username anda : ").strip().lower()
    
    if username_terpakai(username):
        print("[ERROR] Username sudah dipakai.")
        return
        
    password = input("masukkan password anda : ").strip()
    role = input("silahkan memasukkan role anda (admin/kasir/gudang/manager) : ").lower()

    if role not in ROLE:
        print("[ERROR] Role tidak valid.")
        return

    db["pengguna"][id_pengguna] = {
        "nama" : nama,
        "username" : username,
        "password" : buat_hash_password(password), 
        "role" : role
    }
    
    if simpan_data():
        print(f"[SUKSES] pengguna '{nama}' berhasil ditambahkan!")
    else:
        del db["pengguna"][id_pengguna]


def edit_pengguna():
    print("\n--- EDIT DATA PENGGUNA ---")
    id_pengguna = input("masukkan ID pengguna yang ingin diedit: ").strip().upper()
    
    if id_pengguna in db["pengguna"]:
        pengguna = db["pengguna"][id_pengguna]

        print("Kosongkan input jika tidak ingin diubah.")
        nama_baru = input(f"Nama baru [{pengguna['nama']}]: ").strip()
        username_baru = input(f"Username baru [{pengguna['username']}]: ").strip().lower()
        
        if username_baru and username_terpakai(username_baru, id_pengguna):
            print("[ERROR] Username sudah digunakan pengguna lain.")
            return

        password_baru = input("Password baru [***]: ").strip()
        role_baru = input(f"Role baru [{pengguna['role']}]: ").strip().lower()

        if nama_baru:
            pengguna['nama'] = nama_baru
        if username_baru:
            pengguna['username'] = username_baru
        if password_baru:
            pengguna['password'] = buat_hash_password(password_baru)
        if role_baru and role_baru in ROLE:
            pengguna['role'] = role_baru

        if simpan_data():
            print("[SUKSES] Data pengguna berhasil diedit")
    else:
        print("[ERROR] ID pengguna tidak ditemukan.")


def hapus_pengguna(admin_login):
    print("\n--- HAPUS DATA PENGGUNA ---")
    id_pengguna = input("Masukkan ID pengguna yang ingin dihapus: ").strip().upper()
    
    if id_pengguna in db["pengguna"]:
        if id_pengguna == admin_login:
            print("[ERROR] Tidak boleh menghapus akun admin yang sedang dipakai.")
            return
            
        nama = db["pengguna"][id_pengguna]['nama']
        del db["pengguna"][id_pengguna]
        
        if simpan_data():
            print(f"Data pengguna '{nama}' berhasil dihapus.")
    else:
        print("ID pengguna tidak ditemukan.")


def daftar_barang():
    print("\n=== DATA BARANG ===")
    if not db["barang"]:
        print("Belum ada barang.")
        return
    print(f"{'ID':<10} {'Nama barang':<25} {'Stok':>6} {'Harga':>15}")
    print("-" * 60)
    for id_b, b in db["barang"].items():
        print(f"{id_b:<10} {b['nama_barang'][:25]:<25} {b['stok']:>6} {rupiah(b['harga']):>15}")


def tambah_barang():
    """Menambahkan barang baru ke dalam database gudang."""
    print("\n=== TAMBAH BARANG ===")
    id_b = input_wajib("ID barang: ").upper()
    if id_b in db["barang"]:
        print("[ERROR] ID barang sudah terdaftar.")
        return
    nama = input_wajib("Nama barang: ")
    stok = input_angka("Stok awal: ")
    harga = input_angka("Harga satuan (Rp): ", 1)

    db["barang"][id_b] = {"nama_barang": nama, "stok": stok, "harga": harga}
    if simpan_data():
        print("[SUKSES] Barang berhasil ditambahkan.")
    else:
        del db["barang"][id_b]


def edit_barang():
    """Memperbarui informasi nama, stok, atau harga barang yang sudah ada."""
    daftar_barang()
    id_b = input_wajib("ID barang yang diedit: ").upper()
    b = db["barang"].get(id_b)
    if not b:
        print("[ERROR] ID barang tidak ditemukan.")
        return

    nama = input(f"Nama baru [{b['nama_barang']}]: ").strip()
    stok = input(f"Stok baru [{b['stok']}]: ").strip()
    harga = input(f"Harga baru [{b['harga']}]: ").strip()

    try:
        stok_baru = int(stok) if stok else b["stok"]
        harga_baru = int(harga) if harga else b["harga"]
        if stok_baru < 0 or harga_baru < 1:
            raise ValueError
    except ValueError:
        print("[ERROR] Stok harus >= 0 dan harga harus >= 1.")
        return

    b.update({
        "nama_barang": nama or b["nama_barang"],
        "stok": stok_baru,
        "harga": harga_baru
    })

    if simpan_data():
        print("[SUKSES] Barang diperbarui.")


def hapus_barang():
    """Menghapus data barang dari sistem."""
    daftar_barang()
    id_b = input_wajib("ID barang yang dihapus: ").upper()
    if id_b not in db["barang"]:
        print("[ERROR] ID barang tidak ditemukan.")
        return

    if input("Yakin hapus barang? (y/t): ").strip().lower() == "y":
        del db["barang"][id_b]
        if simpan_data():
            print("[SUKSES] Barang dihapus.")


def heapify(arr, n, i):
    """Fungsi helper untuk algoritma Heap Sort."""
    terbesar = i
    kiri, kanan = 2 * i + 1, 2 * i + 2
    if kiri < n and arr[kiri][1]["nama_barang"].casefold() > arr[terbesar][1]["nama_barang"].casefold():
        terbesar = kiri
    if kanan < n and arr[kanan][1]["nama_barang"].casefold() > arr[terbesar][1]["nama_barang"].casefold():
        terbesar = kanan
    if terbesar != i:
        arr[i], arr[terbesar] = arr[terbesar], arr[i]
        heapify(arr, n, terbesar)


def urut_barang_heap_sort():
    """Mengurutkan barang secara A-Z menggunakan algoritma Heap Sort."""
    arr = list(db["barang"].items())
    n = len(arr)
    for i in range(n // 2 - 1, -1, -1):
        heapify(arr, n, i)
    for i in range(n - 1, 0, -1):
        arr[0], arr[i] = arr[i], arr[0]
        heapify(arr, i, 0)

    print("\n=== BARANG TERURUT A-Z (HEAP SORT) ===")
    if not arr:
        print("Belum ada barang.")
    for id_b, b in arr:
        print(f"{id_b} | {b['nama_barang']} | stok {b['stok']} | {rupiah(b['harga'])}")


def cari_barang():
    """Mencari barang berdasarkan kata kunci nama."""
    keyword = input_wajib("Cari nama barang: ").casefold()
    hasil = [(k, b) for k, b in db["barang"].items()
             if keyword in b["nama_barang"].casefold()]
    if not hasil:
        print("Barang tidak ditemukan.")
        return
    for id_b, b in sorted(hasil, key=lambda x: x[1]["nama_barang"].casefold()):
        print(f"{id_b} | {b['nama_barang']} | stok {b['stok']} | {rupiah(b['harga'])}")


def cari_pengguna():
    keyword = input_wajib("Cari nama pengguna: ").casefold()
    hasil = [(k, p) for k, p in db["pengguna"].items()
             if keyword in p["nama"].casefold()]
    if not hasil:
        print("Pengguna tidak ditemukan.")
    for id_p, p in hasil:
        print(f"{id_p} | {p['nama']} | @{p['username']} | {p['role']}")


def tampil_keranjang(keranjang):
    print("\n=== KERANJANG BELANJA ===")
    if not keranjang:
        print("Keranjang masih kosong.")
        return 0
    total = 0
    for id_b, jumlah in keranjang.items():
        b = db["barang"][id_b]
        subtotal = jumlah * b["harga"]
        total += subtotal
        print(f"{b['nama_barang']} ({id_b}): {jumlah} x {rupiah(b['harga'])} = {rupiah(subtotal)}")
    print(f"TOTAL: {rupiah(total)}")
    return total


def format_struk(trx):
    garis = "=" * 46
    baris = [garis, "SMK MART".center(46), "STRUK PEMBELIAN".center(46), garis,
             f"No. Transaksi : {trx['nomor']}", f"Tanggal       : {trx['tanggal']}",
             f"Kasir         : {trx['kasir_nama']} (@{trx['kasir_username']})", "-" * 46]
    for item in trx["item"]:
        baris.append(item["nama_barang"])
        kiri = f"  {item['jumlah']} x {rupiah(item['harga'])}"
        kanan = rupiah(item["subtotal"])
        baris.append(f"{kiri:<27}{kanan:>19}")
    baris += ["-" * 46,
              f"{'TOTAL':<25}{rupiah(trx['total']):>21}",
              f"{'TUNAI':<25}{rupiah(trx['bayar']):>21}",
              f"{'KEMBALIAN':<25}{rupiah(trx['kembalian']):>21}",
              garis, "Terima kasih sudah berbelanja!".center(46), garis]
    return "\n".join(baris)


def cetak_struk(trx):
    isi = format_struk(trx)
    print("\n" + isi)
    try:
        FOLDER_STRUK.mkdir(parents=True, exist_ok=True)
        lokasi_struk = FOLDER_STRUK / f"{trx['nomor']}.txt"
        lokasi_struk.write_text(isi + "\n", encoding="utf-8")
        print(f"[SUKSES] File nota disimpan: {lokasi_struk}")
    except OSError as error:
        print(f"[PERINGATAN] Struk tampil, tetapi gagal tersimpan: {error}")


def transaksi_penjualan(kasir):
    if not db["barang"]:
        print("[ERROR] Belum ada barang. Minta bagian gudang menambahkan barang.")
        return
    keranjang = {}
    print("\n=== TRANSAKSI PENJUALAN ===")
    print("Masukkan ID barang, ketik 'selesai' untuk bayar, 'batal' untuk membatalkan.")
    while True:
        daftar_barang()
        tampil_keranjang(keranjang)
        id_b = input("ID barang / selesai / batal: ").strip().upper()
        if id_b == "BATAL":
            print("Transaksi dibatalkan. Stok tidak berubah.")
            return
        if id_b == "SELESAI":
            if not keranjang:
                print("[ERROR] Keranjang kosong.")
                continue
            break
        if id_b not in db["barang"]:
            print("[ERROR] ID barang tidak ditemukan.")
            continue
        b = db["barang"][id_b]
        tersedia = b["stok"] - keranjang.get(id_b, 0)
        if tersedia <= 0:
            print("[ERROR] Stok untuk barang ini sudah habis/terpakai di keranjang.")
            continue
        print(f"Stok yang masih bisa ditambahkan: {tersedia}")
        jumlah = input_angka("Jumlah tambahan: ", 1)
        if jumlah > tersedia:
            print(f"[ERROR] Stok tidak cukup, maksimal tambahan {tersedia}.")
            continue
        keranjang[id_b] = keranjang.get(id_b, 0) + jumlah
        print("[SUKSES] Barang masuk keranjang.")

    total = tampil_keranjang(keranjang)
    print("Ketik 0 pada pembayaran untuk membatalkan transaksi.")
    while True:
        bayar = input_angka("Uang yang dibayarkan (Rp): ")
        if bayar == 0:
            print("Transaksi dibatalkan. Stok tidak berubah.")
            return
        if bayar < total:
            print(f"[ERROR] Uang kurang {rupiah(total - bayar)}.")
            continue
        break

    import copy
    baru = copy.deepcopy(db)
    daftar_item = []
    for id_b, jumlah in keranjang.items():
        b = baru["barang"][id_b]
        if jumlah > b["stok"]:
            print("[ERROR] Stok berubah; transaksi tidak dapat diselesaikan.")
            return
        b["stok"] -= jumlah
        daftar_item.append({"id_barang": id_b, "nama_barang": b["nama_barang"],
                            "jumlah": jumlah, "harga": b["harga"],
                            "subtotal": jumlah * b["harga"]})
    trx = {"nomor": f"TRX{baru['nomor_berikutnya']:06d}",
           "tanggal": datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
           "kasir_id": kasir[0], "kasir_nama": kasir[1]["nama"],
           "kasir_username": kasir[1]["username"], "item": daftar_item,
           "total": total, "bayar": bayar, "kembalian": bayar - total}
    baru["transaksi"].append(trx)
    baru["nomor_berikutnya"] += 1
    if not simpan_data(baru):
        print("[ERROR] Transaksi gagal disimpan. Stok belum dikurangi.")
        return
    db.clear()
    db.update(baru)
    print("\n[SUKSES] Pembayaran berhasil dan stok otomatis berkurang.")
    cetak_struk(trx)


def riwayat_transaksi():
    print("\n=== RIWAYAT TRANSAKSI ===")
    if not db["transaksi"]:
        print("Belum ada transaksi.")
        return
    for trx in db["transaksi"]:
        print(f"{trx['nomor']} | {trx['tanggal']} | {trx['kasir_nama']} | {rupiah(trx['total'])}")


def cetak_ulang_struk():
    riwayat_transaksi()
    if not db["transaksi"]:
        return
    nomor = input_wajib("Nomor transaksi untuk cetak ulang: ").upper()
    trx = next((t for t in db["transaksi"] if t["nomor"] == nomor), None)
    if trx:
        cetak_struk(trx)
    else:
        print("[ERROR] Nomor transaksi tidak ditemukan.")


def laporan_penjualan():
    riwayat_transaksi()
    print("\n=== REKAP PENJUALAN ===")
    rekap = {}
    for t in db["transaksi"]:
        id_k = t["kasir_id"]
        if id_k not in rekap:
            rekap[id_k] = {"nama": t["kasir_nama"], "jumlah": 0, "total": 0}
        rekap[id_k]["jumlah"] += 1
        rekap[id_k]["total"] += t["total"]
    for id_k, p in db["pengguna"].items():
        if p["role"] == "kasir" and id_k not in rekap:
            rekap[id_k] = {"nama": p["nama"], "jumlah": 0, "total": 0}
    for id_k, r in rekap.items():
        print(f"{id_k} | {r['nama']} | {r['jumlah']} transaksi | {rupiah(r['total'])}")
    print(f"TOTAL OMZET: {rupiah(sum(t['total'] for t in db['transaksi']))}")


def menu_admin(id_login):
    while True:
        print("\n=== MENU ADMIN ===")
        print("1. Tambah pengguna\n2. Edit pengguna\n3. Hapus pengguna\n4. Tampilkan pengguna\n5. Cari pengguna\n6. Logout")
        pilih = input("Pilih (1-6): ").strip()
        if pilih == "1": tambah_pengguna()
        elif pilih == "2": edit_pengguna()
        elif pilih == "3": hapus_pengguna(id_login)
        elif pilih == "4": tampilkan_data_pengguna()
        elif pilih == "5": cari_pengguna()
        elif pilih == "6": break
        else: print("Pilihan tidak valid.")


def menu_gudang():
    while True:
        print("\n=== MENU GUDANG ===")
        print("1. Tambah barang\n2. Edit barang\n3. Hapus barang\n4. Tampilkan barang\n5. Urutkan barang (Heap Sort)\n6. Cari barang\n7. Logout")
        pilih = input("Pilih (1-7): ").strip()
        if pilih == "1": tambah_barang()
        elif pilih == "2": edit_barang()
        elif pilih == "3": hapus_barang()
        elif pilih == "4": daftar_barang()
        elif pilih == "5": urut_barang_heap_sort()
        elif pilih == "6": cari_barang()
        elif pilih == "7": break
        else: print("Pilihan tidak valid.")


def menu_kasir(id_login):
    while True:
        kasir = (id_login, db["pengguna"][id_login])
        print(f"\n=== MENU KASIR | {kasir[1]['nama']} ===")
        print("1. Transaksi penjualan dan cetak nota\n2. Cari barang\n3. Lihat barang\n4. Cetak ulang struk\n5. Logout")
        pilih = input("Pilih (1-5): ").strip()
        if pilih == "1": transaksi_penjualan(kasir)
        elif pilih == "2": cari_barang()
        elif pilih == "3": daftar_barang()
        elif pilih == "4": cetak_ulang_struk()
        elif pilih == "5": break
        else: print("Pilihan tidak valid.")


def menu_manager():
    while True:
        print("\n=== MENU MANAGER ===")
        print("1. Daftar pengguna\n2. Daftar barang\n3. Cari pengguna\n4. Cari barang\n5. Laporan transaksi dan omzet kasir\n6. Cetak ulang nota\n7. Logout")
        pilih = input("Pilih (1-7): ").strip()
        if pilih == "1": tampilkan_data_pengguna()
        elif pilih == "2": daftar_barang()
        elif pilih == "3": cari_pengguna()
        elif pilih == "4": cari_barang()
        elif pilih == "5": laporan_penjualan()
        elif pilih == "6": cetak_ulang_struk()
        elif pilih == "7": break
        else: print("Pilihan tidak valid.")


def main():
    print("\n=== SELAMAT DATANG DI SMK MART ===")
    setup_pertama()
    while True:
        print("\n=== LOGIN SMK MART ===")
        username = input("Username (0 untuk keluar): ").strip().lower()
        if username == "0":
            print("Terima kasih. Program selesai.")
            break
        password = input("Password: ")
        login = next(((id_p, p) for id_p, p in db["pengguna"].items()
                      if p["username"] == username and cek_password(password, p["password"])), None)
        if not login:
            print("[ERROR] Username atau password salah.")
            continue
        id_login, pengguna = login
        print(f"[SUKSES] Halo, {pengguna['nama']}! Login sebagai {pengguna['role']}.")
        if pengguna["role"] == "admin": menu_admin(id_login)
        elif pengguna["role"] == "gudang": menu_gudang()
        elif pengguna["role"] == "kasir": menu_kasir(id_login)
        elif pengguna["role"] == "manager": menu_manager()


#db = muat_data()
db = {"pengguna": {}, "barang": {}, "transaksi": [], "nomor_berikutnya": 1}

try:
    main()
except (KeyboardInterrupt, EOFError):
    print("\nProgram dihentikan.")
