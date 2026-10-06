from __future__ import annotations

from typing import Any


def _checker(painter: Any, width: int, height: int) -> None:
    from PySide6.QtGui import QColor

    size = 12
    for y in range(0, height, size):
        for x in range(0, width, size):
            color = QColor("#F8FAFC") if (x // size + y // size) % 2 == 0 else QColor("#E8EEF5")
            painter.fillRect(x, y, size, size, color)


def asset_pixmap(subject: str, width: int = 150, height: int = 86) -> Any:
    from PySide6.QtCore import QPointF, QRectF, Qt
    from PySide6.QtGui import QColor, QPainter, QPen, QPixmap, QPolygonF

    pixmap = QPixmap(width, height)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    _checker(painter, width, height)

    cx = width / 2
    cy = height / 2 + 5
    key = subject.lower()
    painter.setPen(QPen(QColor("#29445E"), 2))

    if key == "pohon":
        painter.fillRect(QRectF(cx - 5, cy - 4, 10, 29), QColor("#8B5E3C"))
        painter.setBrush(QColor("#45A764"))
        for dx, dy, rx, ry in [(-22, -10, 23, 17), (0, -23, 28, 21), (23, -9, 22, 17)]:
            painter.drawEllipse(QPointF(cx + dx, cy + dy), rx, ry)
    elif key == "rumah":
        painter.setBrush(QColor("#FFF0CF"))
        painter.drawRoundedRect(QRectF(cx - 38, cy - 15, 76, 42), 4, 4)
        painter.setBrush(QColor("#D95C4F"))
        painter.drawPolygon(
            QPolygonF(
                [QPointF(cx - 45, cy - 15), QPointF(cx, cy - 44), QPointF(cx + 45, cy - 15)]
            )
        )
        painter.fillRect(QRectF(cx - 7, cy + 3, 14, 24), QColor("#704A34"))
        painter.fillRect(QRectF(cx - 28, cy - 4, 16, 13), QColor("#9DD6F5"))
        painter.fillRect(QRectF(cx + 12, cy - 4, 16, 13), QColor("#9DD6F5"))
    elif key == "awan":
        painter.setPen(QPen(QColor("#B5C1CD"), 1))
        painter.setBrush(QColor("#F3F7FB"))
        for dx, dy, rx, ry in [(-24, 4, 28, 17), (0, -8, 34, 23), (26, 5, 28, 17)]:
            painter.drawEllipse(QPointF(cx + dx, cy + dy), rx, ry)
    elif key == "mobil":
        painter.setBrush(QColor("#E34E46"))
        painter.drawRoundedRect(QRectF(cx - 42, cy - 8, 84, 24), 8, 8)
        painter.drawRoundedRect(QRectF(cx - 22, cy - 27, 47, 20), 7, 7)
        painter.setBrush(QColor("#263238"))
        painter.drawEllipse(QPointF(cx - 27, cy + 16), 8, 8)
        painter.drawEllipse(QPointF(cx + 28, cy + 16), 8, 8)
    elif key in {"anak", "tokoh"}:
        shirt = QColor("#2D7FE7") if key == "anak" else QColor("#E26D8C")
        painter.setBrush(QColor("#F4C6A5"))
        painter.drawEllipse(QPointF(cx, cy - 24), 15, 15)
        painter.setBrush(QColor("#4C382C"))
        painter.drawPie(QRectF(cx - 16, cy - 39, 32, 25), 0, 180 * 16)
        painter.setBrush(shirt)
        painter.drawRoundedRect(QRectF(cx - 17, cy - 8, 34, 34), 7, 7)
    elif key == "matahari":
        painter.setPen(QPen(QColor("#F1B51C"), 3))
        for x1, y1, x2, y2 in [
            (0, -37, 0, -25),
            (0, 37, 0, 25),
            (-37, 0, -25, 0),
            (37, 0, 25, 0),
            (-27, -27, -18, -18),
            (27, -27, 18, -18),
            (-27, 27, -18, 18),
            (27, 27, 18, 18),
        ]:
            painter.drawLine(QPointF(cx + x1, cy + y1), QPointF(cx + x2, cy + y2))
        painter.setBrush(QColor("#FFD447"))
        painter.drawEllipse(QPointF(cx, cy), 21, 21)
    elif key == "gunung":
        painter.setBrush(QColor("#587C9E"))
        painter.drawPolygon(
            QPolygonF([QPointF(cx - 58, cy + 28), QPointF(cx - 10, cy - 38), QPointF(cx + 28, cy + 28)])
        )
        painter.setBrush(QColor("#7599B6"))
        painter.drawPolygon(
            QPolygonF([QPointF(cx - 14, cy + 28), QPointF(cx + 27, cy - 28), QPointF(cx + 61, cy + 28)])
        )
        painter.setBrush(QColor("#F7FAFC"))
        painter.drawPolygon(
            QPolygonF([QPointF(cx - 23, cy - 20), QPointF(cx - 10, cy - 38), QPointF(cx + 3, cy - 20)])
        )
    elif key == "papan":
        painter.fillRect(QRectF(cx - 5, cy - 2, 10, 34), QColor("#8B5E3C"))
        painter.setBrush(QColor("#A97449"))
        painter.drawRoundedRect(QRectF(cx - 45, cy - 28, 90, 30), 3, 3)
    elif key in {"kucing", "anjing"}:
        _draw_animal(painter, cx, cy - 2, 0.72, "cat" if key == "kucing" else "dog")
    elif key == "burung":
        painter.setBrush(QColor("#4E7FA9"))
        painter.drawEllipse(QPointF(cx, cy), 27, 16)
        painter.drawEllipse(QPointF(cx + 18, cy - 9), 12, 12)
        painter.setBrush(QColor("#F4A340"))
        painter.drawPolygon(
            QPolygonF([QPointF(cx + 30, cy - 8), QPointF(cx + 42, cy - 4), QPointF(cx + 30, cy)])
        )
    elif key == "semak":
        painter.setBrush(QColor("#4FAE68"))
        for dx, dy, r in [(-30, 8, 22), (-10, -4, 25), (15, 0, 25), (33, 11, 19)]:
            painter.drawEllipse(QPointF(cx + dx, cy + dy), r, r * 0.7)
    elif key == "pagar":
        painter.setPen(QPen(QColor("#8B5E3C"), 5))
        for dx in [-42, -21, 0, 21, 42]:
            painter.drawLine(QPointF(cx + dx, cy - 25), QPointF(cx + dx, cy + 28))
        painter.drawLine(QPointF(cx - 50, cy - 5), QPointF(cx + 50, cy - 5))
        painter.drawLine(QPointF(cx - 50, cy + 15), QPointF(cx + 50, cy + 15))
    elif key == "lampu":
        painter.setPen(QPen(QColor("#243648"), 4))
        painter.drawLine(QPointF(cx, cy - 24), QPointF(cx, cy + 32))
        painter.setBrush(QColor("#243648"))
        painter.drawRoundedRect(QRectF(cx - 13, cy - 39, 26, 19), 4, 4)
        painter.setBrush(QColor("#FFE8A3"))
        painter.drawRect(QRectF(cx - 7, cy - 34, 14, 10))

    painter.end()
    return pixmap


def _draw_village(painter: Any, width: int, height: int) -> None:
    from PySide6.QtCore import QPointF, QRectF, Qt
    from PySide6.QtGui import QColor, QLinearGradient, QPen, QPolygonF

    gradient = QLinearGradient(0, 0, 0, height)
    gradient.setColorAt(0.0, QColor("#A7DAFF"))
    gradient.setColorAt(0.58, QColor("#EAF6D6"))
    gradient.setColorAt(1.0, QColor("#A6D27E"))
    painter.fillRect(0, 0, width, height, gradient)

    painter.setPen(QPen(QColor("#7697AC"), 2))
    painter.setBrush(QColor("#6E91AA"))
    painter.drawPolygon(
        QPolygonF([QPointF(0, height * 0.55), QPointF(width * 0.22, height * 0.20), QPointF(width * 0.39, height * 0.55)])
    )
    painter.setBrush(QColor("#87A9BE"))
    painter.drawPolygon(
        QPolygonF([QPointF(width * 0.25, height * 0.55), QPointF(width * 0.48, height * 0.27), QPointF(width * 0.68, height * 0.55)])
    )
    painter.setBrush(QColor("#F7FAFC"))
    painter.drawPolygon(
        QPolygonF([QPointF(width * 0.18, height * 0.27), QPointF(width * 0.22, height * 0.20), QPointF(width * 0.26, height * 0.28)])
    )

    painter.setPen(QPen(QColor("#4F6F43"), 2))
    painter.setBrush(QColor("#F8E7C7"))
    painter.drawRect(QRectF(width * 0.08, height * 0.48, width * 0.22, height * 0.22))
    painter.setBrush(QColor("#C65D49"))
    painter.drawPolygon(
        QPolygonF([QPointF(width * 0.05, height * 0.48), QPointF(width * 0.19, height * 0.37), QPointF(width * 0.33, height * 0.48)])
    )
    painter.fillRect(QRectF(width * 0.13, height * 0.57, width * 0.04, height * 0.13), QColor("#8A5B43"))
    painter.fillRect(QRectF(width * 0.21, height * 0.55, width * 0.05, height * 0.06), QColor("#9ED4F2"))

    painter.setBrush(QColor("#5A9C55"))
    for x, y, r in [(0.67, 0.47, 0.09), (0.76, 0.42, 0.10), (0.85, 0.50, 0.08)]:
        painter.drawEllipse(QPointF(width * x, height * y), width * r, height * r * 0.7)
    painter.fillRect(QRectF(width * 0.755, height * 0.48, width * 0.025, height * 0.30), QColor("#7A543B"))

    painter.setPen(QPen(QColor("#B88B5A"), 5))
    fence_y = height * 0.72
    for x in range(int(width * 0.05), int(width * 0.94), int(width * 0.05)):
        painter.drawLine(QPointF(x, fence_y - 24), QPointF(x, fence_y + 28))
    painter.drawLine(QPointF(width * 0.04, fence_y - 4), QPointF(width * 0.95, fence_y - 4))
    painter.drawLine(QPointF(width * 0.04, fence_y + 16), QPointF(width * 0.95, fence_y + 16))

    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QColor("#7FC45B"))
    painter.drawRect(QRectF(0, height * 0.78, width, height * 0.22))
    painter.setBrush(QColor("#DBCDB5"))
    painter.drawPolygon(
        QPolygonF([QPointF(width * 0.42, height), QPointF(width * 0.51, height * 0.72), QPointF(width * 0.60, height)])
    )


