"""
Autor: Leandro Monteiro
Arquivo responsável por classes auxiliares criadas pelo frame principal.
helper.py
"""

import os
import wx
import wx.lib.scrolledpanel as scrolled
import wx.grid as gridlib
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from datetime import datetime
import copy
import csv

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
        self.exportWindow = None
        self.reportList = []

        self.initUI()
        self.Bind(wx.EVT_CLOSE, self.OnCloseWindow)

        self.CenterOnScreen()

    def initUI(self):
        ''' Inicializa a UI. '''

        self.scrolledSizer = wx.BoxSizer(wx.VERTICAL)
        self.scrolled = scrolled.ScrolledPanel(self, -1, style=wx.SUNKEN_BORDER)
        self.scrolled.SetSizer(self.scrolledSizer)
        self.scrolled.SetupScrolling(scroll_x=False)
        self.order = ['Válvula (%)', 'Medidor de Vazão (Q (l/min))', 'Motor Elétrico (RPM (%))',
        'Manovacuômetro (mca)', 'Manômetro (mca)', 'Piezômetro (m)']

        self.Bind(wx.EVT_CHAR_HOOK, self.OnKey)

    def OnKey(self, event):
        ''' Chamada quando o usuário aperta qualque tecla. '''

        # Ctrl + R
        if event.ControlDown() and event.GetKeyCode() == 82:
            if not self.exportWindow:
                self.exportWindow = Export(self)
                self.exportWindow.ShowModal()

    def TakeNote(self, before, obj):
        ''' Toma nota de uma modificação. Grava o estado do sistema anterior, o que foi mudado pelo usuário
        e o estado posterior. '''

        self.Freeze()
        dic = {}

        listCtrl = wx.ListCtrl(self.scrolled, -1, size=((775, 90)), style=wx.LC_REPORT | wx.SUNKEN_BORDER)
        listCtrl.InsertColumn(0, self.order[0])
        listCtrl.InsertColumn(1, self.order[1])
        listCtrl.InsertColumn(2, self.order[2])
        listCtrl.InsertColumn(3, self.order[3])
        listCtrl.InsertColumn(4, self.order[4])
        listCtrl.InsertColumn(5, self.order[5])

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
        dic['before'] = copy.deepcopy(before)

        # Pegando as informações do controle que mudou.
        listCtrl.InsertItem(1, '')
        listCtrl.SetItemBackgroundColour(1, '#83de9b')
        value = obj.GetValue()
        if obj.GetName() == 'abertura':
            listCtrl.SetItem(1, 0, value)
            dic['changed'] = {'abertura': value}
        else:
            listCtrl.SetItem(1, 2, value)
            dic['changed'] = {'rpm': value}

        # Pegando as informações depois da mudança.
        after = {}
        listCtrl.InsertItem(2, '')
        for i in range(0, len(self.parent.ctrls)):
            value = self.parent.ctrls[i].GetValue()
            listCtrl.SetItem(2, i, value)
            after[self.parent.ctrls[i].GetName()] = value

        dic['after'] = copy.deepcopy(after)
        self.scrolledSizer.Add(listCtrl, flag=wx.ALL, border=5)
        self.scrolled.SendSizeEvent()
        self.reportList.append(dic)
        self.Thaw()

    def ClearScrolled(self):
        ''' Limpa o `self.scrolled`. '''

        self.scrolled.DestroyChildren()
        self.reportList.clear()
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


