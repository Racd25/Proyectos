from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.recycleview import RecycleView
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.properties import BooleanProperty
from kivy.uix.recycleboxlayout import RecycleBoxLayout
from kivy.uix.behaviors import FocusBehavior
from kivy.uix.recycleview.layout import LayoutSelectionBehavior
from kivy.uix.popup import Popup
from kivy.clock import Clock
from datetime import datetime,timedelta
from kivy.lang import Builder
from sqlqueries import QueriesSQLite
from kivy.properties import ObjectProperty
Builder.load_file("ventas/ventas.kv")










class SelectableRecycleBoxLayout(FocusBehavior, LayoutSelectionBehavior, RecycleBoxLayout):
    """Adds selection and focus behaviour to the view."""
    touch_deselect_last = BooleanProperty(True)

class SelectableBoxLayout(RecycleDataViewBehavior, BoxLayout):
    """Add selection support to the Label."""
    index = None
    selected = BooleanProperty(False)
    selectable = BooleanProperty(True)

    def refresh_view_attrs(self, rv, index, data):
        self.index = index
        self.ids['_hashtag'].text = str(1 + index)
        self.ids['_articulo'].text = data['nombre'].capitalize()
        self.ids['_cantidad'].text = str(data['cantidad_carrito'])
        self.ids['_precio_por_articulo'].text = "{:.2f}".format(data['precio'])
        self.ids['_precio'].text = "{:.2f}".format(data['precio_total'])
        return super(SelectableBoxLayout, self).refresh_view_attrs(rv, index, data)

    def on_touch_down(self, touch):
        """Add selection on touch down."""
        if super(SelectableBoxLayout, self).on_touch_down(touch):
            return True
        if self.collide_point(*touch.pos) and self.selectable:
            return self.parent.select_with_touch(self.index, touch)

    def apply_selection(self, rv, index, is_selected):
        """Respond to the selection of items in the view."""
        self.selected = is_selected
        if is_selected:
            rv.data[index]['seleccionado']= True
        else:
            rv.data[index]['seleccionado']= False



class SelectableBoxLayoutPopup(RecycleDataViewBehavior, BoxLayout):
    index = None
    selected = BooleanProperty(False)
    selectable = BooleanProperty(True)
    stock_level = ObjectProperty('normal')

    def refresh_view_attrs(self, rv, index, data):
        self.index = index
        self.ids['_codigo'].text = data['codigo']
        self.ids['_articulo'].text = data['nombre'].capitalize()
        self.ids['_cantidad'].text = str(data['cantidad'])  # cantidad o descripción
        self.ids['_precio'].text = "{:.2f}".format(data['precio'])

        # Cambiar color según stock solo para productos
        if data.get('tipo_registro') == 'producto':
            cantidad = int(data['cantidad'])
            if cantidad < 2:
                self.stock_level = 'critical'
            elif cantidad < 5:
                self.stock_level = 'warning'
            else:
                self.stock_level = 'normal'
        else:
            self.stock_level = 'normal'  # servicios no tienen stoc

        return super(SelectableBoxLayoutPopup, self).refresh_view_attrs(rv, index, data)
    
    
    
    def on_touch_down(self, touch):
        '''Agregar selección al presionar'''
        if super(SelectableBoxLayoutPopup, self).on_touch_down(touch):
            return True
        if self.collide_point(*touch.pos) and self.selectable:
            return self.parent.select_with_touch(self.index, touch)

    def apply_selection(self, rv, index, is_selected):
        '''Responder a la selección de ítems en la vista.'''
        self.selected = is_selected
        rv.data[index]['seleccionado'] = is_selected

                    
