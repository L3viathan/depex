# depex

depex is a utility for organizing your experimental scripts and figuring out/documenting their dependencies between eachother.

There are a few requirements for depex to work on your experiments:

- Communication between different steps has to be via files, that all share the
  same (root) directory (e.g. a Git repo).
- Running the individual commands has to be idempotent, i.e. running a script
  twice shouldn't be a problem.
- The graph of dependencies between commands and data files has to be a
  Directed Acyclic Graph, meaning there can be no cyclic dependencies.

Apart from these requirements, I'm not aware of further restrictions.

## Usage

Like with git, you have to first initialize a depex project:

    depex init

This creates the (hidden) file `.depex.json`, which contains all the important
data. You shouldn't have to ever manually touch this file.

The next step is to add commands. Commands have a name, and a command line.
For example, this declares that there exists a command called `SIW` which
should, when executed call a python script:

    depex add SIW python3 split-into-words.py

After you have added a command, you have to declare its dependencies and
dependents. Commands only depend on data files, which only depend on commands.
No commands depend on other commands.

The following example declares that `SIW` reads from (depends on) the file
`source.txt`, and writes the files `words.txt` (which therefore depends on
`SIW`).

    depex reads SIW source.txt
    depex writes SIW words.txt

You can specify several dependencies at once.

By running

    depex status

you can get a list of all files that have changed since depex last saw them.
Before depex has done an initial run, all files will appear here. You also get
a list of commands that need to be run (in the correct order).

Finally, the most important command, and the only one you really need after you
declared all dependencies and commands:

    depex run

This figures out which files have changed, and runs all dependent commands in
the right order, including _their_ dependents. `depex run` is idempotent, i.e.
running it several times won't make a difference (in fact, depex will figure
out that it doesn't need to run again).

Whenever a file is changed, you can call `depex run` again to call the required
commands. If you should ever need to call _all_ commands, independent of their
status (for example in order to reproduce the experiments), you can use the
`--force-all` switch:

    depex run --force-all

All depex sub-commands optionally take a `--help` switch, which will display
help related to that command.

## Demo

[![asciicast](https://asciinema.org/a/T2WTOlI8hcopRYJkbUhAQaOHn.png)](https://asciinema.org/a/T2WTOlI8hcopRYJkbUhAQaOHn)

## License

depex is licensed under the MIT license, see `LICENSE`.
