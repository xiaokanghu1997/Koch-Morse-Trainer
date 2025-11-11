from PySide6.QtWidgets import QApplication, QVBoxLayout, QWidget, QMainWindow
import pyqtgraph as pg
import sys

class ChartWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("双Y轴组合图表")
        self.resize(1200, 800)
        
        # 创建中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建布局
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 创建绘图窗口
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground('w')
        self.plot_widget.setTitle("销售额与增长率", color="k", size="16pt")
        self.plot_widget.setLabel('left', '销售额 (万元)', color='#0078D4')
        self.plot_widget.setLabel('bottom', '月份', color='black')
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)
        
        # 添加柱状图（销售额）
        x_bar = [1, 2, 3, 4, 5, 6]
        y_bar = [100, 150, 130, 180, 220, 200]
        bargraph = pg.BarGraphItem(
            x=x_bar, 
            height=y_bar, 
            width=0.6, 
            brush='#0078D4',
            name='销售额'
        )
        self.plot_widget.addItem(bargraph)
        
        # 创建第二个Y轴（右侧）
        view_box2 = pg.ViewBox()
        self.plot_widget.scene().addItem(view_box2)
        self.plot_widget.getAxis('right').linkToView(view_box2)
        view_box2.setXLink(self.plot_widget)
        self.plot_widget.getAxis('right').setLabel('增长率 (%)', color='#E74856')
        self.plot_widget.showAxis('right')
        
        # 添加折线图到第二个Y轴（增长率）
        x_line = [1, 2, 3, 4, 5, 6]
        y_line = [0, 50, -13, 38, 22, -9]  # 增长率百分比
        pen = pg.mkPen(color='#E74856', width=3)
        line = pg.PlotCurveItem(
            x_line, 
            y_line, 
            pen=pen,
            name='增长率'
        )
        scatter = pg.ScatterPlotItem(
            x_line, 
            y_line, 
            size=10, 
            brush='#E74856'
        )
        view_box2.addItem(line)
        view_box2.addItem(scatter)
        
        # 更新视图函数
        def updateViews():
            view_box2.setGeometry(self.plot_widget.getViewBox().sceneBoundingRect())
            view_box2.linkedViewChanged(self.plot_widget.getViewBox(), view_box2.XAxis)
        
        updateViews()
        self.plot_widget.getViewBox().sigResized.connect(updateViews)
        
        # 添加图例
        self.plot_widget.addLegend()
        
        # 设置X轴刻度
        x_labels = [(1, '1月'), (2, '2月'), (3, '3月'), 
                    (4, '4月'), (5, '5月'), (6, '6月')]
        x_axis = self.plot_widget.getAxis('bottom')
        x_axis.setTicks([x_labels])
        
        layout.addWidget(self.plot_widget)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ChartWindow()
    window.show()
    sys.exit(app.exec())