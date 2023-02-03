from flask import Flask, jsonify, Response
from flask_cors import CORS

import pandas as pd
import numpy as np

from data import downsampled_df, release_tag_df, collection_tag_df

app = Flask(__name__)


@app.after_request
def cors(response):
    response.headers.add("Access-Control-Allow-Headers", "Content-Type,Authorization")
    response.headers.add("Access-Control-Allow-Methods", "GET,PUT,POST,DELETE,OPTIONS")
    response.headers.add("Access-Control-Allow-Credentials", "true")

    return response


@app.get("/fish/")
def get_fish_species():
    """Retrieve all of the unique species included in the dataset.

    Returns:
        _type_: A flask response with data of the list of unique species
    """

    at_tracked_species = [
        species
        for species in downsampled_df["species"].unique()
        if type(species) == str
    ]

    return jsonify(at_tracked_species)


@app.get("/fish/<species>")
def get_map_data_for_selected_species(species: str) -> Response:
    """Retrieve the positional and time series data of a given fish species.

    Args:
        species (str): species of fish to get positional data for

    Returns:
        Response: _description_
    """

    species_df: pd.DataFrame = downsampled_df[downsampled_df["species"] == species]

    unique_fish_in_species = [
        fish for fish in species_df["tag_code"].unique() if type(fish) == str
    ]

    output_array = []

    for fish in unique_fish_in_species:
        fish_dict = {
            "acoustic_tag": fish,
            "path": species_df[species_df["tag_code"] == fish][
                "position"
            ].values.tolist(),
            "timestamps": species_df[species_df["tag_code"] == fish][
                "datetime"
            ].values.tolist(),
            "collected": True
            if any(species_df[species_df["tag_code"] == fish]["collected"] == 1)
            else False,
        }

        min_val = min(fish_dict["timestamps"])
        max_val = max(fish_dict["timestamps"])

        # minmax scale timestamps to work with Deck.gl TripsLayer
        fish_dict["timestamps"] = [
            ((val - min_val) / (max_val - min_val) * 1000)
            for val in fish_dict["timestamps"]
        ]

        output_array.append(fish_dict)

    return jsonify(output_array)


@app.get("/stats/<species>")
def get_stats_for_selected_species(species: str) -> Response:
    """Retrieve collection and release statistics of a given fish species.

    Args:
        species (str): species of fish to retrieve statistics for

    Returns:
        Response: A flask response with statistics data
    """

    species_release_df: pd.DataFrame = release_tag_df[
        release_tag_df["Species Name"] == species
    ]
    collection_df: pd.DataFrame = collection_tag_df[
        collection_tag_df["Site Name"].str.contains("Final Collection Point")
    ]

    species_released_PIT_tags = [tag for tag in species_release_df["Tag Code"].unique()]
    species_released_count = len(species_released_PIT_tags)

    species_collected_tags = [
        tag
        for tag in collection_df["Tag Code"].unique()
        if tag in species_released_PIT_tags
    ]
    species_collected_count = len(species_collected_tags)

    species_summary = {
        "total_released": species_released_count,
        "total_collected": species_collected_count,
        "total_percentage": f"{(species_collected_count/species_released_count)*100} %",
    }

    return jsonify(species_summary)


if __name__ == "__main__":
    app.run(debug=True)
