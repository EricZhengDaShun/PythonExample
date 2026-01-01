import sys
import numpy as np
from scipy.stats import norm
from PySide6 import QtWidgets, QtCore, QtGui
import pyqtgraph as pg

# --- 1. 定義 Black-Scholes 模型函數 (邏輯不變) ---
def black_scholes_call(S, K, T, r, sigma):
    if np.isscalar(T):
        if T <= 1e-5:
            return np.maximum(S - K, 0)
    
    d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    
    call_price = (S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2))
    return call_price

# --- 2. 自定義 Sidebar 風格的群組框 (樣式不變) ---
class SidebarGroup(QtWidgets.QGroupBox):
    def __init__(self, title):
        super().__init__(title)
        self.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 14px;
                border: 1px solid #d3d3d3;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 5px;
                color: #31333F;
            }
        """)

# --- 3. 主視窗程式 ---
class OptionStrategyApp(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Reehl's Option Math Visualizer (PySide6 Edition)")
        self.resize(1200, 800)

        font = QtGui.QFont("Microsoft JhengHei", 10)
        self.setFont(font)

        central_widget = QtWidgets.QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QtWidgets.QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ===========================
        # 左側 Sidebar (介面程式碼省略，與上版相同)
        # ===========================
        self.sidebar = QtWidgets.QWidget()
        self.sidebar.setFixedWidth(320)
        self.sidebar.setStyleSheet("background-color: #f0f2f6; border-right: 1px solid #dcdcdc;")
        sidebar_layout = QtWidgets.QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(20, 20, 20, 20)
        sidebar_layout.setSpacing(15)

        group_market = SidebarGroup("1. 市場參數")
        layout_market = QtWidgets.QFormLayout()
        self.spin_price = QtWidgets.QDoubleSpinBox()
        self.spin_price.setRange(1, 1000)
        self.spin_price.setValue(100.0)
        self.spin_price.setSuffix(" $")
        self.lbl_iv_val = QtWidgets.QLabel("25 %")
        self.slider_iv = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.slider_iv.setRange(10, 100)
        self.slider_iv.setValue(25)
        self.lbl_days_val = QtWidgets.QLabel("30 Days")
        self.slider_days = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.slider_days.setRange(0, 90)
        self.slider_days.setValue(30)
        self.spin_rate = QtWidgets.QDoubleSpinBox()
        self.spin_rate.setRange(0, 20)
        self.spin_rate.setValue(4.0)
        self.spin_rate.setSingleStep(0.1)
        self.spin_rate.setSuffix(" %")
        layout_market.addRow("當前股價:", self.spin_price)
        layout_market.addRow("隱含波動率:", self.lbl_iv_val)
        layout_market.addRow(self.slider_iv)
        layout_market.addRow("距離到期:", self.lbl_days_val)
        layout_market.addRow(self.slider_days)
        layout_market.addRow("無風險利率:", self.spin_rate)
        group_market.setLayout(layout_market)
        sidebar_layout.addWidget(group_market)

        group_strategy = SidebarGroup("2. 策略設定 (蝶式)")
        layout_strategy = QtWidgets.QFormLayout()
        self.spin_atm = QtWidgets.QDoubleSpinBox()
        self.spin_atm.setRange(1, 1000)
        self.spin_atm.setValue(100.0)
        self.spin_width = QtWidgets.QDoubleSpinBox()
        self.spin_width.setRange(0.5, 50)
        self.spin_width.setValue(5.0)
        self.spin_width.setSingleStep(0.5)
        layout_strategy.addRow("中間履約價:", self.spin_atm)
        layout_strategy.addRow("履約價間距:", self.spin_width)
        group_strategy.setLayout(layout_strategy)
        sidebar_layout.addWidget(group_strategy)

        self.info_box = QtWidgets.QLabel()
        self.info_box.setWordWrap(True)
        self.info_box.setStyleSheet("""
            background-color: #dbeafe; color: #1e3a8a; padding: 10px; border-radius: 5px; font-size: 12px;
        """)
        sidebar_layout.addWidget(self.info_box)
        sidebar_layout.addStretch()
        main_layout.addWidget(self.sidebar)

        # ===========================
        # 右側 Main Content (圖表與文字)
        # ===========================
        self.content = QtWidgets.QWidget()
        self.content.setStyleSheet("background-color: white;")
        content_layout = QtWidgets.QVBoxLayout(self.content)
        content_layout.setContentsMargins(30, 30, 30, 30)

        title_label = QtWidgets.QLabel("📊 選擇權策略數學分析：蝶式價差 (Butterfly Spread)")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #31333F;")
        content_layout.addWidget(title_label)

        desc_label = QtWidgets.QLabel(
            "此工具模擬 C.B. Reehl 書中強調的「期望值與時間價值」概念。\n"
            "觀察「當前曲線 (T+0)」如何隨著「時間流逝」與「波動率變化」而向到期損益線收斂。"
        )
        desc_label.setStyleSheet("color: #555; font-size: 14px; margin-bottom: 10px;")
        content_layout.addWidget(desc_label)

        # --- PyQtGraph 圖表設定 ---
        pg.setConfigOption('background', 'w')
        pg.setConfigOption('foreground', 'k')
        pg.setConfigOption('antialias', True) # 開啟反鋸齒讓線條更平滑
        
        self.plot_widget = pg.PlotWidget()
        # 網格線稍微調深一點點
        self.plot_widget.showGrid(x=True, y=True, alpha=0.4)
        self.plot_widget.setLabel('bottom', "標的股價 (Stock Price)", **{'font-size': '12pt'})
        self.plot_widget.setLabel('left', "損益 (P&L)", **{'font-size': '12pt'})
        self.plot_widget.setMouseEnabled(x=True, y=False)
        
        # 建立圖形物件
        self.curve_exp = self.plot_widget.plot(pen=pg.mkPen(color='#d62728', width=2, style=QtCore.Qt.DashLine), name="到期損益")
        self.curve_curr = self.plot_widget.plot(pen=pg.mkPen(color='#1f77b4', width=3), name="當前損益")
        self.curve_zero = pg.PlotCurveItem(pen=None) 
        self.plot_widget.addItem(self.curve_zero)
        self.fill = pg.FillBetweenItem(self.curve_curr, self.curve_zero, brush=pg.mkBrush(31, 119, 180, 50))
        self.plot_widget.addItem(self.fill)

        # --- 【修改點 1】加強靜態輔助線 ---
        # 現價線：加粗 (width=2)，顏色加深
        self.line_price = pg.InfiniteLine(angle=90, movable=False, 
                                          pen=pg.mkPen(color='#555555', style=QtCore.Qt.DashLine, width=2))
        # 零軸線：加粗 (width=2)，純黑色
        self.line_zero = pg.InfiniteLine(angle=0, movable=False, 
                                         pen=pg.mkPen(color='black', width=2))
        self.plot_widget.addItem(self.line_price)
        self.plot_widget.addItem(self.line_zero)

        # --- 【修改點 2】新增互動式滑鼠跟隨十字線 ---
        # 建立兩條新的 InfiniteLine，初始設為隱藏
        # 使用細的黑色虛線
        hover_pen = pg.mkPen(color='k', width=1, style=QtCore.Qt.DotLine)
        self.vLineHover = pg.InfiniteLine(angle=90, movable=False, pen=hover_pen)
        self.hLineHover = pg.InfiniteLine(angle=0, movable=False, pen=hover_pen)
        self.vLineHover.hide()
        self.hLineHover.hide()
        self.plot_widget.addItem(self.vLineHover, ignoreBounds=True)
        self.plot_widget.addItem(self.hLineHover, ignoreBounds=True)
        
        # 監聽滑鼠移動事件
        self.plot_widget.scene().sigMouseMoved.connect(self.mouseMoved)

        # Legend 樣式微調
        self.legend = self.plot_widget.addLegend(frame=True, brush=pg.mkBrush(255,255,255,200))

        content_layout.addWidget(self.plot_widget, stretch=1)

        # --- 書中概念對應 (文字區 - 略縮以節省空間) ---
        self.explanation_label = QtWidgets.QLabel()
        self.explanation_label.setWordWrap(True)
        self.explanation_label.setStyleSheet("font-size: 13px; color: #444; line-height: 1.5;")
        self.explanation_label.setTextFormat(QtCore.Qt.RichText)
        self.explanation_label.setText("""
            <h3>💡 書中概念對應</h3>
            <ul>
                <li>紅色的三角形區域就是獲利目標區。</li>
                <li>試著減少 <b>「距離到期天數」</b>，藍色曲線會逐漸隆起貼近紅色虛線 (時間價值)。</li>
                <li>試著增加 <b>「隱含波動率」</b>，藍色曲線會變得更平坦 (Vega 風險)。</li>
            </ul>
        """)
        content_layout.addWidget(self.explanation_label)
        
        main_layout.addWidget(self.content)

        # --- 訊號連接 ---
        self.spin_price.valueChanged.connect(self.update_plot)
        self.slider_iv.valueChanged.connect(self.update_ui_labels)
        self.slider_iv.valueChanged.connect(self.update_plot)
        self.slider_days.valueChanged.connect(self.update_ui_labels)
        self.slider_days.valueChanged.connect(self.update_plot)
        self.spin_rate.valueChanged.connect(self.update_plot)
        self.spin_atm.valueChanged.connect(self.update_plot)
        self.spin_width.valueChanged.connect(self.update_plot)

        self.update_ui_labels()
        self.update_plot()

    # --- 【修改點 3】滑鼠移動處理函數 ---
    def mouseMoved(self, evt):
        pos = evt
        # 檢查滑鼠是否在繪圖區域內
        if self.plot_widget.sceneBoundingRect().contains(pos):
            # 將螢幕座標轉換為圖表座標 (數據座標)
            mousePoint = self.plot_widget.plotItem.vb.mapSceneToView(pos)
            x_val = mousePoint.x()
            y_val = mousePoint.y()

            # 顯示並移動十字線到滑鼠位置
            self.vLineHover.show()
            self.hLineHover.show()
            self.vLineHover.setPos(x_val)
            self.hLineHover.setPos(y_val)
            
            # 選用：可以在這裡添加一個 Tooltip 或 Label 來顯示當前的 x, y 數值
            # self.plot_widget.setToolTip(f"Price: {x_val:.2f}, P&L: {y_val:.2f}")

        else:
            # 滑鼠移出時隱藏十字線
            self.vLineHover.hide()
            self.hLineHover.hide()

    def update_ui_labels(self):
        iv = self.slider_iv.value()
        days = self.slider_days.value()
        self.lbl_iv_val.setText(f"{iv} %")
        self.lbl_days_val.setText(f"{days} Days")

    def update_plot(self):
        S0 = self.spin_price.value()
        sigma = self.slider_iv.value() / 100.0
        days = self.slider_days.value()
        T = days / 365.0
        r = self.spin_rate.value() / 100.0
        K_mid = self.spin_atm.value()
        width = self.spin_width.value()
        K_low = K_mid - width
        K_high = K_mid + width

        self.info_box.setText(f"買入 Call @ ${K_low:.1f}\n賣出 2 Calls @ ${K_mid:.1f}\n買入 Call @ ${K_high:.1f}")

        # 計算成本
        cost_low = black_scholes_call(S0, K_low, T, r, sigma)
        cost_mid = black_scholes_call(S0, K_mid, T, r, sigma)
        cost_high = black_scholes_call(S0, K_high, T, r, sigma)
        entry_cost = (cost_low + cost_high) - (2 * cost_mid)

        # 設定標題字型大小
        self.plot_widget.plotItem.setTitle(f"蝶式價差損益圖 (成本: ${entry_cost:.2f})", **{'font-size': '16pt', 'color': '#31333F'})

        # 產生數據並繪圖
        x = np.linspace(S0 * 0.8, S0 * 1.2, 300) # 增加點數讓曲線更平滑

        val_low_exp = np.maximum(x - K_low, 0)
        val_mid_exp = np.maximum(x - K_mid, 0)
        val_high_exp = np.maximum(x - K_high, 0)
        strategy_val_exp = (val_low_exp + val_high_exp) - (2 * val_mid_exp)
        y_exp = strategy_val_exp - entry_cost

        val_low_cur = black_scholes_call(x, K_low, T, r, sigma)
        val_mid_cur = black_scholes_call(x, K_mid, T, r, sigma)
        val_high_cur = black_scholes_call(x, K_high, T, r, sigma)
        strategy_val_cur = (val_low_cur + val_high_cur) - (2 * val_mid_cur)
        y_cur = strategy_val_cur - entry_cost

        self.curve_exp.setData(x, y_exp)
        self.curve_curr.setData(x, y_cur)
        self.curve_zero.setData(x, np.zeros_like(x)) 
        
        # 更新靜態現價線位置
        self.line_price.setPos(S0)

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = OptionStrategyApp()
    window.show()
    sys.exit(app.exec())