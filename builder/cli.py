"""
Command line interface for user space Apptainer/Singularity container builder.
Created by DeiC, deic.dk

The classes in this module implements the command line main command and
subcommands.

Classes
-------
BuilderCLI
    Build Apptainer/Singularity containers for HPC systems in user space. (The
    main CLI command.)
Build
    Build a container.(The "build" subcommand.)
Info
    Obtain info about the state of all required dependencies for building a
    container. (The "info" subcommand.)
"""

import argparse
import pathlib

import container
import pack


class Build:
    """
    Build a container.

    The "build" subcommand.

    Parameters
    ----------
    image_path : pathlike
        Path to the built container image.
    base_image : str
        Base image to use for the container which may be any valid
        Apptainer/Singularity <BUILD SPEC>.
    conda_env : pathlike, optional
        Path to a Conda environment.yml file to install and activate in the
        container.
    """

    def __init__(self, *, image_path=None, base_image=None, conda_env=None):
        """Create the "build" subcommand."""
        self.image_path = image_path.absolute()
        self.base_image = base_image
        if conda_env is not None:
            self.conda_env = conda_env.absolute()
        else:
            self.conda_env = None

    @classmethod
    def add_arguments(cls, parser):
        """
        Add command line arguments to arguments parser.

        Parameters
        ----------
        parser : argparse.ArgumentParser
            The argument parser to add arguments to.
        """
        parser.add_argument(
            "image_path",
            help=_extract_help_from_docstring("image_path", cls.__doc__),
            type=pathlib.Path,
        )
        parser.add_argument(
            "--base-image",
            required=True,
            help=_extract_help_from_docstring("base_image", cls.__doc__),
        )
        parser.add_argument(
            "--conda-env",
            help=_extract_help_from_docstring("conda_env", cls.__doc__),
            type=pathlib.Path,
        )

    def execute(self):
        """Execute the subcommand."""
        with container.Sandbox(self.base_image) as sandbox:
            if self.conda_env is not None:
                # Install supplied conda env
                conda_install = pack.CondaInstall(sandbox.sandbox_dir)
                conda_env_name = "conda_container_env"
                conda_install.run_command(
                    f"conda env create -f {self.conda_env.as_posix()} "
                    f"-n {conda_env_name}"
                )

                # Activate env on container startup
                sandbox.add_to_env(conda_install.conda_runtime_bootstrap_script)
                sandbox.add_to_env(f"conda activate {conda_env_name}")

                # Cleanup
                conda_install.cleanup_unused_files()

            sandbox.build_image(self.image_path)


class Info:
    """
    Obtain info about the state of all required dependencies for building a container.

    The "info" subcommand.
    """

    @classmethod
    def add_arguments(cls, parser):
        """
        Add command line arguments to arguments parser.

        Parameters
        ----------
        parser : argparse.ArgumentParser
            The argument parser to add arguments to.
        """
        pass

    def execute(self):
        """Execute the subcommand."""
        print("Sorry, no information about your system is available at this time.")


class BuilderCLI:
    """
    Build Apptainer/Singularity containers for HPC systems in user space.

    The main CLI command.
    """

    def __init__(self):
        """Create a command line interface for the container builder."""
        # Setup main command parser
        builder_cli_doc_summary = self.__doc__.strip().splitlines()[0]
        parser = argparse.ArgumentParser(description=builder_cli_doc_summary)
        subparsers = parser.add_subparsers(title="subcommands")

        # Add subcommands parsers
        subcommands = [Build, Info]
        for subcommand_cls in subcommands:
            subcommand_doc_summary = subcommand_cls.__doc__.strip().splitlines()[0]
            sub_parser = subparsers.add_parser(
                name=subcommand_cls.__name__.lower(),
                help=subcommand_doc_summary,
                description=subcommand_doc_summary,
            )
            subcommand_cls.add_arguments(sub_parser)
            sub_parser.set_defaults(subcommand_cls=subcommand_cls)

        # Parse args
        self.args = parser.parse_args()
        subcommand_args = {
            key: val for key, val in vars(self.args).items() if key != "subcommand_cls"
        }

        try:
            self.subcommand = self.args.subcommand_cls(**subcommand_args)
        except AttributeError:
            # Print help if no subcommand was given
            class NoSubcommand:
                def execute(self):
                    parser.print_help()

            self.subcommand = NoSubcommand()


def _extract_help_from_docstring(arg, docstring):
    """
    Extract the description of `arg` in `string`.

    Parameters
    ----------
    arg : str
        The name of the argument.
    docstring : str
        The numpydoc docstring in which `arg` is documented.
    """
    arg_found = False
    arg_desc = []
    for line in docstring.splitlines():
        if arg_found:
            if " : " in line or line.strip() == "":
                # No more description lines, return the description
                return "".join(arg_desc).lstrip().lower().rstrip(".")
            else:
                # Extract line as part of arg description
                arg_desc.extend([line, " "])
        elif f"{arg} : " in line:
            # We found the requested arg in the docstring
            arg_found = True
    else:
        # We didn't find the arg in the docstring
        raise KeyError(f"The docstring does not include {arg=}")


if __name__ == "__main__":
    # Create BuilderCLI to parse command line args and run the specified
    # subcommand
    cli = BuilderCLI()
    cli.subcommand.execute()