class Export(wx.Dialog):
    def __init__(self, parent):
        super().__init__(parent)

        self.parent = parent
        self.reportList = self.parent.reportList
        self.order = parent.order
        # self.password = 'lamiph@2021!'
        self.SetTitle('Exportar relatório')
        self.SetIcon(wx.Icon('images/icons/app_logo.ico'))

        self.initUI()
        self.SetFocus()
        self.Center()

        self.Bind(wx.EVT_CLOSE, self.OnCloseWindow)

    def initUI(self):
        ''' Inicializa a UI. '''

        master = wx.BoxSizer(wx.VERTICAL)
        extension = wx.BoxSizer(wx.HORIZONTAL)
        password = wx.BoxSizer(wx.HORIZONTAL)

        choices = ['PDF .pdf', 'Tabela .csv']
        self.combo = wx.ComboBox(self, -1, choices[0], size=((110, 23)), style=wx.CB_READONLY, choices=choices)
        extension.Add( wx.StaticText(self, -1, 'Formato:', size=(50, 23)), flag=wx.TOP, border=2 )
        extension.Add(self.combo, flag=wx.LEFT, border=5)

        # password.Add( wx.StaticText(self, -1, 'Senha: ', size=(50, 23)), flag=wx.TOP, border=2 )
        # self.passCtrl = wx.TextCtrl(self, -1, size=((110, 23)), style=wx.TE_PASSWORD | wx.TE_PROCESS_ENTER)
        # password.Add(self.passCtrl, flag=wx.LEFT, border=5)

        self.expBtn = wx.Button(self, -1, 'Exportar')
        self.expBtn.Bind(wx.EVT_BUTTON, self.OnExport)
        # self.passCtrl.Bind(wx.EVT_TEXT_ENTER, self.OnExport)

        master.Add(extension, flag=wx.ALL, border=5)
        # master.Add(password, flag=wx.ALL, border=5)
        master.Add(self.expBtn, flag=wx.ALL | wx.ALIGN_CENTER, border=5)

        self.SetSizerAndFit(master)

    def OnExport(self, event):
        ''' Chamada quando o botão `Exportar` é clicado. '''

        if len(self.reportList) == 0:
            wx.MessageBox('O relatório está vazio. Modifique alguns parâmetros para exportar.', 'Relatório vazio', wx.OK | wx.ICON_INFORMATION)
            return

        # # Não é importante que esta função fique super protegida.
        # if not self.passCtrl.GetValue() == self.password:
        #     wx.MessageBox('Senha incorreta.', 'Erro', wx.OK | wx.ICON_ERROR)
        #     return

        choice = self.combo.GetValue().split()[0]
        if choice == 'PDF':
            func = self.writePDF
            suffix = '.pdf'
        else:
            func = self.writeCSV
            suffix = '.csv'

        dialog = wx.FileDialog(self, f"Escolha um nome para o arquivo", '', '', f'*{suffix}', wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
        if dialog.ShowModal() == wx.ID_OK:
            filename = dialog.GetFilename()
            filename = self.putFileSuffix(filename, suffix)
            file_dir = dialog.GetDirectory()
            file_path = os.path.join(file_dir, filename)
            func(file_path)
            wx.MessageBox(f'Arquivo {filename} salvo com sucesso.', 'Sucesso', wx.OK | wx.ICON_INFORMATION)

    def writeCSV(self, filepath):
        ''' Exporta o relatório como .csv. '''

        with open(filepath, 'w', encoding='utf-8', newline='') as f:
            writerObj = csv.writer(f, delimiter=',')
            head = self.order[:]
            head.insert(0, 'Situação')
            writerObj.writerow(head)

            for state in self.reportList:
                before = [value for value in state['before'].values()]
                before.insert(0, 'Antes')
                writerObj.writerow(before)

                if 'abertura' in state['changed']:
                    writerObj.writerow(['Alteração', state['changed']['abertura'], '', '', '', '', ''])
                else:
                    writerObj.writerow(['Alteração', '', '', state['changed']['rpm'], '', '', ''])

                after = [value for value in state['after'].values()]
                after.insert(0, 'Depois')
                writerObj.writerow(after)
                writerObj.writerow('')

            now = datetime.now().strftime("%d/%m/%Y às %H:%M:%S")
            writerObj.writerow(['Obtido em:', now])

    def writePDF(self, filepath):
        ''' Exporta o relatório como .pdf. '''

        flowables = []
        styles = getSampleStyleSheet()
        spacer = Spacer(1, 0.25 * inch)
        image = Image('images/lab_logo.png', width=45, height=92)

        titleStyle = ParagraphStyle('yourtitle', fontName="Helvetica-Bold", fontSize=12,
        parent=styles['Heading1'], alignment=1, spaceAfter=8)

        flowables.append(image)
        flowables.append(spacer)
        flowables.append(Paragraph("Laboratório Virtual - Relatório de Uso", titleStyle))

        head = self.order[:]
        head.insert(0, 'Situação')

        for state in self.reportList:
            before = [value for value in state['before'].values()]
            before.insert(0, 'Antes')

            if 'abertura' in state['changed']:
                changed = ['Alteração', state['changed']['abertura'], '', '', '', '', '']
            else:
                changed = ['Alteração', '', '', state['changed']['rpm'], '', '', '']

            after = [value for value in state['after'].values()]
            after.insert(0, 'Depois')

            data = [head, before, changed, after]

            tblstyle = TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), '#c2c2c2'),
                ('BACKGROUND', (0, 1), (-1, 1), '#f0f0f0'),
                ('BACKGROUND', (0, 2), (-1, 2), '#83de9b'),
                ('BACKGROUND', (0, 3), (-1, 3), '#f0f0f0'),
                ('FONTSIZE', (0, 0), (-1, -1), 5)])

            tbl = Table(data)
            tbl.setStyle(tblstyle)
            flowables.append(tbl)
            flowables.append(spacer)


        now = datetime.now().strftime("Dados obtidos em %d/%m/%Y às %H:%M:%S")
        p = Paragraph(now, styles['Normal'])
        flowables.append(p)

        ### ------------------ ###

        doc = SimpleDocTemplate(filepath, pagesize=A4)
        doc.build(flowables)

    def putFileSuffix(self, filename, suffix):
        ''' Verifica se filename ja possui o sufixo informado. Se nao, adiciona e retorna filename modificado.'''

        size = len(suffix)
        fileSuffix =  filename[-size:].lower()

        if fileSuffix == suffix:
            return filename
        else:
            return filename + suffix

    def OnCloseWindow(self, event):
        ''' Chamada quando a janela é fechada. '''

        self.parent.exportWindow = None
        self.Destroy()