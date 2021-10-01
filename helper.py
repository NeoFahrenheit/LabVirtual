"""
Autor: Leandro Monteiro
Arquivo responsável por classes auxiliares criadas pelo frame principal.
helper.py
"""

import wx
import wx.lib.scrolledpanel as scrolled

class ItemFrame(wx.Panel):
    ''' Responsável por criar os itens dos equipamentos no Painel de Controle. '''

    def __init__(self, scrolledPanel, parent, dic):
        super().__init__(scrolledPanel)

        self.SetBackgroundColour('#cfe1ff')
        sizer = wx.BoxSizer(wx.VERTICAL)

        exitButton = wx.Button(self, dic['index'] + 1000, size=(32, 32))
        exitButton.SetBitmap(wx.Bitmap(f"images/icons/close.png"))
        exitButton.Bind(wx.EVT_LEFT_DOWN, parent.OnClosePanel)

        itemBitmap = wx.StaticBitmap(self, -1, wx.Bitmap(f"images/{dic['buttonName']}.png"))
        itemName = wx.StaticText(self, -1, dic['buttonName'])

        # Pega o min, max e step.
        words = dic['unit'].split(']')
        if len(words) > 1:
            values = words[0][1:].split(',')
            initialV = values[0].strip()
            minV = int(values[1])
            maxV = int(values[2])
            step = int(values[3])

            unit = words[1].strip() # %? cma?

        if dic['isControllable']:
            l = [str(v) for v in range(minV, maxV + 1, step)]
            if l[0] != initialV:
                l.insert(0, initialV)

            ctrl = wx.ComboBox(self, 1000 + dic['index'], l[0], choices=l, name=dic['jsonKey'], style=wx.CB_READONLY, size=((80, 23)))
            ctrl.Bind(wx.EVT_COMBOBOX, parent.OnValueChanged)
            unitText = wx.StaticText(self, -1, unit, size=((60, 23)), style=wx.ALIGN_CENTER)

        else:
            ctrl = wx.TextCtrl(self, 1000 + dic['index'], style=wx.TE_READONLY, name=dic['jsonKey'], size=((80, 23)))
            unitText = wx.StaticText(self, -1, dic['unit'], size=((60, 23)), style=wx.ALIGN_CENTER)

        parent.ctrls.append(ctrl)

        dataSizer = wx.BoxSizer(wx.HORIZONTAL)
        dataSizer.Add(ctrl)
        dataSizer.Add(unitText, flag=wx.TOP | wx.LEFT, border=3)

        sizer.Add(exitButton, flag=wx.ALIGN_RIGHT | wx.ALL, border=5)
        sizer.Add(itemBitmap, flag=wx.ALL | wx.ALIGN_CENTER, border=5)
        sizer.Add(itemName, flag=wx.ALL | wx.ALIGN_CENTER, border=5)
        sizer.Add(dataSizer, flag=wx.ALL | wx.ALIGN_CENTER, border=5)

        self.Hide()
        self.SetSizer(sizer)

class Report(wx.Frame):
    ''' Responsável por gerenciar as modificações no sistema, como também a janela de relatório. '''

    def __init__(self, parent):
        style = wx.DEFAULT_FRAME_STYLE & (~wx.MAXIMIZE_BOX) & (~wx.RESIZE_BORDER)
        super().__init__(parent, style=style)

        self.SetIcon(wx.Icon('images/icons/app_logo.ico'))

        self.SetTitle('Relatório')
        self.SetSize((640, 400))
        self.parent = parent

        self.initUI()
        self.Bind(wx.EVT_CLOSE, self.OnCloseWindow)

        self.CenterOnScreen()

    def initUI(self):
        ''' Inicializa a UI. '''

        self.scrolledSizer = wx.BoxSizer(wx.VERTICAL)
        self.scrolled = scrolled.ScrolledPanel(self, -1, style=wx.SUNKEN_BORDER)
        self.scrolled.SetSizer(self.scrolledSizer)
        self.scrolled.SetupScrolling(scroll_x=False)
        #self.scrolled.SetBackgroundColour(wx.WHITE)

    def TakeNote(self, before, obj):
        ''' Toma nota de uma modificação. Grava o estado do sistema anterior, o que foi mudado pelo usuário
        e o estado posterior. '''

        listCtrl = wx.ListCtrl(self.scrolled, -1, size=((610, 90)), style=wx.LC_REPORT | wx.SUNKEN_BORDER)
        listCtrl.InsertColumn(0, 'Válvula (%)')
        listCtrl.InsertColumn(1, 'Medidor de Vazão (Q (l/min))')
        listCtrl.InsertColumn(2, 'RPM do Motor (%)')
        listCtrl.InsertColumn(3, 'Vacuômetro (mca)')
        listCtrl.InsertColumn(4, 'Manômetro (mca)')

        listCtrl.SetColumnWidth(1, 170)
        listCtrl.SetColumnWidth(2, 115)
        listCtrl.SetColumnWidth(3, 115)
        listCtrl.SetColumnWidth(4, 115)

        # Pegando as informações de antes da mudança.
        listCtrl.InsertItem(0, before['abertura'])
        listCtrl.SetItem(0, 1, before['q(l/m)'])
        listCtrl.SetItem(0, 2, before['rpm'])
        listCtrl.SetItem(0, 3, before['p1'])
        listCtrl.SetItem(0, 4, before['p2'])

        # Pegando as informações do controle que mudou.
        listCtrl.InsertItem(1, '')
        listCtrl.SetItemBackgroundColour(1, '#83de9b')
        if obj.GetName() == 'abertura':
            listCtrl.SetItem(1, 0, obj.GetValue())
        else:
            listCtrl.SetItem(1, 2, obj.GetValue())

        # Pegando as informações depois da mudança.
        listCtrl.InsertItem(2, '')
        for i in range(0, len(self.parent.ctrls)):
            listCtrl.SetItem(2, i, self.parent.ctrls[i].GetValue())

        self.scrolledSizer.Add(listCtrl, flag=wx.ALL, border=5)
        self.scrolled.SendSizeEvent()

    def Translator(self, name):
        ''' Recebe uma jsonKey e retorna o nome do equipamento. '''

        if name == 'abertura':
            return 'Válvula'
        elif name == 'rpm':
            return 'RPM do Motor'
        elif name == 'q(l/m)':
            return 'Medidor de Vazão'
        elif name == 'p1':
            return 'Vacuômetro'
        elif name == 'p2':
            return 'Manômetro'
        else:
            return None

    def ClearScrolled(self):
        ''' Limpa o `self.scrolled`. '''

        self.scrolled.DestroyChildren()
        self.scrolled.SendSizeEvent()

    def OnCloseWindow(self, event):
        ''' Chamada quando o usuário fecha a janela. '''

        self.Hide()
