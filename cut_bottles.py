# -*- coding: utf-8 -*-
"""EKB SHIELD — вырезание бутылок из `resourcepack/новые/*.jpg` в текстуры пака.

Исходники — jpg-рендеры пиксель-арта, у которых прозрачность запечена в
картинку «шахматкой». Просто выбросить два цвета клеток нельзя: у половины
бутылок стекло и этикетки ровно такие же белые, как светлая клетка.

Поэтому фон опознаётся по локальной статистике окна ~2 клеток:
у шахматки СКО равно половине контраста клеток, а среднее лежит ровно
посередине между их цветами; у плоской белой этикетки СКО около нуля.
Дальше — заливка от рамки кадра (внутрь бутылки она не проходит, мешает
тёмный контур) и чистка остатков полупрозрачного водяного знака.

Фазу сетки не подгоняем: у этих картинок период по X и по Y разный и
у каждого файла свой, а локальная статистика от фазы не зависит.

Запуск:  py -3 cut_bottles.py [--out КАТАЛОГ]
"""
import argparse
import glob
import os

import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, "resourcepack", "новые")
DST = os.path.join(ROOT, "resourcepack", "assets", "shield", "textures", "item")

# номер исходного фото -> имя текстуры (см. CustomModelData в plugins/BreweryX/recipes.yml)
BOTTLES = {
    1:  "vodka_absolut",        # 1006
    2:  "jagermeister_bottle",  # 1001
    3:  "rum_bottle",           # 1004
    4:  "samogon_jar",          # 1005
    5:  "beer_bottle",          # 1002
    6:  "vodka_passionfruit",   # 1011
    7:  "vodka_mojito",         # 1012
    8:  "whiskey_bottle",       # 1008
    9:  "tequila_bottle",       # 1003
    10: "jagermeister_orange",  # 1009
    11: "samogon_green",        # 1013
    12: "jagermeister_dark",    # 1010
    13: "vodka_plain",          # 1007
}

WINDOW = 27        # окно локальной статистики, ~2 клетки шахматки
SIZE = 64          # размер текстуры
INNER = 60         # сама бутылка, остальное — поля


def local_stats(a, k):
    """локальные среднее и СКО в окне k x k (края — отражением)"""
    o = k // 2
    ap = np.pad(a, ((o, k - 1 - o), (o, k - 1 - o)), mode="reflect")

    def wsum(x):
        c = np.cumsum(np.cumsum(x, axis=0, dtype=np.float64), axis=1)
        c = np.pad(c, ((1, 0), (1, 0)), mode="constant")
        h, w = x.shape[0] - k + 1, x.shape[1] - k + 1
        return c[k:k + h, k:k + w] - c[0:h, k:k + w] - c[k:k + h, 0:w] + c[0:h, 0:w]

    n = float(k * k)
    m = wsum(ap) / n
    return m, np.sqrt(np.maximum(wsum(ap * ap) / n - m * m, 0.0))


def cell_colors(gray, neutral):
    """цвета тёмной и светлой клеток шахматки по самому чистому углу кадра"""
    h, w = gray.shape
    s = 90
    best = None
    for y, x in ((0, 0), (0, w - s), (h - s, 0), (h - s, w - s)):
        nb = neutral[y:y + s, x:x + s]
        if nb.mean() < 0.9:
            continue
        lo, hi = np.percentile(gray[y:y + s, x:x + s], [8, 92])
        if not (18 < hi - lo < 70):
            continue
        if best is None or nb.mean() > best[0]:
            best = (float(nb.mean()), float(lo), float(hi))
    if best is None:
        lo, hi = np.percentile(gray[neutral], [10, 90])
        return float(lo), float(hi)
    return best[1], best[2]


def propagate(seed, allow, iters):
    """заливка seed по маске allow (4-связно)"""
    cur = seed & allow
    for _ in range(iters):
        n = cur.copy()
        n[1:, :] |= cur[:-1, :]
        n[:-1, :] |= cur[1:, :]
        n[:, 1:] |= cur[:, :-1]
        n[:, :-1] |= cur[:, 1:]
        n &= allow
        if n.sum() == cur.sum():
            return n
        cur = n
    return cur


