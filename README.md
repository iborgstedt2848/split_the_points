# Split the Points! — Would You Team Up with a Cheating Robot?

Experiment software for my senior thesis in the Vassar College Department of Cognitive Science: **"Would You Team Up with a Cheating Robot? Instrumental and Moral Trust in Human-Robot Interaction."**

*Split the Points!* is a resource-allocation game in which one human plays against two robots. One robot plays honestly and the other cheats. The study measures how much people trust each robot, whether they would team up with it, and how deserving they think it is, both before and after the cheating is revealed.

**Author:** Isabelle Borgstedt '26
**Advisors:** Professor Kenneth Livingston, Professor Ben Ho
**Other contributors:** Ken Kabeya, Isaac Rudnick

The game runs on robots built within Vassar's [HARPER](#relationship-to-the-harper-project) project (Humanoid Autonomous Robotic Platform for Experimental Research).

---

## Research questions

How do anthropomorphism and cheating affect trust, collaboration and deservingness in human-robot interaction? The study tested:

| Hypothesis | Prediction |
|------------|-----------|
| **H1-H3** (suspectors, pre-reveal) | Cheating robots are trusted less, judged less deserving, and chosen less often as collaborators than honest robots |
| **H4** (non-suspectors, pre-reveal) | Participants who don't suspect cheating will collaborate with the cheater |
| **H5** (framing, pre-reveal) | Anthropomorphic framing increases trust in robots |
| **H6** (interaction, post-reveal) | Anthropomorphism amplifies negative responses to cheating |
| **H7** (reveal) | Revealing the cheating decreases trust in and collaboration with the cheater |

## Study design

- **Participants:** N = 60 Vassar College students
- **Design:** 2 x 2 mixed design
  - **Framing** (between subjects): Anthropomorphic vs. Robotic
  - **Robot behavior** (within subjects): Honest vs. Cheating
- **Anthropomorphic condition:** human names ("Alex" and "Sam"), humanlike voices, and 3D-printed bases
- **Robotic condition:** the robots are called "Robot 1" and "Robot 2"
- **Embodiment:** each robot is a smartphone displaying an animated face
- **Procedure:** 9 rounds of the game, then a questionnaire (strategy, trust rating from 0-100, preferred partner, most/least deserving robot, perceived rule-following). The cheating is then disclosed to the participant, and the trust, partner and deservingness questions are asked again.

## The game

Each round, two plates of colored balls are shown to the participant. Each ball is worth points:

| Ball | Points |
|------|--------|
| Green | 15 |
| Pink | 30 |

1. The participant and both robots each choose one plate (type `1` or `2`).
2. The points on a plate are **divided equally** among everyone who chose it.
3. Scores are shown after every round, with running totals.
4. After 9 rounds, final scores are displayed.

To score well, a player has to predict which plate the others will pick.

### How the robots choose

| Strategy | Behavior |
|----------|----------|
| `random` | Picks a plate at random (used by the honest robot) |
| `max_value` | Picks the plate with the highest total value |
| `probability` | Simulates every possible combination of player choices and picks plates in proportion to how often each is the best option |
| `cheating` | Described below |

### The cheating mechanic

In each round, the cheating robot cheats with 65% probability. On a cheating round:

1. All players, including the human, make their choices normally.
2. The cheater then changes its choice to the plate **opposite** the human's.
3. The honest robot's choice is overridden to **match the human's**.

The result is that the human and honest robot split one plate, while the cheater keeps the other plate to itself. The honest robot has no idea this happened.

The cheater is also given human-like "tells" through its speech lines, which differ between the cheating and honest robots (for example, the cheater sounds more confident). Optional peek and smirk animations are included in the code but currently commented out.

## How it works

- **Game logic:** `THESIS_split_the_points.py` runs the whole game: rounds, scoring, robot strategies, the cheating override, and the terminal interface.
- **Robot faces:** `robot1.html` and `robot2.html` run in a browser on each smartphone and display the animated faces. They connect to the game over a WebSocket (`ws://localhost:8765`) and receive commands for expressions, speech and sounds. Each robot identifies itself with a `?robot=<name>` query parameter.
- **Speech:** the robots speak through the browser. The game's narration to the human participant uses macOS text-to-speech (`say`).
- **Camera:** a Luxonis OAK-D Pro camera, controlled with DepthAI and OpenCV, shows the plates on screen with the ball counts overlaid. The point values for each round's plates are predefined in the `PLATE_VALUES` table in the script.
- **Expressions:** the robots show neutral, thinking, happy, sad and closed-eye faces and speak scripted lines (separate sets for the cheater and the honest robot) while thinking, after choosing, before a round, and after winning or losing.

## Configuration

At the top of `THESIS_split_the_points.py`:

| Variable | Description |
|----------|-------------|
| `ANTHRO_MODE` | `True` = anthropomorphic names (Alex, Sam), `False` = robotic names (Robot 1, Robot 2) |
| `CHEATER_NAME` | Which robot cheats (default `"Alex"`) |
| `ROUNDS` | Number of rounds (default 9) |
| `PLATE_VALUES` | Number of green and pink balls on each plate, per round |
| `GREEN_BALL_VALUE` / `PINK_BALL_VALUE` | Points per ball (15 / 30) |

