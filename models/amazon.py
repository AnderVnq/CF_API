import json
import pymysql
from sshtunnel import SSHTunnelForwarder









class Amazon:
    def __init__(self, platform):
        self.platform = platform
        self.__db_connection = DBConnection()  # Inicializar la conexión de base de datos
        self.__product_detail = self.__db_connection.fetch_product_detail(self.platform)  # Obtener detalles del producto al iniciar


    # Métodos para acceder y modificar product_detail
    def get_product_detail(self):
        return self.__product_detail

    def set_product_detail(self, detail):
        self.__product_detail = detail


    # def update(self, **kwargs):
    #     # Actualiza solo los atributos que se pasan como argumentos
    #     for key, value in kwargs.items():
    #         if hasattr(self, key):
    #             setattr(self, key, value)


    # def to_json(self):
    #     # Convierte el objeto a un JSON
    #     return json.dumps(self.__dict__,ensure_ascii=False)



    @classmethod
    def massive_update_model(cls, table, data, id_field='uuid', batch_size=100):
    # Crear una instancia de DBConnection (usando valores por defecto)
        db_connection = DBConnection()
        db_connection.open_connection()  # Abrir la conexión (incluye el túnel SSH)

        cursor = None  # Inicializar cursor en el ámbito de método
        update_count = 0
        batch = []

        try:

            cursor = db_connection.connection.cursor()  # Acceder directamente a la conexión

            for item in data:
                set_clause = ', '.join([f"{key} = %s" for key in item.keys() if key != id_field])
                values = [item[key] for key in item.keys() if key != id_field]
                values.append(item[id_field])
                query = f"UPDATE {table} SET {set_clause} WHERE {id_field} = %s"
                batch.append((query, values))

                if len(batch) >= batch_size:
                    for q, v in batch:
                        cursor.execute(q, v)
                    db_connection.connection.commit()  # Confirmar cambios
                    update_count += len(batch)
                    batch = []  # Limpiar el lote después de ejecutar

            # Ejecutar cualquier consulta restante en el lote
            if batch:
                for q, v in batch:
                    cursor.execute(q, v)
                db_connection.connection.commit()  # Confirmar cambios
                update_count += len(batch)

            print(f"Total de registros actualizados: {update_count}")
            return update_count  # Retornar el número total de registros actualizados

        except Exception as e:
            print(f"Error al actualizar los registros: {e}")
            db_connection.connection.rollback()  # Deshacer cambios en caso de error
            return None  # Retornar None en caso de error

        finally:
            if cursor:
                cursor.close()  # Cerrar el cursor si fue creado
            db_connection.close_connection()  # Cerrar la conexión

    
    @classmethod
    def execute_procedure(cls, platform, data):
        # Crear una instancia de DBConnection (usando valores por defecto)
        db_connection = DBConnection()
        db_connection.open_connection()  # Abrir la conexión (incluye el túnel SSH)

        try:
            # Serializar los datos
            #instance = cls(sku=None)
            
            cursor = db_connection.connection.cursor()

            # Llamar al procedimiento almacenado
            cursor.callproc('SP_SkuListToUpdate_AmazonPythonV1', (platform,data))
            rows_affected = cursor.rowcount 
            db_connection.connection.commit()  

            if rows_affected > 0:
                print(f"Procedimiento ejecutado con éxito, filas afectadas: {rows_affected}")
            else:
                print("Procedimiento ejecutado con éxito, pero no se afectaron filas.")
        

            print("Procedimiento ejecutado con éxito")
            return True
        except Exception as e:
            print(f"Error al ejecutar el procedimiento: {e}")
            return False
        finally:
            if cursor:
                cursor.close()
            db_connection.close_connection()  # Cerrar la conexión y el túnel SSH

#scraping







#conection


class DBConnection:
    def __init__(self, ssh_host='comprafacil.pics', ssh_port=22, ssh_user='scraper',
                 ssh_password='@AppScraper..', db_host='localhost', db_port=3306,
                 db_user='scraper', db_password='AppScraper2024!!', db_name='dev_scp'):
        self.ssh_host = ssh_host
        self.ssh_port = ssh_port
        self.ssh_user = ssh_user
        self.ssh_password = ssh_password
        self.db_host = db_host
        self.db_port = db_port
        self.db_user = db_user
        self.db_password = db_password
        self.db_name = db_name
        self.connection = None
        self.ssh_tunnel = None

    def open_connection(self):
        try:
            self.ssh_tunnel = SSHTunnelForwarder(
                (self.ssh_host, self.ssh_port),
                ssh_username=self.ssh_user,
                ssh_password=self.ssh_password,
                remote_bind_address=(self.db_host, self.db_port)
            )
            self.ssh_tunnel.start()

            self.connection = pymysql.connect(
                host='127.0.0.1',
                port=self.ssh_tunnel.local_bind_port,
                user=self.db_user,
                password=self.db_password,
                database=self.db_name
            )
            print("Conexión exitosa a la base de datos")
        except Exception as e:
            print(f"Error al abrir la conexión: {e}")

    def close_connection(self):
        if self.connection:
            self.connection.close()
        if self.ssh_tunnel:
            self.ssh_tunnel.stop()

    def fetch_product_detail(self, platform):
        """Ejecutar el procedimiento almacenado para obtener detalles del producto."""
        try:
            self.open_connection()  # Abrir la conexión

            with self.connection.cursor() as cursor:
                cursor.execute("SET @result = '';")  # Inicializa la variable @result
                cursor.execute("CALL SP_SkuListToUpdate_AmazonPythonV1(%s, @result);", (platform,))
                cursor.execute("SELECT @result;")
                result = cursor.fetchone()[0]
                
                result_list = json.loads(result) if result else []
                return result_list  # Devolver la lista de diccionarios

        except Exception as e:
            print(f"Error al obtener detalles del producto: {e}")
            return []  # Devolver una lista vacía en caso de error
        finally:
            self.close_connection() 