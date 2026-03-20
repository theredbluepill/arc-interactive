"""hn04: four-peg Hanoi — ACTION1–4 pick peg; ACTION5 pick/drop."""

from arcengine import ARCBaseGame, Camera, GameAction, Level, RenderableUserDisplay, Sprite

BG, PAD = 5, 4


class U(RenderableUserDisplay):
    def render_interface(self, f):
        return f


PEGX = (1, 4, 7, 10)
BASEY = 9


def spr():
    return {
        "d1": Sprite(
            pixels=[[11]],
            name="d1",
            visible=True,
            collidable=False,
            tags=["disk", "1"],
        ),
        "d2": Sprite(
            pixels=[[12]],
            name="d2",
            visible=True,
            collidable=False,
            tags=["disk", "2"],
        ),
        "d3": Sprite(
            pixels=[[13]],
            name="d3",
            visible=True,
            collidable=False,
            tags=["disk", "3"],
        ),
        "d4": Sprite(
            pixels=[[14]],
            name="d4",
            visible=True,
            collidable=False,
            tags=["disk", "4"],
        ),
        "peg": Sprite(
            pixels=[[3]],
            name="peg",
            visible=True,
            collidable=True,
            tags=["peg"],
        ),
    }


s = spr()


def lvl(d):
    parts = [s["peg"].clone().set_position(x, BASEY) for x in PEGX]
    parts += [
        s["d4"].clone().set_position(1, BASEY - 1),
        s["d3"].clone().set_position(1, BASEY - 2),
        s["d2"].clone().set_position(1, BASEY - 3),
        s["d1"].clone().set_position(1, BASEY - 4),
    ]
    return Level(sprites=parts, grid_size=(12, 12), data={"difficulty": d})


levels = [lvl(i) for i in range(1, 8)]


class Hn04(ARCBaseGame):
    def __init__(self) -> None:
        super().__init__(
            "hn04",
            levels,
            Camera(0, 0, 16, 16, BG, PAD, [U()]),
            False,
            1,
            [1, 2, 3, 4, 5],
        )

    def on_set_level(self, level: Level) -> None:
        self._st = [[4, 3, 2, 1], [], [], []]
        self._hand = None
        self._peg = 0
        self._ds: dict[int, Sprite | None] = {1: None, 2: None, 3: None, 4: None}
        for sp in self.current_level._sprites:
            if "disk" not in sp.tags:
                continue
            for t in sp.tags:
                if t.isdigit():
                    self._ds[int(t)] = sp
        self._layout()

    def _layout(self) -> None:
        for pi, stack in enumerate(self._st):
            x = PEGX[pi]
            for i, sz in enumerate(stack):
                sp = self._ds[sz]
                if sp is not None:
                    sp.set_position(x, BASEY - 1 - i)
        if self._hand:
            sp = self._ds[self._hand]
            if sp is not None:
                sp.set_position(PEGX[self._peg], 2)

    def step(self) -> None:
        v = self.action.id.value
        if v in (1, 2, 3, 4):
            self._peg = v - 1
        elif self.action.id == GameAction.ACTION5:
            st = self._st[self._peg]
            if self._hand is None and st:
                self._hand = st.pop()
            elif self._hand is not None:
                top = st[-1] if st else 99
                if top > self._hand:
                    st.append(self._hand)
                    self._hand = None
        self._layout()
        if self._st[3] == [4, 3, 2, 1]:
            self.next_level()
        self.complete_action()
