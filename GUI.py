import wx


class SettingsPanel(wx.Panel):
    def __init__(self, parent):
        super(__class__, self).__init__(parent)
        sizerTop = wx.FlexGridSizer(3, 2, 35)

        # slider on the left
        slider_LCD_backlight = wx.Slider(self, minValue=0, maxValue=10,
                                         style=wx.SL_INVERSE | wx.SL_VERTICAL | wx.SL_VALUE_LABEL | wx.SL_LEFT,
                                         name='Display brightness')
        slider_LCD_backlight.SetBackgroundColour('#F000E511')
        label_slider_LCD_backlight = wx.StaticText(self, label=slider_LCD_backlight.GetName(), size=(1, -1),
                                                   style=wx.ALIGN_CENTRE)
        label_slider_LCD_backlight.SetBackgroundColour('#efaaef55')

        # slider on the right
        slider_throughput = wx.Slider(self, style=wx.SL_VERTICAL | wx.SL_INVERSE | wx.SL_VALUE_LABEL, name='Quality')
        slider_throughput.SetBackgroundColour('#d0002511')
        label_slider_throughput = wx.StaticText(self, label=slider_throughput.GetName(), size=(1, -1),
                                                style=wx.ALIGN_CENTRE)
        label_slider_throughput.SetBackgroundColour('#f00055aa')

        sizerTop.AddGrowableRow(0, 0)
        sizerTop.AddGrowableCol(0, 0)
        sizerTop.AddGrowableCol(2, 0)

        sizerTop.AddMany([(slider_LCD_backlight, 1, wx.GROW),
                          (wx.StaticText(self, label="RIGHT"), 1, wx.ALIGN_RIGHT),
                          (slider_throughput, 1, wx.GROW),
                          (label_slider_LCD_backlight, 0, wx.EXPAND | wx.ALL, 5),
                          (wx.StaticText(self, label="LEFT"), 1, wx.ALIGN_LEFT),
                          (label_slider_throughput, 0, wx.EXPAND | wx.ALL, 5)
                          ])

        self.SetSizer(sizerTop)


class ConnectionPanel(wx.Panel):
    def __init__(self, parent):
        super(__class__, self).__init__(parent)
        sizer = wx.GridSizer(1, 2, 0)

        model_name = 'domkamerka'

        self.label_conn_status = wx.StaticText(self, label=f'{model_name} connected', style=wx.ALIGN_CENTRE)
        self.label_conn_status.SetForegroundColour('#E2007D')
        sizer.Add(self.label_conn_status, wx.ID_ANY, wx.ALIGN_CENTRE)

        button = wx.Button(self, label='Reconnect', )
        sizer.Add(button, wx.ID_ANY, wx.ALIGN_CENTRE)

        self.SetSizer(sizer)
        self.Layout()


class MainFrame(wx.Frame):
    def __init__(self, *args, **kwargs):
        style = wx.DEFAULT_FRAME_STYLE & ~(wx.RESIZE_BORDER | wx.MAXIMIZE_BOX)
        size = (380, 500)
        super(__class__, self).__init__(*args, **kwargs, style=style, size=size)
        # override the styling
        from pathlib import Path
        self.SetIcon(wx.Icon(Path('res').joinpath(Path('iconka.png')).as_posix()))

        sizerV = wx.BoxSizer(wx.VERTICAL)

        self.panel_connection = ConnectionPanel(self)
        sizerV.Add(self.panel_connection, 2, wx.GROW)

        self.panel_settings = SettingsPanel(self)
        sizerV.Add(self.panel_settings, 9, wx.GROW)

        footer = wx.StaticText(self, label='authorship (~ownership) → amateusz @ github.com')
        footer.SetForegroundColour('#ffffff33')
        sizerV.Add(footer, 0, wx.ALIGN_CENTRE | wx.ALL, 10)

        self.SetSizer(sizerV)
        self.SetAutoLayout(1)
        # sizer.Fit(self) #


class GoProStreamGUI(wx.App):
    def OnInit(self):
        self.frame = MainFrame(None, wx.ID_ANY, "GoPro LiveStream Tool")
        self.frame.Show(True)
        # self.frame.Bind(wx.EVT_CLOSE, self.OnFrameClose)
        # self.frame.Bind(wx.EVT_MOUSEWHEEL, self.OnScrollInFrame)
        # self.frame.Bind(wx.EVT_SLIDER, self.OnSlider)

        return True

    def OnSlider(self, event):
        print(event.GetSelection())
        event.Skip()

    def OnFrameClose(self, event):
        # gopro.quit()
        event.Skip()

    def OnScrollInFrame(self, event):
        # print(dir(event))
        scroll_amount = event.GetWheelRotation() / 120.0
        scroll_axis = event.GetWheelAxis()
        if scroll_axis == wx.MOUSE_WHEEL_HORIZONTAL:
            if scroll_amount < 0:
                print('→')
            else:
                print('←')
        elif scroll_axis == wx.MOUSE_WHEEL_VERTICAL:
            if scroll_amount < 0:
                print('↑')
            else:
                print('↓')

        event.Skip()


if __name__ == '__main__':
    gui = GoProStreamGUI(useBestVisual=True)
    gui.MainLoop()
