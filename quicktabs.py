"""
PyQt based Tabs with webpages popup.

Left/Right/Space/Tab keys can be used to switch tabs. Other keys close the app.
Mouse can also be used to navigate webpages, but a click outside of the app
window closes the app.
There is also a timer (default 60s) closing the app, which is reset when a key
is pressed.

Application always opens up in the middle of the screen and has no close button
or window frame, hence it can be close only by the above described events.

Each tab should have an HTML code, tab name and a size multiplier
"""

from PyQt4.QtGui import QTabWidget, QApplication
from PyQt4.QtWebKit import QWebView, QWebPage
from PyQt4.QtCore import Qt, QSize, QPoint, QTimer


class QuickTabs(QTabWidget):

    """
    Popup window with tabs showing webpages.

    Closes on loosing focus or any keybord action.
    """

    def __init__(self, **kwargs):
        """
        Initialize popup.

        Make sure it closes on loosing focus and keybord actions.
        """
        super(QuickTabs, self).__init__(**kwargs)
        from sys import platform
        if "linux" in platform:
            self.setWindowFlags(Qt.FramelessWindowHint | Qt.Popup)
        elif "darwin" in platform:
            self.setWindowFlags(Qt.FramelessWindowHint)
        elif "win" in platform:
            self.setWindowFlags(Qt.FramelessWindowHint | Qt.Popup)
        self.setAttribute(Qt.WA_QuitOnClose)
        self.timeout = None

    def addTabs(self, tabs):
        """
        Add tabs to the popup.

        Each tab is given as a tuple (html, name, resize). The last parameter
        indicates if the text should be rescaled.

        Tabs should not grab focus for main window to close on loosing focus.
        """
        for html, name, resize in tabs:
            tab = QWebView()
            tab.setFocusPolicy(Qt.NoFocus)
            if resize != 1:
                tab.setTextSizeMultiplier(resize)
                tab.linkClicked.connect(self.unscale)
            self.addTab(tab, name)
            tab.setHtml(html)
            if resize != 1:
                tab.page().setLinkDelegationPolicy(QWebPage.DelegateAllLinks)
        tab.parent().setFocusPolicy(Qt.NoFocus)

    def keyPressEvent(self, e):
        """
        Close window on most keypresses.

        Except for arrows, Tab, Backspace and Space for tab navigation.
        """
        key = e.key()
        if key in (Qt.Key_Right, Qt.Key_Tab, Qt.Key_Space):
            self.setCurrentIndex(self.currentIndex()+1)
        elif key in (Qt.Key_Left, Qt.Key_Backspace, Qt.Key_Delete):
            self.setCurrentIndex(self.currentIndex()-1)
        else:
            self.close()
        # reset timer
        if self.timeout:
            self.timer.setInterval(self.timeout * 1000)

    def focusOutEvent(self, e):
        """ Close window on any keypress. """
        self.close()

    def unscale(self, url):
        """ Remove scaling from a tab. """
        self.currentWidget().load(url)
        self.currentWidget().setTextSizeMultiplier(1)

    @classmethod
    def App(cls, width, height, timeout=60):
        """ Return application and created window. """
        app = QApplication([])
        win = QuickTabs()
        win.resize(QSize(width, height))
        rect = QApplication.desktop().screenGeometry()
        x = (rect.width() - win.width()) / 2
        y = (rect.height() - win.height()) / 2
        win.move(QPoint(x, y))
        win.show()
        win.raise_()
        if timeout:
            timer = QTimer()
            timer.start(timeout * 1000)
            timer.timeout.connect(win.close)
            win.timer = timer
        win.timeout = timeout
        return app, win
