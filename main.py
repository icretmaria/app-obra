import os
import time
from datetime import datetime
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.clock import Clock
from plyer import gps, camera

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Image, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

class AplicativoObra(App):
    def build(self):
        # Inicialização das variáveis de armazenamento e estado do GPS
        self.fotos_acumuladas = []
        self.coordenadas_atuais = {"x": 0.0, "y": 0.0, "z": 0.0}
        
        # Configuração da interface gráfica principal
        layout_principal = BoxLayout(orientation='vertical', padding=20, spacing=15)
        
        # Painel superior de status para monitoramento em campo
        self.label_status = Label(
            text="GPS: Aguardando sinal...\nFotos capturadas: 0",
            size_hint_y=None,
            height=120,
            font_size='16sp',
            halign='center',
            valign='middle'
        )
        self.label_status.bind(size=self.label_status.setter('text_size'))
        layout_principal.add_widget(self.label_status)
        
        # Área de rolagem para logs de operações em tempo real
        scroll = ScrollView(size_hint_y=1)
        self.label_log = Label(
            text="Sistema inicializado.\nPronto para iniciar a vistoria.",
            size_hint_y=None,
            font_size='14sp',
            halign='left',
            valign='top'
        )
        self.label_log.bind(size=self.label_log.setter('text_size'))
        self.label_log.bind(texture_size=lambda instance, value: setattr(instance, 'height', value[1]))
        scroll.add_widget(self.label_log)
        layout_principal.add_widget(scroll)
        
        # Botão de ação para ativação da câmera gráfica
        btn_foto = Button(
            text="Tirar Foto do Local",
            size_hint_y=None,
            height=80,
            font_size='18sp',
            background_color=(0.1, 0.6, 0.3, 1)
        )
        btn_foto.bind(on_press=self.executar_captura_foto)
        layout_principal.add_widget(btn_foto)
        
        # Botão de ação para compilação do relatório técnico
        btn_relatorio = Button(
            text="Finalizar e Gerar Relatório PDF",
            size_hint_y=None,
            height=80,
            font_size='18sp',
            background_color=(0.2, 0.4, 0.8, 1)
        )
        btn_relatorio.bind(on_press=self.gerar_relatorio_pdf)
        layout_principal.add_widget(btn_relatorio)
        
        # Inicialização programada dos serviços de localização do dispositivo
        Clock.schedule_once(self.inicializar_gps, 1)
        
        return layout_principal

    def inicializar_gps(self, dt):
        """
        Configura e inicializa os listeners do hardware de posicionamento global (GPS).
        """
        try:
            gps.configure(on_location=self.on_location_callback, on_status=self.on_status_callback)
            gps.start(minTime=1000, minDistance=1)
            self.atualizar_log("[SISTEMA] Procurando satélites GPS...")
        except Exception as erro:
            self.atualizar_log(f"[ERRO GPS] Falha ao iniciar hardware: {str(erro)}")

    def on_location_callback(self, **kwargs):
        """
        Callback acionado em segundo plano a cada atualização de coordenadas do sensor.
        """
        self.coordenadas_atuais["x"] = kwargs.get("lat", 0.0)
        self.coordenadas_atuais["y"] = kwargs.get("lon", 0.0)
        self.coordenadas_atuais["z"] = kwargs.get("altitude", 0.0)
        
        self.label_status.text = (
            f"GPS: Sinal Ativo\n"
            f"Fotos capturadas: {len(self.fotos_acumuladas)}"
        )

    def on_status_callback(self, stype, status):
        self.atualizar_log(f"[GPS Status] Tipo: {stype} | Status: {status}")

    def atualizar_log(self, texto):
        horario = datetime.now().strftime("%H:%M:%S")
        self.label_log.text = f"[{horario}] {texto}\n" + self.label_log.text

    def executar_captura_foto(self, instance):
        """
        Instancia a intenção de captura de imagem síncrona com os metadados geográficos.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        nome_foto = f"foto_obra_{timestamp}.jpg"
        
        # Armazena temporariamente na pasta de cache do aplicativo para compilação posterior
        pasta_cache = self.user_data_dir
        caminho_foto = os.path.join(pasta_cache, nome_foto)
        
        try:
            # Registra instantaneamente os dados do ponto no momento do clique
            dados_ponto = {
                "caminho": caminho_foto,
                "hora": datetime.now().strftime("%d/%m/%Y às %H:%M:%S"),
                "x": self.coordenadas_atuais["x"],
                "y": self.coordenadas_atuais["y"],
                "z": self.coordenadas_atuais["z"]
            }
            
            # Chama a câmera nativa através da abstração do Plyer
            camera.take_picture(filename=caminho_foto, on_complete=lambda path: self.confirmar_captura(dados_ponto))
        except Exception as erro:
            self.atualizar_log(f"[ERRO CÂMERA] Falha no disparo: {str(erro)}")

    def confirmar_captura(self, dados_ponto):
        """
        Valida a existência do arquivo físico de imagem e insere o registro na memória.
        """
        # Delay de segurança para conclusão de gravação de IO do hardware Android
        time.sleep(1)
        if os.path.exists(dados_ponto["caminho"]):
            self.fotos_acumuladas.append(dados_ponto)
            self.atualizar_log(f"[SUCESSO] Foto {len(self.fotos_acumuladas)} armazenada.")
            self.label_status.text = f"GPS: Sinal Ativo\nFotos capturadas: {len(self.fotos_acumuladas)}"
        else:
            self.atualizar_log("[AVISO] Arquivo de imagem não foi detectado no armazenamento.")

    def gerar_relatorio_pdf(self, instance):
        """
        Exporta as imagens consolidadas estruturadas com as legendas para a pasta Downloads.
        """
        if not self.fotos_acumuladas:
            self.atualizar_log("[ERRO] Memória vazia. Tire fotos antes de gerar o PDF.")
            return

        try:
            nome_pdf = f"Relatorio_Obra_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            
            # Aponta para a pasta pública de Downloads do dispositivo Android
            pasta_downloads = "/storage/emulated/0/Download"
            if not os.path.exists(pasta_downloads):
                # Fallback genérico caso a estrutura do dispositivo mude
                pasta_downloads = os.path.join(os.path.expanduser("~"), "Downloads")
                os.makedirs(pasta_downloads, exist_ok=True)
                
            caminho_final_pdf = os.path.join(pasta_downloads, nome_pdf)
            
            doc = SimpleDocTemplate(caminho_final_pdf, pagesize=letter)
            elementos_pdf = []
            
            estilos = getSampleStyleSheet()
            estilo_legenda = ParagraphStyle(
                'EstiloLegenda',
                parent=estilos['Normal'],
                fontSize=10,
                leading=14,
                spaceBefore=6,
                spaceAfter=20
            )
            
            for item in self.fotos_acumuladas:
                img_pdf = Image(item["caminho"], width=400, height=300)
                elementos_pdf.append(img_pdf)
                
                texto_legenda = (
                    f"<b>Registro:</b> {item['hora']}<br/>"
                    f"<b>Coordenadas:</b> X (Lat): {item['x']:.6f} | Y (Lon): {item['y']:.6f} | Z (Alt): {item['z']:.2f} m"
                )
                elementos_pdf.append(Paragraph(texto_legenda, estilo_legenda))
                elementos_pdf.append(Spacer(1, 15))
                
            doc.build(elementos_pdf)
            self.atualizar_log(f"[SUCESSO] PDF gerado em Downloads:\n{nome_pdf}")
            
            # Limpa a lista de memória para a próxima vistoria técnica
            self.fotos_acumuladas.clear()
            self.label_status.text = "GPS: Sinal Ativo\nFotos capturadas: 0"
            
        except Exception as erro:
            self.atualizar_log(f"[ERRO PDF] Falha na compilação: {str(erro)}")

if __name__ == "__main__":
    AplicativoObra().run()
