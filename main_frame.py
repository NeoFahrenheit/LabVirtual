"""
Janela responsável pela classe inicial do programa, MainFrame.
main_frame.py
"""

import os
import wx
from wx.core import Colour
import wx.lib.platebtn as pb
import wx.lib.scrolledpanel as scrolled
from pubsub import pub
import json
import sound
import settings
import helper
import tutorial
import about

class MainFrame(wx.Panel):
    def __init__(self, parent, folderPath):
        super().__init__(parent)

        self.parent = parent
        self.path = folderPath
        self.images = []        # Contém os paths das imagens da pasta
        self.widgets = []       # (btnRef, sizerRefs, btnCoordinates)
        self.ctrls = []         # Widgets que exibem ou recebem dados (wx.Slider, wx.TextCtrl, wx.ComboBox)
        self.buttons = []       # Irá conter os dados de buttons.json
        self.data = []          # Irá conter os dados de data.json
        self.tables = []        # Irá conter os dados das tabelas dos equipamentos (zoom)
        self.lastStatus = {}    # Irá conter os valores de todo o sistema antes da mudança de valor.
        self.canAcess = []      # Irá conter bools de permissão de acesso as principais funções.

        self.index = 0
        self.version = 1.0

        self.sound = sound.SoundManager(self)
        self.report = helper.Report(self)
        self.pumpCurve = None

        self.isTutorial = False         # Apenas para indicar se o tutorial deve começar no startup.
        self.isInitMax = False
        self.isSoundActive = True
        self.isTooltip = True           # True para valor da medição, False para nenhuma.
        self.isEquipZoom = False        # Se a imagem atualmente exibida é de algum 'zoom'.
        self.curZoomTablePos = None     # Lista com as coordenadas do último zoom. Ex: [x, y]
        self.canShowMotorPanel = False
        self.miscButtons = []
        self.miscButtonsRef = []
        self.waterFlowBitmaps = []
        self.greenArrowBitmaps = []
        self.mascotBitmaps = []

        self.settingsWindow = None
        self.aboutWindow = None
        self.tutorialObj = tutorial.MainTutorial(self)

        self.initUI()
        self.getButtons()
        self.OnValueChanged(None)
        self.getSystemStatus()

        self.Bind(wx.EVT_SIZE, self.OnResizing)
        self.SetDoubleBuffered(True)

        self.updateButtonTooltips()
        self.LoadConfigFile()

        if self.isInitMax:
            self.parent.Maximize()

        if self.isTutorial:
            self.initTutorial(None)

        self.parent.Centre()

    def initUI(self):
        ''' Inicializa a UI. '''

        self.SetBackgroundColour((171, 171, 171, 255))

        self.mainSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.imageSizer = wx.BoxSizer(wx.VERTICAL)

        self.scrolledSizer = wx.BoxSizer(wx.VERTICAL)
        self.scrolled = scrolled.ScrolledPanel(self, -1, style=wx.SUNKEN_BORDER)
        self.scrolled.SetMinSize((190, 600))
        self.scrolled.SetSizer(self.scrolledSizer)
        self.scrolled.Show(False)
        self.scrolled.SetupScrolling(scroll_x=False)
        self.scrolledSizer.Add( wx.StaticText(self.scrolled, -1, 'Painel de Controle'), flag=wx.ALIGN_CENTER | wx.ALL, border=10)
        self.scrolled.SetBackgroundColour('#f0f0f0')

        self.bmpImage = wx.StaticBitmap(self, wx.ID_ANY)
        self.tutorialBitmap = None
        self.tableBitmap = None

        self.mainSizer.Add(self.scrolled, 1, wx.EXPAND)
        self.imageSizer.Add(self.bmpImage, 1, wx.EXPAND)
        self.mainSizer.Add(self.imageSizer, 9, wx.EXPAND)

        self.images = self.getFolderImages(f'{self.path}')

        self.SetSizerAndFit(self.mainSizer)
        self.frameImage(self.images[self.index])

        pub.subscribe(self.AcessPermissionHandler, 'acessHandler')
        for _ in range(0, 17):
            self.canAcess.append(True)

    def initTutorial(self, event):
        ''' Inicia o tutorial. '''

        if self.tutorialObj.isTutorialInProgress:
            self.tutorialObj.endTutorial()

        self.tutorialObj.InitTutorial()

    def endTutorial(self, event):
        ''' Finaliza o tutorial. '''

        if self.tutorialObj.isTutorialInProgress:
            self.tutorialObj.endTutorial()

    def OnAbout(self, event):
        ''' Abre a janela de Sobre. '''

        if not self.aboutWindow:
            self.aboutWindow = about.About(self)
            self.aboutWindow.ShowModal()

    def setTutButtonBitmap(self, bitmap):
        ''' Atualiza a variável `self.mascotImage` com uma nova referência a um wx.StaticBitmap. '''

        self.tutButton.SetBitmap(bitmap)

    def LoadConfigFile(self):
        ''' Carrega o arquivo com as configurações e as aplica. '''

        frame = settings.Settings(self)
        frame.Destroy()

    def getButtons(self):
        ''' Popula a lista `self.widgets`. '''

        with open(f"{self.path}/buttons.json", 'r', encoding='utf-8') as f:
            text = f.read()
            self.buttons = json.loads(text)

        with open(f"{self.path}/data.json", 'r', encoding='utf-8') as f:
            text = f.read()
            self.data = json.loads(text)

        with open(f"{self.path}/misc_buttons.json", 'r', encoding='utf-8') as f:
            text = f.read()
            self.miscButtons = json.loads(text)

        with open(f"{self.path}/tables.json", 'r', encoding='utf-8') as f:
            text = f.read()
            self.tables = json.loads(text)

        for dic in self.buttons:
            b = pb.PlateButton(self.bmpImage, 1000 + dic['index'], style=pb.PB_STYLE_NOBG, name=dic['jsonKey'], size=((129, 35)))
            b.Bind(wx.EVT_BUTTON, self.OnButton)
            b.SetBitmap(wx.Bitmap(f"images/buttons/0_{dic['buttonName']}.png"))

            s = helper.ItemFrame(self.scrolled, self, dic)
            self.scrolledSizer.Add(s, flag=wx.ALL | wx.ALIGN_CENTER, border=10)

            # (btnRef, sizerRef, btnCoordinates)
            self.widgets.append((b, s, dic['coordinates']))

        self.getMiscButtons()

    def getTutorialFile(self, jsonName):
        ''' Carrega e retorna o .json do tutorial. '''

        with open(f"{self.path}/{jsonName}.json", 'r', encoding='utf-8') as f:
            text = f.read()
            outList = json.loads(text)

        return outList

    def getMiscButtons(self):
        ''' Popula a lista self.misc_buttons. '''

        for dic in self.miscButtons:
            b = pb.PlateButton(self.bmpImage, -1, style=pb.PB_STYLE_NOBG, name=dic['buttonName'], size=((70, 45)))
            b.Bind(wx.EVT_BUTTON, self.OnMiscButton)
            b.SetBitmap(wx.Bitmap(f"images/buttons/0_{dic['buttonName']}.png"))
            self.miscButtonsRef.append((b, None, dic['coordinates']))   # Uma gambiarra para o reaproveitamento de função.

    def getSystemStatus(self):
        ''' Guarda o estado de todo o sistema, como o nome dos equipamentos e valores, no dicionário `self.lastStatus`. '''

        self.lastStatus.clear()
        for ctrl in self.ctrls:
            self.lastStatus[ctrl.GetName()] = ctrl.GetValue()

    def AcessPermissionHandler(self, index=0, boolValue=True, setAll=False):
        ''' Modifica para `bool` em `index` na lista self.canAcess.
        Se `setAll` for True, `boolValue` será usado para a lista inteira. '''

        if setAll:
            for i in range(0, len(self.canAcess)):
                self.canAcess[i] = boolValue
        else:
            self.canAcess[index] = boolValue

    def OnButton(self, event):
        ''' Chamada quando um botão é clicado. '''

        obj = event.GetEventObject()
        ID = obj.GetId() - 1000

        # [9] -> Registro Esfera, botao
        if not self.canAcess[ID + 9]:
            return

        if self.tutorialObj.isTutorialInProgress:
            self.tutorialObj.Notify(None, buttonPressed=True)

        if self.widgets[ID][1].IsShown():
            self.widgets[ID][1].Hide()
        else:
            # Motor Elétrico ID = 2
            if ID == 2:
                if self.canShowMotorPanel:
                    self.widgets[ID][1].Show()
                else:
                    pub.sendMessage('OnStatusBar', msg='Ligue o motor elétrico para acessar o painel.', isError=True)
            else:
                self.widgets[ID][1].Show()

        self.updateScrolledVisibility()
        self.frameImage(self.images[self.index], True)

    def OnMiscButton(self, event):
        ''' Quando qualquer um dos outros botões for clicado. '''

        btn = event.GetEventObject()
        name = btn.GetName()
        rpmCtrl = self.ctrls[2]     # ctrls[2] = Motor Elétrico

        if name == 'onMotor':
            if not self.canAcess[15]:
                return

            self.canShowMotorPanel = True
            if self.getRPMValue() == 0:
                rpmCtrl.SetValue('890 (50)')
                self.widgets[2][1].Show(True)
                self.updateScrolledVisibility()
                self.OnValueChanged(self.ctrls[2])

        elif name == 'offMotor':
            if not self.canAcess[16]:
                return

            self.canShowMotorPanel = False
            if self.getRPMValue() != 0:
                rpmCtrl.SetValue('0 (0)')
                self.widgets[2][1].Hide()
                self.updateScrolledVisibility()
                self.OnValueChanged(self.ctrls[2])


    def updateScrolledVisibility(self):
        ''' Atualiza a visibilidade do self.scrolled. '''

        isAnyShown = []
        for i in range (0, len(self.widgets)):
            isAnyShown.append(self.widgets[i][1].IsShown())

        if any(isAnyShown):
            self.scrolled.Show(True)
        else:
            self.scrolled.Show(False)

    def showButtons(self, show):
        ''' Mostra ou esconde todos os botoões da imagem. '''

        for d in self.widgets:
            btn = d[0]
            btn.Show(show)

        for d in self.miscButtonsRef:
            btn = d[0]
            btn.Show(show)

    def updateButtons(self):
        ''' Atualiza a posição dos botões na tela. '''

        sizerDim = self.imageSizer.GetSize()
        sizer_aspect = sizerDim[0] / sizerDim[1]

        for btn in self.widgets:
            btn[0].Position = self.getButtonPosition(btn, sizerDim, sizer_aspect)

        for btn in self.miscButtonsRef:
            btn[0].Position = self.getButtonPosition(btn, sizerDim, sizer_aspect)

    def getButtonPosition(self, btn, sizerDim, sizer_aspect):
        ''' Retorna a posição de um botão do sistema. '''

        button_horizontal = int(sizerDim[0] * btn[2][self.index][0])
        button_vertical = int(sizerDim[1] * btn[2][self.index][1])

        if self.image_aspect <= sizer_aspect:
            # Frame is wider than image so find the horizontal white space size to add
            image_width = sizerDim[1] * self.image_aspect
            horizontal_offset = (sizerDim[0] - image_width) / 2
            button_horizontal = int(horizontal_offset + image_width * btn[2][self.index][0])

        elif self.image_aspect > sizer_aspect:
            # Frame is higher than image so find the vertical white space size to add
            image_height = sizerDim[0] / self.image_aspect
            vertical_offset = (sizerDim[1] - image_height) / 2
            button_vertical = int(vertical_offset + image_height * btn[2][self.index][1])

        return (button_horizontal, button_vertical)

    def getTutButtonPosition(self, pos):
        ''' Retorna a posição para a exibição do botão do mascote na imagem. '''

        sizerDim = self.imageSizer.GetSize()
        sizer_aspect = sizerDim[0] / sizerDim[1]

        image_horizontal = int(sizerDim[0] * pos[0])
        image_vertical = int(sizerDim[1] * pos[1])

        if self.image_aspect <= sizer_aspect:
            # Frame is wider than image so find the horizontal white space size to add
            image_width = sizerDim[1] * self.image_aspect
            horizontal_offset = (sizerDim[0] - image_width) / 2
            image_horizontal = int(horizontal_offset + image_width * pos[0])

        elif self.image_aspect > sizer_aspect:
            # Frame is higher than image so find the vertical white space size to add
            image_height = sizerDim[0] / self.image_aspect
            vertical_offset = (sizerDim[1] - image_height) / 2
            image_vertical = int(vertical_offset + image_height * pos[1])

        return (image_horizontal, image_vertical)

    def replaceImage(self, index, path):
        ''' Substitui a imagem em `index` pela imagem (`path`) na lista `self.images`.
        Retorna True em caso de sucesso. '''

        if index < 0 or index >= len(self.images):
            return False

        self.images[index] = path
        if not self.isEquipZoom:
            self.frameImage(self.images[self.index])

        return True

    def getFirstImagePath(self):
        ''' Retorna o caminho da primeira imagem corresponde ao `self.index = 0`. '''

        return self.images[0]

    def frameImage(self, path, isJustResize=False):
        ''' Recebe o path da imagem e atualiza na tela. '''

        self.Freeze()
        if not isJustResize:
            self.bitmap = wx.Bitmap(path, wx.BITMAP_TYPE_ANY)

            if self.tutorialObj.isTutorialInProgress:
                self.drawTutorialImage()

            if self.isEquipZoom and not self.tutorialObj.isTutorialInProgress:
                self.drawTableImage()

            self.image = self.bitmap.ConvertToImage()
            self.image_aspect = self.image.GetSize()[0] / self.image.GetSize()[1]

        self.Layout()   # Para atualizar o tamanho do self.imageSizer

        image_width, image_height = self.imageSizer.GetSize()
        new_image_width = image_width
        new_image_height = int(new_image_width / self.image_aspect)

        if new_image_height > image_height:
            new_image_height = image_height
            new_image_width = int(new_image_height * self.image_aspect)

        scaledImage = self.image.Scale(new_image_width, new_image_height, wx.IMAGE_QUALITY_BILINEAR)

        self.bmpImage.SetBitmap(scaledImage.ConvertToBitmap())
        self.Layout()
        self.updateButtons()
        self.Thaw()     # Freeze() e Thaw() previne flickering.

    def drawTutorialImage(self):
        ''' Desenha a imagem do tutorial por cima da imagem base. '''

        if not self.tutorialBitmap:
            return

        pos = self.tutorialObj.pos
        dc = wx.MemoryDC(self.bitmap)

        equip = self.tutorialObj.curEquip
        if equip:
            dc.DrawBitmap(wx.Bitmap(self.getWaterFlowBitmap(equip)), 0, 0, True)
        else:
            dc.DrawBitmap(self.baseWaterFlowBitmap, 0, 0, True)
            index = self.tutorialObj.index
            if index >= 14 and index <= 18:
                dc.DrawBitmap(wx.Bitmap(self.greenArrowBitmaps[index - 14]), 0, 0, True)

        dc.DrawBitmap(self.tutorialBitmap, pos[0], pos[1], True)
        del dc

        self.bmpImage.SetBitmap(self.bitmap)

    def drawTableImage(self):
        ''' Desenha a imagem do tutorial por cima da imagem base. '''

        if not self.tableBitmap:
            return

        pos = self.curZoomTablePos
        dc = wx.MemoryDC(self.bitmap)
        dc.DrawBitmap(self.tableBitmap, pos[0], pos[1], True)
        del dc
        self.bmpImage.SetBitmap(self.bitmap)

    def loadTutorialBitmaps(self):
        ''' Carrega as imagens para as listas de bitmap. '''

        if len(self.waterFlowBitmaps) > 0:
            return

        equips = ['Piezômetro', 'Manovacuômetro', 'Motor Elétrico', 'Bomba', 'Manômetro', 'Medidor de Vazão', 'Registro Esfera']
        for equip in equips:
            self.waterFlowBitmaps.append( (equip, wx.Bitmap(f'data/system1/misc/overlays/{equip}_overlay.png')) )

        for i in range(0, 5):
            self.greenArrowBitmaps.append(wx.Bitmap(f'data/system1/misc/overlays/{i + 14}_overlay.png'))

        for i in range(0, 21):
            self.mascotBitmaps.append( wx.Bitmap(f'images/tutorial/{str(i)}.png') )

        self.baseWaterFlowBitmap = wx.Bitmap('data/system1/misc/overlays/base_overlay.png')

    def getWaterFlowBitmap(self, name):
        ''' Retorna o wx.Bitmap do equipamento em `name`. Retorna None em caso de erro. '''

        for bitmap in self.waterFlowBitmaps:
            if bitmap[0] == name:
                return bitmap[1]

        return None

    def getFolderImages(self, path):
        ''' Recebe uma string com o caminho da pasta e retorna uma lista com os paths de todas as imagens da pasta. '''

        jpgs = [f for f in os.listdir(path) if f[-4:] == ".JPG"]
        return [os.path.join(path, f) for f in jpgs]

    def OnValueChanged(self, event):
        ''' Chamada quando o valor em qualquer um dos botões é modificado. '''

        if event:
            if isinstance(event, wx._core.CommandEvent):
                name = event.GetEventObject().GetName()
                value = event.GetEventObject().GetValue()
                # Se "mudar" para o mesmo valor, encerramos.
                if self.lastStatus[name] == value:
                    return

        values = []

        # Pega os valores dos widgets que o usuário pode modificar o valor.
        for i in range(0, len(self.buttons)):
            dic = {}
            if self.buttons[i]['isControllable']:
                key = self.buttons[i]['jsonKey']
                dic['key'] = key
                dic['value'] = self.ctrls[i].GetValue()
                values.append(dic)

                dic = {}

        # Encontra no data.json o index corresponde aos dados dos widgets.
        index = -1
        hook = 'rpm'
        for dic in values:
            # Usaremos um "anzol" para pegar todos os outros dados.
            if dic['key'] == hook:
                if dic['value'] == '0 (0)':
                    self.canShowMotorPanel = False
                    self.widgets[2][1].Hide()   # widgets[2][1] --> Painel Motor Elétrico
                    self.updateScrolledVisibility()

                for i in range(0, len(self.data)):
                    if dic['value'] == self.data[i][hook]:
                        index = i
                        break

        for dic in values:
            if dic['key'] != hook:
                for i in range(index, len(self.data)):
                    key = dic['key']
                    if int(dic['value']) == self.data[i][key]:
                        index = i
                        break

        self.refreshOnDisplayValues(index)
        self.updateButtonTooltips()

        if event:
            if isinstance(event, wx._core.CommandEvent):
                self.report.TakeNote(self.lastStatus, event.GetEventObject())
            else:
                self.report.TakeNote(self.lastStatus, event)    # É um pb.PlateButton

            self.updateSoundPlay()
            self.getSystemStatus()

            if self.tutorialObj.isTutorialInProgress:
                self.tutorialObj.Notify(self.lastStatus)

    def refreshOnDisplayValues(self, index):
        ''' Recebe um `index` do índice no arquivo data.json que contém os dados que deverá ser exibido em um widget. '''

        self.dataIndex = index
        for i in range(0, len(self.buttons)):
            if not self.buttons[i]['isControllable']:
                key = self.widgets[i][0].GetName()
                value = str(self.data[index][key])
                self.ctrls[i].SetValue(value)

    def getTableCoordinates(self, name):
        ''' Procura na lista `self.tables` e retorna as coordenadas (int, int) para aquela tabela. '''

        for dic in self.tables:
            if name == dic['name']:
                return dic['coordinates']

        return None

    def OnClosePanel(self, event):
        ''' Chamada quando o botão de fechar dentro de um `ItemFrame` for clicado. '''

        obj = event.GetEventObject()
        ID = obj.GetId() - 1000

        self.widgets[ID][1].Hide()

        self.updateScrolledVisibility()
        self.frameImage(self.images[self.index], True)

    def HideScrolled(self):
        ''' Esconde todos os itens do Painel de Controle e o esconde. '''

        for i in range(0, len(self.widgets)):
            self.widgets[i][1].Hide()

        self.updateScrolledVisibility()

    def OnNext(self, event):
        ''' Quando o usuário clica para ir para a próxima imagem. '''

        if not self.canAcess[1]:
            return

        if self.tutorialObj.isTutorialInProgress:
            self.tutorialObj.Notify('right')
            return

        if not self.isEquipZoom:
            self.index += 1
        else:
            self.isEquipZoom = False

        if self.index >= len(self.images):
            self.index = 0

        self.frameImage(self.images[self.index])
        self.showButtons(True)

    def OnPrevious(self, event):
        ''' Quando o usuário clica para voltar para a imagem anterior. '''

        if not self.canAcess[0]:
            return

        if self.tutorialObj.isTutorialInProgress:
            self.tutorialObj.Notify('left')
            return

        if not self.isEquipZoom:
            self.index -= 1
        else:
            self.isEquipZoom = False

        if self.index < 0:
            self.index = len(self.images) - 1

        self.frameImage(self.images[self.index])
        self.showButtons(True)

    def OnResizing(self, event):
        ''' Chamada quando a janela muda de tamanho. '''

        self.frameImage(self.images[self.index], True)
        event.Skip()

    def OnSettings(self, event):
        ''' Abre a janela de configurações. '''

        if not self.settingsWindow:
            self.settingsWindow = settings.Settings(self, True)
            self.settingsWindow.Show()

    def OnReport(self, event):
        ''' Mostra a janela de relatorio. '''

        if not self.report.IsShown():
            self.report.Show()

    def OnClearReport(self, event):
        ''' Limpa a janela do relatório. '''

        self.report.ClearScrolled()

    def OnEquip(self, event):
        ''' Chamada quando o usuário clica para ver um dos equipamentos, seja pela toolbar ou menu. '''

        if isinstance(event, str):
            name = event
        else:
            ID = event.GetId()

            # [2] -> Bomba, Zoom
            if not self.canAcess[(ID - 1000) + 2]:
                return

            try:
                name = event.GetEventObject().GetToolShortHelp(ID)
            except:
                name = event.GetEventObject().GetLabel(ID)

        self.isEquipZoom = True
        self.tableBitmap = wx.Bitmap(f'{self.path}/tables/{name}.png', wx.BITMAP_TYPE_PNG)
        self.curZoomTablePos = self.getTableCoordinates(name)
        self.showButtons(False)
        self.frameImage(f'{self.path}/misc/{name}.jpg')

    def OnPumpCurve(self, event):
        ''' Chamada quando o usuário clica em um botão para abrir a janela da curva teórica da bomba. '''

        if not self.pumpCurve:
            self.pumpCurve = helper.BombCurve(self)
            self.pumpCurve.ShowModal()

    def updateButtonStyle(self, style):
        ''' Muda o estilo dos botões. '''

        if style == 'Borda transparente':
            style = pb.PB_STYLE_NOBG
        elif style == 'Cor gradiente':
            style = pb.PB_STYLE_GRADIENT
        elif style == 'Bordas redondas':
            style = pb.PB_STYLE_DEFAULT
        elif style == 'Bordas quadradas':
            style = pb.PB_STYLE_SQUARE
        else:
            return

        # (btnRef, sizerRef, btnCoordinates)
        for button in self.widgets:
            button[0]._style = style

        for button in self.miscButtonsRef:
            button[0]._style = style

        self.bmpImage.Refresh(False)

    def updateButtonHoverColor(self, new_color):
        ''' Atualiza a cor de fundo (hover) dos botões. '''

        color = Colour(new_color)
        for button in self.widgets:
            button[0].SetPressColor(Colour(color))

        for button in self.miscButtonsRef:
            button[0].SetPressColor(Colour(color))

        self.bmpImage.Refresh(False)

    def updateButtonBackgroundColor(self, color):
        ''' Atualiza a cor de fundo dos botões. '''

        if color == 'Azul':
            index = 1
        else:
            index = 0

        for i in range (0, len(self.buttons)):
            dic = self.buttons[i]
            self.widgets[i][0].SetBitmap(wx.Bitmap(f"images/buttons/{index}_{dic['buttonName']}.png"))

        for btn in self.miscButtonsRef:
            name = btn[0].GetName()
            btn[0].SetBitmap(wx.Bitmap(f"images/buttons/{index}_{name}.png"))

        self.bmpImage.Refresh(False)

    def updateButtonTooltips(self):
        ''' Atualiza o conteúdo das tooltips do botões de acordo com self.isTooltip.
        0 para valor da medição, 1 para descrição. '''

        if self.isTooltip:
            dic = self.data[self.dataIndex]
            for i in range(0, len(self.widgets)):
                key = self.widgets[i][0].GetName()
                value = dic[key]
                unit = self.buttons[i]['unit']

                if key == 'rpm':
                    unit = 'RPM (%)'

                self.widgets[i][0].SetToolTip(f"{value} {unit}")

        else:
            for i in range(0, len(self.widgets)):
                self.widgets[i][0].SetToolTip('')

    def getRPMValue(self):
        ''' Retorna o valor em `int` do Motor Elétrico. '''

        return int(self.ctrls[2].GetValue().split()[0])

    def updateSoundPlay(self):
        ''' Atualiza o estado do som da motor elétrico, se pode tocar ou não. '''

        rpm = self.getRPMValue()
        registro = int(self.ctrls[0].GetValue())    # ctrls[0] -> 'Registro Esfera'
        isWaterFlowing = rpm > 0 and registro > 0

        if isWaterFlowing:
            self.replaceImage(0, f'{self.path}/misc/0_water.jpg')
        else:
            self.replaceImage(0, f'{self.path}/0.JPG')

        if self.isSoundActive:
            if rpm > 0:
                self.sound.SoundPlayback('rpm', True)
            else:
                self.sound.SoundPlayback('rpm', False)

            if isWaterFlowing:
                self.sound.SoundPlayback('abertura', True)
            else:
                self.sound.SoundPlayback('abertura', False)

        else:
            self.sound.SoundPlayback('rpm', False)
            self.sound.SoundPlayback('abertura', False)

    def updateSoundVolume(self, newVolume):
        ''' Atualiza o volume do som. '''

        self.sound.SoundVolume(newVolume)

    def updateIsInitMaxVariable(self, new_value):
        ''' Atualiza o valor de self.isInitMax. '''

        self.isInitMax = new_value

    def updateIsSoundActiveVariable(self, new_value):
        ''' Atualiza o valor de self.isSoundActive. '''

        self.isSoundActive = new_value

