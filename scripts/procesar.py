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
    catalogo = []
    max_id = 0
    
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                raw = json.load(f)
                if isinstance(raw, list):
                    catalogo = raw
                    for item in catalogo:
                        if isinstance(item.get("id"), int) and item["id"] > max_id:
                            max_id = item["id"]
        except Exception:
            catalogo = []

    # Mapeo de productos existentes por nombre para acumular/actualizar
    existentes = {p.get("nombre", "").strip().upper(): p for p in catalogo if "nombre" in p}

    csv_files = glob.glob(os.path.join(SCRAPER_DIR, "*.csv"))
    if not csv_files:
        print("No hay CSVs para procesar.")
        return

    for filepath in csv_files:
        try:
            df = pd.read_csv(filepath)
        except Exception:
            continue

        for _, row in df.iterrows():
            nombre = str(row.get("data") or row.get("NOMBRE DEL PRODUCTO") or "").strip()
            if not nombre or nombre.lower() == "nan":
                continue

            costo_raw = row.get("price") or row.get("PRECIO COSTO") or 0
            costo = parse_price(costo_raw)
            if costo == 0:
                continue

            precios = calcular_precios(costo)
            imagen = str(row.get("image") or row.get("FOTOS") or "").strip()
            if imagen.lower() == "nan":
                imagen = ""

            subcat = str(row.get("SUBCATEGORÍA") or "Accesorios").strip()
            if subcat.lower() == "nan":
                subcat = "Accesorios"

            norm_name = nombre.upper()

            if norm_name in existentes:
                # Actualizar existente
                p = existentes[norm_name]
                p["costo"] = precios["costo_prenda"]
                p["lista"] = precios["precio_lista"]
                p["transferencia"] = precios["precio_transferencia"]
                p["mayorista"] = precios["precio_mayorista"]
                p["cuota_monto"] = precios["cuota_3"]
                p["stock"] = 10
                if imagen:
                    p["imagen"] = imagen
                    p["imagen_url"] = imagen
                    p["img"] = imagen
            else:
                # Crear nuevo con la estructura exacta de tu web
                max_id += 1
                nuevo_prod = {
                    "tienda": "BAKANO",
                    "id": max_id,
                    "proveedor": "Monamu",
                    "rubro": "Indumentaria",
                    "seccion": subcat,
                    "categoria": subcat,
                    "subcategoria": subcat,
                    "nombre": nombre,
                    "costo": precios["costo_prenda"],
                    "lista": precios["precio_lista"],
                    "transferencia": precios["precio_transferencia"],
                    "mayorista": precios["precio_mayorista"],
                    "cuotas": 3,
                    "cuota_monto": precios["cuota_3"],
                    "stock": 10,
                    "variantes": [],
                    "peso": 150,
                    "imagen": imagen,
                    "imagen_url": imagen,
                    "img": imagen
                }
                catalogo.append(nuevo_prod)
                existentes[norm_name] = nuevo_prod

    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(catalogo, f, ensure_ascii=False, indent=2)

    print(f"Catálogo actualizado correctamente. Total: {len(catalogo)} items.")

if __name__ == "__main__":
    main()
