# Golf Simulator Project

This project is a 3D golf ball flight simulator split into separate Python files so it is easier to edit in VS Code later.

## What it does

You can choose:
- club
- swing percentage
- hole distance
- hole direction
- shot direction
- wind speed
- wind direction
- hole-in-one tolerance

Then it calculates:
- ball speed
- launch angle
- 3D trajectory
- landing point
- long/short error
- left/right error
- miss distance
- hole in one or missed

## Files

- `app.py` - Streamlit app with controls and plots
- `main.py` - simple Python run file
- `golf_sim/models.py` - data classes
- `golf_sim/clubs.py` - reads club data from CSV
- `golf_sim/physics.py` - conversions and derived values
- `golf_sim/simulation.py` - Euler-method 3D simulation
- `golf_sim/plotting.py` - 3D and top-down plots
- `golf_sim/data/clubs.csv` - bag data
- `requirements.txt` - packages to install

## How to run in VS Code

Open the extracted folder in VS Code, then open a terminal and run:

```bash
pip install -r requirements.txt
```

### Run the app

```bash
streamlit run app.py
```

Then open the local address Streamlit gives you.

### Or run the simple Python file

```bash
python main.py
```

## Notes

- The simulator uses a 3D Euler-method model.
- Club data is stored in `golf_sim/data/clubs.csv`.
- You can edit the bag values there later.
- The hole-in-one rule uses a distance tolerance in meters.
