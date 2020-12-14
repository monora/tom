# -*- coding: utf-8 -*-

"""Console script for TOM. Not yet functional!
"""
import sys
import click


@click.command()
def main(args=None):
    """Console script for tom."""
    click.echo("Replace this message by putting your code into "
               "tom.cli.main")
    click.echo("See click documentation at http://click.pocoo.org/")
    return 0


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
