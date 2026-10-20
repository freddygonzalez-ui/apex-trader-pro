from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.uix.image import Image
from kivy.uix.scrollview import ScrollView
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.metrics import dp, sp
import os
import csv
import threading
from datetime import datetime
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

Window.clearcolor = (0.07, 0.09, 0.12, 1)

# Configurar sesión HTTP robusta con reintentos automáticos
session = requests.Session()
retries = Retry(total=3, backoff_factor=0.5, status_forcelist=[500, 502, 503, 504])
session.mount('https://', HTTPAdapter(max_retries=retries))


def calcular_ema(precios, periodo):
    if len(precios) < periodo:
        return sum(precios) / len(precios)
    k = 2 / (periodo + 1)
    ema = sum(precios[:periodo]) / periodo
    for precio in precios[periodo:]:
        ema = (precio * k) + (ema * (1 - k))
    return ema

def calcular_rsi(precios, periodo=14):
    if len(precios) < periodo + 1:
        return 50.0
    ganancias = []
    perdidas = []
    for i in range(1, len(precios)):
        diferencia = precios[i] - precios[i - 1]
        if diferencia > 0:
            ganancias.append(diferencia)
            perdidas.append(0)
        else:
            ganancias.append(0)
            perdidas.append(abs(diferencia))
    avg_gain = sum(ganancias[:periodo]) / periodo
    avg_loss = sum(perdidas[:periodo]) / periodo
    for i in range(periodo, len(ganancias)):
        avg_gain = (avg_gain * (periodo - 1) + ganancias[i]) / periodo
        avg_loss = (avg_loss * (periodo - 1) + perdidas[i]) / periodo
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100.0 - (100.0 / (1.0 + rs))

def calcular_macd(precios, rapida=12, lenta=26, senal=9):
    if len(precios) < lenta + senal:
        return 0.0, 0.0, 0.0
    macd_line = []
    for i in range(lenta, len(precios) + 1):
        sub_precios = precios[:i]
        ema_r = calcular_ema(sub_precios, rapida)
        ema_l = calcular_ema(sub_precios, lenta)
        macd_line.append(ema_r - ema_l)
    linea_macd_actual = macd_line[-1]
    linea_signal_actual = calcular_ema(macd_line, senal)
    histograma = linea_macd_actual - linea_signal_actual
    return linea_macd_actual, linea_signal_actual, histograma

def calcular_atr(velas, periodo=14):
    if len(velas) < periodo + 1:
        return 0.0
    tr_lista = []
    for i in range(1, len(velas)):
        high = float(velas[i][2])
        low = float(velas[i][3])
        prev_close = float(velas[i-1][4])
        tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
        tr_lista.append(tr)
    atr = sum(tr_lista[:periodo]) / periodo
    for i in range(periodo, len(tr_lista)):
        atr = (atr * (periodo - 1) + tr_lista[i]) / periodo
    return atr

def calcular_adx(velas, periodo=14):
    if len(velas) < periodo * 2:
        return 20.0
    
    tr_list, pdm_list, mdm_list = [], [], []
    for i in range(1, len(velas)):
        h = float(velas[i][2])
        l = float(velas[i][3])
        c_prev = float(velas[i-1][4])
        h_prev = float(velas[i-1][2])
        l_prev = float(velas[i-1][3])
        
        tr = max(h - l, abs(h - c_prev), abs(l - c_prev))
        tr_list.append(tr)
        
        pdm = h - h_prev if (h - h_prev) > (l_prev - l) else 0
        pdm = max(pdm, 0)
        pdm_list.append(pdm)
        
        mdm = l_prev - l if (l_prev - l) > (h - h_prev) else 0
        mdm = max(mdm, 0)
        mdm_list.append(mdm)
        
    atr = sum(tr_list[:periodo])
    pdi = sum(pdm_list[:periodo])
    mdi = sum(mdm_list[:periodo])
    
    dx_list = []
    for i in range(periodo, len(tr_list)):
        atr = atr - (atr / periodo) + tr_list[i]
        pdi = pdi - (pdi / periodo) + pdm_list[i]
        mdi = mdi - (mdi / periodo) + mdm_list[i]
        
        plus_di = (pdi / atr) * 100 if atr > 0 else 0
        minus_di = (mdi / atr) * 100 if atr > 0 else 0
        
        suma_di = plus_di + minus_di
        dx = (abs(plus_di - minus_di) / suma_di * 100) if suma_di > 0 else 0
        dx_list.append(dx)
        
    if not dx_list:
        return 20.0
    return sum(dx_list[-periodo:]) / min(len(dx_list), periodo)