class Init(wx.Frame):
    def __init__(self, parent):
        super().__init__(parent)

        self.SetIcon(wx.Icon('images/icons/app_logo.ico'))
        self.SetTitle('Laboratório Virtual de Bombas Hidráulicas')
        self.SetMinSize((1200, 700))

        self.frame = MainFrame(self, 'data/system1')

        self.statusBar = self.CreateStatusBar()
        self.menu = wx.MenuBar()
        self.initMenu()
        self.toolbar = self.CreateToolBar()
        self.initToolbar()
        self.Bind(wx.EVT_CHAR_HOOK, self.OnKey)
        pub.subscribe(self.printOnStatusBar, 'OnStatusBar')

        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.OnTimer)

        self.frame.Show()
        self.Centre()

    def initToolbar(self):
        ''' Inicializa a toolbar. '''

        left_arrow = self.toolbar.AddTool(wx.ID_ANY, 'Left', wx.Bitmap('images/icons/left.png'), 'Anterior')
        right_arrow = self.toolbar.AddTool(wx.ID_ANY, 'Right', wx.Bitmap('images/icons/right.png'), 'Próxima')
        settings = self.toolbar.AddTool(wx.ID_ANY, 'Settings', wx.Bitmap('images/icons/settings.png'), 'Configurações')
        self.toolbar.AddSeparator()

        bomba =  self.toolbar.AddTool(1000, 'Bomba', wx.Bitmap('images/icons/water_pump.png'), 'Bomba')
        motor =  self.toolbar.AddTool(1001, 'Motor Elétrico', wx.Bitmap('images/icons/motor.png'), 'Motor Elétrico')
        registro =  self.toolbar.AddTool(1002, 'Registro Esfera', wx.Bitmap('images/icons/registro_esfera.png'), 'Registro Esfera')
        vazao =  self.toolbar.AddTool(1003, 'Medidor de Vazão', wx.Bitmap('images/icons/medidor_de_vazao.png'), 'Medidor de Vazão')
        manovac =  self.toolbar.AddTool(1004, 'Manovacuômetro', wx.Bitmap('images/icons/manovacuometro.png'), 'Manovacuômetro')
        mano =  self.toolbar.AddTool(1005, 'Manômetro', wx.Bitmap('images/icons/manometro.png'), 'Manômetro')
        piezometro =  self.toolbar.AddTool(1006, 'Piezômetro', wx.Bitmap('images/icons/piezometro.png'), 'Piezômetro')
        graph =  self.toolbar.AddTool(1007, 'Curva Teórica da Bomba', wx.Bitmap('images/icons/graph.png'), 'Curva Teórica da Bomba')

        self.Bind(wx.EVT_TOOL, self.frame.OnNext, right_arrow)
        self.Bind(wx.EVT_TOOL, self.frame.OnPrevious, left_arrow)
        self.Bind(wx.EVT_TOOL, self.frame.OnSettings, settings)

        self.Bind(wx.EVT_TOOL, self.frame.OnEquip, motor)
        self.Bind(wx.EVT_TOOL, self.frame.OnEquip, bomba)
        self.Bind(wx.EVT_TOOL, self.frame.OnEquip, registro)
        self.Bind(wx.EVT_TOOL, self.frame.OnEquip, vazao)
        self.Bind(wx.EVT_TOOL, self.frame.OnEquip, manovac)
        self.Bind(wx.EVT_TOOL, self.frame.OnEquip, mano)
        self.Bind(wx.EVT_TOOL, self.frame.OnEquip, piezometro)
        self.Bind(wx.EVT_TOOL, self.frame.OnPumpCurve, graph)

        self.toolbar.Realize()

    def initMenu(self):
        ''' Inicializa o menu. '''

        # Menu 'Arquivo'
        fileMenu = wx.Menu()
        left = fileMenu.Append(-1, 'Anterior', 'Retroceder imagem')
        right = fileMenu.Append(-1, 'Próxima', 'Avançar imagem')
        settings = fileMenu.Append(-1, 'Configurações', 'Abrir a janela de configurações')
        fileMenu.AppendSeparator()
        leave = fileMenu.Append(wx.ID_EXIT, 'Sair', 'Sair do programa')

        # Menu Relatório
        reportMenu = wx.Menu()
        openReport = reportMenu.Append(-1, 'Abrir relatório', 'Abrir a janela de relatório')
        clearReport = reportMenu.Append(-1, 'Limpar relatório', 'Limpar a janela de relatório')

        # Menu 'Equipamentos'
        equipMenu = wx.Menu()
        bomba = equipMenu.Append(1000, 'Bomba', 'Visualizar a Bomba')
        motor = equipMenu.Append(1001, 'Motor Elétrico', 'Visualizar o Motor Elétrico')
        registro = equipMenu.Append(1002, 'Registro Esfera', 'Visualizar o Registro Esfera')
        vazao = equipMenu.Append(1003, 'Medidor de Vazão', 'Visualizar o Medidor de Vazão')
        manovac = equipMenu.Append(1004, 'Manovacuômetro', 'Visualizar o Manovacuômetro')
        mano = equipMenu.Append(1005, 'Manômetro', 'Visualizar o Manômetro')
        piezometro = equipMenu.Append(1006, 'Piezômetro', 'Visualizar o Piezômetro')
        graph = equipMenu.Append(1007, 'Curva Teórica da Bomba', 'Ver curva teórica da bomba')

        # Menu 'Ajuda'
        ajudaMenu = wx.Menu()
        tutorial = ajudaMenu.Append(-1, 'Iniciar tutorial', 'Reiniciar o tutorial')
        endTutorial = ajudaMenu.Append(-1, 'Encerrar tutorial', 'Encerrar o tutorial')
        sobre = ajudaMenu.Append(wx.ID_ABOUT, 'Sobre', 'Sobre este programa')

        # Bindings
        self.Bind(wx.EVT_MENU, self.frame.OnPrevious, left)
        self.Bind(wx.EVT_MENU, self.frame.OnNext, right)
        self.Bind(wx.EVT_MENU, self.frame.OnReport, openReport)
        self.Bind(wx.EVT_MENU, self.frame.OnClearReport, clearReport)
        self.Bind(wx.EVT_MENU, self.frame.OnSettings, settings)
        self.Bind(wx.EVT_MENU, self.OnCloseApp, leave)

        self.Bind(wx.EVT_MENU, self.frame.OnEquip, motor)
        self.Bind(wx.EVT_MENU, self.frame.OnEquip, bomba)
        self.Bind(wx.EVT_MENU, self.frame.OnEquip, registro)
        self.Bind(wx.EVT_MENU, self.frame.OnEquip, vazao)
        self.Bind(wx.EVT_MENU, self.frame.OnEquip, manovac)
        self.Bind(wx.EVT_MENU, self.frame.OnEquip, mano)
        self.Bind(wx.EVT_MENU, self.frame.OnEquip, piezometro)
        self.Bind(wx.EVT_MENU, self.frame.OnPumpCurve, graph)

        self.Bind(wx.EVT_MENU, self.frame.initTutorial, tutorial)
        self.Bind(wx.EVT_MENU, self.frame.endTutorial, endTutorial)
        self.Bind(wx.EVT_MENU, self.frame.OnAbout, sobre)

        self.menu.Append(fileMenu, '&Arquivo')
        self.menu.Append(reportMenu, '&Relatório')
        self.menu.Append(equipMenu, '&Equipamentos')
        self.menu.Append(ajudaMenu, 'Ajuda')

        self.SetMenuBar(self.menu)

    def OnKey(self, event):
        ''' Captura teclas. '''

        if event.GetKeyCode() == wx.WXK_LEFT:
            self.frame.OnPrevious(None)

        elif event.GetKeyCode() == wx.WXK_RIGHT:
            self.frame.OnNext(None)

    def printOnStatusBar(self, msg, showTime=3000, isError=False, isSucess=False):
        ''' Escreve `msg` na status bar. '''

        self.statusBar.SetStatusText(msg)
        self.timer.StartOnce(showTime)

        if isError:
            self.statusBar.SetBackgroundColour('#eb928a')
            self.statusBar.Refresh()
        elif isSucess:
            self.statusBar.SetBackgroundColour('#95e6a7')
            self.statusBar.Refresh()

    def OnTimer(self, event):
        ''' Chamada a cada x segundos, segundo o timer. '''

        self.statusBar.SetStatusText("")
        self.statusBar.SetBackgroundColour(wx.NullColour)
        self.statusBar.Refresh()

    def OnCloseApp(self, event):
        ''' Fecha o app. '''

        self.Destroy()

app = wx.App()
frame = Init(None)
frame.Show()
app.MainLoop()