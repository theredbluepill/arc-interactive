"""cw01: 2-SAT style — literals on a line; **ACTION6** toggles; all clauses must have a true literal."""

from __future__ import annotations

from arcengine import ARCBaseGame, Camera, GameAction, Level, RenderableUserDisplay, Sprite

BG, PAD = 5, 4
CAM = 16


class Cw01UI(RenderableUserDisplay):
    def render_interface(self, frame):
        return frame


def lit(x, y, var: int, neg: bool):
    c = 8 if neg else 9
    return Sprite(
        pixels=[[c]],
        name="l",
        visible=True,
        collidable=False,
        tags=["lit", f"v{var}", "neg" if neg else "pos"],
    ).clone().set_position(x, y)


def mk(clauses: list[list[tuple[int, int, int, bool]]], d: int) -> Level:
    sl: list[Sprite] = []
    for ci, cl in enumerate(clauses):
        for x, y, v, ng in cl:
            sl.append(lit(x, y + ci * 3, v, ng))
    return Level(
        sprites=sl,
        grid_size=(12, 12),
        data={"clauses": clauses, "difficulty": d},
    )


levels = [
    mk([[(2, 1, 0, False), (4, 1, 1, True)], [(2, 1, 1, False), (4, 1, 0, True)]], 1),
    mk(
        [
            [(1, 1, 0, False), (3, 1, 1, False)],
            [(5, 1, 0, True), (7, 1, 1, True)],
            [(2, 1, 0, True), (6, 1, 1, False)],
        ],
        2,
    ),
    mk([[(2, 2, 0, False), (5, 2, 0, True)], [(3, 2, 1, False), (6, 2, 1, True)]], 3),
    mk([[(1, 1, 0, False)], [(3, 1, 0, True)], [(5, 1, 1, False)]], 4),
    mk([[(2, 1, 0, False), (4, 1, 1, True), (6, 1, 0, True)]], 5),
    mk([[(1, 1, 0, False), (4, 1, 1, False)], [(2, 1, 0, True), (5, 1, 1, True)]], 6),
    mk([[(2, 1, 0, False), (5, 1, 1, True)], [(3, 1, 1, False), (6, 1, 0, True)], [(4, 1, 0, True), (7, 1, 1, False)]], 7),
]


class Cw01(ARCBaseGame):
    def __init__(self) -> None:
        super().__init__(
            "cw01",
            levels,
            Camera(0, 0, CAM, CAM, BG, PAD, [Cw01UI()]),
            False,
            1,
            [6],
        )

    def on_set_level(self, level: Level) -> None:
        self._val = [False, False]
        self._clauses = level.get_data("clauses")

    def _sat(self) -> bool:
        for cl in self._clauses:
            ok = False
            for _x, _y, v, neg in cl:
                t = self._val[int(v) % 2]
                if neg:
                    t = not t
                if t:
                    ok = True
            if not ok:
                return False
        return True

    def step(self) -> None:
        if self.action.id != GameAction.ACTION6:
            self.complete_action()
            return
        c = self.camera.display_to_grid(
            self.action.data.get("x", 0), self.action.data.get("y", 0)
        )
        if c:
            sp = self.current_level.get_sprite_at(
                int(c[0]), int(c[1]), ignore_collidable=True
            )
            if sp and "lit" in sp.tags:
                for t in sp.tags:
                    if t.startswith("v") and t[1:].isdigit():
                        vi = int(t[1:]) % 2
                        self._val[vi] = not self._val[vi]
                        break
        if self._sat():
            self.next_level()
        self.complete_action()
