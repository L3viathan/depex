import os
import json
import hashlib
import functools as ft
import click
import networkx as nx


class DepexStore:
    def __init__(self):
        self.open_count = 0
    def __enter__(self):
        if not self.open_count:
            with open(".depex.json") as f:
                self.store = json.load(f)
        self.open_count += 1
        return self.store
    def __exit__(self, *err):
        if self.open_count == 1:
            with open(".depex.json", "w") as f:
                json.dump(self.store, f)
        self.open_count -= 1


def hash_file(filename):
    with open(filename, "rb") as f:
        h = hashlib.sha256()
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def make_dependency_graph():
    g = nx.DiGraph()
    with Store as store:
        for command in store["commands"]:
            g.add_node(command)
        for command in store["reads"]:
            for file in store["reads"][command]:
                node = f":{file}"
                g.add_node(node)
                g.add_edge(node, command)
        for command in store["writes"]:
            for file in store["writes"][command]:
                node = f":{file}"
                g.add_node(node)
                g.add_edge(command, node)
    if not nx.is_directed_acyclic_graph(g):
        raise ValueError("Graph is cyclic")
    return g


def get_reachable_nodes(g, changed):
    return ft.reduce(
        set.union,
        (set(nx.shortest_path(g, f":{c}").keys()) for c in changed),
    )


def get_changed_files():
    # Get all files that have different hashes
    with Store as store:
        all_files = [
            file
            for cmd in store["reads"]
            for file in store["reads"][cmd]
        ]
        for file in all_files:
            if store["hashes"].get(file, 0) != hash_file(file):
                yield file

def update_hash(file):
    # Update the hash of a file
    print("Updating hash of", file)
    with Store as store:
        store["hashes"][file] = hash_file(file)

def run_command(cmd):
    with Store as store:
        os.system(store["commands"][cmd])

@click.group()
def cli():
    pass

@cli.command()
def init():
    """Create the .depex.json file and initialize it with the right hashes"""
    with open(".depex.json", "w") as f:
        json.dump({
            "hashes": {},
            "reads": {},
            "writes": {},
            "commands": {},
        }, f)

@cli.command()
@click.argument("name")
@click.argument("command", nargs=-1)
def add(name, command):
    """Add a command (but don't actually run it)"""
    print("add:", name, command)
    with Store as store:
        store["commands"][name] = " ".join(command)


@cli.command()
@click.argument("name")
@click.argument("files", nargs=-1)
def reads(name, files):
    """Declare that a command depends on one or more files"""
    print("depend:", name, files)
    with Store as store:
        dependencies = set(store["reads"].get(name, []))
        dependencies.update(set(files))
        store["reads"][name] = list(dependencies)


@cli.command()
@click.argument("name")
@click.argument("files", nargs=-1)
def writes(name, files):
    """Declare that a command creates one or more files"""
    print("depend:", name, files)
    with Store as store:
        dependents = set(store["writes"].get(name, []))
        dependents.update(set(files))
        store["writes"][name] = list(dependents)

@cli.command()
@click.option("--only/--all", default=False)
@click.argument("name", required=False)
def run(only, name):
    """
    Run a specific command (and everything that depends on it), or everything
    that has changed.
    """
    print("run:", only, name)
    changed_files = list(get_changed_files())
    if not changed_files:
        return
    print("changed:", changed_files)
    g = make_dependency_graph()
    reachable_nodes = get_reachable_nodes(g, changed_files)

    order = list(nx.topological_sort(g))
    print("order:", order)
    starting_pos = min(order.index(f":{file}") for file in changed_files)
    with Store as store:
        for node in order[starting_pos:]:
            if node in reachable_nodes and not node.startswith(":"):
                print("Running", node)
                run_command(node)
                for dependent in store["writes"][node]:
                    update_hash(dependent)
        for file in changed_files:
            update_hash(file)


if __name__ == '__main__':
    Store = DepexStore()
    cli()
"""
depex init
depex add readcorpus python3 read-corpus file.txt --with-args
depex reads readcorpus file.txt other.json
depex run readcorpus  # notices that hash changes for out.txt
depex add visualize python3 visualize.py
depex reads readcorpus out.txt
depex writes readcorpus out.txt
touch file.txt
depex run  # without arg: everything that's necessary: readcorpus, visualize

All commands have to be idempotent.
"""
