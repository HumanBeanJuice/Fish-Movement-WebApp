import pandas as pd
import numpy as np


position_df: pd.DataFrame = pd.read_csv("fishPos_20190604.csv.gz")
sensor_tag_dfs: dict = pd.read_excel("PIT_CE.xlsx", sheet_name=None)
release_tag_df: pd.DataFrame = sensor_tag_dfs["Release"]
collection_tag_df: pd.DataFrame = sensor_tag_dfs["Collection"]


collection_tag_df["Detection Time"] = pd.to_datetime(
    collection_tag_df["Detection Time"], unit="s"
)

# Clean position data
# Filter out results where the MSE is in the 75% quantile
upper_quantile = position_df["MSE"].quantile(0.75)
position_df = position_df.loc[(position_df["MSE"] < upper_quantile)]

# Invert Z axis (already in meters)
position_df["Z"] = position_df["Z"] * -1

# Convert x and y offsets into meters
position_df["X"] = position_df["X"] * 0.3048
position_df["Y"] = position_df["Y"] * 0.3048

# Set Z-axis floor to 0 (jumping fish)
position_df["Z"] = position_df["Z"].apply(lambda x: 0 if x > 0 else x)

# Get the 4-7 characters of the AT Tag for joining onto PIT
position_df["Acoustic Tag"] = position_df["Tag_code"].str[3:7]
position_df["Acoustic Tag"] = position_df["Acoustic Tag"].str.lower()

release_tag_df["Acoustic Tag"] = release_tag_df["Acoustic Tag"].astype(str)

# Join the release data on the position dataframe
at_release_df = position_df.merge(release_tag_df, how="left", on="Acoustic Tag")

# Join the collection data on the position dataframe
at_release_df = at_release_df.merge(collection_tag_df, how="left", on="Tag Code")

# Get list of unique tags which were collected at the final collection point
collected_df = collection_tag_df[
    collection_tag_df["Site Name"].str.contains("Final Collection Point")
]
collected_fish_tags = [tag for tag in collected_df["Tag Code"].unique()]

at_release_df["Collected"] = np.where(
    at_release_df["Tag Code"].isin(collected_fish_tags), True, False
)
at_release_df["Collection Time"] = np.where(
    at_release_df["Collected"] == True,
    at_release_df["Detection Time"],
    np.datetime64("NaT"),
)

# Change date_time column to pd.Timestamps and index on
at_release_df["Date_time"] = pd.to_datetime(at_release_df["Date_time"]).dt.floor("Min")
at_release_df.set_index("Date_time", inplace=True, drop=False)

columns = [
    "datetime",
    "tag_code",
    "x",
    "y",
    "z",
    "mse",
    "acoustic_tag",
    "short_tag",
    "released_at",
    "species",
    "site",
    "detected_at",
    "antenna",
    "collected",
    "collected_at",
]

at_release_df.columns = columns

# Data set collects movement every 3 seconds, downsample data to every 30s

downsampled_df = pd.DataFrame(columns=columns)

# downsample for each unique fish
for tag in at_release_df["tag_code"].unique():

    df = at_release_df[at_release_df["tag_code"] == tag]

    # Discrete fish can not be in two places at once
    df = df[~df.index.duplicated()]

    # Downsample to 30s
    df = df.resample("30s").first()

    window = 5

    # Clean up potential outliers / bad sensor data using a rolling median and std
    df["median_x"] = df["x"].rolling(window).median()
    df["std_x"] = df["x"].rolling(window).std()
    df["median_y"] = df["y"].rolling(window).median()
    df["std_y"] = df["y"].rolling(window).std()
    df["median_z"] = df["z"].rolling(window).median()
    df["std_z"] = df["z"].rolling(window).std()

    # Fill bad data points (bad = value is outside 3stds of the median) for each coordinate with NaN for interpolation later

    df["x"] = np.where(
        (df["x"] >= df["median_x"] + (df["std_x"] * 3))
        | (df["x"] >= df["median_x"] - (df["std_x"] * 3)),
        np.NaN,
        df["x"],
    )
    df["y"] = np.where(
        (df["y"] >= df["median_y"] + (df["std_y"] * 3))
        | (df["y"] >= df["median_y"] - (df["std_y"] * 3)),
        np.NaN,
        df["y"],
    )
    df["z"] = np.where(
        (df["z"] >= df["median_z"] + (df["std_z"] * 3))
        | (df["z"] >= df["median_z"] - (df["std_z"] * 3)),
        np.NaN,
        df["z"],
    )

    df["x"] = df["x"].interpolate(method="time")
    df["y"] = df["y"].interpolate(method="time")
    df["z"] = df["z"].interpolate(method="time")

    downsampled_df = pd.concat([downsampled_df, df])

downsampled_df["position"] = downsampled_df[["x", "y", "z"]].values.tolist()
