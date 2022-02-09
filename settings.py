"""
Autor: Leandro Monteiro
Janela responsável pelo menu de configurações.
settings.py
"""

import os
import wx, wx.adv
from wx.core import Colour
from pubsub import pub

class Settings(wx.Frame):
    def __init__(self, parent, onlyLoadToUI=False):
        style = wx.DEFAULT_FRAME_STYLE & (~wx.MAXIMIZE_BOX) & (~wx.MINIMIZE_BOX) & (~wx.RESIZE_BORDER)
        super().__init__(parent, style=style)

        self.SetIcon(wx.Icon('images/icons/settings.png'))

        self.parent = parent
        self.fileLines = []

        self.SetTitle('Configurações')
        self.SetSize((470, 250))

        self.initUI()
        self.CenterOnParent()

        self.OpenFile()
        self.applyUserConfig(onlyLoadToUI)

        self.Bind(wx.EVT_CLOSE, self.OnCloseWindow)

    def initUI(self):
        ''' Inicializa a UI. '''

        masterSizer = wx.BoxSizer(wx.VERTICAL)
        btnSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.SetBackgroundColour('#e8e8e8')

        note = wx.Notebook(self, -1)
        note.SetBackgroundColour(wx.WHITE)

        self.aparencia = AparenciaFrame(note, self.parent)
        self.exibicao = ExibicaoFrame(note, self.parent)
        self.som = SomFrame(note, self.parent)

        note.AddPage(self.aparencia, "Aparência")
        note.AddPage(self.exibicao, "Exibição")
        note.AddPage(self.som, "Som")

        okBtn = wx.Button(self, -1, 'OK')
        okBtn.Bind(wx.EVT_BUTTON, self.OnOkButton)
        cancelBtn = wx.Button(self, -1, 'Cancelar')
        cancelBtn.Bind(wx.EVT_BUTTON, self.OnCancelButton)
        resetBtn = wx.Button(self, -1, 'Configuração padrão')
        resetBtn.Bind(wx.EVT_BUTTON, self.OnResetButton)

        btnSizer.Add(resetBtn)
        btnSizer.Add(okBtn, flag=wx.LEFT, border=105)
        btnSizer.Add(cancelBtn, flag=wx.LEFT, border=20)

        masterSizer.Add(note, flag=wx.ALL | wx.EXPAND, border=5)
        masterSizer.Add(btnSizer, flag=wx.TOP | wx.LEFT | wx.RIGHT, border=5)
        self.SetSizer(masterSizer)

    def OnOkButton(self, event):
        ''' Chamada quando o usuário clica no botão de OK. '''

        self.getUserConfig()
        self.SaveFile()
        self.CloseFrame()
        self.parent.bmpImage.Refresh()

    def OnCancelButton(self, event):
        ''' Chamada quando o usuário clica no botão de Cancelar. '''

        self.applyUserConfig(False)
        self.CloseFrame()

    def OnResetButton(self, event):
        ''' Chamada quando o usuário clica no botão de Configurão Padrão. '''

        self.getDefaultConfig()
        self.applyUserConfig(False)
        self.SaveFile()

        pub.sendMessage('OnStatusBar', msg='Configuração restaurada para o padrão com sucesso.')

    def OnCloseWindow(self, event):
        ''' Chamada quando o usuário clica no `X` para fechar a janela. '''

        self.OnCancelButton(None)

    def CloseFrame(self):
        ''' Fecha o frame. '''

        self.parent.settingsWindow = None
        self.Destroy()

    def strToInt(self, value):
        ''' Recebe uma string e tenta converter para int. Retorna o int em caso de sucesso, False caso contrário.
        Normalmente é usado isinstance() depois para diferenciar `bool` de `int`. '''

        try:
            new_value = int(value)
            return new_value
        except:
            return False

    def getDefaultConfig(self):
        ''' Inicializa gv.fileLines com as configurações padrão. '''

        self.fileLines.clear()

        self.fileLines.append(f"version = {str(self.parent.version)}\n")
        self.fileLines.append("buttonStyle = Borda transparente\n")
        self.fileLines.append("buttonBackgroundColor = Branco\n")
        self.fileLines.append("buttonHoverColor = 14120448\n")
        self.fileLines.append("tooltipContent = 1\n")
        self.fileLines.append("initMaximized = 0\n")
        self.fileLines.append("soundActive = 1\n")
        self.fileLines.append("volume = 25\n")
        self.fileLines.append("tutorial = 1")

    def getUserConfig(self):
        ''' Carrega as configurações atuais para gv.fileLines. '''

        self.fileLines.clear()

        self.fileLines.append(f"version = {str(self.parent.version)}\n")
        self.fileLines.append(f"buttonStyle = {self.aparencia.GetStyle()}\n")
        self.fileLines.append(f"buttonBackgroundColor = {self.aparencia.GetBtnBackgroundColor()}\n")
        self.fileLines.append(f"buttonHoverColor = {self.aparencia.GetHoverColor()}\n")
        self.fileLines.append(f"tooltipContent = {self.exibicao.GetTooltipValue()}\n")
        self.fileLines.append(f"initMaximized = {int(self.exibicao.GetMaxCheck())}\n")
        self.fileLines.append(f"soundActive = {int(self.som.GetSomValue())}\n")
        self.fileLines.append(f"volume = {self.som.GetVolume()}\n")
        self.fileLines.append(f"tutorial = {int(self.parent.isTutorial)}")

    def applyUserConfig(self, onlyLoadToUI):
        ''' Aplica as configurações em self.fileLines. '''

        for line in self.fileLines:
            config = line.split('=')[0].strip()

            if config == 'buttonStyle':
                style = line.split('=')[1].strip()
                if style in ['Borda transparente', 'Cor gradiente', 'Bordas redondas', 'Bordas quadradas']:
                    self.aparencia.SetStyle(style)
                    if not onlyLoadToUI: self.aparencia.OnStyleChange(None)

            elif config == 'buttonBackgroundColor':
                color = line.split('=')[1].strip()
                if color in ['Branco', 'Azul']:
                    self.aparencia.SetBtnBackgroundColor(color)
                    if not onlyLoadToUI: self.aparencia.OnBtnBackgoundChange(None)

            elif config == 'buttonHoverColor':
                color = line.split('=')[1].strip()
                color = self.strToInt(color)
                if isinstance(color, int) and Colour(color).IsOk():
                    self.aparencia.SetHoverColor(color)
                    if not onlyLoadToUI: self.parent.updateButtonHoverColor(color)

            elif config == 'tooltipContent':
                value = line.split('=')[1].strip()
                value = self.strToInt(value)
                if isinstance(value, int):
                    self.exibicao.SetTooltipValue(value)
                    if not onlyLoadToUI: self.exibicao.OnTooltipChange(None)

            elif config == 'initMaximized':
                value = line.split('=')[1].strip()
                value = self.strToInt(value)
                if isinstance(value, int):
                    self.exibicao.SetMaxCheck(value)
                    if not onlyLoadToUI: self.exibicao.OnMaxChange(None)

            elif config == 'soundActive':
                value = line.split('=')[1].strip()
                value = self.strToInt(value)
                if isinstance(value, int):
                    self.som.SetSomValue(value)
                    if not onlyLoadToUI: self.som.OnSomChange(None)

            elif config == 'volume':
                value = line.split('=')[1].strip()
                value = self.strToInt(value)
                if isinstance(value, int):
                    self.som.SetVolume(value)
                    if not onlyLoadToUI: self.som.OnVolumeChange(value)

            elif config == 'tutorial':
                value = line.split('=')[1].strip()
                value = self.strToInt(value)
                if isinstance(value, int):
                    self.parent.isTutorial = bool(value)

    def SaveFile(self):
        ''' Escreve as configurações para o arquivo e o salva. '''

        with open(f"{os.path.expanduser('~')}/labvirtual_config.ini", 'w', encoding='utf-8') as f:
            f.write(''.join(self.fileLines))

    def OpenFile(self):
        ''' Carrega as informações do arquivo para self.fileLines.'''

        try:
            with open(f"{os.path.expanduser('~')}/labvirtual_config.ini", 'r', encoding='utf-8') as f:
                self.fileLines = f.readlines()
        except:
            self.getDefaultConfig()
            self.SaveFile()
            self.applyUserConfig(False)

