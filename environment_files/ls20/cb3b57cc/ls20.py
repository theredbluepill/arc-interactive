# MIT License
#
# Copyright (c) 2026 ARC Prize Foundation
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import math
from typing import List, Tuple

import numpy as np
from arcengine import (
    ARCBaseGame,
    Camera,
    Level,
    RenderableUserDisplay,
    Sprite,
)

# Create sprites dictionary with all sprite definitions
sprites = {
    "dcb": Sprite(
        pixels=[
            [-1, 0, -1],
            [0, 0, -1],
            [-1, 0, 0],
        ],
        name="dcb",
        visible=True,
        collidable=True,
        layer=1,
    ),
    "fij": Sprite(
        pixels=[
            [0, 0, 0],
            [-1, -1, 0],
            [0, -1, 0],
        ],
        name="fij",
        visible=True,
        collidable=False,
        layer=-2,
    ),
    "ggk": Sprite(
        pixels=[
            [5, 5, 5, 5, 5, 5, 5],
            [5, -1, -1, -1, -1, -1, 5],
            [5, -1, -1, -1, -1, -1, 5],
            [5, -1, -1, -1, -1, -1, 5],
            [5, -1, -1, -1, -1, -1, 5],
            [5, -1, -1, -1, -1, -1, 5],
            [5, 5, 5, 5, 5, 5, 5],
        ],
        name="ggk",
        visible=True,
        collidable=True,
        tags=["yar", "vdr"],
        layer=-3,
    ),
    "hep": Sprite(
        pixels=[
            [5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
            [5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
            [5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
            [5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
            [5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
            [5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
            [5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
            [5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
            [5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
            [5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
        ],
        name="hep",
        visible=True,
        collidable=True,
        tags=["nfq"],
        layer=1,
    ),
    "hul": Sprite(
        pixels=[
            [3, 3, -1, -1, -1, -1, -1, 3, 3],
            [3, 3, 3, 3, 3, 3, 3, 3, 3],
            [3, 3, 3, 3, 3, 3, 3, 3, 3],
            [3, 3, 3, 3, 3, 3, 3, 3, 3],
            [3, 3, 3, 3, 3, 3, 3, 3, 3],
            [3, 3, 3, 3, 3, 3, 3, 3, 3],
            [3, 3, 3, 3, 3, 3, 3, 3, 3],
            [3, 3, 3, 3, 3, 3, 3, 3, 3],
            [3, 3, 3, 3, 3, 3, 3, 3, 3],
        ],
        name="hul",
        visible=True,
        collidable=True,
        layer=-4,
    ),
    "kdj": Sprite(
        pixels=[
            [0, -1, 0],
            [-1, 0, -1],
            [0, -1, 0],
        ],
        name="kdj",
        visible=True,
        collidable=True,
        tags=["wex"],
        layer=10,
    ),
    "kdy": Sprite(
        pixels=[
            [-2, -2, -2, -2, -2],
            [-2, -2, 0, -2, -2],
            [-2, 1, 0, 0, -2],
            [-2, -2, 1, -2, -2],
            [-2, -2, -2, -2, -2],
        ],
        name="kdy",
        visible=True,
        collidable=True,
        tags=["bgt"],
        layer=-1,
    ),
    "krg": Sprite(
        pixels=[
            [11],
        ],
        name="krg",
        visible=True,
        collidable=True,
        layer=3,
    ),
    "lhs": Sprite(
        pixels=[
            [5, 5, 5, 5, 5],
            [5, 5, 5, 5, 5],
            [5, 5, 5, 5, 5],
            [5, 5, 5, 5, 5],
            [5, 5, 5, 5, 5],
        ],
        name="lhs",
        visible=True,
        collidable=False,
        tags=["mae"],
        layer=-3,
    ),
    "lyd": Sprite(
        pixels=[
            [-1, 0, -1],
            [-1, 0, -1],
            [0, 0, 0],
        ],
        name="lyd",
        visible=True,
        collidable=True,
    ),
    "mgu": Sprite(
        pixels=[
            [5, 5, 5, 5, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [5, 5, 5, 5, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [5, 5, 5, 5, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [5, 5, 5, 5, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [5, 5, 5, 5, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [5, 5, 5, 5, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [5, 5, 5, 5, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [5, 5, 5, 5, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [5, 5, 5, 5, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [5, 5, 5, 5, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [5, 5, 5, 5, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [5, 5, 5, 5, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [5, 5, 5, 5, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [5, 5, 5, 5, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [5, 5, 5, 5, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [5, 5, 5, 5, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [5, 5, 5, 5, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [5, 5, 5, 5, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [5, 5, 5, 5, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [5, 5, 5, 5, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [5, 5, 5, 5, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [5, 5, 5, 5, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [5, 5, 5, 5, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [5, 5, 5, 5, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [5, 5, 5, 5, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [5, 5, 5, 5, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [5, 5, 5, 5, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [5, 5, 5, 5, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [5, 5, 5, 5, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [5, 5, 5, 5, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [5, 5, 5, 5, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [5, 5, 5, 5, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [5, 5, 5, 5, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [5, 5, 5, 5, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [5, 5, 5, 5, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [5, 5, 5, 5, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [5, 5, 5, 5, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [5, 5, 5, 5, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [5, 5, 5, 5, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [5, 5, 5, 5, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [5, 5, 5, 5, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [5, 5, 5, 5, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [5, 5, 5, 5, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [5, 5, 5, 5, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [5, 5, 5, 5, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [5, 5, 5, 5, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [5, 5, 5, 5, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [5, 5, 5, 5, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [5, 5, 5, 5, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [5, 5, 5, 5, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [5, 5, 5, 5, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [5, 5, 5, 5, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [4, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 4, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [4, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 4, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [4, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 4, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [4, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 4, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [4, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 4, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [4, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 4, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [4, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 4, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [4, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 4, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
            [4, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 4, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
            [4, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 4, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
            [4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
        ],
        name="mgu",
        visible=True,
        collidable=True,
    ),
    "nio": Sprite(
        pixels=[
            [-1, 0, 0],
            [0, -1, 0],
            [-1, 0, -1],
        ],
        name="nio",
        visible=True,
        collidable=True,
    ),
    "nlo": Sprite(
        pixels=[
            [4, 4, 4, 4, 4],
            [4, 4, 4, 4, 4],
            [4, 4, 4, 4, 4],
            [4, 4, 4, 4, 4],
            [4, 4, 4, 4, 4],
        ],
        name="nlo",
        visible=True,
        collidable=True,
        tags=["jdd"],
        layer=-5,
    ),
    "opw": Sprite(
        pixels=[
            [0, 0, -1],
            [-1, 0, 0],
            [0, -1, 0],
        ],
        name="opw",
        visible=True,
        collidable=True,
    ),
    "pca": Sprite(
        pixels=[
            [12, 12, 12, 12, 12],
            [12, 12, 12, 12, 12],
            [9, 9, 9, 9, 9],
            [9, 9, 9, 9, 9],
            [9, 9, 9, 9, 9],
        ],
        name="pca",
        visible=True,
        collidable=True,
        tags=["caf"],
    ),
    "qqv": Sprite(
        pixels=[
            [-2, -2, -2, -2, -2],
            [-2, 9, 14, 14, -2],
            [-2, 9, 0, 8, -2],
            [-2, 12, 12, 8, -2],
            [-2, -2, -2, -2, -2],
        ],
        name="qqv",
        visible=True,
        collidable=False,
        tags=["gic"],
        layer=-1,
    ),
    "rzt": Sprite(
        pixels=[
            [0, -1, -1],
            [-1, 0, -1],
            [-1, -1, 0],
        ],
        name="rzt",
        visible=True,
        collidable=True,
        tags=["axa"],
    ),
    "snw": Sprite(
        pixels=[
            [5, 5, 5, 5, 5, 5, 5],
            [5, -1, -1, -1, -1, -1, 5],
            [5, -1, -1, -1, -1, -1, 5],
            [5, -1, -1, -1, -1, -1, 5],
            [5, -1, -1, -1, -1, -1, 5],
            [5, -1, -1, -1, -1, -1, 5],
            [5, 5, 5, 5, 5, 5, 5],
        ],
        name="snw",
        visible=True,
        collidable=True,
        tags=["yar"],
        layer=-3,
    ),
    "tmx": Sprite(
        pixels=[
            [0, -1, 0],
            [0, -1, 0],
            [0, 0, 0],
        ],
        name="tmx",
        visible=True,
        collidable=True,
    ),
    "tuv": Sprite(
        pixels=[
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, -1, -1, -1, -1, -1, -1, -1, -1, 0],
            [0, -1, -1, -1, -1, -1, -1, -1, -1, 0],
            [0, -1, -1, -1, -1, -1, -1, -1, -1, 0],
            [0, -1, -1, -1, -1, -1, -1, -1, -1, 0],
            [0, -1, -1, -1, -1, -1, -1, -1, -1, 0],
            [0, -1, -1, -1, -1, -1, -1, -1, -1, 0],
            [0, -1, -1, -1, -1, -1, -1, -1, -1, 0],
            [0, -1, -1, -1, -1, -1, -1, -1, -1, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        ],
        name="tuv",
        visible=False,
        collidable=True,
        tags=["fng"],
        layer=5,
    ),
    "ulq": Sprite(
        pixels=[
            [0, 0, 0, 0, 0, 0, 0],
            [0, -1, -1, -1, -1, -1, 0],
            [0, -1, -1, -1, -1, -1, 0],
            [0, -1, -1, -1, -1, -1, 0],
            [0, -1, -1, -1, -1, -1, 0],
            [0, -1, -1, -1, -1, -1, 0],
            [0, 0, 0, 0, 0, 0, 0],
        ],
        name="ulq",
        visible=False,
        collidable=True,
        tags=["qex"],
        layer=-1,
    ),
    "vxy": Sprite(
        pixels=[
            [-2, -2, -2, -2, -2],
            [-2, 0, -2, -2, -2],
            [-2, -2, 0, 0, -2],
            [-2, -2, 0, -2, -2],
            [-2, -2, -2, -2, -2],
        ],
        name="vxy",
        visible=True,
        collidable=False,
        tags=["gsu"],
        layer=-1,
    ),
    "zba": Sprite(
        pixels=[
            [11, 11, 11],
            [11, -1, 11],
            [11, 11, 11],
        ],
        name="zba",
        visible=True,
        collidable=False,
        tags=["iri"],
        layer=-1,
    ),
}


# Create levels array with all level definitions
levels = [
    # krg
    Level(
        sprites=[
            sprites["hep"].clone().set_position(1, 53),
            sprites["hul"].clone().set_position(32, 8).set_rotation(180),
            sprites["kdj"].clone().set_position(3, 55).set_scale(2),
            sprites["kdy"].clone().set_position(19, 30),
            sprites["lhs"].clone().set_position(34, 10),
            sprites["mgu"].clone(),
            sprites["nlo"].clone().set_position(4, 0),
            sprites["nlo"].clone().set_position(9, 0),
            sprites["nlo"].clone().set_position(4, 5),
            sprites["nlo"].clone().set_position(14, 0),
            sprites["nlo"].clone().set_position(19, 0),
            sprites["nlo"].clone().set_position(24, 0),
            sprites["nlo"].clone().set_position(29, 0),
            sprites["nlo"].clone().set_position(39, 0),
            sprites["nlo"].clone().set_position(44, 0),
            sprites["nlo"].clone().set_position(49, 0),
            sprites["nlo"].clone().set_position(54, 0),
            sprites["nlo"].clone().set_position(59, 0),
            sprites["nlo"].clone().set_position(4, 10),
            sprites["nlo"].clone().set_position(4, 15),
            sprites["nlo"].clone().set_position(4, 20),
            sprites["nlo"].clone().set_position(4, 25),
            sprites["nlo"].clone().set_position(59, 15),
            sprites["nlo"].clone().set_position(59, 20),
            sprites["nlo"].clone().set_position(59, 25),
            sprites["nlo"].clone().set_position(59, 30),
            sprites["nlo"].clone().set_position(59, 20),
            sprites["nlo"].clone().set_position(59, 25),
            sprites["nlo"].clone().set_position(59, 30),
            sprites["nlo"].clone().set_position(59, 35),
            sprites["nlo"].clone().set_position(59, 40),
            sprites["nlo"].clone().set_position(59, 45),
            sprites["nlo"].clone().set_position(59, 35),
            sprites["nlo"].clone().set_position(59, 40),
            sprites["nlo"].clone().set_position(59, 45),
            sprites["nlo"].clone().set_position(59, 50),
            sprites["nlo"].clone().set_position(59, 55),
            sprites["nlo"].clone().set_position(59, 50),
            sprites["nlo"].clone().set_position(59, 55),
            sprites["nlo"].clone().set_position(54, 55),
            sprites["nlo"].clone().set_position(49, 55),
            sprites["nlo"].clone().set_position(44, 55),
            sprites["nlo"].clone().set_position(39, 55),
            sprites["nlo"].clone().set_position(34, 55),
            sprites["nlo"].clone().set_position(29, 55),
            sprites["nlo"].clone().set_position(24, 55),
            sprites["nlo"].clone().set_position(19, 55),
            sprites["nlo"].clone().set_position(4, 40),
            sprites["nlo"].clone().set_position(4, 45),
            sprites["nlo"].clone().set_position(4, 50),
            sprites["nlo"].clone().set_position(9, 50),
            sprites["nlo"].clone().set_position(4, 55),
            sprites["nlo"].clone().set_position(9, 55),
            sprites["nlo"].clone().set_position(14, 55),
            sprites["nlo"].clone().set_position(4, 45),
            sprites["nlo"].clone().set_position(54, 25),
            sprites["nlo"].clone().set_position(54, 20),
            sprites["nlo"].clone().set_position(34, 0),
            sprites["nlo"].clone().set_position(59, 10),
            sprites["nlo"].clone().set_position(59, 5),
            sprites["nlo"].clone().set_position(54, 15),
            sprites["nlo"].clone().set_position(54, 10),
            sprites["nlo"].clone().set_position(44, 5),
            sprites["nlo"].clone().set_position(39, 5),
            sprites["nlo"].clone().set_position(34, 5),
            sprites["nlo"].clone().set_position(29, 5),
            sprites["nlo"].clone().set_position(54, 50),
            sprites["nlo"].clone().set_position(54, 45),
            sprites["nlo"].clone().set_position(24, 5),
            sprites["nlo"].clone().set_position(19, 5),
            sprites["nlo"].clone().set_position(9, 35),
            sprites["nlo"].clone().set_position(9, 45),
            sprites["nlo"].clone().set_position(19, 50),
            sprites["nlo"].clone().set_position(9, 40),
            sprites["nlo"].clone().set_position(49, 5),
            sprites["nlo"].clone().set_position(54, 5),
            sprites["nlo"].clone().set_position(49, 50),
            sprites["nlo"].clone().set_position(14, 50),
            sprites["nlo"].clone().set_position(14, 5),
            sprites["nlo"].clone().set_position(9, 5),
            sprites["nlo"].clone().set_position(9, 30),
            sprites["nlo"].clone().set_position(9, 25),
            sprites["nlo"].clone().set_position(9, 20),
            sprites["nlo"].clone().set_position(9, 15),
            sprites["nlo"].clone().set_position(9, 10),
            sprites["nlo"].clone().set_position(49, 10),
            sprites["nlo"].clone().set_position(44, 20),
            sprites["nlo"].clone().set_position(39, 10),
            sprites["nlo"].clone().set_position(44, 10),
            sprites["nlo"].clone().set_position(49, 15),
            sprites["nlo"].clone().set_position(29, 10),
            sprites["nlo"].clone().set_position(29, 15),
            sprites["nlo"].clone().set_position(39, 15),
            sprites["nlo"].clone().set_position(44, 15),
            sprites["nlo"].clone().set_position(49, 20),
            sprites["nlo"].clone().set_position(14, 15),
            sprites["nlo"].clone().set_position(19, 15),
            sprites["nlo"].clone().set_position(24, 15),
            sprites["nlo"].clone().set_position(24, 10),
            sprites["nlo"].clone().set_position(19, 10),
            sprites["nlo"].clone().set_position(14, 10),
            sprites["nlo"].clone().set_position(29, 20),
            sprites["nlo"].clone().set_position(39, 20),
            sprites["nlo"].clone().set_position(24, 20),
            sprites["nlo"].clone().set_position(29, 40),
            sprites["nlo"].clone().set_position(19, 20),
            sprites["nlo"].clone().set_position(14, 20),
            sprites["nlo"].clone().set_position(54, 30),
            sprites["nlo"].clone().set_position(24, 40),
            sprites["nlo"].clone().set_position(14, 45),
            sprites["nlo"].clone().set_position(29, 35),
            sprites["nlo"].clone().set_position(4, 30).color_remap(None, 4),
            sprites["nlo"].clone().set_position(4, 35),
            sprites["nlo"].clone().set_position(54, 35),
            sprites["nlo"].clone().set_position(54, 40),
            sprites["nlo"].clone().set_position(14, 40),
            sprites["nlo"].clone().set_position(24, 50),
            sprites["nlo"].clone().set_position(29, 50),
            sprites["nlo"].clone().set_position(39, 50),
            sprites["nlo"].clone().set_position(44, 50),
            sprites["nlo"].clone().set_position(34, 50),
            sprites["nlo"].clone().set_position(29, 30),
            sprites["pca"].clone().set_position(39, 45),
            sprites["rzt"].clone().set_position(35, 11),
            sprites["snw"].clone().set_position(33, 9),
            sprites["tuv"].clone().set_position(1, 53),
            sprites["ulq"].clone().set_position(33, 9),
        ],
        grid_size=(64, 64),
        data={
            "vxy": 42,
            "tuv": 5,
            "nlo": 9,
            "opw": 0,
            "qqv": 5,
            "ggk": 9,
            "fij": 270,
            "kdy": False,
        },
        name="krg",
    ),
    # mgu
    Level(
        sprites=[
            sprites["hep"].clone().set_position(1, 53),
            sprites["hul"].clone().set_position(12, 38),
            sprites["kdj"].clone().set_position(3, 55).set_scale(2),
            sprites["kdy"].clone().set_position(49, 45),
            sprites["lhs"].clone().set_position(14, 40),
            sprites["mgu"].clone(),
            sprites["nlo"].clone().set_position(4, 0),
            sprites["nlo"].clone().set_position(9, 0),
            sprites["nlo"].clone().set_position(4, 5),
            sprites["nlo"].clone().set_position(14, 0),
            sprites["nlo"].clone().set_position(19, 0),
            sprites["nlo"].clone().set_position(24, 0),
            sprites["nlo"].clone().set_position(29, 0),
            sprites["nlo"].clone().set_position(39, 0),
            sprites["nlo"].clone().set_position(44, 0),
            sprites["nlo"].clone().set_position(49, 0),
            sprites["nlo"].clone().set_position(54, 0),
            sprites["nlo"].clone().set_position(59, 0),
            sprites["nlo"].clone().set_position(4, 10),
            sprites["nlo"].clone().set_position(4, 15),
            sprites["nlo"].clone().set_position(4, 20),
            sprites["nlo"].clone().set_position(4, 25),
            sprites["nlo"].clone().set_position(4, 30),
            sprites["nlo"].clone().set_position(4, 35),
            sprites["nlo"].clone().set_position(59, 15),
            sprites["nlo"].clone().set_position(59, 20),
            sprites["nlo"].clone().set_position(59, 25),
            sprites["nlo"].clone().set_position(59, 30),
            sprites["nlo"].clone().set_position(59, 20),
            sprites["nlo"].clone().set_position(59, 25),
            sprites["nlo"].clone().set_position(59, 30),
            sprites["nlo"].clone().set_position(59, 35),
            sprites["nlo"].clone().set_position(59, 40),
            sprites["nlo"].clone().set_position(59, 45),
            sprites["nlo"].clone().set_position(59, 35),
            sprites["nlo"].clone().set_position(59, 40),
            sprites["nlo"].clone().set_position(59, 45),
            sprites["nlo"].clone().set_position(59, 50),
            sprites["nlo"].clone().set_position(59, 55),
            sprites["nlo"].clone().set_position(59, 50),
            sprites["nlo"].clone().set_position(59, 55),
            sprites["nlo"].clone().set_position(54, 55),
            sprites["nlo"].clone().set_position(49, 55),
            sprites["nlo"].clone().set_position(44, 55),
            sprites["nlo"].clone().set_position(39, 55),
            sprites["nlo"].clone().set_position(34, 55),
            sprites["nlo"].clone().set_position(29, 55),
            sprites["nlo"].clone().set_position(24, 55),
            sprites["nlo"].clone().set_position(19, 55),
            sprites["nlo"].clone().set_position(4, 40),
            sprites["nlo"].clone().set_position(4, 45),
            sprites["nlo"].clone().set_position(4, 50),
            sprites["nlo"].clone().set_position(9, 50),
            sprites["nlo"].clone().set_position(4, 55),
            sprites["nlo"].clone().set_position(9, 55),
            sprites["nlo"].clone().set_position(14, 55),
            sprites["nlo"].clone().set_position(4, 45),
            sprites["nlo"].clone().set_position(54, 30),
            sprites["nlo"].clone().set_position(34, 0),
            sprites["nlo"].clone().set_position(59, 10),
            sprites["nlo"].clone().set_position(59, 5),
            sprites["nlo"].clone().set_position(54, 15),
            sprites["nlo"].clone().set_position(54, 10),
            sprites["nlo"].clone().set_position(9, 35),
            sprites["nlo"].clone().set_position(9, 45),
            sprites["nlo"].clone().set_position(19, 50),
            sprites["nlo"].clone().set_position(9, 40),
            sprites["nlo"].clone().set_position(54, 5),
            sprites["nlo"].clone().set_position(14, 45),
            sprites["nlo"].clone().set_position(14, 50),
            sprites["nlo"].clone().set_position(9, 5),
            sprites["nlo"].clone().set_position(9, 30),
            sprites["nlo"].clone().set_position(9, 25),
            sprites["nlo"].clone().set_position(19, 30),
            sprites["nlo"].clone().set_position(24, 30),
            sprites["nlo"].clone().set_position(19, 40),
            sprites["nlo"].clone().set_position(19, 45),
            sprites["nlo"].clone().set_position(19, 35),
            sprites["nlo"].clone().set_position(39, 15),
            sprites["nlo"].clone().set_position(39, 35),
            sprites["nlo"].clone().set_position(44, 30),
            sprites["nlo"].clone().set_position(34, 45),
            sprites["nlo"].clone().set_position(14, 5),
            sprites["nlo"].clone().set_position(39, 20),
            sprites["nlo"].clone().set_position(44, 20),
            sprites["nlo"].clone().set_position(24, 20),
            sprites["nlo"].clone().set_position(44, 25),
            sprites["nlo"].clone().set_position(39, 40),
            sprites["nlo"].clone().set_position(39, 45),
            sprites["nlo"].clone().set_position(24, 35),
            sprites["nlo"].clone().set_position(24, 25),
            sprites["nlo"].clone().set_position(24, 50),
            sprites["nlo"].clone().set_position(19, 25),
            sprites["nlo"].clone().set_position(24, 40),
            sprites["nlo"].clone().set_position(24, 45),
            sprites["nlo"].clone().set_position(29, 45),
            sprites["nlo"].clone().set_position(29, 30),
            sprites["nlo"].clone().set_position(29, 25),
            sprites["nlo"].clone().set_position(24, 15),
            sprites["nlo"].clone().set_position(44, 35),
            sprites["nlo"].clone().set_position(54, 34),
            sprites["pca"].clone().set_position(29, 40),
            sprites["rzt"].clone().set_position(15, 41),
            sprites["snw"].clone().set_position(13, 39),
            sprites["tuv"].clone().set_position(1, 53),
            sprites["ulq"].clone().set_position(13, 39),
            sprites["zba"].clone().set_position(15, 16),
            sprites["zba"].clone().set_position(30, 51),
        ],
        grid_size=(64, 64),
        data={
            "vxy": 42,
            "tuv": 5,
            "nlo": 9,
            "opw": 270,
            "qqv": 5,
            "ggk": 9,
            "fij": 0,
            "kdy": False,
        },
        name="mgu",
    ),
    # puq
    Level(
        sprites=[
            sprites["hep"].clone().set_position(1, 53),
            sprites["hul"].clone().set_position(52, 48),
            sprites["kdj"].clone().set_position(3, 55).set_scale(2),
            sprites["kdy"].clone().set_position(49, 10),
            sprites["lhs"].clone().set_position(54, 50),
            sprites["mgu"].clone(),
            sprites["nlo"].clone().set_position(4, 0),
            sprites["nlo"].clone().set_position(9, 0),
            sprites["nlo"].clone().set_position(4, 5),
            sprites["nlo"].clone().set_position(14, 0),
            sprites["nlo"].clone().set_position(19, 0),
            sprites["nlo"].clone().set_position(24, 0),
            sprites["nlo"].clone().set_position(29, 0),
            sprites["nlo"].clone().set_position(39, 0),
            sprites["nlo"].clone().set_position(44, 0),
            sprites["nlo"].clone().set_position(49, 0),
            sprites["nlo"].clone().set_position(54, 0),
            sprites["nlo"].clone().set_position(59, 0),
            sprites["nlo"].clone().set_position(4, 10),
            sprites["nlo"].clone().set_position(4, 15),
            sprites["nlo"].clone().set_position(4, 20),
            sprites["nlo"].clone().set_position(4, 25),
            sprites["nlo"].clone().set_position(4, 30),
            sprites["nlo"].clone().set_position(4, 35),
            sprites["nlo"].clone().set_position(59, 15),
            sprites["nlo"].clone().set_position(59, 20),
            sprites["nlo"].clone().set_position(59, 25),
            sprites["nlo"].clone().set_position(59, 30),
            sprites["nlo"].clone().set_position(59, 20),
            sprites["nlo"].clone().set_position(59, 25),
            sprites["nlo"].clone().set_position(59, 30),
            sprites["nlo"].clone().set_position(59, 35),
            sprites["nlo"].clone().set_position(59, 40),
            sprites["nlo"].clone().set_position(59, 45),
            sprites["nlo"].clone().set_position(59, 35),
            sprites["nlo"].clone().set_position(59, 40),
            sprites["nlo"].clone().set_position(59, 45),
            sprites["nlo"].clone().set_position(59, 50),
            sprites["nlo"].clone().set_position(59, 55),
            sprites["nlo"].clone().set_position(59, 50),
            sprites["nlo"].clone().set_position(59, 55),
            sprites["nlo"].clone().set_position(54, 55),
            sprites["nlo"].clone().set_position(49, 55),
            sprites["nlo"].clone().set_position(44, 55),
            sprites["nlo"].clone().set_position(39, 55),
            sprites["nlo"].clone().set_position(34, 55),
            sprites["nlo"].clone().set_position(29, 55),
            sprites["nlo"].clone().set_position(24, 55),
            sprites["nlo"].clone().set_position(19, 55),
            sprites["nlo"].clone().set_position(4, 40),
            sprites["nlo"].clone().set_position(4, 45),
            sprites["nlo"].clone().set_position(4, 50),
            sprites["nlo"].clone().set_position(9, 50),
            sprites["nlo"].clone().set_position(4, 55),
            sprites["nlo"].clone().set_position(9, 55),
            sprites["nlo"].clone().set_position(14, 55),
            sprites["nlo"].clone().set_position(4, 45),
            sprites["nlo"].clone().set_position(34, 0),
            sprites["nlo"].clone().set_position(59, 10),
            sprites["nlo"].clone().set_position(59, 5),
            sprites["nlo"].clone().set_position(39, 10),
            sprites["nlo"].clone().set_position(14, 25),
            sprites["nlo"].clone().set_position(19, 40),
            sprites["nlo"].clone().set_position(19, 45),
            sprites["nlo"].clone().set_position(19, 35),
            sprites["nlo"].clone().set_position(49, 50),
            sprites["nlo"].clone().set_position(39, 35),
            sprites["nlo"].clone().set_position(39, 40),
            sprites["nlo"].clone().set_position(39, 45),
            sprites["nlo"].clone().set_position(14, 30),
            sprites["nlo"].clone().set_position(49, 45),
            sprites["nlo"].clone().set_position(49, 40),
            sprites["nlo"].clone().set_position(14, 20),
            sprites["nlo"].clone().set_position(14, 50),
            sprites["nlo"].clone().set_position(39, 5),
            sprites["nlo"].clone().set_position(39, 50),
            sprites["nlo"].clone().set_position(44, 45),
            sprites["nlo"].clone().set_position(19, 50),
            sprites["nlo"].clone().set_position(44, 40),
            sprites["nlo"].clone().set_position(44, 50),
            sprites["nlo"].clone().set_position(44, 20),
            sprites["nlo"].clone().set_position(49, 20),
            sprites["nlo"].clone().set_position(39, 20),
            sprites["nlo"].clone().set_position(19, 10),
            sprites["nlo"].clone().set_position(14, 35),
            sprites["nlo"].clone().set_position(39, 15),
            sprites["nlo"].clone().set_position(34, 35),
            sprites["nlo"].clone().set_position(14, 10),
            sprites["nlo"].clone().set_position(14, 15),
            sprites["nlo"].clone().set_position(44, 35),
            sprites["nlo"].clone().set_position(24, 35),
            sprites["nlo"].clone().set_position(34, 10),
            sprites["nlo"].clone().set_position(24, 10),
            sprites["pca"].clone().set_position(9, 45),
            sprites["qqv"].clone().set_position(29, 45),
            sprites["rzt"].clone().set_position(55, 51),
            sprites["snw"].clone().set_position(53, 49),
            sprites["tuv"].clone().set_position(1, 53),
            sprites["ulq"].clone().set_position(53, 49),
            sprites["zba"].clone().set_position(20, 31),
            sprites["zba"].clone().set_position(35, 6),
            sprites["zba"].clone().set_position(50, 36),
        ],
        grid_size=(64, 64),
        data={
            "vxy": 42,
            "tuv": 5,
            "nlo": 9,
            "opw": 270,
            "qqv": 5,
            "ggk": 12,
            "fij": 0,
            "kdy": False,
        },
        name="puq",
    ),
    # tmx
    Level(
        sprites=[
            sprites["hep"].clone().set_position(1, 53),
            sprites["hul"].clone().set_position(7, 3).set_rotation(90),
            sprites["kdj"].clone().set_position(3, 55).set_scale(2),
            sprites["lhs"].clone().set_position(9, 5),
            sprites["mgu"].clone(),
            sprites["nlo"].clone().set_position(4, 0),
            sprites["nlo"].clone().set_position(9, 0),
            sprites["nlo"].clone().set_position(4, 5),
            sprites["nlo"].clone().set_position(14, 0),
            sprites["nlo"].clone().set_position(19, 0),
            sprites["nlo"].clone().set_position(24, 0),
            sprites["nlo"].clone().set_position(29, 0),
            sprites["nlo"].clone().set_position(39, 0),
            sprites["nlo"].clone().set_position(44, 0),
            sprites["nlo"].clone().set_position(49, 0),
            sprites["nlo"].clone().set_position(54, 0),
            sprites["nlo"].clone().set_position(59, 0),
            sprites["nlo"].clone().set_position(4, 10),
            sprites["nlo"].clone().set_position(4, 15),
            sprites["nlo"].clone().set_position(4, 20),
            sprites["nlo"].clone().set_position(4, 25),
            sprites["nlo"].clone().set_position(4, 30),
            sprites["nlo"].clone().set_position(4, 35),
            sprites["nlo"].clone().set_position(59, 15),
            sprites["nlo"].clone().set_position(59, 20),
            sprites["nlo"].clone().set_position(59, 25),
            sprites["nlo"].clone().set_position(59, 30),
            sprites["nlo"].clone().set_position(59, 20),
            sprites["nlo"].clone().set_position(59, 25),
            sprites["nlo"].clone().set_position(59, 30),
            sprites["nlo"].clone().set_position(59, 35),
            sprites["nlo"].clone().set_position(59, 40),
            sprites["nlo"].clone().set_position(59, 45),
            sprites["nlo"].clone().set_position(59, 35),
            sprites["nlo"].clone().set_position(59, 40),
            sprites["nlo"].clone().set_position(59, 45),
            sprites["nlo"].clone().set_position(59, 50),
            sprites["nlo"].clone().set_position(59, 55),
            sprites["nlo"].clone().set_position(59, 50),
            sprites["nlo"].clone().set_position(59, 55),
            sprites["nlo"].clone().set_position(54, 55),
            sprites["nlo"].clone().set_position(49, 55),
            sprites["nlo"].clone().set_position(44, 55),
            sprites["nlo"].clone().set_position(39, 55),
            sprites["nlo"].clone().set_position(34, 55),
            sprites["nlo"].clone().set_position(29, 55),
            sprites["nlo"].clone().set_position(24, 55),
            sprites["nlo"].clone().set_position(19, 55),
            sprites["nlo"].clone().set_position(4, 40),
            sprites["nlo"].clone().set_position(4, 45),
            sprites["nlo"].clone().set_position(4, 50),
            sprites["nlo"].clone().set_position(9, 50),
            sprites["nlo"].clone().set_position(4, 55),
            sprites["nlo"].clone().set_position(9, 55),
            sprites["nlo"].clone().set_position(14, 55),
            sprites["nlo"].clone().set_position(4, 45),
            sprites["nlo"].clone().set_position(34, 0),
            sprites["nlo"].clone().set_position(59, 10),
            sprites["nlo"].clone().set_position(59, 5),
            sprites["nlo"].clone().set_position(19, 30),
            sprites["nlo"].clone().set_position(14, 10),
            sprites["nlo"].clone().set_position(9, 10),
            sprites["nlo"].clone().set_position(24, 25),
            sprites["nlo"].clone().set_position(29, 30),
            sprites["nlo"].clone().set_position(19, 10),
            sprites["nlo"].clone().set_position(29, 5),
            sprites["nlo"].clone().set_position(9, 20),
            sprites["nlo"].clone().set_position(14, 15),
            sprites["nlo"].clone().set_position(29, 25),
            sprites["nlo"].clone().set_position(29, 35),
            sprites["nlo"].clone().set_position(34, 35),
            sprites["nlo"].clone().set_position(19, 50),
            sprites["nlo"].clone().set_position(39, 50),
            sprites["nlo"].clone().set_position(39, 30),
            sprites["nlo"].clone().set_position(49, 35),
            sprites["nlo"].clone().set_position(9, 15),
            sprites["nlo"].clone().set_position(49, 10),
            sprites["nlo"].clone().set_position(49, 15),
            sprites["nlo"].clone().set_position(44, 10),
            sprites["nlo"].clone().set_position(29, 40),
            sprites["nlo"].clone().set_position(29, 20),
            sprites["nlo"].clone().set_position(39, 45),
            sprites["nlo"].clone().set_position(39, 50),
            sprites["nlo"].clone().set_position(44, 50),
            sprites["nlo"].clone().set_position(19, 25),
            sprites["nlo"].clone().set_position(39, 35),
            sprites["nlo"].clone().set_position(14, 50),
            sprites["nlo"].clone().set_position(9, 45),
            sprites["pca"].clone().set_position(54, 5),
            sprites["qqv"].clone().set_position(34, 30),
            sprites["rzt"].clone().set_position(10, 6),
            sprites["snw"].clone().set_position(8, 4),
            sprites["tuv"].clone().set_position(1, 53),
            sprites["ulq"].clone().set_position(8, 4),
            sprites["vxy"].clone().set_position(24, 30),
            sprites["zba"].clone().set_position(35, 41),
            sprites["zba"].clone().set_position(15, 46),
            sprites["zba"].clone().set_position(25, 21),
            sprites["zba"].clone().set_position(55, 51),
        ],
        grid_size=(64, 64),
        data={
            "vxy": 42,
            "tuv": 5,
            "nlo": 9,
            "opw": 0,
            "qqv": 4,
            "ggk": 14,
            "fij": 0,
            "kdy": False,
        },
        name="tmx",
    ),
    # zba
    Level(
        sprites=[
            sprites["hep"].clone().set_position(1, 53),
            sprites["hul"].clone().set_position(52, 3).set_rotation(180),
            sprites["kdj"].clone().set_position(3, 55).set_scale(2),
            sprites["kdy"].clone().set_position(19, 40),
            sprites["lhs"].clone().set_position(54, 5),
            sprites["mgu"].clone(),
            sprites["nlo"].clone().set_position(4, 0),
            sprites["nlo"].clone().set_position(9, 0),
            sprites["nlo"].clone().set_position(4, 5),
            sprites["nlo"].clone().set_position(14, 0),
            sprites["nlo"].clone().set_position(19, 0),
            sprites["nlo"].clone().set_position(24, 0),
            sprites["nlo"].clone().set_position(29, 0),
            sprites["nlo"].clone().set_position(39, 0),
            sprites["nlo"].clone().set_position(44, 0),
            sprites["nlo"].clone().set_position(49, 0),
            sprites["nlo"].clone().set_position(54, 0),
            sprites["nlo"].clone().set_position(59, 0),
            sprites["nlo"].clone().set_position(4, 10),
            sprites["nlo"].clone().set_position(4, 15),
            sprites["nlo"].clone().set_position(4, 20),
            sprites["nlo"].clone().set_position(4, 25),
            sprites["nlo"].clone().set_position(4, 30),
            sprites["nlo"].clone().set_position(4, 35),
            sprites["nlo"].clone().set_position(59, 15),
            sprites["nlo"].clone().set_position(59, 20),
            sprites["nlo"].clone().set_position(59, 25),
            sprites["nlo"].clone().set_position(59, 30),
            sprites["nlo"].clone().set_position(59, 20),
            sprites["nlo"].clone().set_position(59, 25),
            sprites["nlo"].clone().set_position(59, 30),
            sprites["nlo"].clone().set_position(59, 35),
            sprites["nlo"].clone().set_position(59, 40),
            sprites["nlo"].clone().set_position(59, 45),
            sprites["nlo"].clone().set_position(59, 35),
            sprites["nlo"].clone().set_position(59, 40),
            sprites["nlo"].clone().set_position(59, 45),
            sprites["nlo"].clone().set_position(59, 50),
            sprites["nlo"].clone().set_position(59, 55),
            sprites["nlo"].clone().set_position(59, 50),
            sprites["nlo"].clone().set_position(59, 55),
            sprites["nlo"].clone().set_position(54, 55),
            sprites["nlo"].clone().set_position(49, 55),
            sprites["nlo"].clone().set_position(44, 55),
            sprites["nlo"].clone().set_position(39, 55),
            sprites["nlo"].clone().set_position(34, 55),
            sprites["nlo"].clone().set_position(29, 55),
            sprites["nlo"].clone().set_position(24, 55),
            sprites["nlo"].clone().set_position(19, 55),
            sprites["nlo"].clone().set_position(4, 40),
            sprites["nlo"].clone().set_position(4, 45),
            sprites["nlo"].clone().set_position(4, 50),
            sprites["nlo"].clone().set_position(9, 50),
            sprites["nlo"].clone().set_position(4, 55),
            sprites["nlo"].clone().set_position(9, 55),
            sprites["nlo"].clone().set_position(14, 55),
            sprites["nlo"].clone().set_position(4, 45),
            sprites["nlo"].clone().set_position(34, 0),
            sprites["nlo"].clone().set_position(59, 10),
            sprites["nlo"].clone().set_position(59, 5),
            sprites["nlo"].clone().set_position(29, 30),
            sprites["nlo"].clone().set_position(29, 35),
            sprites["nlo"].clone().set_position(49, 10),
            sprites["nlo"].clone().set_position(49, 5),
            sprites["nlo"].clone().set_position(29, 15),
            sprites["nlo"].clone().set_position(29, 20),
            sprites["nlo"].clone().set_position(24, 25),
            sprites["nlo"].clone().set_position(19, 25),
            sprites["nlo"].clone().set_position(49, 15),
            sprites["nlo"].clone().set_position(24, 30),
            sprites["nlo"].clone().set_position(24, 20),
            sprites["nlo"].clone().set_position(34, 20),
            sprites["nlo"].clone().set_position(34, 30),
            sprites["nlo"].clone().set_position(49, 35),
            sprites["nlo"].clone().set_position(49, 40),
            sprites["nlo"].clone().set_position(49, 45),
            sprites["nlo"].clone().set_position(49, 50),
            sprites["nlo"].clone().set_position(44, 50),
            sprites["nlo"].clone().set_position(44, 5),
            sprites["nlo"].clone().set_position(14, 25),
            sprites["nlo"].clone().set_position(49, 20),
            sprites["nlo"].clone().set_position(49, 30),
            sprites["nlo"].clone().set_position(14, 50),
            sprites["nlo"].clone().set_position(9, 45),
            sprites["pca"].clone().set_position(54, 50),
            sprites["qqv"].clone().set_position(29, 25),
            sprites["rzt"].clone().set_position(55, 6),
            sprites["snw"].clone().set_position(53, 4),
            sprites["tuv"].clone().set_position(1, 53),
            sprites["ulq"].clone().set_position(53, 4),
            sprites["vxy"].clone().set_position(19, 10),
            sprites["zba"].clone().set_position(40, 6),
            sprites["zba"].clone().set_position(10, 6),
            sprites["zba"].clone().set_position(40, 51),
        ],
        grid_size=(64, 64),
        data={
            "vxy": 42,
            "tuv": 5,
            "nlo": 9,
            "opw": 90,
            "qqv": 4,
            "ggk": 12,
            "fij": 0,
            "kdy": False,
        },
        name="zba",
    ),
    # lyd
    Level(
        sprites=[
            sprites["ggk"].clone().set_position(53, 34),
            sprites["hep"].clone().set_position(1, 53),
            sprites["hul"].clone().set_position(52, 48),
            sprites["hul"].clone().set_position(52, 33),
            sprites["kdj"].clone().set_position(3, 55).set_scale(2),
            sprites["kdy"].clone().set_position(19, 25),
            sprites["lhs"].clone().set_position(54, 50),
            sprites["lhs"].clone().set_position(54, 35),
            sprites["mgu"].clone(),
            sprites["nlo"].clone().set_position(4, 0),
            sprites["nlo"].clone().set_position(9, 0),
            sprites["nlo"].clone().set_position(4, 5),
            sprites["nlo"].clone().set_position(14, 0),
            sprites["nlo"].clone().set_position(19, 0),
            sprites["nlo"].clone().set_position(24, 0),
            sprites["nlo"].clone().set_position(29, 0),
            sprites["nlo"].clone().set_position(39, 0),
            sprites["nlo"].clone().set_position(44, 0),
            sprites["nlo"].clone().set_position(49, 0),
            sprites["nlo"].clone().set_position(54, 0),
            sprites["nlo"].clone().set_position(59, 0),
            sprites["nlo"].clone().set_position(4, 10),
            sprites["nlo"].clone().set_position(4, 15),
            sprites["nlo"].clone().set_position(4, 20),
            sprites["nlo"].clone().set_position(4, 25),
            sprites["nlo"].clone().set_position(4, 30),
            sprites["nlo"].clone().set_position(4, 35),
            sprites["nlo"].clone().set_position(59, 15),
            sprites["nlo"].clone().set_position(59, 20),
            sprites["nlo"].clone().set_position(59, 25),
            sprites["nlo"].clone().set_position(59, 30),
            sprites["nlo"].clone().set_position(59, 20),
            sprites["nlo"].clone().set_position(59, 25),
            sprites["nlo"].clone().set_position(59, 30),
            sprites["nlo"].clone().set_position(59, 35),
            sprites["nlo"].clone().set_position(59, 40),
            sprites["nlo"].clone().set_position(59, 45),
            sprites["nlo"].clone().set_position(59, 35),
            sprites["nlo"].clone().set_position(59, 40),
            sprites["nlo"].clone().set_position(59, 45),
            sprites["nlo"].clone().set_position(59, 50),
            sprites["nlo"].clone().set_position(59, 55),
            sprites["nlo"].clone().set_position(59, 50),
            sprites["nlo"].clone().set_position(59, 55),
            sprites["nlo"].clone().set_position(54, 55),
            sprites["nlo"].clone().set_position(49, 55),
            sprites["nlo"].clone().set_position(44, 55),
            sprites["nlo"].clone().set_position(39, 55),
            sprites["nlo"].clone().set_position(34, 55),
            sprites["nlo"].clone().set_position(29, 55),
            sprites["nlo"].clone().set_position(24, 55),
            sprites["nlo"].clone().set_position(19, 55),
            sprites["nlo"].clone().set_position(4, 40),
            sprites["nlo"].clone().set_position(4, 45),
            sprites["nlo"].clone().set_position(4, 50),
            sprites["nlo"].clone().set_position(9, 50),
            sprites["nlo"].clone().set_position(4, 55),
            sprites["nlo"].clone().set_position(9, 55),
            sprites["nlo"].clone().set_position(14, 55),
            sprites["nlo"].clone().set_position(4, 45),
            sprites["nlo"].clone().set_position(34, 0),
            sprites["nlo"].clone().set_position(59, 10),
            sprites["nlo"].clone().set_position(59, 5),
            sprites["nlo"].clone().set_position(29, 30),
            sprites["nlo"].clone().set_position(54, 10),
            sprites["nlo"].clone().set_position(24, 30),
            sprites["nlo"].clone().set_position(34, 30),
            sprites["nlo"].clone().set_position(49, 35),
            sprites["nlo"].clone().set_position(49, 40),
            sprites["nlo"].clone().set_position(49, 45),
            sprites["nlo"].clone().set_position(49, 50),
            sprites["nlo"].clone().set_position(44, 50),
            sprites["nlo"].clone().set_position(49, 30),
            sprites["nlo"].clone().set_position(54, 5),
            sprites["nlo"].clone().set_position(44, 45),
            sprites["nlo"].clone().set_position(39, 50),
            sprites["nlo"].clone().set_position(44, 40),
            sprites["nlo"].clone().set_position(34, 50),
            sprites["nlo"].clone().set_position(39, 45),
            sprites["nlo"].clone().set_position(49, 25),
            sprites["nlo"].clone().set_position(19, 10),
            sprites["nlo"].clone().set_position(14, 30),
            sprites["nlo"].clone().set_position(44, 30),
            sprites["nlo"].clone().set_position(49, 5),
            sprites["nlo"].clone().set_position(24, 10),
            sprites["nlo"].clone().set_position(34, 25),
            sprites["nlo"].clone().set_position(19, 30),
            sprites["nlo"].clone().set_position(34, 15),
            sprites["nlo"].clone().set_position(29, 10),
            sprites["nlo"].clone().set_position(9, 45),
            sprites["nlo"].clone().set_position(14, 50),
            sprites["nlo"].clone().set_position(14, 25),
            sprites["nlo"].clone().set_position(44, 35),
            sprites["nlo"].clone().set_position(14, 15),
            sprites["nlo"].clone().set_position(34, 10),
            sprites["nlo"].clone().set_position(14, 10),
            sprites["pca"].clone().set_position(24, 50),
            sprites["qqv"].clone().set_position(24, 25),
            sprites["rzt"].clone().set_position(55, 51),
            sprites["rzt"].clone().set_position(55, 36),
            sprites["snw"].clone().set_position(53, 49),
            sprites["tuv"].clone().set_position(1, 53),
            sprites["ulq"].clone().set_position(53, 34),
            sprites["ulq"].clone().set_position(53, 49),
            sprites["vxy"].clone().set_position(29, 25),
            sprites["zba"].clone().set_position(45, 26),
            sprites["zba"].clone().set_position(10, 41),
            sprites["zba"].clone().set_position(55, 16),
            sprites["zba"].clone().set_position(45, 6),
            sprites["zba"].clone().set_position(20, 16),
        ],
        grid_size=(64, 64),
        data={
            "vxy": 42,
            "tuv": [5, 0],
            "nlo": [9, 8],
            "opw": [90, 90],
            "qqv": 0,
            "ggk": 14,
            "fij": 0,
            "kdy": False,
        },
        name="lyd",
    ),
    # fij
    Level(
        sprites=[
            sprites["hep"].clone().set_position(1, 53),
            sprites["hul"].clone().set_position(27, 48),
            sprites["kdj"].clone().set_position(3, 55).set_scale(2),
            sprites["kdy"].clone().set_position(54, 20),
            sprites["lhs"].clone().set_position(29, 50),
            sprites["mgu"].clone(),
            sprites["nlo"].clone().set_position(4, 0),
            sprites["nlo"].clone().set_position(9, 0),
            sprites["nlo"].clone().set_position(4, 5),
            sprites["nlo"].clone().set_position(14, 0),
            sprites["nlo"].clone().set_position(19, 0),
            sprites["nlo"].clone().set_position(24, 0),
            sprites["nlo"].clone().set_position(29, 0),
            sprites["nlo"].clone().set_position(39, 0),
            sprites["nlo"].clone().set_position(44, 0),
            sprites["nlo"].clone().set_position(49, 0),
            sprites["nlo"].clone().set_position(54, 0),
            sprites["nlo"].clone().set_position(59, 0),
            sprites["nlo"].clone().set_position(4, 10),
            sprites["nlo"].clone().set_position(4, 15),
            sprites["nlo"].clone().set_position(4, 20),
            sprites["nlo"].clone().set_position(4, 25),
            sprites["nlo"].clone().set_position(4, 30),
            sprites["nlo"].clone().set_position(4, 35),
            sprites["nlo"].clone().set_position(59, 15),
            sprites["nlo"].clone().set_position(59, 20),
            sprites["nlo"].clone().set_position(59, 25),
            sprites["nlo"].clone().set_position(59, 30),
            sprites["nlo"].clone().set_position(59, 20),
            sprites["nlo"].clone().set_position(59, 25),
            sprites["nlo"].clone().set_position(59, 30),
            sprites["nlo"].clone().set_position(59, 35),
            sprites["nlo"].clone().set_position(59, 40),
            sprites["nlo"].clone().set_position(59, 45),
            sprites["nlo"].clone().set_position(59, 35),
            sprites["nlo"].clone().set_position(59, 40),
            sprites["nlo"].clone().set_position(59, 45),
            sprites["nlo"].clone().set_position(59, 50),
            sprites["nlo"].clone().set_position(59, 55),
            sprites["nlo"].clone().set_position(59, 50),
            sprites["nlo"].clone().set_position(59, 55),
            sprites["nlo"].clone().set_position(54, 55),
            sprites["nlo"].clone().set_position(49, 55),
            sprites["nlo"].clone().set_position(44, 55),
            sprites["nlo"].clone().set_position(39, 55),
            sprites["nlo"].clone().set_position(34, 55),
            sprites["nlo"].clone().set_position(29, 55),
            sprites["nlo"].clone().set_position(24, 55),
            sprites["nlo"].clone().set_position(19, 55),
            sprites["nlo"].clone().set_position(4, 40),
            sprites["nlo"].clone().set_position(4, 45),
            sprites["nlo"].clone().set_position(4, 50),
            sprites["nlo"].clone().set_position(9, 50),
            sprites["nlo"].clone().set_position(4, 55),
            sprites["nlo"].clone().set_position(9, 55),
            sprites["nlo"].clone().set_position(14, 55),
            sprites["nlo"].clone().set_position(4, 45),
            sprites["nlo"].clone().set_position(34, 0),
            sprites["nlo"].clone().set_position(59, 10),
            sprites["nlo"].clone().set_position(59, 5),
            sprites["nlo"].clone().set_position(24, 40),
            sprites["nlo"].clone().set_position(49, 10),
            sprites["nlo"].clone().set_position(49, 5),
            sprites["nlo"].clone().set_position(39, 20),
            sprites["nlo"].clone().set_position(29, 20),
            sprites["nlo"].clone().set_position(24, 25),
            sprites["nlo"].clone().set_position(49, 15),
            sprites["nlo"].clone().set_position(24, 20),
            sprites["nlo"].clone().set_position(34, 20),
            sprites["nlo"].clone().set_position(39, 45),
            sprites["nlo"].clone().set_position(34, 40),
            sprites["nlo"].clone().set_position(24, 45),
            sprites["nlo"].clone().set_position(34, 45),
            sprites["nlo"].clone().set_position(24, 50),
            sprites["nlo"].clone().set_position(34, 50),
            sprites["nlo"].clone().set_position(49, 20),
            sprites["nlo"].clone().set_position(39, 40),
            sprites["nlo"].clone().set_position(54, 40),
            sprites["nlo"].clone().set_position(19, 50),
            sprites["nlo"].clone().set_position(34, 20),
            sprites["nlo"].clone().set_position(24, 35),
            sprites["nlo"].clone().set_position(39, 50),
            sprites["nlo"].clone().set_position(44, 20),
            sprites["nlo"].clone().set_position(9, 45),
            sprites["nlo"].clone().set_position(14, 50),
            sprites["nlo"].clone().set_position(19, 45),
            sprites["pca"].clone().set_position(14, 10),
            sprites["qqv"].clone().set_position(9, 40),
            sprites["rzt"].clone().set_position(30, 51),
            sprites["snw"].clone().set_position(28, 49),
            sprites["tuv"].clone().set_position(1, 53),
            sprites["ulq"].clone().set_position(28, 49),
            sprites["vxy"].clone().set_position(19, 40),
            sprites["zba"].clone().set_position(55, 6),
            sprites["zba"].clone().set_position(30, 26),
            sprites["zba"].clone().set_position(55, 51),
            sprites["zba"].clone().set_position(15, 46),
            sprites["zba"].clone().set_position(15, 21),
            sprites["zba"].clone().set_position(45, 6),
        ],
        grid_size=(64, 64),
        data={
            "vxy": 42,
            "tuv": 0,
            "nlo": 8,
            "opw": 180,
            "qqv": 1,
            "ggk": 12,
            "fij": 0,
            "kdy": True,
        },
        name="fij",
    ),
]


BACKGROUND_COLOR = 3
PADDING_COLOR = 3


class jvq(RenderableUserDisplay):
    zba: List[Tuple[int, int]]

    def __init__(self, vxy: "Ls20", ulq: int):
        self.tuv = vxy
        self.tmx = ulq
        self.snw = ulq

    def rzt(self, qqv: int) -> None:
        self.snw = max(0, min(qqv, self.tmx))

    def pca(self) -> bool:
        if self.snw >= 0:
            self.snw -= 1
        return self.snw >= 0

    def opw(self) -> None:
        self.snw = self.tmx

    def render_interface(self, frame: np.ndarray) -> np.ndarray:
        if self.tmx == 0 or self.tuv.xhp:
            return frame

        nlo = 1.5
        if self.tuv.qee:
            for hhe in range(64):
                for dcv in range(64):
                    if math.dist((hhe, dcv), (self.tuv.mgu.y + nlo, self.tuv.mgu.x + nlo)) > 20.0:
                        frame[hhe, dcv] = 5

            if self.tuv.nio and self.tuv.nio.is_visible:
                nio = self.tuv.nio.render()
                mgu = 3
                lyd = 55
                for hhe in range(6):
                    for w in range(6):
                        if nio[hhe][w] != -1:
                            frame[lyd + hhe, mgu + w] = nio[hhe][w]

        for hhe in range(self.tmx):
            mgu = 13 + hhe
            lyd = 61
            frame[lyd : lyd + 2, mgu] = 11 if self.tmx - hhe - 1 < self.snw else 3

        for lhs in range(3):
            mgu = 56 + 3 * lhs
            lyd = 61
            for x in range(2):
                frame[lyd : lyd + 2, mgu + x] = 8 if self.tuv.lbq > lhs else 3
        return frame


class Ls20(ARCBaseGame):
    def __init__(self) -> None:
        dcb = levels[0].get_data("vxy") if levels else 0
        fij = dcb if dcb else 0
        self.ggk = jvq(self, fij)
        self.hep = []
        self.hul = [12, 9, 14, 8]
        self.kdj = [0, 90, 180, 270]

        self.hep.append(sprites["opw"])
        self.hep.append(sprites["lyd"])
        self.hep.append(sprites["tmx"])
        self.hep.append(sprites["nio"])
        self.hep.append(sprites["dcb"])
        self.hep.append(sprites["fij"])
        self.qee = False

        super().__init__("ls20", levels, Camera(0, 0, 16, 16, BACKGROUND_COLOR, PADDING_COLOR, [self.ggk]), False, 1, [1, 2, 3, 4])

        self.krg()

    def krg(self) -> None:
        fig = self.current_level.get_data("vxy")
        if fig:
            self.ggk.tmx = fig
            self.ggk.opw()

    def on_set_level(self, level: Level) -> None:
        self.mgu = self.current_level.get_sprites_by_tag("caf")[0]
        self.nio = self.current_level.get_sprites_by_tag("wex")[0]
        self.nlo = self.current_level.get_sprites_by_tag("nfq")[0]
        self.opw = self.current_level.get_sprites_by_tag("fng")[0]
        self.pca = self.current_level.get_sprites_by_tag("axa")
        self.qqv = self.current_level.get_sprites_by_tag("mae")
        self.rzt = [False] * len(self.pca)

        self.snw = 0
        self.tmx = 0
        self.tuv = 0
        self.krg()

        self.cjl = []
        self.vxy = []
        self.qee = self.current_level.get_data("kdy")

        self.gfy = self.current_level.get_data("tuv")
        if isinstance(self.gfy, int):
            self.gfy = [self.gfy]

        yxt = self.current_level.get_data("opw")
        if isinstance(yxt, int):
            yxt = [yxt]

        lxu = self.current_level.get_data("nlo")
        if isinstance(lxu, int):
            lxu = [lxu]

        for dqk in range(len(self.qqv)):
            self.cjl.append(self.kdj.index(yxt[dqk]))
            self.vxy.append(self.hul.index(lxu[dqk]))
            self.pca[dqk].pixels = self.hep[self.gfy[dqk]].pixels.copy()
            self.pca[dqk].color_remap(0, self.hul[self.vxy[dqk]])
            self.pca[dqk].set_rotation(self.kdj[self.cjl[dqk]])

        self.pxr()
        self.egb = sprites["krg"].clone()
        self.current_level.add_sprite(self.egb)
        self.egb.set_visible(False)
        self.lbq = 3
        self.vcn: List[Sprite] = []
        self.bzf: List[Sprite] = []
        self.osd: List[Sprite] = []
        self.xhp = False
        self.kbj = False
        self.rjw = self.mgu.x
        self.qbn = self.mgu.y

    def rbt(self, edo: int, cdg: int, hds: int, xwr: int) -> List[Sprite]:
        oyx = self.current_level._sprites
        return [bes for bes in oyx if bes.x >= edo and bes.x < edo + hds and bes.y >= cdg and bes.y < cdg + xwr]

    def step(self) -> None:
        if self.xhp:
            self.egb.set_visible(False)
            self.nio.set_visible(True)
            self.xhp = False
            self.complete_action()
            return

        if self.kbj:
            self.nlo.color_remap(None, 5)
            self.kbj = False
            self.complete_action()
            return

        lgr = 0
        kyr = 0
        axv = False
        if self.action.id.value == 1:
            kyr = -1
            axv = True
        elif self.action.id.value == 2:
            kyr = 1
            axv = True
        elif self.action.id.value == 3:
            lgr = -1
            axv = True
        elif self.action.id.value == 4:
            lgr = 1
            axv = True

        if not axv:
            self.complete_action()
            return

        xpb = False
        qul, cfy = self.mgu.x + lgr * 5, self.mgu.y + kyr * 5
        yet = self.rbt(qul, cfy, 5, 5)

        mnc = False
        for oib in yet:
            if oib.tags is None:
                break
            elif "jdd" in oib.tags:
                mnc = True
                break
            elif "mae" in oib.tags:
                qzq = self.qqv.index(oib)
                if not self.qhg(qzq):
                    self.nlo.color_remap(None, 0)
                    self.kbj = True
                    return
            elif "iri" in oib.tags:
                xpb = True
                self.ggk.rzt(self.ggk.tmx)
                self.vcn.append(oib)
                self.current_level.remove_sprite(oib)
            elif "gsu" in oib.tags:
                self.snw = (self.snw + 1) % len(self.hep)
                self.nio.pixels = self.hep[self.snw].pixels.copy()
                self.nio.color_remap(0, self.hul[self.tmx])
                self.ihm()
            elif "gic" in oib.tags:
                apq = (self.tmx + 1) % len(self.hul)
                self.nio.color_remap(self.hul[self.tmx], self.hul[apq])
                self.tmx = apq
                self.ihm()
            elif "bgt" in oib.tags:
                self.tuv = (self.tuv + 1) % 4
                self.nio.set_rotation(self.kdj[self.tuv])
                self.ihm()

        if not mnc:
            self.mgu.set_position(qul, cfy)

        if self.nje():
            self.next_level()
            self.complete_action()
            return

        if not xpb and not self.ggk.pca():
            self.lbq -= 1
            if self.lbq == 0:
                self.lose()
                self.complete_action()
                return
            self.egb.set_visible(True)
            self.egb.set_scale(64)
            self.egb.set_position(0, 0)
            self.nio.set_visible(False)

            self.xhp = True
            self.rzt = [False] * len(self.qqv)
            self.mgu.set_position(self.rjw, self.qbn)
            self.pxr()
            for bqs in self.vcn:
                self.current_level.add_sprite(bqs)
            for grk in self.bzf:
                self.current_level.add_sprite(grk)
            for qmb in self.osd:
                self.current_level.add_sprite(qmb)
            self.vcn = []
            self.bzf = []
            self.osd = []
            self.ggk.rzt(self.ggk.tmx)
            self.opw.set_visible(False)
            for sfs in self.current_level.get_sprites_by_tag("qex"):
                sfs.set_visible(False)
            for pqv in self.current_level.get_sprites_by_tag("yar"):
                pqv.set_visible(True)
            return
        self.complete_action()

    def pxr(self) -> None:
        self.tuv = self.kdj.index(self.current_level.get_data("fij"))
        self.tmx = self.hul.index(self.current_level.get_data("ggk"))
        self.snw = self.current_level.get_data("qqv")
        self.nio.pixels = self.hep[self.snw].pixels.copy()
        self.nio.color_remap(0, self.hul[self.tmx])
        self.nio.set_rotation(self.kdj[self.tuv])

    def ihm(self) -> None:
        kic = False
        for fxn, qis in enumerate(self.qqv):
            dbb = self.current_level.get_sprite_at(qis.x - 1, qis.y - 1, "qex")
            if self.qhg(fxn) and not self.rzt[fxn]:
                kic = True
                if dbb:
                    dbb.set_visible(True)
            else:
                if dbb:
                    dbb.set_visible(False)
        self.opw.set_visible(kic)

    def qhg(self, azz: int) -> bool:
        return self.snw == self.gfy[azz] and self.tmx == self.vxy[azz] and self.tuv == self.cjl[azz]

    def nje(self) -> bool:
        for uop, ywm in enumerate(self.qqv):
            if not self.rzt[uop] and self.mgu.x == ywm.x and self.mgu.y == ywm.y and self.qhg(uop):
                self.rzt[uop] = True
                self.bzf.append(self.qqv[uop])

                self.osd.append(self.pca[uop])
                self.current_level.remove_sprite(self.qqv[uop])
                self.current_level.remove_sprite(self.pca[uop])

                xkp = self.current_level.get_sprite_at(ywm.x - 1, ywm.y - 1, "yar")
                if xkp and "vdr" in xkp.tags:
                    xkp.set_visible(False)
                    aoj = self.current_level.get_sprite_at(ywm.x - 1, ywm.y - 1, "qex")
                    if aoj:
                        aoj.set_visible(False)
                    self.opw.set_visible(False)

        for uop in range(len(self.rzt)):
            if not self.rzt[uop]:
                return False
        return True
