import sys, os; sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + '/..'))
import sys, datetime
from PyQt5.QtWidgets import QApplication, QWidget, QTextEdit, QSizePolicy, QGraphicsBlurEffect, QHBoxLayout, QLabel, QVBoxLayout, QStackedLayout, QPushButton
from PyQt5.QtCore import Qt, QRect, QThread, pyqtSignal, QParallelAnimationGroup, QPropertyAnimation, QEasingCurve, QTimer
from PyQt5.QtGui import QColor, QPainter, QBrush, QFont, QPixmap
from conversation_core import NagaConversation
import os
BG_ALPHA=0.7 # 聊天背景透明度40%
USER_NAME=os.getenv('COMPUTERNAME')or os.getenv('USERNAME')or'用户' # 自动识别电脑名
MAC_BTN_SIZE=36 # mac圆按钮直径扩大1.5倍
MAC_BTN_MARGIN=16 # 右侧边距
MAC_BTN_GAP=12 # 按钮间距
ANIMATION_DURATION = 300  # 动画时长统一配置

class TitleBar(QWidget):
    def __init__(s, text, parent=None):
        super().__init__(parent)
        s.text = text
        s.setFixedHeight(100)
        s.setAttribute(Qt.WA_TranslucentBackground)
        s._offset = None
        # mac风格按钮
        for i,(txt,color,hover,cb) in enumerate([
            ('-','#FFBD2E','#ffe084',lambda:s.parent().showMinimized()),
            ('×','#FF5F57','#ff8783',lambda:s.parent().close())]):
            btn=QPushButton(txt,s)
            btn.setGeometry(s.width()-MAC_BTN_MARGIN-MAC_BTN_SIZE*(2-i)-MAC_BTN_GAP*(1-i),36,MAC_BTN_SIZE,MAC_BTN_SIZE)
            btn.setStyleSheet(f"QPushButton{{background:{color};border:none;border-radius:{MAC_BTN_SIZE//2}px;color:#fff;font:18pt;}}QPushButton:hover{{background:{hover};}}")
            btn.clicked.connect(cb)
            setattr(s,f'btn_{"min close".split()[i]}',btn)
    def mousePressEvent(s, e):
        if e.button()==Qt.LeftButton: s._offset = e.globalPos()-s.parent().frameGeometry().topLeft()
    def mouseMoveEvent(s, e):
        if s._offset and e.buttons()&Qt.LeftButton:
            s.parent().move(e.globalPos()-s._offset)
    def mouseReleaseEvent(s,e):s._offset=None
    def paintEvent(s, e):
        qp = QPainter(s)
        qp.setRenderHint(QPainter.Antialiasing)
        w, h = s.width(), s.height()
        qp.setPen(QColor(255,255,255,180))
        qp.drawLine(0, 2, w, 2)
        qp.drawLine(0, h-3, w, h-3)
        font = QFont("Consolas", max(10, (h-40)//2), QFont.Bold)
        qp.setFont(font)
        rect = QRect(0, 20, w, h-40)
        for dx,dy in [(-1,0),(1,0),(0,-1),(0,1)]:
            qp.setPen(QColor(0,0,0))
            qp.drawText(rect.translated(dx,dy), Qt.AlignCenter, s.text)
        qp.setPen(QColor(255,255,255))
        qp.drawText(rect, Qt.AlignCenter, s.text)
    def resizeEvent(s,e):
        x=s.width()-MAC_BTN_MARGIN
        for i,btn in enumerate([s.btn_min,s.btn_close]):btn.move(x-MAC_BTN_SIZE*(2-i)-MAC_BTN_GAP*(1-i),36)

class Worker(QThread):
    finished=pyqtSignal(str)
    def __init__(s, naga, u):super().__init__();s.naga=naga;s.u=u
    def run(s):
        import asyncio
        async def collect():
            result = []
            async for chunk in s.naga.process(s.u):
                # 如果chunk是元组，取内容，否则直接用
                if isinstance(chunk, tuple) and len(chunk) == 2:
                    _, content = chunk
                else:
                    content = chunk
                result.append(str(content))
            return ''.join(result)
        a = asyncio.run(collect())
        s.finished.emit(a)

class ChatWindow(QWidget):
    def __init__(s):
        super().__init__()
        s.resize(1800, 1400)
        s.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        s.setAttribute(Qt.WA_TranslucentBackground)
        s._offset = None
        fontfam,fontbig,fontsize='Lucida Console',16,16
        main=QHBoxLayout(s);main.setContentsMargins(0,100,0,0);main.setSpacing(0)
        chat_area=QWidget(s)
        vlay=QVBoxLayout(chat_area);vlay.setContentsMargins(0,0,0,0);vlay.setSpacing(0)
        s.text = QTextEdit(chat_area)
        s.text.setReadOnly(True)
        s.text.setStyleSheet(f"background:rgba(17,17,17,{int(BG_ALPHA*255)});color:#fff;border-radius:24px;border:none;font:{fontbig}pt '{fontfam}';")
        vlay.addWidget(s.text,1)
        s.input_wrap=QWidget(chat_area)
        s.input_wrap.setFixedHeight(48)
        hlay=QHBoxLayout(s.input_wrap);hlay.setContentsMargins(0,0,0,0);hlay.setSpacing(0)
        s.prompt=QLabel('>',s.input_wrap)
        s.prompt.setStyleSheet(f"color:#fff;font:{fontsize}pt '{fontfam}';background:transparent;padding-right:8px;")
        hlay.addWidget(s.prompt)
        s.input = QTextEdit(s.input_wrap)
        s.input.setStyleSheet(f"background:rgba(17,17,17,{int(BG_ALPHA*255)});color:#fff;border-radius:24px;border:none;font:{fontsize}pt '{fontfam}';")
        s.input.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        s.input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        hlay.addWidget(s.input)
        vlay.addWidget(s.input_wrap,0)
        main.addWidget(chat_area,2)
        gap=QWidget(s);gap.setFixedWidth(30);gap.setStyleSheet("background:transparent;")
        main.addWidget(gap)
        # 侧栏
        s.side=QWidget(s);s.side.setStyleSheet(f"background:rgba(17,17,17,{int(BG_ALPHA*255)});border-radius:24px;")
        s.side.setMinimumWidth(400);s.side.setMaximumWidth(400) # 固定400像素
        s.side.enterEvent=lambda e:s.side.setStyleSheet("background:transparent;border-radius:24px;")
        s.side.leaveEvent=lambda e:s.side.setStyleSheet(f"background:rgba(17,17,17,{int(BG_ALPHA*255)});border-radius:24px;")
        stack=QStackedLayout(s.side);stack.setContentsMargins(0,0,0,0)
        s.img=QLabel(s.side)
        s.img.setSizePolicy(QSizePolicy.Ignored,QSizePolicy.Ignored)
        s.img.setAlignment(Qt.AlignCenter)
        s.img.setMinimumSize(1,1)
        s.img.setMaximumSize(16777215,16777215)
        s.img.setStyleSheet('background:transparent;')
        stack.addWidget(s.img)
        nick=QLabel("● 娜迦2.0",s.side)
        nick.setStyleSheet("color:#fff;font:18pt 'Consolas';background:rgba(0,0,0,0.5);padding:12px 0 12px 0;border-radius:12px;")
        nick.setAlignment(Qt.AlignHCenter|Qt.AlignTop)
        nick.setAttribute(Qt.WA_TransparentForMouseEvents)
        stack.addWidget(nick)
        main.addWidget(s.side,1)
        s.nick=nick
        s.naga=NagaConversation()
        s.worker=None
        s.full_img=0 # 立绘展开标志
        s.input.textChanged.connect(s.adjust_input_height)
        s.input.installEventFilter(s)
        s.setLayout(main)
        s.titlebar = TitleBar('NAGA AGENT', s)
        s.titlebar.setGeometry(0,0,s.width(),100)
        s.side.mousePressEvent=s.toggle_full_img # 侧栏点击切换立绘
    def resizeEvent(s, e):
        s.titlebar.setGeometry(0,0,s.width(),100)
        if hasattr(s,'img') and hasattr(s,'nick'):
            s.img.resize(s.img.parent().width(), s.img.parent().height())
            s.nick.resize(s.img.width(), 48) # 48为昵称高度，可自调
            s.nick.move(0,0)
            p=os.path.join(os.path.dirname(__file__),'standby.png')
            q=QPixmap(p)
            if os.path.exists(p) and not q.isNull():
                s.img.setPixmap(q.scaled(s.img.width(),s.img.height(),Qt.KeepAspectRatioByExpanding,Qt.SmoothTransformation))
    def adjust_input_height(s):
        doc = s.input.document()
        h = int(doc.size().height())+10
        s.input.setFixedHeight(min(max(48, h), 120))
        s.input_wrap.setFixedHeight(s.input.height())
        s.resizeEvent(None)
    def eventFilter(s, obj, event):
        if obj is s.input and event.type()==6:
            if event.key()==Qt.Key_Return and not (event.modifiers()&Qt.ShiftModifier):
                s.on_send();return True
        return False
    def add_user_message(s, name, content):
        # 支持多行换行显示，将\n替换为<br>，用富文本格式
        #s.text.setTextFormat(Qt.RichText) # ~~设置为富文本~~（冗余代码，启用会导致进程崩溃）
        content_html = str(content).replace('\n', '<br>')
        s.text.append(f"<span style='color:#fff;font-size:12pt;font-family:Lucida Console;'>{name}</span>")
        s.text.append(f"<span style='color:#fff;font-size:16pt;font-family:Lucida Console;'>{content_html}</span>")
    def on_send(s):
        u = s.input.toPlainText().strip()
        if u:
            s.add_user_message(USER_NAME, u)
            s.input.clear()
            if s.worker and s.worker.isRunning():return
            s.worker=Worker(s.naga,u)
            s.worker.finished.connect(lambda a:s.add_user_message("娜迦",a))
            s.worker.start()
    def toggle_full_img(s,e):
        s.full_img^=1  # 立绘展开标志切换
        target_width = 800 if s.full_img else 400  # 目标宽度
        group = QParallelAnimationGroup(s)  # 并行动画组
        # 侧栏宽度动画
        side_anim = QPropertyAnimation(s.side, b"minimumWidth", s)
        side_anim.setDuration(ANIMATION_DURATION)
        side_anim.setStartValue(s.side.width())
        side_anim.setEndValue(target_width)
        side_anim.setEasingCurve(QEasingCurve.InOutQuad)
        group.addAnimation(side_anim)
        side_anim2 = QPropertyAnimation(s.side, b"maximumWidth", s)
        side_anim2.setDuration(ANIMATION_DURATION)
        side_anim2.setStartValue(s.side.width())
        side_anim2.setEndValue(target_width)
        side_anim2.setEasingCurve(QEasingCurve.InOutQuad)
        group.addAnimation(side_anim2)
        # 聊天区域宽度动画
        chat_area = s.side.parent().findChild(QWidget)
        if hasattr(s, 'chat_area'):
            chat_area = s.chat_area
        else:
            chat_area = s.side.parent().children()[1]
        chat_anim = QPropertyAnimation(chat_area, b"minimumWidth", s)
        chat_anim.setDuration(ANIMATION_DURATION)
        chat_anim.setStartValue(chat_area.width())
        chat_anim.setEndValue(1800 - target_width - 30)
        chat_anim.setEasingCurve(QEasingCurve.InOutQuad)
        group.addAnimation(chat_anim)
        chat_anim2 = QPropertyAnimation(chat_area, b"maximumWidth", s)
        chat_anim2.setDuration(ANIMATION_DURATION)
        chat_anim2.setStartValue(chat_area.width())
        chat_anim2.setEndValue(1800 - target_width - 30)
        chat_anim2.setEasingCurve(QEasingCurve.InOutQuad)
        group.addAnimation(chat_anim2)
        # 输入框高度动画
        input_hide_anim = QPropertyAnimation(s.input_wrap, b"maximumHeight", s)
        input_hide_anim.setDuration(ANIMATION_DURATION)
        input_hide_anim.setStartValue(s.input_wrap.height())
        input_hide_anim.setEndValue(0 if s.full_img else 48)
        input_hide_anim.setEasingCurve(QEasingCurve.InOutQuad)
        group.addAnimation(input_hide_anim)
        # 输入框透明度动画
        input_opacity_anim = QPropertyAnimation(s.input, b"windowOpacity", s)
        input_opacity_anim.setDuration(ANIMATION_DURATION)
        input_opacity_anim.setStartValue(1.0)
        input_opacity_anim.setEndValue(0.0 if s.full_img else 1.0)
        input_opacity_anim.setEasingCurve(QEasingCurve.InOutQuad)
        group.addAnimation(input_opacity_anim)
        # 动画结束后处理显示/隐藏和焦点
        group.finished.connect(lambda: None)
        # 侧栏样式
        if s.full_img:
            s.side.setStyleSheet("background:transparent;border-radius:24px;")
            s.side.enterEvent = s.side.leaveEvent = lambda e: None
        else:
            s.side.setStyleSheet(f"background:rgba(17,17,17,{int(BG_ALPHA*255)});border-radius:24px;")
            s.side.enterEvent = lambda e: s.side.setStyleSheet("background:transparent;border-radius:24px;")
            s.side.leaveEvent = lambda e: s.side.setStyleSheet(f"background:rgba(17,17,17,{int(BG_ALPHA*255)});border-radius:24px;")
        # 立绘图片同步缩放
        p = os.path.join(os.path.dirname(__file__), 'standby.png')
        q = QPixmap(p)
        s.img.setPixmap(q.scaled(target_width, s.side.height(), Qt.KeepAspectRatio if s.full_img else Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation))
        group.start()

if __name__=="__main__":
    app = QApplication(sys.argv)
    win = ChatWindow()
    win.show()
    sys.exit(app.exec_())