def erode(m, n=1):
    for _ in range(n):
        e = m.copy()
        e[1:, :] &= m[:-1, :]
        e[:-1, :] &= m[1:, :]
        e[:, 1:] &= m[:, :-1]
        e[:, :-1] &= m[:, 1:]
        m = e
    return m


def label_largest(mask):
    """самая большая 4-связная область булевой маски"""
    lab = np.where(mask, np.arange(mask.size).reshape(mask.shape), -1)
    for _ in range(sum(mask.shape)):
        n = lab.copy()
        n[1:, :] = np.maximum(n[1:, :], lab[:-1, :])
        n[:-1, :] = np.maximum(n[:-1, :], lab[1:, :])
        n[:, 1:] = np.maximum(n[:, 1:], lab[:, :-1])
        n[:, :-1] = np.maximum(n[:, :-1], lab[:, 1:])
        n = np.where(mask, n, -1)
        if (n == lab).all():
            break
        lab = n
    ids, cnt = np.unique(lab[mask], return_counts=True)
    return mask & (lab == ids[int(np.argmax(cnt))])


def largest_blob(fg, k=2, er=2):
    """самая большая область в полном разрешении, через уменьшённую сетку.

    Перед разметкой область сужается, чтобы тонкие перемычки из остатков
    ореола не склеивали бутылку с мусором.
    """
    H, W = fg.shape
    core = erode(fg, er)
    h, w = H // k, W // k
    small = core[:h * k, :w * k].reshape(h, k, w, k).all(axis=(1, 3))
    if not small.any():
        return fg
    keep = label_largest(small)
    seed = np.zeros((H, W), bool)
    seed[:h * k, :w * k] = np.kron(keep, np.ones((k, k), bool))
    return propagate(seed & fg, fg, 2 * k + 2 * er + 2)


def keep_axis_runs(fg):
    """оставить только отрезки, проходящие через оси бутылки.

    Силуэт бутылки сплошной и по горизонтали, и по вертикали, а обрывки
    водяного знака лежат отдельными отрезками сбоку и сверху — так они и
    отсеиваются: сначала строки через вертикальную ось, потом столбцы через
    самую широкую строку.
    """
    def runs_through(m, axis_index, along_rows):
        a = m if along_rows else m.T
        out = np.zeros_like(a)
        n = a.shape[1]
        for i in range(a.shape[0]):
            line = a[i]
            if not line[axis_index]:
                continue
            l = r = axis_index
            while l > 0 and line[l - 1]:
                l -= 1
            while r + 1 < n and line[r + 1]:
                r += 1
            out[i, l:r + 1] = True
        return out if along_rows else out.T

    fg = runs_through(fg, int(np.argmax(fg.sum(axis=0))), True)
    return runs_through(fg, int(np.argmax(fg.sum(axis=1))), False)


def cutout(path):
    """маска непрозрачных пикселей бутылки"""
    im = Image.open(path).convert("RGB")
    a = np.asarray(im).astype(np.float64)
    H, W, _ = a.shape
    gray = a.mean(2)
    neutral = (a.max(2) - a.min(2)) <= 18

    lo, hi = cell_colors(gray, neutral)
    delta = hi - lo
    mid = 0.5 * (lo + hi)
    lm, ls = local_stats(gray, WINDOW)

    # пиксель лежит на одном из двух локальных уровней клетки (lm +- ls).
    # Так опознаётся и полупрозрачный водяной знак поверх шахматки:
    # у него уровни смещены и сжаты, но структура клеток сохраняется.
    level = neutral & (np.abs(np.abs(gray - lm) - ls) < 0.20 * delta)
    exact = neutral & ((np.abs(gray - hi) < 0.34 * delta) | (np.abs(gray - lo) < 0.34 * delta))
    checker = (np.abs(lm - mid) < 0.30 * delta) & (ls > 0.30 * delta) & (ls < 0.85 * delta)

    border = np.zeros((H, W), bool)
    border[0, :] = border[-1, :] = True
    border[:, 0] = border[:, -1] = True

    bg = propagate(border & level & checker | border & exact & checker,
                   (level | exact) & checker, 4000)
    bg = propagate(bg, level | exact, WINDOW)      # доесть ореол шириной с окно

    # плоские почти белые пятна, примыкающие к фону, — это водяной знак.
    # У бутылок такие пятна отгорожены тёмным контуром, внутрь заливка не идёт.
    haze = neutral & (gray > mid + 0.15 * delta) & (ls < 0.22 * delta)
    bg = propagate(bg, bg | haze, 4000)

    # габарит бутылки по её «твёрдым» пикселям: цветным или более тёмным,
    # чем любая клетка фона. Водяной знак нейтральный и светлый, в него не
    # попадает, поэтому всё за этой рамкой можно смело срезать
    solid = (~neutral) | (gray < lo - 12)
    solid = largest_blob(propagate(solid, np.ones_like(solid), 6), k=2, er=0) & solid
    ys, xs = np.nonzero(solid)
    pad = 8
    box = np.zeros_like(solid)
    box[max(0, ys.min() - pad):ys.max() + 1 + pad, max(0, xs.min() - pad):xs.max() + 1 + pad] = True

    return im, keep_axis_runs(largest_blob(~bg & box))