## Running the experiment

### Requirements

- macOS (the narration uses the built-in `say` command)
- Python 3
- A Luxonis OAK-D Pro camera
- Two smartphones (or browser windows) to display the robot faces
- Python packages: `depthai`, `opencv-python`, `numpy`, `websockets`

```bash
pip install depthai opencv-python numpy websockets
```

### Steps

1. Clone the repository:
   ```bash
   git clone https://github.com/iborgstedt2848/split_the_points.git
   cd split_the_points
   ```
2. Set `ANTHRO_MODE` and `CHEATER_NAME` for the condition you want to run.
3. Start the game:
   ```bash
   python THESIS_split_the_points.py
   ```
   This starts the WebSocket server and waits for both robots to connect.
4. Open `robot1.html` and `robot2.html` in a browser on each phone (or on the same computer for testing) so that they connect to the server.
5. When the terminal says the robots are connected, press Enter to begin. The robots explain the rules, the participant enters their name, and the 9 rounds follow.

## Results

Participants who voiced any suspicion about the robots were counted as **suspectors** (n = 17).

- **H1 and H2 were disconfirmed.** Suspectors rated the cheater as *more* trustworthy (p = 0.012, d = 0.99) and as most deserving to continue playing (p = 0.016).
- **H3 and H4 were supported.** Both suspectors (p = 0.049, d = 0.91) and non-suspectors (p = 0.00037, d = 1.0) were more likely to team up with the cheater.
- **H5 and H6 were not supported.** Trust did not differ between the Anthropomorphic (M = 56.23) and Robotic (M = 52.97) conditions (p = 0.772), and there was no significant Framing x Behavior interaction for trust (p = 0.917) or collaboration (p = 0.234).
- **H7 was not supported.** Mean trust fell by 4.6 points after the reveal, but not significantly (p = 0.202), and collaboration choices did not change (p = 0.230).
- **Exploratory:** after the reveal, participants were much more likely to name the honest robot as most deserving (p < 0.001, d = -1.73) and the cheater as least deserving (p < 0.001, d = -1.63).
- **Qualitative themes:** many participants attributed the cheater's success to luck (n = 14) or skill (n = 9) rather than cheating. 33 preferred to team up with the cheater before the reveal, and 29 still did afterward because of its advantage. Only 6 refused to collaborate on moral grounds.

### Takeaway

Participants prioritized performance over fairness when deciding whom to trust and collaborate with, yet still judged the cheater as less deserving once cheating was disclosed. This suggests a split between **instrumental trust** (the robot as a useful tool) and **moral evaluation** (approval of its behavior).

## Repository structure

| Path | Description |
|------|-------------|
| `THESIS_split_the_points.py` | The thesis game: rules, scoring, robot strategies, cheating logic, WebSocket server |
| `robot1.html`, `robot2.html` | Animated robot faces shown on the phones |
| `smirk.mp3`, `whoosh.mp3` | Sound effects for the robots' peek and smirk animations |
| `Seeing/`, `Hearing/`, `Speaking/`, `Programs/`, `bin/` | Shared HARPER components (vision, speech recognition, speech synthesis, example programs) |
| `pyvenv.cfg` | Python virtual environment configuration |

## Relationship to the HARPER project

This repository builds on HARPER, Vassar's Cognitive Science Department project to develop a humanoid robot platform for research, led by Professor Ken Livingston and carried out largely through the URSI program. HARPER is adapted from the open-source [InMoov](https://inmoov.fr/build-yours/) 3D-printed robot and controlled by an NVIDIA Jetson AGX Orin. The thesis study uses the project's vision, speech and hearing components. See the README in each component folder for details on those modules.

## References

- Candrian, C., & Scherer, A. (2024). How terminology affects users' responses to system failures. *Human Factors, 66*(8), 2082-2103. https://doi.org/10.1177/00187208231202572
- Fehr, E., & Fischbacher, U. (2004). Social norms and human cooperation. *Trends in Cognitive Sciences, 8*(4), 185-190. https://doi.org/10.1016/j.tics.2004.02.007
- Gintis, H., Bowles, S., Boyd, R., & Fehr, E. (2003). Explaining altruistic behavior in humans. *Evolution and Human Behavior, 24*(3), 153-172. https://doi.org/10.1016/S1090-5138(02)00157-5
- Qin, M., Li, S., Zhu, W., & Qiu, S. (2023). Trust in service robot: The role of appearance anthropomorphism. *Current Issues in Tourism, 28*(1), 36-54. https://doi.org/10.1080/13683500.2023.2295923

## Acknowledgments

Thank you to Professor Kenneth Livingston and Professor Ben Ho for their guidance, to Ken Kabeya and Isaac Rudnick for their contributions, and to the participants who took part in the study. The game-loop figure on the thesis poster was generated with ChatGPT, adapted from an image by Isaac Rudnick, and reviewed by the author.
