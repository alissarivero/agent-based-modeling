# ODD protocol: Forage Lab

This document follows the Overview, Design concepts, and Details (ODD) protocol for describing agent-based models (Grimm et al. 2006, 2010, 2020). It describes the v1 foraging model implemented in this repository. The model is a discrete-space, discrete-time ABM. It is not implemented in Mesa; the engine is a seeded NumPy loop so that every figure can be regenerated from a recorded configuration.

## 1. Purpose and patterns

The model compares three foraging strategies on match-paired landscapes under five social-spacing rules and two exposure schedules. The intended pattern is a strategy × landscape-class × social-condition × schedule factorial: how much reward agents collect, how many high-value cells they clear, and whether repeating the same map improves later episodes.

The model does **not** claim to fit human or animal data. It is a transparent experimental platform.

## 2. Entities, state variables, and scales

**Entities**

- *Landscape cell*: a square on an \(N \times N\) grid (\(N = 110\) by default) with an original reward in \([0, 1]\) and a residual reward that starts equal to the original value.
- *Agent*: a forager with type `{searcher, maximizer, random}`, integer coordinates, cumulative episode score, a Boolean `visited` map for the current episode, and a spatial memory (`seen`, `belief` of last observed positive values, `known_residual`). Unseen cells have no value; the first episode starts fully obscure.

**Scales**

- Space: one cell is one spatial unit. Movement and social distance use Chebyshev (chess-king) metric.
- Time: one tick is one sequential activation round. An episode lasts 200 ticks after the initial spawn collection. A session is five episodes.

**Match-paired landscapes**

Five density levels (target means 0.25, 0.35, 0.45, 0.55, 0.65) each produce a triplet: smooth, rough, and random maps that share the **exact same multiset of cell values**. Smooth and rough arrange those values by the rank order of Gaussian random fields (correlation lengths 18 and 5). Random permutes them. Spatial structure is therefore the only difference within a triplet.

## 3. Process overview and scheduling

1. Load the frozen landscape for `(triplet_id, landscape_class)` and copy it into residual.
2. Spawn agents (solo at center; attract pair on adjacent center cells; avoid pair five cells apart on the center row).
3. Each agent senses, collects the spawn cell, and senses again.
4. For ticks \(1 \ldots 200\):
   - Shuffle agent order with the session RNG.
   - For each agent: sense; filter legal moves by the social constraint against the partner’s **current** position; choose a policy move (or stay if none are legal); step; collect; sense.
5. Resources refill (or a new map is loaded) at the start of the next episode. Agents are **never told**. Episode 0 begins with a blank map: every cell is unknown until it enters the vision window. From episode 1 on, they keep `seen` / `belief` from the last grid and treat those remembered values as their prior. When they observe a cell again they overwrite the belief with whatever is actually there. On **repeat-five** that prior is the same landscape (now refilled). On **each-grid** it is the previous triplet member, which may be wrong.

## 4. Design concepts

**Basic principles.** Locally informed foraging on depleting patches, with hard social spacing.

**Emergence.** Joint coverage, competition on rich cells, learning on a repeated map, and interference when a silent map change makes last-grid memory wrong.

**Adaptation / objectives.** Searchers cover cells whose remembered residual is at least \(\tau = 0.7\). Maximizers climb `value / max(distance, 1)`. Random walkers ignore value.

**Sensing.** Chebyshev vision radius 7. Agents observe current residual in that square window and write it into memory. They never receive a cue that the landscape changed.

**Interaction.** Collection is exclusive: the first agent to occupy a cell in activation order takes its residual and zeros it. Social rules are hard filters, not preferences.

**Stochasticity.** Landscape library uses a fixed landscape seed. Session seed drives activation order, random walks, and policy tie-breaks.

**Collectives.** None beyond the temporary pair.

**Observation.** Per agent per episode: reward, unique cells visited, high-value cells that agent cleared, cells ever seen, path. Per episode: remaining reward, map-level high-value clearance, mean pairwise distance, constraint violations (must be 0).

## 5. Initialization

Default constants live in `sim.config.SimConfig`. Landscapes are generated once (`python -m sim`) and stored with SHA-256 checksums in `data/landscapes/manifest.json`. A mission specifies landscape class, triplet id, social condition, agent type(s), scheduler, and seed.

## 6. Input data

The model does not read external empirical time series. The only inputs are the frozen landscape library and the mission / batch specification.

## 7. Submodels

**Collection.** `score += residual[y, x]; residual[y, x] = 0`.

**Searcher.** Among seen, unvisited cells with remembered residual \(\ge \tau\), move to reduce Chebyshev distance to the nearest (RNG tie-break). Else move to the legal neighbor that maximizes the number of unseen cells inside the new vision window.

**Maximizer.** Among seen, unvisited cells with residual \(> 0\), target \(\arg\max\) of `residual / max(d, 1)`, then step toward it. Else the same frontier rule.

**Random.** Uniform among legal 8-neighbors.

**Social filters.** Attract: after the move, pair distance \(\le 2\). Avoid: \(\ge 5\). Solo: no filter.

**Schedulers.** `repeat_five`: same map, five episodes, resources refill. `each_grid`: one episode on each of the five maps in the chosen class. In both cases agents keep last-grid memory and receive no change signal.