def _fit_box(fg, size):
    ys, xs = np.nonzero(fg)
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    sc = size / float(max(y1 - y0, x1 - x0))
    return (y0, y1, x0, x1), max(1, int(round((x1 - x0) * sc))), max(1, int(round((y1 - y0) * sc)))


def _resample(arr, nw, nh):
    img = Image.fromarray(arr.astype(np.float32), "F").resize((nw, nh), Image.BOX)
    return np.asarray(img, dtype=np.float64)


def to_png(im, fg, size=SIZE, inner=INNER):
    """вписать вырезанную бутылку в квадрат size x size

    Обрывки водяного знака держатся за бутылку тонкой перемычкой: в полном
    разрешении они с ней связаны, а после уменьшения перемычка исчезает,
    поэтому мусор отсеивается ещё раз уже на итоговом масштабе.
    """
    a = np.asarray(im).astype(np.float64)

    (y0, y1, x0, x1), nw, nh = _fit_box(fg, inner)
    keep = label_largest(_resample(fg[y0:y1, x0:x1].astype(np.float64), nw, nh) > 0.35)
    if keep.any():
        up = Image.fromarray(keep.astype(np.uint8) * 255).resize((x1 - x0, y1 - y0), Image.NEAREST)
        fg = fg.copy()
        fg[y0:y1, x0:x1] &= np.asarray(up) > 127

    (y0, y1, x0, x1), nw, nh = _fit_box(fg, inner)
    alpha = fg[y0:y1, x0:x1].astype(np.float64)
    pm = a[y0:y1, x0:x1] * alpha[:, :, None]      # премультиплай: фон не подтечёт при ресайзе

    al = _resample(alpha, nw, nh)
    ch = [_resample(pm[:, :, i], nw, nh) for i in range(3)]
    col = np.clip(np.stack([np.where(al > 1e-4, c / np.maximum(al, 1e-6), 0) for c in ch], axis=2), 0, 255)

    out = np.zeros((size, size, 4), np.uint8)
    oy, ox = (size - nh) // 2, (size - nw) // 2
    out[oy:oy + nh, ox:ox + nw, :3] = col.astype(np.uint8)
    out[oy:oy + nh, ox:ox + nw, 3] = np.clip(al * 255, 0, 255).astype(np.uint8)
    return Image.fromarray(out, "RGBA")


def main():
    ap = argparse.ArgumentParser(description="вырезать бутылки в текстуры ресурспака")
    ap.add_argument("--src", default=SRC, help="каталог с исходными jpg")
    ap.add_argument("--out", default=DST, help="куда класть png")
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)
    for num, name in sorted(BOTTLES.items()):
        found = glob.glob(os.path.join(args.src, "photo_%d_*.jpg" % num))
        if not found:
            print("photo_%-2d — исходник не найден, пропущено" % num)
            continue
        im, fg = cutout(found[0])
        path = os.path.join(args.out, name + ".png")
        to_png(im, fg).save(path)
        print("photo_%-2d -> %s" % (num, os.path.basename(path)))


if __name__ == "__main__":
    main()