def _draw_animal(
    painter: Any,
    x: float,
    y: float,
    scale: float,
    kind: str,
    selected: bool = False,
    label: str = "",
) -> None:
    from PySide6.QtCore import QPointF, QRectF, Qt
    from PySide6.QtGui import QColor, QPen, QPolygonF

    fur = QColor("#F0A04B") if kind == "cat" else QColor("#B87342")
    painter.setPen(QPen(QColor("#5B3A2A"), max(1.0, 2.0 * scale)))
    painter.setBrush(fur)
    painter.drawEllipse(QPointF(x, y + 34 * scale), 38 * scale, 30 * scale)
    painter.drawEllipse(QPointF(x, y - 10 * scale), 31 * scale, 28 * scale)
    if kind == "cat":
        painter.drawPolygon(
            QPolygonF(
                [
                    QPointF(x - 26 * scale, y - 22 * scale),
                    QPointF(x - 16 * scale, y - 50 * scale),
                    QPointF(x - 6 * scale, y - 23 * scale),
                ]
            )
        )
        painter.drawPolygon(
            QPolygonF(
                [
                    QPointF(x + 26 * scale, y - 22 * scale),
                    QPointF(x + 16 * scale, y - 50 * scale),
                    QPointF(x + 6 * scale, y - 23 * scale),
                ]
            )
        )
    else:
        painter.setBrush(QColor("#6B3F2B"))
        painter.drawEllipse(QPointF(x - 31 * scale, y - 10 * scale), 11 * scale, 23 * scale)
        painter.drawEllipse(QPointF(x + 31 * scale, y - 10 * scale), 11 * scale, 23 * scale)
        painter.setBrush(fur)

    painter.setBrush(QColor("#FFFFFF"))
    painter.drawEllipse(QPointF(x - 10 * scale, y - 10 * scale), 7 * scale, 8 * scale)
    painter.drawEllipse(QPointF(x + 10 * scale, y - 10 * scale), 7 * scale, 8 * scale)
    painter.setBrush(QColor("#111827"))
    painter.drawEllipse(QPointF(x - 10 * scale, y - 9 * scale), 2.5 * scale, 3.5 * scale)
    painter.drawEllipse(QPointF(x + 10 * scale, y - 9 * scale), 2.5 * scale, 3.5 * scale)
    painter.drawEllipse(QPointF(x, y + 2 * scale), 3.2 * scale, 3 * scale)

    if selected:
        painter.setPen(QPen(QColor("#2563EB"), 3))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRect(QRectF(x - 58 * scale, y - 62 * scale, 116 * scale, 134 * scale))
        if label:
            painter.fillRect(
                QRectF(x - 58 * scale, y - 82 * scale, 58 * scale, 20 * scale),
                QColor("#2563EB"),
            )
            painter.setPen(QColor("#FFFFFF"))
            painter.drawText(
                QRectF(x - 56 * scale, y - 80 * scale, 54 * scale, 16 * scale),
                int(Qt.AlignmentFlag.AlignCenter),
                label,
            )