class ApexTraderApp(App):
    def build(self):
        root_layout = FloatLayout()
        
        # Búsqueda y validación del logo (soporta .png o .jpg)
        ruta_logo = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logo.png')
        if not os.path.exists(ruta_logo):
            ruta_logo = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logo.jpg')
            
        # 1. Logo como marca de agua en el fondo (PROPORCIONAL)
        if os.path.exists(ruta_logo):
            bg_logo = Image(
                source=ruta_logo,
                size_hint=(0.7, 0.7),
                pos_hint={'center_x': 0.5, 'center_y': 0.5},
                opacity=0.10,
                allow_stretch=True,
                keep_ratio=True  # Mantiene la proporción sin deformar
            )
            root_layout.add_widget(bg_logo)
            
        content_layout = BoxLayout(orientation='vertical', padding=dp(12), spacing=dp(8))
        
        controls_layout = BoxLayout(
            orientation='vertical', 
            spacing=dp(6), 
            size_hint_y=None
        )
        controls_layout.bind(minimum_height=controls_layout.setter('height'))

        # 2. Cabecera con Logo más grande al lado del Título
        header_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(48), spacing=dp(10))
        
        if os.path.exists(ruta_logo):
            logo_header = Image(
                source=ruta_logo,
                size_hint=(None, None),
                size=(dp(48), dp(48)),
                allow_stretch=True,
                keep_ratio=True
            )
            header_layout.add_widget(logo_header)

        titulo = Label(
            text="[b]APEX TRADER PRO[/b]\n[size=12sp](Multi-Operación)[/size]", 
            markup=True, 
            font_size=sp(16), 
            halign='left',
            valign='middle',
            color=(0.9, 0.92, 0.95, 1)
        )
        titulo.bind(size=titulo.setter('text_size'))
        header_layout.add_widget(titulo)
        controls_layout.add_widget(header_layout)
        
        self.label_saldo = Label(
            text="[b]Saldo Demo:[/b] $1,000.00 USDT",
            markup=True,
            font_size=sp(16),
            size_hint_y=None,
            height=dp(28),
            color=(0.15, 0.85, 1, 1)
        )
        controls_layout.add_widget(self.label_saldo)
        
        controls_layout.add_widget(Label(text="Selecciona Criptomoneda (Top 10 Estables):", font_size=sp(12), size_hint_y=None, height=dp(20), color=(0.7, 0.75, 0.8, 1)))
        
        self.lista_criptos = [
            'BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'BNBUSDT', 'XRPUSDT', 
            'ADAUSDT', 'AVAXUSDT', 'LINKUSDT', 'SUIUSDT', 'NEARUSDT'
        ]
        
        self.spinner_symbol = Spinner(
            text='XRPUSDT',
            values=self.lista_criptos,
            font_size=sp(16),
            size_hint_y=None,
            height=dp(42),
            background_normal='',
            background_color=(0.15, 0.20, 0.28, 1),
            color=(0.9, 0.95, 1, 1)
        )
        controls_layout.add_widget(self.spinner_symbol)
        
        inputs_row = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(68), spacing=dp(12))
        
        col_cap = BoxLayout(orientation='vertical', spacing=dp(4))
        col_cap.add_widget(Label(text="Margen (USDT):", font_size=sp(12), size_hint_y=None, height=dp(18), color=(0.7, 0.75, 0.8, 1)))
        self.input_capital = TextInput(
            text="10",
            multiline=False,
            font_size=sp(16),
            size_hint_y=None,
            height=dp(42),
            input_filter="float",
            padding=[dp(8), dp(8), dp(8), dp(8)]
        )
        col_cap.add_widget(self.input_capital)
        inputs_row.add_widget(col_cap)
        
        col_lev = BoxLayout(orientation='vertical', spacing=dp(4))
        col_lev.add_widget(Label(text="Apalancamiento:", font_size=sp(12), size_hint_y=None, height=dp(18), color=(0.7, 0.75, 0.8, 1)))
        self.input_leverage = TextInput(
            text="10",
            multiline=False,
            font_size=sp(16),
            size_hint_y=None,
            height=dp(42),
            input_filter="float",
            padding=[dp(8), dp(8), dp(8), dp(8)]
        )
        col_lev.add_widget(self.input_leverage)
        inputs_row.add_widget(col_lev)

        controls_layout.add_widget(inputs_row)
        
        self.btn_analizar = Button(
            text="1. Analizar Cascada Estricta + Filtro ADX",
            font_size=sp(14),
            size_hint_y=None,
            height=dp(45),
            background_normal='',
            background_color=(0.12, 0.53, 0.9, 1)
        )
        self.btn_analizar.bind(on_press=self.iniciar_analisis_en_vivo)
        controls_layout.add_widget(self.btn_analizar)
        
        self.layout_botones_decision = BoxLayout(orientation='horizontal', spacing=dp(10), size_hint_y=None, height=dp(42))
        self.btn_long = Button(text="COMPRAR (LONG)", font_size=sp(13), background_normal='', background_color=(0.0, 0.75, 0.4, 1))
        self.btn_long.bind(on_press=lambda x: self.ejecutar_operacion_demo("LONG"))
        self.btn_short = Button(text="VENDER (SHORT)", font_size=sp(13), background_normal='', background_color=(0.95, 0.25, 0.3, 1))
        self.btn_short.bind(on_press=lambda x: self.ejecutar_operacion_demo("SHORT"))
        
        self.layout_botones_decision.add_widget(self.btn_long)
        self.layout_botones_decision.add_widget(self.btn_short)
        controls_layout.add_widget(self.layout_botones_decision)
        self.layout_botones_decision.disabled = True
        self.layout_botones_decision.opacity = 0.3
        
        row_acciones = BoxLayout(orientation='horizontal', spacing=dp(10), size_hint_y=None, height=dp(42))
        self.btn_cerrar = Button(
            text="Cerrar Última Posición",
            font_size=sp(13),
            background_normal='',
            background_color=(0.95, 0.55, 0.1, 1)
        )
        self.btn_cerrar.bind(on_press=lambda x: self.cerrar_ultima_posicion())
        self.btn_cerrar.disabled = True
        self.btn_cerrar.opacity = 0.3
        row_acciones.add_widget(self.btn_cerrar)
        
        self.btn_stats = Button(
            text="Ver Estadísticas (WinRate)",
            font_size=sp(13),
            background_normal='',
            background_color=(0.3, 0.35, 0.45, 1)
        )
        self.btn_stats.bind(on_press=self.mostrar_estadisticas)
        row_acciones.add_widget(self.btn_stats)
        
        controls_layout.add_widget(row_acciones)
        content_layout.add_widget(controls_layout)
        
        # --- SECCIÓN INFERIOR SCROLLABLE ---
        scroll_resultado = ScrollView(size_hint=(1, 1))
        
        self.resultado_label = Label(
            text="Selecciona una cripto y presiona analizar...",
            font_size=sp(16),
            halign='center',
            valign='middle',
            markup=True,
            color=(0.85, 0.88, 0.92, 1),
            size_hint=(1, None)
        )
        self.resultado_label.bind(
            width=lambda instance, value: setattr(instance, 'text_size', (value, None)),
            texture_size=lambda instance, value: setattr(instance, 'height', max(value[1], scroll_resultado.height))
        )
        scroll_resultado.bind(height=lambda instance, value: setattr(self.resultado_label, 'height', max(self.resultado_label.texture_size[1], value)))
        
        scroll_resultado.add_widget(self.resultado_label)
        content_layout.add_widget(scroll_resultado)
        root_layout.add_widget(content_layout)
        
        # Variables de estado (Multi-operación)
        self.saldo_ficticio = 1000.0
        self.operaciones_activas = []
        self.analizando_activo = False
        self.precio_actual_cache = 0.0
        self.atr_cache = 0.0
        self.sim_simbolo = ""
        
        return root_layout

    def actualizar_saldo_ui(self):
        self.label_saldo.text = f"[b]Saldo Demo:[/b] ${self.saldo_ficticio:,.2f} USDT"

    def iniciar_analisis_en_vivo(self, instance):
        if len(self.operaciones_activas) >= 2:
            self.resultado_label.text = "Ya tienes 2 operaciones activas (límite máximo). Cierra una para abrir otra."
            return
        if self.analizando_activo:
            return

        texto_capital = self.input_capital.text.strip()
        texto_leverage = self.input_leverage.text.strip()
        
        if not texto_capital or not texto_leverage:
            self.resultado_label.text = "Rellena todos los campos obligatorios."
            return
        
        margen_bruto = float(texto_capital)
        apalancamiento = float(texto_leverage)
        
        if margen_bruto <= 0 or apalancamiento <= 0:
            self.resultado_label.text = "Valores inválidos detectados."
            return
        if margen_bruto > self.saldo_ficticio:
            self.resultado_label.text = "Saldo insuficiente para este margen."
            return

        self.analizando_activo = True
        self.btn_analizar.text = "Buscando Tendencia Real..."
        
        threading.Thread(target=self.proceso_analisis_thread, daemon=True).start()

    def proceso_analisis_thread(self):
        while self.analizando_activo and len(self.operaciones_activas) < 2:
            try:
                simbolo = self.spinner_symbol.text.strip().upper()
                margen_bruto = float(self.input_capital.text.strip())
                apalancamiento = float(self.input_leverage.text.strip())
                
                url_precio = f"https://api.binance.com/api/v3/ticker/price?symbol={simbolo}"
                resp_precio = session.get(url_precio, timeout=3).json()
                
                if "price" not in resp_precio:
                    Clock.schedule_once(lambda dt: setattr(self.resultado_label, 'text', "Símbolo no encontrado en Binance."))
                    break
                precio_actual = float(resp_precio["price"])
                
                url_1h = f"https://api.binance.com/api/v3/klines?symbol={simbolo}&interval=1h&limit=100"
                url_4h = f"https://api.binance.com/api/v3/klines?symbol={simbolo}&interval=4h&limit=50"
                url_1d = f"https://api.binance.com/api/v3/klines?symbol={simbolo}&interval=1d&limit=50"
                
                resp_1h = session.get(url_1h, timeout=3).json()[:-1] 
                resp_4h = session.get(url_4h, timeout=3).json()[:-1] 
                resp_1d = session.get(url_1d, timeout=3).json()[:-1] 
                
                cierres_1h = [float(i[4]) for i in resp_1h]
                volumenes_1h = [float(i[5]) for i in resp_1h]
                cierres_4h = [float(i[4]) for i in resp_4h]
                cierres_1d = [float(i[4]) for i in resp_1d]
                
                ema20_1h = calcular_ema(cierres_1h, 20)
                ema50_1h = calcular_ema(cierres_1h, 50)
                rsi_1h = calcular_rsi(cierres_1h, 14)
                macd_line, macd_signal, macd_hist = calcular_macd(cierres_1h)
                atr_1h = calcular_atr(resp_1h, 14)
                adx_1h = calcular_adx(resp_1h, 14)
                
                ema20_4h = calcular_ema(cierres_4h, 20)
                ema50_4h = calcular_ema(cierres_4h, 50)
                ema20_1d = calcular_ema(cierres_1d, 20)
                ema50_1d = calcular_ema(cierres_1d, 50)
                
                vol_actual = volumenes_1h[-1]
                vol_media = sum(volumenes_1h[-20:]) / 20
                volumen_fuerte = vol_actual > vol_media

                tendencia_macro_1d = ema20_1d > ema50_1d
                tendencia_media_4h = ema20_4h > ema50_4h
                tendencia_rapida_1h = ema20_1h > ema50_1h
                
                puntos_long = 0
                puntos_short = 0
                
                if tendencia_macro_1d: puntos_long += 25
                else: puntos_short += 25
                
                if tendencia_media_4h: puntos_long += 25
                else: puntos_short += 25
                
                if tendencia_rapida_1h: puntos_long += 20
                else: puntos_short += 20
                
                if macd_hist > 0: puntos_long += 15
                else: puntos_short += 15
                
                if volumen_fuerte:
                    if macd_hist > 0: puntos_long += 15
                    else: puntos_short += 15

                mercado_en_rango = adx_1h < 28

                sugerencia = "MERCADO EN RANGO / ESPERAR"
                color_sug = "ffb703"
                habilitar_botones = False
                
                if not mercado_en_rango:
                    if puntos_long >= 75 and tendencia_macro_1d and tendencia_media_4h:
                        sugerencia = f"COMPRAR (LONG) [Confianza: {puntos_long}% | ADX: {adx_1h:.1f}]"
                        color_sug = "00d26a"
                        habilitar_botones = True
                    elif puntos_short >= 75 and not tendencia_macro_1d and not tendencia_media_4h:
                        sugerencia = f"VENDER (SHORT) [Confianza: {puntos_short}% | ADX: {adx_1h:.1f}]"
                        color_sug = "ff4d4d"
                        habilitar_botones = True
                    else:
                        sugerencia = f"ESPERAR (Confluencia Insuficiente | ADX: {adx_1h:.1f})"
                else:
                    sugerencia = f"MERCADO LATERAL BLOQUEADO (ADX Bajo: {adx_1h:.1f})"

                tasa_comision_pct = 0.0008
                tamano_bruto = margen_bruto * apalancamiento
                comision_est = (tamano_bruto * tasa_comision_pct) * 2
                
                self.precio_actual_cache = precio_actual
                self.sim_simbolo = simbolo
                self.atr_cache = atr_1h
                
                def actualizar_ui_callback(dt):
                    self.resultado_label.text = (
                        f"[b]{simbolo}[/b] | Precio Vivo: ${precio_actual:,.4f}\n"
                        f"RSI: {rsi_1h:.1f} | ADX: {adx_1h:.1f}\n"
                        f"Estado: [color={color_sug}][b]{sugerencia}[/b][/color]\n"
                        f"Comisión Est.: ${comision_est:,.2f} USDT\n"
                        f"Operaciones Activas: {len(self.operaciones_activas)}/2"
                    )
                    if habilitar_botones and len(self.operaciones_activas) < 2:
                        self.layout_botones_decision.disabled = False
                        self.layout_botones_decision.opacity = 1.0
                    else:
                        self.layout_botones_decision.disabled = True
                        self.layout_botones_decision.opacity = 0.3
                    self.btn_analizar.text = "1. Analizar Cascada Estricta + Filtro ADX"

                Clock.schedule_once(actualizar_ui_callback)
                
            except Exception as e:
                Clock.schedule_once(lambda dt, err=e: setattr(self.resultado_label, 'text', f"Sincronizando red... ({err})"))
            
            import time
            time.sleep(3.0)

    def ejecutar_operacion_demo(self, decision):
        if len(self.operaciones_activas) >= 2:
            self.resultado_label.text = "Límite máximo alcanzado (2 operaciones simultáneas)."
            return

        texto_capital = self.input_capital.text.strip()
        texto_leverage = self.input_leverage.text.strip()
        margen_bruto = float(texto_capital)
        apalancamiento = float(texto_leverage)

        if margen_bruto > self.saldo_ficticio:
            self.resultado_label.text = "Saldo insuficiente para ejecutar esta posición."
            return

        self.saldo_ficticio -= margen_bruto
        self.actualizar_saldo_ui()
        
        tamano_bruto = margen_bruto * apalancamiento
        unidades = tamano_bruto / self.precio_actual_cache
        tasa_comision_pct = 0.0008
        comision_total = (tamano_bruto * tasa_comision_pct) * 2

        distancia_sl = self.atr_cache * 2.0
        distancia_tp = self.atr_cache * 5.0
        
        if decision == "LONG":
            sl = self.precio_actual_cache - distancia_sl
            tp = self.precio_actual_cache + distancia_tp
            liq = self.precio_actual_cache * (1 - (0.9 / apalancamiento))
        else:
            sl = self.precio_actual_cache + distancia_sl
            tp = self.precio_actual_cache - distancia_tp
            liq = self.precio_actual_cache * (1 + (0.9 / apalancamiento))

        nueva_op = {
            "simbolo": self.sim_simbolo,
            "decision": decision,
            "entrada": self.precio_actual_cache,
            "margen": margen_bruto,
            "apalancamiento": apalancamiento,
            "unidades": unidades,
            "comision": comision_total,
            "stop_loss": sl,
            "take_profit": tp,
            "liquidacion": liq,
            "tiempo": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "max_precio": self.precio_actual_cache,
            "min_precio": self.precio_actual_cache,
            "activa": True
        }

        self.operaciones_activas.append(nueva_op)
        
        self.btn_cerrar.disabled = False
        self.btn_cerrar.opacity = 1.0

        if len(self.operaciones_activas) >= 2:
            self.layout_botones_decision.disabled = True
            self.layout_botones_decision.opacity = 0.3
            self.analizando_activo = False

        threading.Thread(target=self.monitoreo_multi_thread, args=(nueva_op,), daemon=True).start()

    def monitoreo_multi_thread(self, op):
        import time
        while op["activa"]:
            try:
                url_precio = f"https://api.binance.com/api/v3/ticker/price?symbol={op['simbolo']}"
                respuesta = session.get(url_precio, timeout=2).json()
                precio_vivo = float(respuesta["price"])
                
                razon = None
                if op["decision"] == "LONG":
                    if precio_vivo > op["max_precio"]:
                        op["max_precio"] = precio_vivo
                        nuevo_sl = op["max_precio"] - (self.atr_cache * 1.5)
                        if nuevo_sl > op["stop_loss"]:
                            op["stop_loss"] = nuevo_sl
                            
                    if precio_vivo <= op["stop_loss"]:
                        razon = "Stop-Loss / Trailing Alcanzado"
                    elif precio_vivo >= op["take_profit"]:
                        razon = "Take-Profit Alcanzado"
                    elif precio_vivo <= op["liquidacion"]:
                        razon = "LIQUIDACIÓN FORZOSA"
                else:
                    if precio_vivo < op["min_precio"]:
                        op["min_precio"] = precio_vivo
                        nuevo_sl = op["min_precio"] + (self.atr_cache * 1.5)
                        if nuevo_sl < op["stop_loss"]:
                            op["stop_loss"] = nuevo_sl
                            
                    if precio_vivo >= op["stop_loss"]:
                        razon = "Stop-Loss / Trailing Alcanzado"
                    elif precio_vivo <= op["take_profit"]:
                        razon = "Take-Profit Alcanzado"
                    elif precio_vivo >= op["liquidacion"]:
                        razon = "LIQUIDACIÓN FORZOSA"
                
                pnl_bruto = op["unidades"] * (precio_vivo - op["entrada"]) if op["decision"] == "LONG" else op["unidades"] * (op["entrada"] - precio_vivo)
                pnl_neto = pnl_bruto - op["comision"]
                op["pnl_actual"] = pnl_neto
                op["precio_vivo"] = precio_vivo

                def actualizar_pantalla(dt):
                    texto_ops = f"[b]POSICIONES ACTIVAS ({len(self.operaciones_activas)}/2)[/b]\n\n"
                    for idx, o in enumerate(self.operaciones_activas):
                        color_pnl = "00d26a" if o.get('pnl_actual', 0) >= 0 else "ff4d4d"
                        texto_ops += (
                            f"--- Posición {idx+1}: {o['simbolo']} ({o['decision']}) ---\n"
                            f"Entrada: ${o['entrada']:,.4f} | Vivo: ${o.get('precio_vivo', 0):,.4f}\n"
                            f"SL: ${o['stop_loss']:,.4f} | TP: ${o['take_profit']:,.4f}\n"
                            f"PnL Neto: [color={color_pnl}]${o.get('pnl_actual', 0):,.2f} USDT[/color]\n\n"
                        )
                    self.resultado_label.text = texto_ops

                Clock.schedule_once(actualizar_pantalla)

                if razon:
                    self.cerrar_operacion_especifica(op, razon)
                    break
                    
            except Exception:
                pass
            
            time.sleep(1.5)

    def cerrar_operacion_especifica(self, op, razon):
        if not op["activa"]:
            return
        op["activa"] = False

        try:
            url_precio = f"https://api.binance.com/api/v3/ticker/price?symbol={op['simbolo']}"
            respuesta = session.get(url_precio, timeout=2).json()
            precio_salida = float(respuesta["price"])
        except Exception:
            precio_salida = op.get('precio_vivo', op['entrada'])

        if op["decision"] == "LONG":
            pnl_bruto = op["unidades"] * (precio_salida - op["entrada"])
        else:
            pnl_bruto = op["unidades"] * (op["entrada"] - precio_salida)
            
        pnl_neto = pnl_bruto - op["comision"]
        retorno_total = op["margen"] + pnl_neto
        self.saldo_ficticio += max(0, retorno_total)
        self.actualizar_saldo_ui()

        archivo_csv = "historial_trades.csv"
        archivo_existe = os.path.exists(archivo_csv)
        try:
            with open(archivo_csv, mode="a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                if not archivo_existe:
                    writer.writerow(["Simbolo", "Decision", "Entrada", "Salida", "Margen", "Apalancamiento", "PnL Neto", "Razon", "F_Entrada", "F_Salida"])
                writer.writerow([op['simbolo'], op['decision'], op['entrada'], precio_salida, op['margen'], op['apalancamiento'], round(pnl_neto, 2), razon, op['tiempo'], datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
        except Exception:
            pass

        if op in self.operaciones_activas:
            self.operaciones_activas.remove(op)

        if len(self.operaciones_activas) == 0:
            self.btn_cerrar.disabled = True
            self.btn_cerrar.opacity = 0.3

        self.layout_botones_decision.disabled = False
        self.layout_botones_decision.opacity = 1.0

        color_pnl = "00d26a" if pnl_neto >= 0 else "ff4d4d"
        self.resultado_label.text = (
            f"[b]POSICIÓN CERRADA ({razon})[/b]\n\n"
            f"Símbolo: {op['simbolo']} ({op['decision']})\n"
            f"Precio Salida: ${precio_salida:,.4f}\n"
            f"PnL Neto: [color={color_pnl}]${pnl_neto:,.2f} USDT[/color]\n"
            f"Nuevo Saldo Demo: ${self.saldo_ficticio:,.2f} USDT"
        )

    def cerrar_ultima_posicion(self):
        if self.operaciones_activas:
            ultima = self.operaciones_activas[-1]
            self.cerrar_operacion_especifica(ultima, "Cierre Manual por Usuario")

    def mostrar_estadisticas(self, instance):
        archivo_csv = "historial_trades.csv"
        if not os.path.exists(archivo_csv):
            self.resultado_label.text = "Aún no hay operaciones registradas en el historial."
            return
            
        total_trades = 0
        ganados = 0
        pnl_acumulado = 0.0
        
        try:
            with open(archivo_csv, mode="r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    total_trades += 1
                    pnl = float(row["PnL Neto"])
                    pnl_acumulado += pnl
                    if pnl > 0:
                        ganados += 1
                        
            win_rate = (ganados / total_trades * 100) if total_trades > 0 else 0.0
            color_res = "00d26a" if pnl_acumulado >= 0 else "ff4d4d"
            
            self.resultado_label.text = (
                f"[b]ESTADÍSTICAS DE RENDIMIENTO (WinRate)[/b]\n\n"
                f"Total Operaciones Registradas: {total_trades}\n"
                f"Trades Ganadores: {ganados} ({win_rate:.1f}% WinRate)\n"
                f"PnL Acumulado: [color={color_res}]${pnl_acumulado:,.2f} USDT[/color]"
            )
        except Exception as e:
            self.resultado_label.text = f"Error al leer el archivo de historial: {e}"


if __name__ == '__main__':
    ApexTraderApp().run()
