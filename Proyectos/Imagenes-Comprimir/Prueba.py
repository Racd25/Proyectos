import base64

from pymongo import MongoClient
import gridfs

def upload_image_to_mongo(image_path, db_name="Inrema", collection_name="images"):
    # Conexión al servidor MongoDB (ajusta el URI según tu entorno)
    client = MongoClient("mongodb://localhost:27017/")
    
    # Seleccionar base de datos
    db = client[db_name]
    
    # Crear objeto GridFS
    fs = gridfs.GridFS(db, collection_name)
    
    # Abrir la imagen en modo binario
    with open(image_path, "rb") as img_file:
        # Guardar en MongoDB
        file_id = fs.put(img_file, filename=image_path, tag ="123")
        print(f"Imagen subida con ID: {file_id}")
    
    return file_id

def download_image_from_mongo(file_id, output_path, db_name="Inrema", collection_name="images"):
    client = MongoClient("mongodb://localhost:27017/")
    db = client[db_name]
    fs = gridfs.GridFS(db, collection_name)
    
    # Recuperar archivo
    file_data = fs.get(file_id).read()
    with open(output_path, "wb") as output_file:
        output_file.write(file_data)
    print(f"Imagen descargada en: {output_path}")

# Ejemplo de uso
if __name__ == "__main__":
    # Subir imagen
    img_id = upload_image_to_mongo("abc.jpeg")
    
    # Descargar imagen
    download_image_from_mongo(img_id, "recuperada.png")