class AparenciaFrame(wx.Panel):
    def __init__(self, noteRef, mainFrameRef):
        super().__init__(parent=noteRef)

        self.parent = mainFrameRef

        self.initFrame()

    def initFrame(self):
        ''' Cria a janela. '''

        master = wx.BoxSizer(wx.VERTICAL)
        vBox = wx.StaticBoxSizer(wx.VERTICAL, self, 'Botões')

        style = wx.BoxSizer(wx.HORIZONTAL)
        backgroundColor = wx.BoxSizer(wx.HORIZONTAL)
        hoverColor = wx.BoxSizer(wx.HORIZONTAL)

        textSize = (85, 23)

        text = wx.StaticText(self, -1, 'Estilo', size=textSize)
        choices = ['Borda transparente', 'Cor gradiente', 'Bordas redondas', 'Bordas quadradas']
        self.styleCombo = wx.ComboBox(self, -1, choices[0], choices=choices, style=wx.CB_READONLY, size=((131, 23)))
        self.styleCombo.Bind(wx.EVT_COMBOBOX, self.OnStyleChange)
        style.Add(text, flag=wx.TOP, border=3)
        style.Add(self.styleCombo, flag=wx.LEFT, border=5)

        text = wx.StaticText(self, -1, 'Cor de fundo', size=textSize)
        choices = ['Branco', 'Azul']
        self.btnBackgroundColor = wx.ComboBox(self, -1, choices[0], choices=choices, style=wx.CB_READONLY, size=((131, 23)))
        self.btnBackgroundColor.Bind(wx.EVT_COMBOBOX, self.OnBtnBackgoundChange)
        backgroundColor.Add(text, flag=wx.TOP, border=3)
        backgroundColor.Add(self.btnBackgroundColor, flag=wx.LEFT, border=5)

        text = wx.StaticText(self, -1, 'Cor da seleção', size=textSize)
        self.hoverColorPicker = wx.ColourPickerCtrl(self, -1, size=((132, 23)))
        self.hoverColorPicker.Bind(wx.EVT_COLOURPICKER_CHANGED, self.OnColorChange)
        hoverColor.Add(text, flag=wx.TOP, border=3)
        hoverColor.Add(self.hoverColorPicker, flag=wx.LEFT, border=5)

        vBox.Add(style, flag=wx.ALL, border=10)
        vBox.Add(backgroundColor, flag=wx.LEFT, border=10)
        vBox.Add(hoverColor, flag=wx.LEFT | wx.TOP, border=10)

        master.Add(vBox, flag=wx.ALL, border=5)

        self.SetSizer(master)

    def OnStyleChange(self, event):
        ''' Chamada quando o usuário muda um valor da wx.ComboBox self.styleCombo. '''

        self.parent.updateButtonStyle(self.styleCombo.GetValue())

    def OnBtnBackgoundChange(self, event):
        ''' Chamada quando o usuário muda um valor da wx.ComboBox self.btnBackgroundColor. '''

        self.parent.updateButtonBackgroundColor(self.btnBackgroundColor.GetValue())

    def OnColorChange(self, event):
        ''' Chamada quando o usuário muda o valor da wx.ColourPickerCtrl (`self.hoverColorPicker`).'''

        value = self.hoverColorPicker.GetColour().GetRGB()
        self.parent.updateButtonHoverColor(value)

    def GetStyle(self):
        ''' Retorna o valor da wx.ComboBox que pergunta o estilo do botão. '''

        return self.styleCombo.GetValue()

    def SetStyle(self, new_value):
        ''' Seta o valor da wx.ComboBox que pergunta o estilo do botão. '''

        self.styleCombo.SetValue(new_value)

    def SetBtnBackgroundColor(self, new_color):
        ''' Seta o valor da wx.ComboBox que pergunta a cor do botão. '''

        self.btnBackgroundColor.SetValue(new_color)

    def GetBtnBackgroundColor(self):
        ''' Retorna o valor da wx.ComboBox que pergunta o estilo do botão. '''

        return self.btnBackgroundColor.GetValue()

    def GetHoverColor(self):
        ''' Retorna o valor da wx.ColourPickerCtrl que pergunta a cor da seleção (hover) do botão. '''

        return self.hoverColorPicker.GetColour().GetRGB()

    def SetHoverColor(self, new_color):
        ''' Seta o valor da wx.ColourPickerCtrl que pergunta a cor da seleção (hover) do botão. '''

        self.hoverColorPicker.SetColour(Colour(new_color))


