# PoreBlazer output parser
Turns [PoreBlazer](https://github.com/SarkisovGitHub/PoreBlazer) output files into a Python usable object. Also 'cleans' these files to make them easier to parse.

## Usage
Requires the directory path as input.
```python
from PoreBlazerRun import PoreBlazerRun

pbr = PoreBlazerRun("run1/")

# Pore size distribution table
print(pbr.pbs)

# summary.dat as dict
print(pbr.summary)

# and more
```


## Installation
Local install using pip:
```
pip install git+https://github.com/TimKruikemeijerTUe/PoreBlazer-output-parser.git
```


## Dependencies
This script relies on [polars](https://pola.rs/).

## ToDo
- Implement the filetypes I haven't used yet.