class RV(RecycleView):
    def __init__(self, **kwargs):
        super(RV, self).__init__(**kwargs)
        self.data = []
        self.modificar_producto = None

    def agregar_articulo(self, articulo):
        articulo['seleccionado'] = False
        if 'tipo_registro' not in articulo:
            articulo['tipo_registro'] = 'producto'
        indice = -1
    
        if self.data:
            for i in range(len(self.data)):
                if articulo['codigo'] == self.data[i]['codigo']:
                    indice = i
                    break
                
            if indice >= 0:
                # Para productos, incrementar cantidad
                if self.data[indice].get('tipo_registro') == 'producto':
                    self.data[indice]['cantidad_carrito'] += 1
                    self.data[indice]['precio_total'] = (
                        self.data[indice]['precio'] * self.data[indice]['cantidad_carrito']
                    )
                else:
                    # Para servicios, permitir duplicados incrementando cantidad
                    self.data[indice]['cantidad_carrito'] += 1
                    self.data[indice]['precio_total'] = (
                         self.data[indice]['precio'] * self.data[indice]['cantidad_carrito']
                    )
                self.refresh_from_data()
            else:
                self.data.append(articulo)
        else:
            self.data.append(articulo)
             
    def articulo_seleccionado(self):
        indice =-1
        for i in range(len(self.data)):
            if self.data[i]['seleccionado']:
                indice = i 
                break
        return indice
    def eliminar_articulo(self):
        indice = self.articulo_seleccionado()
        precio=0
        if indice>= 0:
            self._layout_manager.deselect_node(self._layout_manager._last_selected_node)
            precio = self.data[indice] ['precio_total']
            self.data.pop(indice)
            self.refresh_from_data()
        return precio
    
    def modificar_articulo(self):
        indice = self.articulo_seleccionado()
        if indice >= 0:
            popup = CambiarCantidadPopup( self.data[indice],self.actualizar_articulo)
            popup.open()
        else:
            print("No hay artículo seleccionado")
            
    def actualizar_articulo(self,valor):
        indice = self.articulo_seleccionado()

        if indice >= 0:
            if valor ==0:
                self.data.pop(indice)
                self._layout_manager.deselect_node(self._layout_manager._last_selected_node)
            else:
                self.data[indice]['cantidad_carrito'] = valor
                self.data[indice]['precio_total'] = self.data[indice]['precio']*valor
            self.refresh_from_data()
            nuevo_total =0
            for data in self.data:
                nuevo_total+= data['precio_total']
            self.modificar_producto(False,nuevo_total)

            
class ProductoPorNombrePopup(Popup):
    def __init__(self, input_nombre, agregar_producto_callback, **kwargs):
        super(ProductoPorNombrePopup, self).__init__(**kwargs)
        self.input_nombre = input_nombre.lower()
        self.agregar_producto = agregar_producto_callback
    def mostrar_articulos(self):
      connection = QueriesSQLite.create_connection("pdvDB.sqlite")
      inventario_sql=QueriesSQLite.execute_read_query(connection, "SELECT * from productos")
      servicios_sql=QueriesSQLite.execute_read_query(connection, "SELECT * from servicios")
      self.open()
      for nombre in inventario_sql:
          if nombre[1].lower().find(self.input_nombre) >= 0:
              producto = {
                  'codigo': nombre[0],
                  'nombre': nombre[1],
                  'precio': nombre[2],
                  'cantidad': nombre[3],
                  'tipo_registro': 'producto'  # AGREGAR ESTA LÍNEA
              }
              self.ids.rvs.agregar_articulo(producto)
      for nombre in servicios_sql:
          if nombre[1].lower().find(self.input_nombre) >= 0:
              producto = {
                  'codigo': nombre[0],
                  'nombre': nombre[1],
                  'precio': nombre[2],
                  'cantidad': nombre[3],
                  'tipo_registro': 'servicio'  # AGREGAR ESTA LÍNEA
              }
              self.ids.rvs.agregar_articulo(producto)
            
       
            
    def seleccionar_articulo(self):
        indice = self.ids.rvs.articulo_seleccionado()
        if indice >= 0:
            _articulo = self.ids.rvs.data[indice]
            articulo = {
                'codigo': _articulo['codigo'],
                'nombre': _articulo['nombre'],
                'precio': _articulo['precio'],
                'cantidad_carrito': 1,
                'cantidad_inventario': _articulo['cantidad'],  # usado para diferenciar visualización
                'precio_total': _articulo['precio'],
                'tipo_registro': _articulo['tipo_registro']  # importante para después
            }
            if callable(self.agregar_producto):
                self.agregar_producto(articulo)
            self.dismiss()
            
            
class CambiarCantidadPopup (Popup):
    def __init__(self, data,actualizar_articulo_callback, **kwargs):
      super(CambiarCantidadPopup, self).__init__(**kwargs)
      self.data=data
      self.actualizar_articulo=actualizar_articulo_callback
      self.ids.info_nueva_cant_1.text = "Producto: " + self.data['nombre'].capitalize()
      self.ids.info_nueva_cant_2.text = "Cantidad: "+str(self.data['cantidad_carrito'])
    def validar_input(self,texto_input):
        try:
            nueva_cantidad = int(texto_input)
            self.ids.notificacion_no_valido.text=''
            self.actualizar_articulo(nueva_cantidad)
            self.dismiss()
        except:
            self.ids.notificacion_no_valido.text='Cantidad no valida'
 