class ExibicaoFrame(wx.Panel):
    def __init__(self, parent, mainFrameRef):
        super().__init__(parent=parent)

        self.parent = mainFrameRef
        self.initFrame()

    def initFrame(self):
        ''' Cria a janela. '''

        master = wx.BoxSizer(wx.VERTICAL)

        tooltipSizer = wx.BoxSizer(wx.HORIZONTAL)
        startupSizer = wx.BoxSizer(wx.HORIZONTAL)

        self.tooltipCheck = wx.CheckBox(self, -1)
        self.tooltipCheck.Bind(wx.EVT_CHECKBOX, self.OnTooltipChange)
        text = wx.StaticText(self, -1, 'Mostrar o valor dos instrumentos quando o ponteiro estiver sobre o botão')
        tooltipSizer.Add(self.tooltipCheck)
        tooltipSizer.Add(text, flag=wx.LEFT, border=5)

        self.maxCheck = wx.CheckBox(self, -1)
        self.maxCheck.Bind(wx.EVT_CHECKBOX, self.OnMaxChange)
        text = wx.StaticText(self, -1, 'Iniciar o programa maximizado')
        startupSizer.Add(self.maxCheck)
        startupSizer.Add(text, flag=wx.LEFT, border=5)

        master.Add(tooltipSizer, flag=wx.ALL, border=10)
        master.Add(startupSizer, flag=wx.LEFT | wx.TOP, border=10)

        self.SetSizer(master)

    def OnTooltipChange(self, event):
        ''' Chamada quando o usuário muda o valor da tooltip. '''

        value = self.tooltipCheck.GetValue()
        if value:
            self.parent.isTooltip = True
        else:
            self.parent.isTooltip = False

        self.parent.updateButtonTooltips()

    def OnMaxChange(self, event):
        ''' Chamada quando o usuário muda a wx.CheckBox sobre iniciar o programa maximizado. '''

        value = self.maxCheck.GetValue()
        self.parent.updateIsInitMaxVariable(value)

    def GetTooltipValue(self):
        ''' Retorna o valor da wx.ComboBox que pergunta o conteúdo das tooltips.'''

        return int(self.tooltipCheck.GetValue())

    def SetTooltipValue(self, new_value):
        ''' Seta o valor da wx.ComboBox que pergunta o conteúdo das tooltips. '''

        self.tooltipCheck.SetValue(new_value)

    def GetMaxCheck(self):
        ''' Retorna o valor da wx.CheckBox que pergunta sobre iniciar o programa maximizado. '''

        return self.maxCheck.GetValue()

    def SetMaxCheck(self, new_value):
        ''' Seta o valor da wx.CheckBox que pergunta sobre iniciar o programa maximizado. '''

        self.maxCheck.SetValue(new_value)

