from models.amazon import DBConnection



class ResizeImg:

    def __init__(self,platform='amazon'):
        self.platform = platform
        self.__db_connection = DBConnection()  # Inicializar la conexión de base de datos
        self.__product_detail = self.__db_connection.fetch_rezise_img(self.platform)  # Obtener detalles 






    def fetch_data_img(self):
        print(self.__product_detail)
        return self.__product_detail

    # def set_reset_product_detail(self):
    #     self.__product_detail["product"] = []

    # def set_product_data_list_model(self, data):
    #     """Establece la lista de productos directamente desde la base de datos"""
    #     self.__product_detail["product"] = data

    # def set_product_detail_list_model(self, data):
    #     """Agrega un producto a la lista"""
    #     self.__product_detail["product"].append(data)

    # def set_product_detail(self, index, key, data):
    #     """Establece un valor específico en el producto dado un índice y una clave"""
    #     if index < len(self.__["product"]):
    #         self.__product_detail["product"][index][key] = data
    #     else:
    #         print("Index out of range")

    # def get_product_url(self, index, image_key):
    #     """Obtiene la URL de una imagen dada en un producto por índice"""
    #     if index < len(self.__product_detail["product"]) and image_key in self.__product_detail["product"][index]:
    #         return self.__product_detail["product"][index][image_key]
    #     else:
    #         return None

    # def get_all_product_images(self, index):
    #     """Devuelve todas las URLs de imágenes de un producto"""
    #     if index < len(self.__product_detail["product"]):
    #         product = self.__product_detail["product"][index]
    #         return {key: value for key, value in product.items() if 'image_' in key and value is not None}
    #     else:
    #         return None

    # def delete_entire_row_product_model(self, index):
    #     """Elimina un producto completo de la lista"""
    #     if index < len(self.__product_detail["product"]):
    #         del self.__product_detail["product"][index]

    # def delete_product_image(self, index, image_key):
    #     """Elimina una imagen específica de un producto"""
    #     if index < len(self.__product_detail["product"]) and image_key in self.__product_detail["product"][index]:
    #         self.__product_detail["product"][index][image_key] = None

    # def get_product_detail_model(self):
    #     """Devuelve toda la lista de productos"""
    #     return self.__product_detail["product"]

    # def get_product_data(self, index):
    #     """Devuelve los datos de un producto dado su índice"""
    #     if index < len(self.__product_detail["product"]):
    #         return self.__product_detail["product"][index]
    #     else:
    #         return None

    # def set_product_detail_entire_model(self, index, data):
    #     """Reemplaza todo un producto dado su índice"""
    #     if index < len(self.__product_detail["product"]):
    #         self.__product_detail["product"][index] = data
    #     else:
    #         print("Index out of range")

