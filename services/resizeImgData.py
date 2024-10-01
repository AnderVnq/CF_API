from models.resizeImg import ResizeImg
from config import Config
from PIL import Image, ImageOps
import os
import re

class ResizeImage(ResizeImg):

    def __init__(self, platform='amazon'):
        super().__init__(platform)
        
        self.base_paths = Config.get_base_paths()
        self.all_data = self.fetch_data_img()


    

    def resizeImage(self,sufix='_jpg',img_format='jpg',prop_update=None):
        """
        Pasar el prop ya sea 
        img_resize_jpg /
        mg_resize_webp
        """
        #data= self.get_data(index)
        image_quantity=5
        image_url=None
        dir_name_sku=None
        print("entro a la funcion ")
        try:
            for data in self.all_data:
                for i in range(image_quantity+1):
                    if f"image_{i}" in data and data[f"image_{i}"]:
                        if i==0 and data['main_image_url']:
                            image_url= data['main_image_url']
                        else:
                            image_url=data[f"image_{i}"]
                        
                        print("paso los if else")
                        matches = re.search(r'Images/([^/]+)/',image_url)
                        if matches:
                            dir_name_sku = matches.group(1).lower().strip()
                        ext = os.path.splitext(image_url)[1][1:]  # Esto es para obtener la extensión sin el '.'
                        image_name = os.path.splitext(os.path.basename(image_url))[0] 
                        print("paso el matches")
                        origin_img = f"{self.base_paths['public_path']}/Images/{dir_name_sku}/{image_name}.{ext}"
                        try:
                            # Abrir la imagen original con Pillow
                            print("entro al try")
                            imagick = Image.open(origin_img)

                            # Obtener las dimensiones actuales de la imagen
                            width, height = imagick.size
                            print("entro al wid height")
                            print(width,height)
                            # Comprobar si alguna dimensión es mayor a 1000px
                            if width > 1000 or height > 1000:

                                print("entro al if de width")
                                # Redimensionar manteniendo la proporción
                                if width > height:
                                    imagick = ImageOps.fit(imagick, (1000, int(1000 * height / width)), Image.LANCZOS)
                                else:
                                    imagick = ImageOps.fit(imagick, (int(1000 * width / height), 1000), Image.LANCZOS)
                                # Actualizar las dimensiones después del redimensionamiento
                                width, height = imagick.size
                            # Crear un lienzo de 1000x1000 si las dimensiones son menores
                            print("salio del if ")
                            
                            if width < 1000 or height < 1000:
                                # Crear un lienzo blanco
                                print("entro al <1000")
                                canvas = Image.new("RGB", (1000, 1000), "white")

                                # Calcular las posiciones para centrar la imagen en el lienzo
                                x = (1000 - width) // 2
                                y = (1000 - height) // 2
                                # Componer la imagen sobre el lienzo
                                canvas.paste(imagick, (x, y))
                                # Reemplazar la imagen original con el lienzo
                                imagick = canvas
                            # Guardar la imagen redimensionada
                            print("salio del <1000")

                            save_path = f"{self.base_paths['main_path']}/Images/{dir_name_sku}/{dir_name_sku.lower().strip()}_{i}{sufix}.{img_format}"
                            print("paso save_path")
                            imagick.save(save_path)
                            # Actualizar la ruta en el dominio
                            img_domain_located = f"{self.base_paths['domain']}{dir_name_sku}/{dir_name_sku.lower().strip()}_{i}{sufix}.{img_format}"
                            # Limpiar los recursos de Pillow
                            imagick.close()
                            # Retornar la imagen actualizada y el flag de actualización
                            print(dir_name_sku)
                            print(save_path)
                            print(self.base_paths['domain'])
                            print(img_domain_located)
                            return img_domain_located, {prop_update: 0}
                        except Exception as e:
                            print(f"Error procesando la imagen: {e}")
                            return None, {prop_update: 1}
        except Exception as e:
            print(f"ocurrio una exception en resize {e}")


    





    # def get_data(self,index):
    #     data = self.__product_detail[index]
    #     return data