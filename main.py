from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.image import Image
from kivy.core.window import Window
from kivy.clock import Clock
import os
import requests

# Fondo oscuro profesional estilo trading
Window.clearcolor = (0.07, 0.09, 0.12, 1)

class ApexTraderApp(App):
    def build(self):
        root_layout = FloatLayout()
        ruta_logo = 'logo.png'
        
        # --- 1. LOGOTIPO DE FONDO (MARCA DE AGUA) ---
        if os.path.exists(ruta_logo):
            bg_logo = Image(
                source=ruta_logo,
                size_hint=(1.0, 1.0),
                pos_hint={'center_x': 0.5, 'center_y': 0.5},
                opacity=0.10
            )
            root_layout.add_widget(bg_logo)
            
        # --- 2. CONTENIDO PRINCIPAL ---
        content_layout = BoxLayout(orientation='vertical', padding=12, spacing=8)
        
        # Encabezado con Logo y Título
        header_layout = BoxLayout(orientation='horizontal', size_hint=(1, 0.08), spacing=10)
        if os.path.exists(ruta_logo):
            logo_img = Image(source=ruta_logo, size_hint=(None, 1), width=250)
            header_layout.add_widget(logo_img)
            
        titulo = Label(
            text="[b]APEX TRADER PRO[/b]", 
            markup=True, 
            font_size=80, 
            halign='left',
            valign='middle',
            color=(0.9, 0.92, 0.95, 1)
        )
        titulo.bind(size=titulo.setter('text_size'))
        header_layout.add_widget(titulo)
        content_layout.add_widget(header_layout)
        
        # Saldo Demo
        self.label_saldo = Label(
            text="[b]Saldo Demo:[/b] $1,000.00 USDT",
            markup=True,
            font_size=60,
            size_hint=(1, 0.05),
            color=(0.15, 0.85, 1, 1)
        )
        content_layout.add_widget(self.label_saldo)
        
        # Entradas de configuración
        content_layout.add_widget(Label(text="Símbolo (ej: XRPUSDT):", font_size=12, size_hint=(1, 0.03), color=(0.7, 0.75, 0.8, 1)))
        self.input_symbol = TextInput(text="XRPUSDT", multiline=False, font_size=40, size_hint=(1, 0.055))
        content_layout.add_widget(self.input_symbol)
        
        content_layout.add_widget(Label(text="Margen a Invertir (USDT):", font_size=12, size_hint=(1, 0.03), color=(0.7, 0.75, 0.8, 1)))
        self.input_capital = TextInput(text="3", multiline=False, font_size=40, size_hint=(1, 0.055), input_filter='float')
        content_layout.add_widget(self.input_capital)

        content_layout.add_widget(Label(text="Apalancamiento:", font_size=12, size_hint=(1, 0.03), color=(0.7, 0.75, 0.8, 1)))
        self.input_leverage = TextInput(text="10", multiline=False, font_size=40, size_hint=(1, 0.055), input_filter='float')
        content_layout.add_widget(self.input_leverage)
        
        # Botón de análisis y cálculo neto con sugerencia
        self.btn_analizar = Button(
            text="🔍 1. Analizar y Calcular Posición",
            font_size=40,
            size_hint=(1, 0.075),
            background_normal='',
            background_color=(0.12, 0.53, 0.9, 1)
        )
        self.btn_analizar.bind(on_press=self.analizar_mercado)
        content_layout.add_widget(self.btn_analizar)
        
        # Botones de decisión (Long / Short)
        self.layout_botones_decision = BoxLayout(orientation='horizontal', spacing=10, size_hint=(1, 0.07))
        self.btn_long = Button(text="🟢 COMPRAR (LONG)", font_size=40, background_normal='', background_color=(0.0, 0.75, 0.4, 1))
        self.btn_long.bind(on_press=lambda x: self.ejecutar_operacion_demo("LONG"))
        self.btn_short = Button(text="🔴 VENDER (SHORT)", font_size=13, background_normal='', background_color=(0.95, 0.25, 0.3, 1))
        self.btn_short.bind(on_press=lambda x: self.ejecutar_operacion_demo("SHORT"))
        
        self.layout_botones_decision.add_widget(self.btn_long)
        self.layout_botones_decision.add_widget(self.btn_short)
        content_layout.add_widget(self.layout_botones_decision)
        self.layout_botones_decision.disabled = True
        self.layout_botones_decision.opacity = 0.3
        
        # Botón para cerrar posición activa
        self.btn_cerrar = Button(
            text="❌ Cerrar Posición y Realizar PnL",
            font_size=40,
            size_hint=(1, 0.07),
            background_normal='',
            background_color=(0.95, 0.55, 0.1, 1)
        )
        self.btn_cerrar.bind(on_press=lambda x: self.cerrar_posicion_demo())
        content_layout.add_widget(self.btn_cerrar)
        self.btn_cerrar.disabled = True
        self.btn_cerrar.opacity = 0.3
        
        # Etiqueta de resultados, sugerencia y PnL en vivo
        self.resultado_label = Label(
            text="Configura tus parámetros y presiona analizar...",
            font_size=40,
            halign='center',
            valign='middle',
            markup=True,
            color=(0.85, 0.88, 0.92, 1)
        )
        self.resultado_label.bind(size=self.resultado_label.setter('text_size'))
        content_layout.add_widget(self.resultado_label)
        
        root_layout.add_widget(content_layout)
        
        # Variables de estado del simulador
        self.saldo_ficticio = 1000.0
        self.en_operacion = False
        self.precio_actual_cache = 0.0
        self.unidades_cache = 0.0
        self.comision_cache = 0.0
        self.margen_bruto_cache = 0.0
        self.margen_neto_cache = 0.0
        self.tamano_neto_cache = 0.0
        self.apalancamiento_cache = 0.0
        self.sim_simbolo = ""
        self.sim_decision = ""
        self.sim_precio_entrada = 0.0
        self.pnl_neto_actual = 0.0
        
        return root_layout

    def actualizar_saldo_ui(self):
        self.label_saldo.text = f"[b]Saldo Demo:[/b] ${self.saldo_ficticio:,.2f} USDT"

    def analizar_mercado(self, instance):
        if self.en_operacion:
            self.resultado_label.text = "⚠️ Tienes una posición activa. Ciérrala primero."
            return
            
        try:
            simbolo = self.input_symbol.text.strip().upper()
            texto_capital = self.input_capital.text.strip()
            texto_leverage = self.input_leverage.text.strip()
            
            if not simbolo or not texto_capital or not texto_leverage:
                self.resultado_label.text = "⚠️ Rellena todos los campos obligatorios."
                return
            
            margen_bruto = float(texto_capital)
            apalancamiento = float(texto_leverage)
            
            if margen_bruto <= 0 or apalancamiento <= 0:
                self.resultado_label.text = "⚠️ Valores inválidos detectados."
                return
                
            if margen_bruto > self.saldo_ficticio:
                self.resultado_label.text = "❌ Margen superior a tu saldo disponible."
                return
            
            # 1. Consultar precio actual
            url_precio = f"https://api.binance.com/api/v3/ticker/price?symbol={simbolo}"
            resp_precio = requests.get(url_precio, timeout=5).json()
            if "price" not in resp_precio:
                self.resultado_label.text = "❌ Símbolo no encontrado en Binance."
                return
            precio_actual = float(resp_precio["price"])
            
            # 2. Consultar tendencia macro para la sugerencia
            url_velas_macro = f"https://api.binance.com/api/v3/klines?symbol={simbolo}&interval=1d&limit=100"
            resp_velas = requests.get(url_velas_macro, timeout=5).json()
            if isinstance(resp_velas, list) and len(resp_velas) > 0:
                precios_cierre = [float(vela[4]) for vela in resp_velas]
                media_macro = sum(precios_cierre) / len(precios_cierre)
                sugerencia = "COMPRAR (LONG)" if precio_actual > media_macro else "VENDER (SHORT)"
                color_sug = "00d26a" if precio_actual > media_macro else "ff4d4d"
            else:
                sugerencia = "NEUTRAL"
                color_sug = "ffffff"
            
            # --- 3. CÁLCULO NETO TRAS COMISIÓN (0.08% Taker) ---
            tasa_comision_pct = 0.0008
            tamano_bruto = margen_bruto * apalancamiento
            comision_est = tamano_bruto * tasa_comision_pct
            
            margen_neto = margen_bruto - comision_est
            tamano_neto = tamano_bruto - comision_est
            
            if margen_neto <= 0:
                self.resultado_label.text = "❌ Margen insuficiente para cubrir la comisión."
                return

            self.unidades_cache = tamano_neto / precio_actual
            self.comision_cache = comision_est
            self.margen_bruto_cache = margen_bruto
            self.margen_neto_cache = margen_neto
            self.tamano_neto_cache = tamano_neto
            self.apalancamiento_cache = apalancamiento
            self.precio_actual_cache = precio_actual
            self.sim_simbolo = simbolo
            
            self.resultado_label.text = (
                f"[b]{simbolo}[/b] | Precio: ${precio_actual:,.4f}\n"
                f"• Margen Neto: [color=00d26a]${margen_neto:,.4f} USDT[/color] (Comisión: -${comision_est:,.4f})\n"
                f"• Tamaño Neto: [color=15d5ff]${tamano_neto:,.2f} USDT[/color] ({apalancamiento:g}x)\n"
                f"• Sugerencia: [color={color_sug}][b]{sugerencia}[/b][/color]\n\n"
                f"👇 Selecciona tu orden abajo:"
            )
            
            self.layout_botones_decision.disabled = False
            self.layout_botones_decision.opacity = 1.0
            
        except Exception as e:
            self.resultado_label.text = f"Error en análisis: {e}"

    def ejecutar_operacion_demo(self, decision):
        # Descontamos el margen bruto de la cuenta demo
        self.saldo_ficticio -= self.margen_bruto_cache
        self.actualizar_saldo_ui()
        
        self.sim_decision = decision
        self.sim_precio_entrada = self.precio_actual_cache
        self.en_operacion = True
        
        self.layout_botones_decision.disabled = True
        self.layout_botones_decision.opacity = 0.3
        
        self.btn_cerrar.disabled = False
        self.btn_cerrar.opacity = 1.0
        
        self.btn_analizar.text = "📈 Posición Activa en Vivo..."
        
        Clock.schedule_interval(self.actualizar_en_vivo, 3.0)
        self.actualizar_en_vivo(0)

    def actualizar_en_vivo(self, dt):
        if not self.en_operacion:
            return False
        try:
            url_precio = f"https://api.binance.com/api/v3/ticker/price?symbol={self.sim_simbolo}"
            respuesta = requests.get(url_precio, timeout=5).json()
            precio_vivo = float(respuesta["price"])
            
            if self.sim_decision == "LONG":
                pnl_bruto = self.unidades_cache * (precio_vivo - self.sim_precio_entrada)
            else:
                pnl_bruto = self.unidades_cache * (self.sim_precio_entrada - precio_vivo)
                
            self.pnl_neto_actual = pnl_bruto - self.comision_cache
            
            if self.pnl_neto_actual >= 0:
                pnl_formateado = f"[color=00d26a][b]+${self.pnl_neto_actual:,.2f} USDT[/b][/color]"
            else:
                pnl_formateado = f"[color=ff4d4d][b]-${abs(self.pnl_neto_actual):,.2f} USDT[/b][/color]"
                
            texto_en_vivo = (
                f"🚀 [b]{self.sim_simbolo}[/b] ({self.sim_decision} {self.apalancamiento_cache:g}x)\n"
                f"• Margen Neto: ${self.margen_neto_cache:,.2f} | Tamaño Neto: ${self.tamano_neto_cache:,.2f}\n"
                f"Entrada: ${self.sim_precio_entrada:,.4f} ➔ Vivo: ${precio_vivo:,.4f}\n"
                f"PnL Neto Real: {pnl_formateado}"
            )
            self.resultado_label.text = texto_en_vivo
            
        except Exception as e:
            self.resultado_label.text = f"Sincronizando con Binance... ({e})"

    def cerrar_posicion_demo(self):
        if not self.en_operacion:
            return
            
        Clock.unschedule(self.actualizar_en_vivo)
        self.en_operacion = False
        
        # Devolvemos el margen bruto inicial + el PnL neto real
        self.saldo_ficticio += (self.margen_bruto_cache + self.pnl_neto_actual)
        self.actualizar_saldo_ui()
        
        self.btn_cerrar.disabled = True
        self.btn_cerrar.opacity = 0.3
        
        self.btn_analizar.text = "🔍 1. Analizar y Calcular Posición"
        color_res = "00d26a" if self.pnl_neto_actual >= 0 else "ff4d4d"
        signo = "+" if self.pnl_neto_actual >= 0 else ""
        self.resultado_label.text = (
            f"✅ Posición cerrada con éxito.\n"
            f"Comisión Cobrada: -${self.comision_cache:,.4f} USDT\n"
            f"Resultado Neto: [color={color_res}][b]{signo}${self.pnl_neto_actual:,.2f} USDT[/b][/color]"
        )

if __name__ == '__main__':
    ApexTraderApp().run()