def scene_pixmap(mode: str, width: int = 1280, height: int = 720) -> Any:
    from PySide6.QtCore import QPointF, QRectF, Qt
    from PySide6.QtGui import QColor, QFont, QPainter, QPen, QPixmap, QPolygonF

    pixmap = QPixmap(width, height)
    pixmap.fill(QColor("#FFFFFF"))
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    if mode == "overview":
        painter.fillRect(0, 0, width, height, QColor("#F6F2E8"))
        font = QFont("Segoe UI", int(height * 0.055))
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(QColor("#143E61"))
        painter.drawText(
            QRectF(width * 0.07, height * 0.25, width * 0.38, height * 0.10),
            int(Qt.AlignmentFlag.AlignLeft),
            "INDONESIA",
        )
        red_font = QFont("Segoe UI", int(height * 0.040))
        red_font.setBold(True)
        painter.setFont(red_font)
        painter.setPen(QColor("#C9272C"))
        painter.drawText(
            QRectF(width * 0.07, height * 0.35, width * 0.40, height * 0.08),
            int(Qt.AlignmentFlag.AlignLeft),
            "NEGERI KEPULAUAN",
        )
        body_font = QFont("Segoe UI", int(height * 0.022))
        body_font.setBold(True)
        painter.setFont(body_font)
        painter.setPen(QColor("#143E61"))
        painter.drawText(
            QRectF(width * 0.07, height * 0.48, width * 0.38, height * 0.14),
            int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop),
            "RIBUAN PULAU, SATU SEMANGAT\nUNTUK MASA DEPAN YANG LEBIH BAIK",
        )
        painter.fillRect(QRectF(width * 0.07, height * 0.66, width * 0.08, 8), QColor("#C9272C"))

        painter.setPen(Qt.PenStyle.NoPen)
        colors = ["#2B8C4B", "#4FAE68", "#2E9EAA", "#72C7D9"]
        blobs = [
            (0.59, 0.30, 0.10, 0.12),
            (0.67, 0.25, 0.13, 0.08),
            (0.75, 0.36, 0.10, 0.11),
            (0.62, 0.46, 0.11, 0.09),
            (0.76, 0.50, 0.14, 0.08),
            (0.86, 0.42, 0.07, 0.07),
            (0.70, 0.61, 0.09, 0.07),
            (0.84, 0.60, 0.08, 0.05),
        ]
        for index, (x, y, blob_w, blob_h) in enumerate(blobs):
            painter.setBrush(QColor(colors[index % len(colors)]))
            painter.drawEllipse(QRectF(width * x, height * y, width * blob_w, height * blob_h))
        painter.setBrush(QColor("#587C9E"))
        painter.drawPolygon(
            QPolygonF(
                [
                    QPointF(width * 0.62, height * 0.37),
                    QPointF(width * 0.68, height * 0.18),
                    QPointF(width * 0.74, height * 0.37),
                ]
            )
        )
        painter.setBrush(QColor("#F7FAFC"))
        painter.drawPolygon(
            QPolygonF(
                [
                    QPointF(width * 0.655, height * 0.25),
                    QPointF(width * 0.68, height * 0.18),
                    QPointF(width * 0.705, height * 0.25),
                ]
            )
        )
        painter.setPen(QPen(QColor("#6B4F3B"), 5))
        for index in range(4):
            y = height * (0.32 + index * 0.04)
            painter.drawLine(QPointF(width * 0.88, y), QPointF(width * (0.93 - index * 0.01), y))
        painter.drawLine(QPointF(width * 0.905, height * 0.30), QPointF(width * 0.905, height * 0.50))
    else:
        _draw_village(painter, width, height)
        if mode == "single":
            _draw_animal(painter, width * 0.56, height * 0.62, 1.65, "cat", selected=True, label="A014")
        elif mode == "double":
            _draw_animal(painter, width * 0.46, height * 0.63, 1.38, "cat", selected=True, label="A032")
            _draw_animal(painter, width * 0.65, height * 0.63, 1.38, "dog", selected=True, label="A033")
        elif mode == "subtitle":
            _draw_animal(painter, width * 0.56, height * 0.62, 1.35, "cat")
            painter.fillRect(
                QRectF(width * 0.24, height * 0.76, width * 0.52, height * 0.14),
                QColor(15, 23, 42, 215),
            )
            painter.setPen(QColor("#FFFFFF"))
            font = QFont("Segoe UI", int(height * 0.026))
            font.setBold(True)
            painter.setFont(font)
            painter.drawText(
                QRectF(width * 0.26, height * 0.775, width * 0.48, height * 0.11),
                int(Qt.AlignmentFlag.AlignCenter),
                "Pagi yang cerah di desa Bromo,\nseekor kucing kecil berjalan di taman.",
            )

    painter.end()
    return pixmap


