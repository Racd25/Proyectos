

from pymongo import MongoClient
import gridfs
from bson import ObjectId


def download_image_by_tag(tag_value, output_path, db_name="Inrema", collection_name="images"):
    client = MongoClient("mongodb://localhost:27017/")
    db = client[db_name]
    fs = gridfs.GridFS(db, collection_name)

    # Buscar el archivo por tag
    result = db[collection_name + ".files"].find_one({"tag": tag_value})
    if result:
        file_id = result["_id"]
        file_data = fs.get(ObjectId(file_id)).read()
        with open(output_path, "wb") as output_file:
            output_file.write(file_data)
        print(f"Imagen con tag={tag_value} descargada en: {output_path}")
    else:
        print(f"No se encontró archivo con tag={tag_value}")

# Ejemplo de uso independiente
if __name__ == "__main__":
    # Buscar y descargar directamente por tag
    download_image_by_tag("123", "recuperada.png")
