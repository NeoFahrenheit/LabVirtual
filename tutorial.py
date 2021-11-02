"""
Classe responsável pelos tutoriais do programa.
tutorial.py
"""

# self.parent.canAcess[]
# [0] -> Left Arrow
# [1] -> Right Arrow
# [2] -> Bomba, Zoom
# [3] -> Motor Elétrico, Zoom
# [4] -> Registro Esfera, Zoom
# [5] -> Medidor de Vazão, Zoom
# [6] -> Manovacuômetro, Zoom
# [7] -> Manometro, Zoom
# [8] -> Piezômetro, Zoom
# [9] -> Registro Esfera, botao
# [10] -> Medidor de Vazão, botão
# [11] -> Motor Elétrico, botão
# [12] -> Manovacuômetro, botão
# [13] -> Manômetro, botão
# [14] -> Piezometro, botão
# [15] -> Acionar Motor, botão
# [16] -> Desligar Motor, botão

import wx
from pubsub import pub
import settings

class MainTutorial():
    def __init__(self, parent):
        self.parent = parent
        self.index = 0
        self.path = 'images/tutorial'
        self.equipList = ['Piezômetro', 'Piezômetro', None, 'Manovacuômetro', 'Motor Elétrico', 'Bomba', 'Manômetro', 'Medidor de Vazão', None, 'Registro Esfera']
        self.isTutorialInProgress = False
        self.pos = ()

        self.data = self.parent.getTutorialFile('first_tutorial')

    def Notify(self, value, buttonPressed=None):
        ''' Recebe uma notificação com os valores (dict / string) do sistema quando algum for modificado. '''

        if self.index == 20:                    # Última imagem do tutorial.
            self.endTutorial()
            return

        elif isinstance(value, dict):
            if self.parent.getRPMValue() > 0 and self.index == 14:
                self.index += 1
                self.parent.ctrls[2].Enable(False)

            elif int(value['abertura']) > 0 and self.index == 15:
                self.index += 1

        elif buttonPressed and self.index > 15: # A partir deste index, não haverá mais dict em value.
            self.index += 1

        else:                                   # Em sua maioria, eventos da seta do teclado.
            if value == 'right':
                self.index += 1
            elif value == 'left':
                if self.index != 0:
                    self.index -= 1

        self.tutorialHandler()

    def InitTutorial(self):
        ''' Inicia o tutorial. '''

        self.isTutorialInProgress = True
        self.parent.isTutorial = True
        self.index = 0
        self.parent.ctrls[2].SetValue('0 (0)')
        self.parent.ctrls[0].SetValue('0')
        self.parent.OnValueChanged(self.parent.ctrls[0])
        self.parent.OnClearReport(None)
        self.parent.HideScrolled()
        self.parent.index = 0   # Super importante porque vamos usar somente a primeira imagem em self.parent.images

        self.tutorialHandler()

    def refreshTutorialImage(self, isJustRepositioning=False):
        ''' Atualiza a imagem e posição em `self.index` no frame principal. '''

        if not isJustRepositioning:
            self.parent.tutorialBitmap = wx.Bitmap(f"{self.path}/{self.index}.png", wx.BITMAP_TYPE_PNG)

        self.pos = self.data[self.index]['coordinates']

    def tutorialHandler(self):
        ''' Gerencia o progresso do tutorial a partir de `self.index`. '''

        # Seta todos os cliques para False, depois apenas o que queremos para True
        clicks = self.data[self.index]['allowedClicks']
        pub.sendMessage('acessHandler', boolValue=False, setAll=True)
        for i in range(0, len(clicks)):
            pub.sendMessage('acessHandler', index=clicks[i], boolValue=True)

        self.refreshTutorialImage()

        # Visão geral, usuário pode avançar e retroceder.
        if self.index in [0, 1, 2, 3, 6, 12, 19, 20]:
            self.parent.showButtons(False)
            self.parent.frameImage(self.parent.getFirstImagePath())

        # Zoom em algum equipamento.
        elif self.index in [4, 5, 7, 8, 9, 10, 11, 13]:
            self.parent.OnEquip(self.equipList[self.index - 4])

        # Aqui é onde o usuário clica em botões e MODIFICA valores do sistema.
        elif self.index in [14, 15]:
            self.parent.showButtons(True)
            self.parent.isEquipZoom = False
            self.parent.frameImage(self.parent.getFirstImagePath())
            self.parent.updateButtons()

        # Aqui é onde o usuário clica nos botões apenas para visualização.
        # Presume-se que não vai ter mais zoom.
        elif self.index in [16, 17, 18]:
            self.parent.frameImage(self.parent.getFirstImagePath())

    def endTutorial(self):
        ''' Finaliza o tutorial. '''

        self.isTutorialInProgress = False
        self.parent.isEquipZoom = False
        self.parent.ctrls[2].Enable(True)
        pub.sendMessage('acessHandler', boolValue=True, setAll=True)

        self.parent.frameImage(self.parent.getFirstImagePath())
        self.parent.showButtons(True)
        frame = settings.Settings(self.parent, True)
        # Quando o painel Settings() é criado, applyUserConfig() é chamada automaticamente. Ele pega o valor do 'tutorial' do arquivo 'labvirtual_config.ini'
        # e seta em self.parent.isTutorial. Então, precisamos setar self.parent.isTutorial para 0 (false) antes de chamar getUserConfig().

        self.parent.isTutorial = False
        frame.getUserConfig()
        frame.SaveFile()
        frame.Destroy()