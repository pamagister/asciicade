# Command Line Interface

Command line options for asciicade

```bash
asciicade [OPTIONS] <input>
```

For development from a source checkout, the equivalent module invocation is:

```bash
python -m asciicade [OPTIONS] <input>
```

## Options

| Option                | Type | Description                                       | Default    | Choices       |
|-----------------------|------|---------------------------------------------------|------------|---------------|
| --config              | str  | Path to configuration file                        | -          | -             |
| -v, --verbose         | bool | Enable debug logging                              | False      | [True, False] |
| -q, --quiet           | bool | Show warnings and errors only                     | False      | [True, False] |
| `input`               | str  | Path to input (file or folder)                    | *required* | -             |
| `--output`            | str  | Path to output destination                        | *required* | -             |
| `--min_dist`          | int  | Maximum distance between two waypoints            | 25         | -             |
| `--extract_waypoints` | bool | Extract starting points of each track as waypoint | True       | [True, False] |
| `--elevation`         | bool | Include elevation data in waypoints               | True       | [True, False] |


## Examples


### 1. Basic usage

```bash
asciicade input
```

### 2. With verbose logging

```bash
asciicade -v input
asciicade --verbose input
```

### 3. With quiet mode

```bash
asciicade -q input
asciicade --quiet input
```

### 4. With output parameter

```bash
asciicade --output  input
```

### 5. With min_dist parameter

```bash
asciicade --min_dist 25 input
```

### 6. With extract_waypoints parameter

```bash
asciicade --extract_waypoints True input
```

### Developer usage

```bash
python -m asciicade --help
python -m asciicade input
```

# More parameter

For your specific projects that inherit from the library, 
you can add more parameters to the CLI and config file 
by creating your own ConfigManager subclass 
and adding more ConfigParameter instances. 
The documentation generator will automatically include them 
in the generated documentation.
