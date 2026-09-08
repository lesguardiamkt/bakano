import os
import glob
import re
import json
import pandas as pd

DATA_FILE = "productos.json"
SCRAPER_DIR = "scraper"
COSTO_OPERATIVO_FIJO = 1300
DESCUENTO_TRANSFERENCIA = 0.15

def parse_price(val):
    if pd.isna(val):
        return 0.0
    val_str = str(val).replace("$", "").replace(".", "").replace(",", ".").strip()
    match = re.search(r"[-+]?\d*\.?\d+", val_str)
    return float(match.group(0)) if match else 0.0

def calcular_precios(costo_prenda):
    costo_total = costo_prenda + COSTO_OPERATIVO_FIJO
    if costo_total <= 10000:
        precio_lista = round((costo_total * 1.8) / 300) * 300
    elif costo_total <= 20000:
        precio_lista = round((costo_total * 1.7) / 300) * 300
    else:
        precio_lista = round((costo_total * 1.66) / 300) * 300

    cuota_3 = round(precio_lista / 3)
    precio_transf = round((precio_lista * (1 - DESCUENTO_TRANSFERENCIA)) / 100) * 100
    precio_mayorista = round((costo_total * 1.25) / 100) * 100

    return {
        "costo_prenda": int(costo_prenda),
        "costo_total": int(costo_total),
        "precio_lista": int(precio_lista),
        "cuota_3": int(cuota_3),
        "precio_transferencia": int(precio_transf),
        "precio_mayorista": int(precio_mayorista)
    }

def main():
    catalogo = {}
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                raw = json.load(f)
                if isinstance(raw, list):
                    catalogo = {p.get("id", str(i)): p for i, p in enumerate(raw)}
                elif isinstance(raw, dict):
                    catalogo = raw
        except Exception:
            catalogo = {}

    csv_files = glob.glob(os.path.join(SCRAPER_DIR, "*.csv"))
    if not csv_files:
        print("No hay archivos CSV en /scraper")
        return

    for filepath in csv_files:
        try:
            df = pd.read_csv(filepath)
        except Exception as e:
            continue

        for _, row in df.iterrows():
            nombre = str(row.get("data") or row.get("NOMBRE DEL PRODUCTO") or "").strip()
            if not nombre or nombre.lower() == "nan":
                continue

            costo_raw = row.get("price") or row.get("PRECIO COSTO") or 0
            costo = parse_price(costo_raw)
            if costo == 0:
                continue

            clean_id = re.sub(r'[^a-zA-Z0-9]', '', nombre).upper()
            imagen = str(row.get("image") or row.get("FOTOS") or "").strip()
            if imagen.lower() == "nan":
                imagen = ""

            precios = calcular_precios(costo)
            sku = f"MNM-{clean_id[:8]}"

            item_data = {
                "id": clean_id,
                "sku": sku,
                "nombre": nombre,
                "imagen": imagen if imagen else catalogo.get(clean_id, {}).get("imagen", ""),
                "talles": catalogo.get(clean_id, {}).get("talles", "Talle único"),
                "categoria": str(row.get("SUBCATEGORÍA") or catalogo.get(clean_id, {}).get("categoria", "Accesorios")),
                "en_stock": True,
                "precios": precios
            }
            catalogo[clean_id] = item_data

    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(list(catalogo.values()), f, ensure_ascii=False, indent=2)
    print(f"Catálogo actualizado: {len(catalogo)} productos.")

if __name__ == "__main__":
    main()