class PagarPopup(Popup):
    def __init__(self, total,pagado_callback, **kwargs):
      super(PagarPopup, self).__init__(**kwargs)
      self.total= total
      self.pagado =pagado_callback
      self.ids.total.text= "{:.2f}".format(self.total)
      self.ids.boton_pagar.bind(on_release=self.dismiss)
      
    def mostrar_cambio(self):
        recibido = self.ids.recibido.text
        try:
            cambio= float(recibido)- float(self.total)
         
            if cambio >=0:
                self.ids.cambio.text="{:.2f}".format(cambio)
                self.ids.boton_pagar.disabled= False
            else:
                self.ids.cambio.text= "Pago menor a cantidad a pagar"
        except:
            self.ids.cambio.text="Pago no valido"
            
class NuevaCompraPopup(Popup):
    def __init__(self,nueva_compra_callback, **kwargs):
      super(NuevaCompraPopup, self).__init__(**kwargs)
      self.nueva_compra = nueva_compra_callback
      self.ids.aceptar.bind(on_release=self.dismiss)
      
class VentasWindow(BoxLayout):
    usuario = None
	
    def __init__(self,actualizar_productos_callback, **kwargs):
        super().__init__(**kwargs)
        self.total = 0.0
        self.ids.rvs.modificar_producto=self.modificar_producto
        self.actualizar_productos =actualizar_productos_callback
        
        self.ahora= datetime.now()
        self.ids.fecha.text = self.ahora.strftime("%d/%m/%y")
        Clock.schedule_interval(self.actualizar_hora, 1)
        self.ids.hora.text = self.ahora.strftime("%H:%M:%S")

    def agregar_producto_codigo(self, codigo):
        connection = QueriesSQLite.create_connection("pdvDB.sqlite")

        # Buscar primero en productos
        producto_sql = QueriesSQLite.execute_read_query(
            connection, 
            "SELECT codigo, nombre, precio, cantidad FROM productos WHERE codigo = ?", 
            (codigo,)
        )

        if producto_sql:
            item = producto_sql[0]
            articulo = {
                'codigo': item[0],
                'nombre': item[1],
                'precio': item[2], 
                'cantidad_carrito': 1,
                'cantidad_inventario': item[3],
                'precio_total': item[2],
                'tipo_registro': 'producto'  # ← CORREGIR: era 'servicio'
            }
            self.agregar_producto(articulo)
            self.ids.buscar_codigo.text = ''
            return

    # Si no se encuentra, buscar en servicios
        servicio_sql = QueriesSQLite.execute_read_query(
            connection,
            "SELECT codigo, nombre, precio, tipo FROM servicios WHERE codigo = ? AND activo = 1",
            (codigo,)
        )

        if servicio_sql:
            item = servicio_sql[0]
            articulo = {
                'codigo': item[0],
                'nombre': item[1],
                'precio': item[2], 
                'cantidad_carrito': 1,
                'cantidad_inventario': item[3],  # tipo de servicio
                'precio_total': item[2],
                'tipo_registro': 'servicio'
            }
            self.agregar_producto(articulo)
            self.ids.buscar_codigo.text = ''
        return
    def agregar_producto_nombre(self, nombre):
      self.ids.buscar_nombre.text = ''
      popup = ProductoPorNombrePopup(nombre,self.agregar_producto)
      popup.mostrar_articulos()
      popup.open()
    def agregar_producto(self, articulo):
        self.total += articulo['precio']
        self.ids.sub_total.text = '$ ' + "{:.2f}".format(self.total)
        self.ids.rvs.agregar_articulo(articulo)
        print("Producto agregado.")

    def eliminar_producto(self):
        menos_precio=self.ids.rvs.eliminar_articulo()
        self.total-=menos_precio
        self.ids.sub_total.text='$ '+"{:.2f}".format(self.total)
        

    def modificar_producto(self, cambio= True, nuevo_total= None):
        if cambio:
         self.ids.rvs.modificar_articulo()
        else:
            self.total=nuevo_total
            self.ids.sub_total.text='$ '+"{:.2f}".format(self.total)
            
            
    def actualizar_hora (self, *args):
        self.ahora = self.ahora+ timedelta(seconds=1)
        self.ids.hora.text = self.ahora.strftime("%H:%M:%S")

    def pagar(self):
        if self.ids.rvs.data:
           popup = PagarPopup(self.total, self.pagado)
           popup.open()
        else:
            self.ids.notificacion_falla.text = 'No hay nada que pagar'
    


    def pagado(self):
        self.ids.notificacion_exito.text = 'Compra realizada con exito'
        self.ids.notificacion_falla.text = ''
        self.ids.total.text = "{:.2f}".format(self.total)

        self.ids.buscar_codigo.disabled = True
        self.ids.buscar_nombre.disabled = True
        self.ids.pagar.disabled = True

        connection = QueriesSQLite.create_connection("pdvDB.sqlite")
        
        # Consultas SQL
        actualizar_producto = """
        UPDATE
            productos
        SET
            cantidad = ?
        WHERE
            codigo = ?
        """
        
        venta = """ INSERT INTO ventas (total,fecha,username) VALUES (?,?,?)"""
        venta_tuple = (self.total, self.ahora, self.usuario['username'])
        venta_id = QueriesSQLite.execute_query(connection, venta, venta_tuple)
        
        ventas_detalle = """ INSERT INTO ventas_detalle(id_venta, precio, producto, cantidad) VALUES (?, ?, ?, ?) """
        
        actualizar_admin = []

        # Procesar cada item del carrito
        for item in self.ids.rvs.data:
            # Insertar en ventas_detalle (para productos Y servicios)
            ventas_detalle_tuple = (venta_id, item['precio'], item['codigo'], item['cantidad_carrito'])
            QueriesSQLite.execute_query(connection, ventas_detalle, ventas_detalle_tuple)
            
            # Actualizar stock SOLO para productos, NO para servicios
            if item.get('tipo_registro') == 'producto':
                nueva_cantidad = 0
                if item['cantidad_inventario'] - item['cantidad_carrito'] > 0:
                    nueva_cantidad = item['cantidad_inventario'] - item['cantidad_carrito']
                
                producto_tuple = (nueva_cantidad, item['codigo'])
                actualizar_admin.append({'codigo': item['codigo'], 'cantidad': nueva_cantidad})
                QueriesSQLite.execute_query(connection, actualizar_producto, producto_tuple)
            
            # Para servicios, no actualizamos stock ni agregamos a actualizar_admin
            elif item.get('tipo_registro') == 'servicio':
                print(f"Servicio registrado: {item['nombre']} - Cantidad: {item['cantidad_carrito']}")
        
        # Solo actualizar productos en el admin (no servicios)
        self.actualizar_productos(actualizar_admin)
        
      
      
      
    def nueva_compra(self,desde_popup=False):
        if desde_popup:
            self.ids.rvs.data=[]
            self.total=0.0
            self.ids.sub_total.text ='0.00'
            self.ids.total.text ='0.00'
            self.ids.notificacion_exito.text=""
            self.ids.notificacion_falla.text=''
            self.ids.buscar_codigo.disabled= False
            self.ids.buscar_nombre.disabled= False
            self.ids.pagar.disabled=False
            self.ids.rvs.refresh_from_data()
            
        elif len(self.ids.rvs.data):
           popup= NuevaCompraPopup(self.nueva_compra)
           popup.open()
        
    def nueva_compra(self, *args):
        """Reinicia la interfaz para una nueva compra"""
        # Limpiar datos
        self.ids.rvs.data = []
        self.ids.rvs.refresh_from_data()
        self.total = 0.0
    
        # Actualizar interfaz
        self.ids.sub_total.text = '$ 0.00'
        self.ids.total.text = '0.00'
        self.ids.notificacion_exito.text = ''
        self.ids.notificacion_falla.text = ''
    
        # Rehabilitar controles
        self.ids.buscar_codigo.disabled = False
        self.ids.buscar_nombre.disabled = False
        self.ids.pagar.disabled = False
    
        print("Nueva compra iniciada")

    def admin(self):
       # self.parent.parent.current = 'scrn_admin'
      connection = QueriesSQLite.create_connection("pdvDB.sqlite")
      select_products = "SELECT * FROM productos"
      productos = QueriesSQLite.execute_read_query(connection, select_products)

      for producto in productos:
        print(producto)
      self.parent.parent.current ="admin"
    def salir(self):
        print("Signout presionado")

        self.parent.parent.current = "admin"  # o el nombre que tengas
        
    def poner_usuario(self, usuario):
        self.ids.bienvenido_label.text='Bienvenido '+usuario['nombre']
        self.usuario = usuario
        if usuario['tipo'] == 'trabajador':
            self.ids.admin_boton.disabled = True

        else: 
            self.ids.admin_boton.disabled = False
 

class VentasAppX(App):
    def build(self):
        return VentasWindow()

if __name__ == '__main__':
    VentasAppX().run()
    print("Aplicación finalizada")