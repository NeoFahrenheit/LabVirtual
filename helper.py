"""
Autor: Leandro Monteiro
Arquivo responsável por classes auxiliares criadas pelo frame principal.
helper.py
"""

import wx
import wx.lib.scrolledpanel as scrolled
import wx.grid as gridlib

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

        if dic['jsonKey'] == 'rpm':
            l = [f"{value[0]} ({value[1]})" for value in dic['unit']]
            ctrl = wx.ComboBox(self, 1000 + dic['index'], l[0], choices=l, name=dic['jsonKey'], style=wx.CB_READONLY, size=((80, 23)))
            ctrl.Bind(wx.EVT_COMBOBOX, parent.OnValueChanged)
            unitText = wx.StaticText(self, -1, 'RPM (%)', size=((60, 23)), style=wx.ALIGN_CENTER)

        elif dic['jsonKey'] == 'abertura':
            l = ['0', '25', '50', '75', '100']
            ctrl = wx.ComboBox(self, 1000 + dic['index'], l[0], choices=l, name=dic['jsonKey'], style=wx.CB_READONLY, size=((80, 23)))
            ctrl.Bind(wx.EVT_COMBOBOX, parent.OnValueChanged)
            unitText = wx.StaticText(self, -1, dic['unit'], size=((60, 23)), style=wx.ALIGN_CENTER)

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
        style = wx.DEFAULT_FRAME_STYLE & (~wx.MAXIMIZE_BOX) & (~wx.MINIMIZE_BOX) & (~wx.RESIZE_BORDER)
        super().__init__(parent, style=style)

        self.SetIcon(wx.Icon('images/icons/app_logo.ico'))

        self.SetTitle('Relatório')
        self.SetSize((810, 400))
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

    def TakeNote(self, before, obj):
        ''' Toma nota de uma modificação. Grava o estado do sistema anterior, o que foi mudado pelo usuário
        e o estado posterior. '''

        self.Freeze()

        listCtrl = wx.ListCtrl(self.scrolled, -1, size=((775, 90)), style=wx.LC_REPORT | wx.SUNKEN_BORDER)
        listCtrl.InsertColumn(0, 'Válvula (%)')
        listCtrl.InsertColumn(1, 'Medidor de Vazão (Q (l/min))')
        listCtrl.InsertColumn(2, 'Motor Elétrico (RPM (%))')
        listCtrl.InsertColumn(3, 'Manovacuômetro (mca)')
        listCtrl.InsertColumn(4, 'Manômetro (mca)')
        listCtrl.InsertColumn(5, 'Piezômetro (m)')

        listCtrl.SetColumnWidth(1, 170)
        listCtrl.SetColumnWidth(2, 145)
        listCtrl.SetColumnWidth(3, 145)
        listCtrl.SetColumnWidth(4, 115)
        listCtrl.SetColumnWidth(5, 110)

        # Pegando as informações de antes da mudança.
        listCtrl.InsertItem(0, before['abertura'])
        listCtrl.SetItem(0, 1, before['q(l/m)'])
        listCtrl.SetItem(0, 2, before['rpm'])
        listCtrl.SetItem(0, 3, before['p1'])
        listCtrl.SetItem(0, 4, before['p2'])
        listCtrl.SetItem(0, 5, before['piezometro'])

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
        self.Thaw()

    def ClearScrolled(self):
        ''' Limpa o `self.scrolled`. '''

        self.scrolled.DestroyChildren()
        self.scrolled.SendSizeEvent()

    def OnCloseWindow(self, event):
        ''' Chamada quando o usuário fecha a janela. '''

        self.Hide()

class BombCurve(wx.Dialog):
    def __init__(self, parent):
        style = wx.DEFAULT_FRAME_STYLE & (~wx.MAXIMIZE_BOX) & (~wx.MINIMIZE_BOX) & (~wx.RESIZE_BORDER)
        super().__init__(parent, style=style)

        self.parent = parent
        self.SetIcon(wx.Icon('images/icons/app_logo.ico'))
        self.SetTitle('Curva Teórica da Bomba')
        self.SetBackgroundColour(wx.WHITE)

        self.initUI()
        self.Bind(wx.EVT_CLOSE, self.OnCloseWindow)
        self.CenterOnParent()

    def initUI(self):
        ''' Inicializa a UI. '''

        hBox = wx.BoxSizer(wx.HORIZONTAL)
        vBox = wx.BoxSizer(wx.VERTICAL)

        grid = gridlib.Grid(self, -1, size=(250, 350))
        grid.CreateGrid(12, 2)
        grid.SetColLabelSize(0)
        grid.SetRowLabelSize(30)
        grid.SetColSize(0, 100)
        grid.SetColSize(1, 100)
        grid.SetCellSize(0, 0, 1, 2)
        grid.SetDefaultCellAlignment(wx.ALIGN_CENTRE, wx.ALIGN_CENTRE)
        grid.DisableDragRowSize()
        grid.DisableDragColSize()

        grid.SetCellBackgroundColour(0, 0, '#a5a9b0')
        grid.SetCellBackgroundColour(1, 0, '#cad0de')
        grid.SetCellBackgroundColour(1, 1, '#cad0de')
        grid.SetCellBackgroundColour(2, 0, '#e6eaf2')
        grid.SetCellBackgroundColour(2, 1, '#e6eaf2')
        vBox.Add(grid, flag=wx.TOP, border=15)

        for i in range(0, 20):
            for j in range(0, grid.GetNumberRows()):
                grid.SetReadOnly(i, j)

        x = [0, 10, 12.5, 15, 20, 25, 30, 33.6, 38.5]
        y = [22.6, 22.57, 22.42, 22.17, 21.33, 20.05, 18.33, 16.82, 14.39]

        grid.SetCellValue(0, 0, 'Dados da curva da bomba teórica')
        grid.SetCellValue(1, 0, 'Rotação (rpm)')
        grid.SetCellValue(1, 1, '1750')
        grid.SetCellValue(2, 0, 'Q (m³/h)')
        grid.SetCellValue(2, 1, 'H (m)')

        for i in range(0, 9):
            grid.SetCellValue(i + 3, 0, str(x[i]))

        for i in range(0, 9):
            grid.SetCellValue(i + 3, 1, str(y[i]))

        bitmap = wx.StaticBitmap(self, -1, wx.Bitmap('data/system1/misc/curva_bomba.png'))
        bitmap.SetFocus()

        hBox.Add(vBox, flag=wx.EXPAND | wx.ALL, border=5)
        hBox.Add(bitmap, flag=wx.ALL, border=5)

        self.SetSizerAndFit(hBox)

    def OnCloseWindow(self, event):
        ''' Chamada quando o usuário fecha a janela. '''

        self.parent.pumpCurve = None
        self.Destroy()