def project_thumb_pixmap(index: int, width: int = 112, height: int = 58) -> Any:
    from PySide6.QtCore import QPointF, QRectF, Qt
    from PySide6.QtGui import QColor, QLinearGradient, QPainter, QPixmap, QPolygonF

    pixmap = QPixmap(width, height)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    if index == 0:
        gradient = QLinearGradient(0, 0, 0, height)
        gradient.setColorAt(0, QColor("#8CC9F4"))
        gradient.setColorAt(1, QColor("#D7E8C1"))
        painter.fillRect(0, 0, width, height, gradient)
        painter.setBrush(QColor("#667F94"))
        painter.drawPolygon(QPolygonF([QPointF(6, 50), QPointF(48, 9), QPointF(92, 50)]))
        painter.setBrush(QColor("#F7FAFC"))
        painter.drawPolygon(QPolygonF([QPointF(38, 20), QPointF(48, 9), QPointF(58, 20)]))
    elif index == 1:
        painter.fillRect(0, 0, width, height, QColor("#E8D8C6"))
        painter.fillRect(QRectF(10, 12, 36, 34), QColor("#B7845A"))
        painter.setBrush(QColor("#4FAE68"))
        painter.drawEllipse(QPointF(73, 23), 16, 20)
        painter.fillRect(QRectF(70, 31, 6, 17), QColor("#76543B"))
        painter.fillRect(QRectF(88, 18, 11, 31), QColor("#F4C95D"))
    elif index == 2:
        gradient = QLinearGradient(0, 0, width, height)
        gradient.setColorAt(0, QColor("#3F4F87"))
        gradient.setColorAt(1, QColor("#E06A5E"))
        painter.fillRect(0, 0, width, height, gradient)
        painter.setBrush(QColor("#1F2937"))
        for x in [14, 31, 49, 68, 87]:
            painter.drawEllipse(QPointF(x, 42), 7, 12)
    else:
        painter.fillRect(0, 0, width, height, QColor("#7ED1E6"))
        painter.setBrush(QColor("#5BA968"))
        painter.drawEllipse(QPointF(29, 28), 30, 24)
        painter.drawEllipse(QPointF(77, 34), 34, 18)
        painter.setBrush(QColor("#F6E5B3"))
        painter.drawPolygon(QPolygonF([QPointF(25, 56), QPointF(52, 31), QPointF(75, 56)]))

    painter.end()
    return pixmap
