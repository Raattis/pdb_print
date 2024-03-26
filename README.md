# Running

1. run `python pdb_print.py` which generates a `.pdbrc` file
2. copy the `.pdbrc` to your project root
 * Alternatively, you can paste the `.pdbrc` contents to an open pdb session

# Commands

See the generated file for the aliases

The main commands are:
1. `p[ object][ <setting>=<value>][ filter={<string>}]` recursively prints any object attributes
2. `set[ name[ value]]` list, view or set settings by specifying 0, 1 or 2 arguments

## Useful hints

1. `plr filter={<a search pattern>}` will recurse local objects and print any lines with a match