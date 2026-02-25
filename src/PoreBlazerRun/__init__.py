#!/usr/bin/env python3
import re
from pathlib import Path
from typing import TYPE_CHECKING

import polars as pl

if TYPE_CHECKING:
    from polars.dataframe import DataFrame


class PoreBlazerRun:
    """Contains the output of a PoreBlazer run."""

    def __init__(self, path_dir: Path | str, *, clean: bool = True) -> None:
        """Initialize a PoreBlazerRun based on an output directory.

        Parameters
        ----------
        path_dir : Path | str
            The directory with (some) of the output files
        clean : bool, optional
            Whether to clean the output files, by default True
        """
        # Attributes
        self.psd = pl.DataFrame()
        self.occup_vol = pl.DataFrame()
        self.summary = {}
        self.input_file_name = ""

        # Paths
        self.path_dir: Path = Path(path_dir)
        self.existing_paths = self.__get_paths()
        # TODO Other paths

        # Cleaning
        if clean:
            self.clean()

        # Parsing
        if ("psd" in self.existing_paths) and ("psd_cum" in self.existing_paths):
            self.__parse_psds()
        if "summary" in self.existing_paths:
            self.__parse_summary()
        if "occup_vol" in self.existing_paths:
            self.__parse_occup_vol()

    def clean(self) -> None:
        """Clean the output files. Does not do all files yet."""
        if "psd_cum" in self.existing_paths:
            self.__clean_psds(self.existing_paths["psd_cum"])
        if "psd" in self.existing_paths:
            self.__clean_psds(self.existing_paths["psd"])
        self.__clean_summary()
        self.__clean_occup_vol()
        # TODO Others

    def __clean_psds(self, path: Path) -> None:
        # Replace the multiple spaces
        with path.open("r") as file:
            data = file.read()

        while True:
            if "  " in data:
                data = data.replace("  ", " ")
            else:
                data = data.replace("\n ", "\n")
                data = data.replace(" \n", "\n")
                break

        with path.open("w") as file:
            file.write(data)

    def __clean_summary(self) -> None:
        """Make the summary file csv."""
        if "summary" not in self.existing_paths:
            return

        with self.existing_paths["summary"].open(mode="r") as f:
            text = f.read()

        if "," in text:
            return

        text = text.replace(" _", "_")
        text = text.replace(":", "")
        text = re.sub(r"( +)", r" ", text)  # Remove multiple space
        lines = []
        for line in text.splitlines():
            line = line.strip()
            splitted = line.split(" ")
            match len(splitted):
                case 1:
                    line = line
                case 2:
                    line = f"{splitted[0]} {splitted[1]}"
                case 3:
                    line = f"{splitted[0]}_{splitted[1]} {splitted[2]}"
                case _:
                    print("error")
            lines.append(line)

        to_write = "\n".join(lines)

        with self.existing_paths["summary"].open(mode="w") as f:
            f.write(to_write)

    def __clean_occup_vol(self) -> None:
        if "occup_vol" not in self.existing_paths:
            return

        with self.existing_paths["occup_vol"].open(mode="r") as f:
            text = f.read()

        text = re.sub(r"( +)", r" ", text)  # Remove multiple space
        text = "\n".join([line.strip() for line in text.splitlines()])

        with self.existing_paths["occup_vol"].open(mode="w") as f:
            f.write(text)

    def __parse_psds(self) -> None:
        tab_psd_c: DataFrame = pl.read_csv(
            self.existing_paths["psd_cum"],
            separator=" ",
            has_header=False,
            skip_lines=3,
            new_columns=["d", "Volume Fraction"],
        )
        tab_psd: DataFrame = pl.read_csv(
            self.existing_paths["psd"],
            separator=" ",
            has_header=False,
            skip_lines=1,
            new_columns=["d", "Derivative_dist"],
        )

        self.psd = tab_psd_c.join(tab_psd, on="d", how="full", coalesce=True)

    def __parse_summary(self) -> None:
        with self.existing_paths["summary"].open(mode="r") as f:
            lines = f.read().splitlines()

        self.input_file_name = lines[0]
        general_params = {
            line.split(" ")[0]: (
                float(line.split(" ")[1]) if i != 5 else (int(line.split(" ")[1]))
            )
            for i, line in enumerate(lines[1:7])
        }

        total_params = {
            line.split(" ")[0]: float(line.split(" ")[1])
            for i, line in enumerate(lines[8:19])
            if i != 3
        }
        network_params = {
            line.split(" ")[0]: float(line.split(" ")[1])
            for i, line in enumerate(lines[20:])
            if i != 3
        }

        self.summary = {
            "general_output": general_params,
            "total_output": total_params,
            "network_accessible_output": network_params,
        }

    def __parse_occup_vol(self) -> None:
        self.occup_vol = pl.read_csv(
            self.existing_paths["occup_vol"],
            separator=" ",
            has_header=False,
            skip_lines=2,
            new_columns=["Particle", "x", "y", "z"],
        )

    def __get_paths(self) -> dict[str, Path]:
        possible_paths: dict[str, str] = {
            "psd_cum": "Total_psd_cumulative.txt",
            "psd": "Total_psd.txt",
            "summary": "summary.dat",
            "occup_vol": "probe_occupiable_volume.xyz",
            "na_psd_cum": "Network-accessible_psd_cumulative.txt",
            "na_psd": "Network-accessible_psd.txt",
            "N_net_xyz": "nitrogen_network.xyz",
            "N_net_grd": "nitrogen_network.grd",
        }

        return {
            k: self.path_dir / v
            for k, v in possible_paths.items()
            if (self.path_dir / v).exists()
        }