class SomFrame(wx.Panel):
    def __init__(self, noteRef, mainFrameRef):
        super().__init__(parent=noteRef)

        self.parent = mainFrameRef
        self.initFrame()

    def initFrame(self):
        ''' Cria a janela. '''

        master = wx.BoxSizer(wx.VERTICAL)

        somSizer = wx.BoxSizer(wx.HORIZONTAL)
        volumeSizer = wx.BoxSizer(wx.HORIZONTAL)

        self.somCheck = wx.CheckBox(self, -1)
        self.somCheck.Bind(wx.EVT_CHECKBOX, self.OnSomChange)
        text = wx.StaticText(self, -1, 'Ativar som')
        somSizer.Add(self.somCheck)
        somSizer.Add(text, flag=wx.LEFT, border=5)

        text = wx.StaticText(self, -1, 'Volume')
        self.volumeSlider = wx.Slider(self, -1, 0, 0, 100, style=wx.SL_HORIZONTAL | wx.SL_LABELS, size=(150, 37))
        self.volumeSlider.Bind(wx.EVT_SLIDER, self.OnVolumeChange)
        volumeSizer.Add(text, flag=wx.TOP, border=3)
        volumeSizer.Add(self.volumeSlider, flag=wx.LEFT, border=15)

        master.Add(somSizer, flag=wx.ALL, border=10)
        master.Add(volumeSizer, flag=wx.LEFT, border=10)

        self.SetSizer(master)

    def OnSomChange(self, event):
        ''' Chamda quando o usuário muda o estado do som. '''

        value = self.somCheck.GetValue()
        self.parent.updateIsSoundActiveVariable(value)
        self.parent.updateSoundPlay()

    def OnVolumeChange(self, event):
        ''' Chamda quando o usuário muda o volume. '''

        self.parent.updateSoundVolume(self.volumeSlider.GetValue() / 100)

    def GetSomValue(self):
        ''' Retorna o valor da wx.Checbox 'Ativar Som'. '''

        return self.somCheck.GetValue()

    def SetSomValue(self, value):
        ''' Seta o valor da wx.Checbox 'Ativar Som'. '''

        self.somCheck.SetValue(value)

    def GetVolume(self):
        ''' Retorna o volume atual do slider, entre 0 ~ 100. '''

        return self.volumeSlider.GetValue()

    def SetVolume(self, value):
        ''' Seta o volume atual do slider, entre 0 ~ 100. '''

        if value > 100:
            value = 100
        if value < 0:
            value = 0

        self.volumeSlider.SetValue(value)

# app = wx.App()
# frame = Settings(None).Show()
# app.MainLoop()