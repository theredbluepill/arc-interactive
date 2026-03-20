# Games

| Game | Category | Grid | Levels | Description | Preview | Actions |
|------|----------|------|--------|-------------|---------|---------|
| ez01 | Tutorial / Movement Basics | 8×8 | 5 | Go UP to reach the target. | ![ez01](assets/ez01.gif) | • 1-4: Movement |
| ez02 | Tutorial / Movement Basics | 8×8 | 5 | Go LEFT to reach the target. | ![ez02](assets/ez02.gif) | • 1-4: Movement |
| ez03 | Tutorial / Movement Basics | 8×8 | 5 | Go RIGHT to reach the target. | ![ez03](assets/ez03.gif) | • 1-4: Movement |
| ez04 | Tutorial / Movement Basics | 8×8 | 5 | Go DOWN to reach the target. | ![ez04](assets/ez04.gif) | • 1-4: Movement |
| ul01 | Puzzle Mechanics | 8×8 | 5 | Pick up the key to unlock the door and advance. | ![ul01](assets/ul01.gif) | • 1-4: Movement |
| tt01 | Collection | 8-24 | 3 | Collection game. Navigate grid to collect yellow targets while avoiding red hazards (static collidable cells). | ![tt01](assets/tt01.gif) | • 1-4: Movement |
| wm01 | Survival / Timing | 32×32 | 5 | Whack-a-Mole! Click moles before they escape. Meet checkpoint requirements or lose. | ![wm01](assets/wm01.gif) | • 6: Click |
| sv01 | Survival / Timing | 8-24 | 5 | Survival game. Manage hunger and warmth. Green food restores hunger; orange warm zones stop warmth loss. Survive 60 frames to advance. | ![sv01](assets/sv01.gif) | • 1-4: Movement • 5: Idle (wait) |
| pt01 | Pattern Puzzles | 64×64 | 5 | Pattern rotation puzzle. Click tiles to rotate them 90° clockwise and match the target pattern. | ![pt01](assets/pt01.gif) | • 6: Click/Rotate |
| sy01 | Pattern Puzzles | 11×11 | 5 | Mirror Maker. Mirror the pattern from the left side onto the right side. Create a perfect reflection! | ![sy01](assets/sy01.gif) | • 6: Click (place/remove block) |
| sk01 | Environmental Manipulation | 8-12 | 5 | Sokoban. Push blocks onto target pads. Green = placed. Wall blockers ramp up by level. Step limit exceeded = lose. | ![sk01](assets/sk01.gif) | • 1-4: Movement |
| tb01 | Environmental Manipulation | 24×24 | 5 | Bridge Builder. **Multi-island** routes (waypoints + optional reef clusters); bridge open water (ACTION6), walk island-to-island to the green goal. Later levels add **max_bridges** / **step_limit**; blue ticks show level index. Swimming costs a life. | ![tb01](assets/tb01.gif) | • 1-4: Movement • 6: Toggle bridge on water (click) |
| ff01 | Precision / Topology | 64×64 | 5 | Flood fill: click inside **closed** regions to paint them yellow. Five levels mix **rectangles**, **donut/ring**, and **C-bays** with ramping shape count. Sq01-style click ripple in final frame space; **ACTION1–4** are no-ops (pacing). | ![ff01](assets/ff01.gif) | • 1-4: No-op • 6: Click |
| mm01 | Memory / Hidden State | 64×64 | 7 | Memory Match. Level 1 has 2 pairs, then +1 pair per level up to 8 pairs. Flip pairs of hidden tiles to find matching colors. Match all pairs to win. Time runs out = lose. | ![mm01](assets/mm01.gif) | • 6: Click tile |
| ms01 | Memory / Hidden State | 8-16 | 5 | Blind Sapper. Navigate a hidden minefield using deduction. Safe tiles reveal adjacent mine counts. Step on a mine = lose. Reach the goal to win. Tests working memory and deductive planning. | ![ms01](assets/ms01.gif) | • 1-4: Movement |
| sq01 | Sequencing / Ordering | 12×12 | 5 | Sequencing. Click colored blocks in the correct order. Follow the sequence shown at the top! | ![sq01](assets/sq01.gif) | • 6: Click block |
| rs01 | Cognitive Flexibility / Rule Switching | 8-16 | 5 | Rule Switcher. Collect colored targets that match the signpost color at top. Wrong color = lose. After all colors cycle through as safe, collect remaining targets. Tests cognitive flexibility and rule adaptation. | ![rs01](assets/rs01.gif) | • 1-4: Movement |
| pb01 | Environmental Manipulation | 8-10 | 5 | One-box push. Single crate and one goal per level; push the block onto the yellow pad. Step limit exceeded = lose. | ![pb01](assets/pb01.gif) | • 1-4: Movement |
| fs01 | Puzzle Mechanics | 8-10 | 5 | Floor switches. Step on every yellow pressure plate (any order) to open the gray door, then reach the green goal. | ![fs01](assets/fs01.gif) | • 1-4: Movement |
| tp01 | Puzzle Mechanics | 8-10 | 5 | Teleporters. Paired magenta portals warp you to each other; reach the yellow goal. | ![tp01](assets/tp01.gif) | • 1-4: Movement |
| ic01 | Puzzle Mechanics | 8-10 | 5 | Ice slide. Each move slides in a straight line until a wall or red hazard stops you; reach the yellow goal. | ![ic01](assets/ic01.gif) | • 1-4: Movement |
| va01 | Coverage / Path | 4-8 | 5 | Visit all. Walk on every walkable floor cell at least once to clear the level. | ![va01](assets/va01.gif) | • 1-4: Movement |
| pb02 | Environmental Manipulation | 8-10 | 5 | Two crates, two yellow goals; push both blocks onto pads (sk01-style). | ![pb02](assets/pb02.gif) | • 1-4: Movement |
| pb03 | Environmental Manipulation | 8-10 | 5 | Decoy orange pad — pushing a crate onto it loses; real goals stay yellow. | ![pb03](assets/pb03.gif) | • 1-4: Movement |
| fs02 | Puzzle Mechanics | 8-10 | 5 | Floor switches **OR**: stepping on **any** plate opens the door (not all plates). | ![fs02](assets/fs02.gif) | • 1-4: Movement |
| fs03 | Puzzle Mechanics | 8-10 | 5 | Floor switches **sequence**: plates must be stepped in **level sprite order**. | ![fs03](assets/fs03.gif) | • 1-4: Movement |
| tp02 | Puzzle Mechanics | 8-10 | 5 | **Directed** warps only (`directed_pairs` in level data); no reverse hop from destination. | ![tp02](assets/tp02.gif) | • 1-4: Movement |
| tp03 | Puzzle Mechanics | 8-10 | 5 | **Single-use** portals — both tiles removed after one warp. | ![tp03](assets/tp03.gif) | • 1-4: Movement |
| ic02 | Puzzle Mechanics | 8-10 | 5 | **Torus** ice slide: wraps at grid edges until a wall/hazard stops you. | ![ic02](assets/ic02.gif) | • 1-4: Movement |
| ic03 | Puzzle Mechanics | 8-10 | 5 | **Capped** slide: each move travels at most `slide_cap` cells (`level.data`). | ![ic03](assets/ic03.gif) | • 1-4: Movement |
| va02 | Coverage / Path | 4-8 | 5 | Visit every **non-hazard** floor cell; red hazard cells never need coverage. | ![va02](assets/va02.gif) | • 1-4: Movement |
| va03 | Coverage / Path | 4-8 | 5 | **Ordered** visit cells (`visit_order` in level data) before finishing. | ![va03](assets/va03.gif) | • 1-4: Movement |
| nw01 | Puzzle Mechanics | 8-10 | 5 | Arrow tiles (`arrows` in level data) **force** the next cardinal step. | ![nw01](assets/nw01.gif) | • 1-4: Movement |
| bd01 | Coverage / Path | 5-8 | 5 | **No revisits** — entering any cell twice loses; reach the goal. | ![bd01](assets/bd01.gif) | • 1-4: Movement |
| gr01 | Puzzle Mechanics | 8-10 | 5 | **Gravity**: after each move, one auto-step in the level’s gravity direction. | ![gr01](assets/gr01.gif) | • 1-4: Movement |
| dt01 | Puzzle Mechanics | 8-10 | 5 | **Waypoint** (cyan) must be stepped before the yellow goal counts. | ![dt01](assets/dt01.gif) | • 1-4: Movement |
| wk01 | Puzzle Mechanics | 8-10 | 5 | **Weak floor**: brown tiles collapse to holes after you leave; holes are lethal. | ![wk01](assets/wk01.gif) | • 1-4: Movement |
| rf01 | Puzzle Mechanics | 8-10 | 5 | **Mirror half-plane**: on `x >= mid`, left/right inputs are swapped. | ![rf01](assets/rf01.gif) | • 1-4: Movement |
| mo01 | Puzzle Mechanics | 8-10 | 5 | **Momentum**: need **≥2** steps in a row before changing direction; early turn = lose. | ![mo01](assets/mo01.gif) | • 1-4: Movement |
| zq01 | Puzzle Mechanics | 8-10 | 5 | **Zone timer**: blinking red hazard cells toggle on a fixed period (`period`, `hazard_cells`). | ![zq01](assets/zq01.gif) | • 1-4: Movement |
| hm01 | Coverage / Path | 3-6 | 5 | **Hamiltonian** tour — every open cell **exactly once**; revisit = lose. | ![hm01](assets/hm01.gif) | • 1-4: Movement |
| ex01 | Puzzle Mechanics | 8-10 | 5 | **Exit hold**: stand on green exit pad and repeat **ACTION5** `hold_frames` times to clear. | ![ex01](assets/ex01.gif) | • 1-4: Movement • 5: Hold / charge exit |
| gp01 | Pattern Puzzles | 8×8 | 5 | **Grid paint**: **ACTION6** toggles yellow on cells to match gray hints; **ACTION1–4** are no-ops. | ![gp01](assets/gp01.gif) | • 1-4: No-op • 6: Click |
| lo01 | Pattern Puzzles | 3×3–5×5 | 5 | **Lights Out**: **ACTION6** toggles a cell and its neighbors; clear all lights. **ACTION1–4** are no-ops. | ![lo01](assets/lo01.gif) | • 1-4: No-op • 6: Click |
| lw01 | Path / Topology | 24–32 | 5 | **Line weave**: connect colored starts to matching ends with orthogonal paths; colors cannot share cells. |  | • 1–2: Prev/next color • 3–4: No-op • 5: Undo segment • 6: Extend path (click) |
| rp01 | Graph / Logic | 32×32 | 5 | **Relay pulse**: **ACTION6** toggles relays; **ACTION5** fires from the source; orthogonal relay chain must light every lamp (adjacent to a visited relay). |  | • 1–4: No-op • 5: Fire pulse • 6: Toggle relay |
| ml01 | Geometry | 24×24 | 5 | **Mirror laser**: steer a beam from the emitter to the receptor using placeable mirrors (**ACTION6** adjacent); **ACTION5** fires. |  | • 1–4: Move • 5: Fire laser • 6: Place/cycle mirror |
| sf01 | Pattern Puzzles | 64×64 | 5 | **Stencil paint**: move a 3×3 stencil with **ACTION1–4**; **ACTION6** paints all non-wall cells under it; match gray hints. |  | • 1–4: Move stencil • 6: Paint |
| ll01 | Simulation | 32×32 | 5 | **Generations lock**: Conway Life; **ACTION6** toggles cells (budget); **ACTION5** advances one generation; after exactly **N** steps the live set must equal the target. |  | • 1–4: No-op • 5: Step CA • 6: Toggle cell |
| wl01 | Environmental Manipulation | 32×32 | 5 | **Wall craft**: reach the goal; **ACTION5** toggles build mode; **ACTION6** places/removes your walls (shared budget). |  | • 1–4: Move • 5: Build mode • 6: Toggle my wall |
| dd01 | Logistics | 48×48 | 5 | **Drone relay**: pick up crates and deliver to yellow pads; **ACTION6** pings the nearest pad on the HUD. |  | • 1–4: Move • 5: Pickup/drop • 6: Ping pad |
| ck01 | Graph / Logic | 24×24 | 5 | **Circuit stitch**: **ACTION6** toggles wire; **ACTION5** tests whether the cyan input reaches the yellow output (limited checks). |  | • 1–4: No-op • 5: Test wire • 6: Toggle wire |
| ph01 | Field / Math | 24×24 | 5 | **Phase interference**: phases 0–3; **ACTION6** increments a cell; **ACTION5** applies (self + Σ orth neighbors) mod 4 on non-walls; match marked targets. |  | • 1–4: No-op • 5: Blur step • 6: Increment phase |
| bn01 | Exploration | 64×64 | 5 | **Beacon sweep**: hidden targets; **ACTION5** drops a beacon (Chebyshev radius); ghosts show only under light; **ACTION6** flags a cell (wrong cell = lose). |  | • 1–4: Move • 5: Beacon • 6: Flag |
| dl01 | Puzzle / Planning | 12×12 | 5 | **Delay line**: moves queue (max 3); each step runs the oldest pending move then enqueues the current direction; **ACTION6** clears the queue. |  | • 1-4: Enqueue move • 6: Clear queue |
| fw01 | Survival / Simulation | 24×24 | 5 | **Wildfire**: fire spreads on a timer; **ACTION6** splashes water (3×3); reach the green exit. |  | • 1-4: Move • 6: Splash |
| gp02 | Pattern Puzzles | 8×8 | 5 | **Grid paint erase**: floor starts fully painted; **ACTION6** erases yellow; leave paint only on gray hint cells. |  | • 1-4: No-op • 6: Click erase |
| hd01 | Survival / Timing | 16×16 | 5 | **Heat front**: a heat band advances south every N steps; **ACTION5** on a magenta station charges temporary immunity; reach the goal. |  | • 1-4: Move • 5: Charge on station |
| kn01 | Puzzle / Movement | 16×16 | 5 | **Knight’s courier**: **ACTION1–4** use L-shaped knight hops from the active bank; **ACTION5** toggles between two banks (eight directions total). |  | • 1-4: Knight move • 5: Toggle bank |
| lo02 | Pattern Puzzles | 4×4–6×6 | 5 | **Torus Lights Out**: **ACTION6** toggles a cell and orthogonal neighbors with edge wrap; walls block toggles on their cells. |  | • 1-4: No-op • 6: Click |
| mc01 | Coordination | 16×16 | 5 | **Tandem**: two players take the same Δ each step; **ACTION5** swaps which avatar is “lead” for collision resolution; both must reach their goals. |  | • 1-4: Joint move • 5: Swap lead |
| ng01 | Logic / Deduction | 8×8 | 5 | **Nonogram lite**: **ACTION1–4** move the cursor; **ACTION6** cycles empty / filled / mark; filled cells must match the hidden solution. |  | • 1-4: Cursor • 6: Cycle cell |
| ob01 | Multi-Agent | 16×16 | 5 | **Odd one out**: three bodies; **ACTION5** cycles which avatar **ACTION1–4** moves; each reaches its pad. |  | • 1-4: Move active • 5: Cycle active |
| pu01 | Graph / Plumbing | 16×16 | 5 | **Pipe twist**: **ACTION6** toggles horizontal vs vertical pipe on a cell; connect cyan source to yellow sink with orthogonal flow. |  | • 1-4: No-op • 6: Toggle pipe |
| qr01 | Pattern Puzzles | 8×8 | 5 | **Quad twist**: **ACTION6** rotates the 2×2 block of tiles anchored at the click clockwise; match the target pattern. |  | • 1-4: No-op • 6: Rotate 2×2 |
| rs02 | Cognitive Flexibility | 8-16 | 5 | **Dual safe**: collect targets matching **either** color of the active pair (`dual_pairs`); after all pairs have been safe, any remaining target is allowed. |  | • 1-4: Move |
| sk02 | Environmental Manipulation | 8-12 | 5 | **Sliding crate sokoban**: after a successful push, if the cell beyond the crate is empty, the crate slides one more step. |  | • 1-4: Move |
| sp01 | Simulation | 12×12 | 5 | **Sandpile**: **ACTION6** adds a grain; cells with ≥4 topple to neighbors; win when the grid is stable and total grains equals **target_sum**. |  | • 1-4: No-op • 6: Add grain |
| sq02 | Sequencing | 12×12 | 5 | **Shrinking queue**: like sequencing, but only the current expected color block is eligible/visible until unlocked; wrong order resets progress. |  | • 6: Click block |
| sv02 | Survival / Timing | 8-24 | 5 | **Shelter survival**: warmth decay pauses only inside magenta **shelter** zones; hunger rules unchanged; survive 60 steps per level. |  | • 1-4: Move • 5: Idle |
| tb02 | Environmental Manipulation | 24×24 | 5 | **Bridge decay**: like bridge builder, but a bridge sprite is removed when you **leave** that water cell. |  | • 1-4: Move • 6: Toggle bridge |
| tc01 | Puzzle / Fields | 16×16 | 5 | **Conveyor layer**: after each resolved move, you are pushed one more step by the arrow at your **destination** cell (`arrows` in level data). |  | • 1-4: Move |
| tt02 | Collection | 16-24 | 3 | **Patrol hazards**: collect yellow targets while red **patrol** hazards step along authored tracks (`patrols`) every player step. |  | • 1-4: Move |
| zm01 | Territory | 16×16 | 5 | **Flood duel**: two colors expand from seeds; **ACTION5** switches the active color; **ACTION6** claims a floor cell orthogonally adjacent to your region (cover a target fraction to win). |  | • 1-4: Move • 5: Switch color • 6: Expand |
| as01 | Logistics | 12×12 | 5 | **Assembly fetch**: **ACTION5** pickup/drop tagged parts; deliver to matching workstations in **order** from `level.data`. |  | • 1-4: Move • 5: Pickup/drop |
| bp01 | Graph / Power | 14×14 | 5 | **Battery mesh**: carry charge; drop on towers to link a range-1 power graph; goal activates when powered. |  | • 1-4: Move • 5: Charge pickup/drop |
| bn02 | Exploration | 64×64 | 5 | **Manhattan beacon**: like bn01 but reveal uses L1 (Manhattan) radius. |  | • 1-4: Move • 5: Beacon • 6: Flag |
| ck02 | Graph / Logic | 24×24 | 5 | **Circuit junction**: wire like ck01; on `junction` cells, **no right turn** relative to incoming wire direction. |  | • 1-4: No-op • 5: Test wire • 6: Toggle wire |
| cr01 | Environmental Manipulation | 16×16 | 5 | **Creek crossing**: limited **ACTION6** planks on river; planks break when you leave; reach the goal. |  | • 1-4: Move • 6: Place plank |
| dm01 | Tiling | 8×8 | 5 | **Domino cover**: **ACTION6** toggles dominoes on valid pairs; cover all marked cells once. |  | • 6: Toggle domino |
| ex02 | Puzzle Mechanics | 8-10 | 5 | **Sliding exit hold**: **ACTION5** on pad increments hold; moving only **decays** hold by 1 (not full reset). |  | • 1-4: Move • 5: Hold |
| fl01 | Path / Numberlink | 12×12 | 5 | **Numberlink**: connect numbered endpoints with paths of exact per-pair length; no overlap (`pairs`, `length` in data). |  | • 1-4: Cursor • 6: Extend/cut |
| ff02 | Precision / Topology | 64×64 | 5 | **Flood unpaint**: interiors start filled; **ACTION6** erases a clicked enclosure; gray hints must end empty. **ACTION1–4** no-op. |  | • 1-4: No-op • 6: Click erase region |
| gp03 | Pattern Puzzles | 8×8 | 5 | **Three-state grid paint**: cycle cell colors with **ACTION6**; match per-cell `goal` palette in data. |  | • 1-4: No-op • 6: Cycle paint |
| lw02 | Path / Topology | 24–32 | 5 | **Shared corridor weave**: like lw01 but paths may **share** cells; **perpendicular** entry to another color’s visited cell is forbidden. |  | • 1–2: Color • 3–4: No-op • 5: Undo • 6: Extend |
| ml02 | Geometry | 24×24 | 5 | **Dual-receptor laser**: **ACTION5** fires; beam must hit **all** receptors in one shot (beam passes through receptors). |  | • 1-4: Move • 5: Fire • 6: Mirror |
| mm02 | Memory / Hidden State | 64×64 | 5 | **Memory triples**: flip three tiles; clear when all three match color. |  | • 6: Click tile |
| ms02 | Memory / Hidden State | 8-16 | 5 | **Flag sapper**: **ACTION6** plants flags on hidden mines; wrong flag = lose; reach the goal. |  | • 1-4: Move • 6: Flag |
| mx01 | Puzzle Mechanics | 10×10 | 5 | **Maze melt**: **ACTION5** melts one adjacent wall segment (budget); reach exit when a path exists. |  | • 1-4: Move • 5: Melt |
| nw02 | Puzzle Mechanics | 8-12 | 5 | **Vector arrows**: arrow tiles **add** to a pending (dx,dy); next move executes the **sum** clamped to one step. |  | • 1-4: Move |
| ph02 | Field / Math | 24×24 | 5 | **Phase multiply**: **ACTION5** applies multiply-style update with orthogonal neighbors **mod N** (`mod_n` in data). |  | • 1-4: No-op • 5: Step • 6: Inc |
| pt02 | Pattern Puzzles | 64×64 | 5 | **Row/column rotate**: **ACTION6** rotates a full row **or** column of 3×3 tiles (nearest axis wins). |  | • 6: Click band |
| rp02 | Graph / Logic | 32×32 | 5 | **Pulse depth**: relays + **amplifiers** reset hop budget (`max_pulse_depth`); light all lamps. |  | • 1–4: No-op • 5: Fire • 6: Toggle relay |
| rz01 | Environmental Manipulation | 12×12 | 5 | **Rush grid**: push **1×2** cars along their axis like sokoban; clear the exit car. |  | • 1-4: Move |
| sg01 | Survival / Timing | 8×8 | 5 | **Signal lock**: sweeping cursor; **ACTION6** in the green window scores; miss shrinks the window. |  | • 1-4: No-op • 6: Commit |
| sk03 | Environmental Manipulation | 8-12 | 5 | **Sticky mud sokoban**: sliding crate chain **stops** on mud floor (`mud` tag); mud is walkable. |  | • 1-4: Move |
| st01 | Stealth | 16×16 | 5 | **Sentry sweep**: cone-vision guards; spotted = lose; **ACTION5** whistles to nudge a guard forward one cell. |  | • 1-4: Move • 5: Whistle |
| sy02 | Pattern Puzzles | 11×11 | 5 | **Staggered mirror**: mirror targets use half-row offset (`mirror_stagger` in data). |  | • 6: Place/remove block |
| tb03 | Environmental Manipulation | 24×24 | 5 | **Reef growth**: like bridge decay, plus random **rock** spawns on water every **M** steps (`reef_every`). |  | • 1-4: Move • 6: Toggle bridge |
| tg01 | Survival | 12×12 | 5 | **Tag evasion**: chaser moves every other step; survive **T** steps or reach a safe zone. |  | • 1-4: Move |
| tt03 | Collection | 16-24 | 3 | **Collector spawns**: patrol collection plus new yellow targets every **K** steps until cap (`spawn_every`, `target_cap`). |  | • 1-4: Move |
| ul02 | Puzzle Mechanics | 8-12 | 5 | **Two-key unlock**: key A before door A and key B before door B; wrong door order loses. |  | • 1-4: Move |
| wm02 | Survival / Timing | 32×32 | 5 | **Lane moles**: moles spawn in rotating lane columns; wrong-lane click while a mole is up costs a life. |  | • 6: Click |
| zq02 | Puzzle Mechanics | 8-10 | 5 | **Dual-phase hazards**: two independent blinking hazard sets with different `period` / phase offset in data. |  | • 1-4: Move |
