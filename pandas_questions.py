"""Plotting referendum results in pandas.

In short, we want to make beautiful map to report results of a referendum. In
some way, we would like to depict results with something similar to the maps
that you can find here:
https://github.com/x-datascience-datacamp/datacamp-assignment-pandas/blob/main/example_map.png

To do that, you will load the data as pandas.DataFrame, merge the info and
aggregate them by regions and finally plot them on a map using `geopandas`.
"""
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt


def load_data():
    """Load data from the CSV files referundum/regions/departments."""
    referendum = pd.DataFrame({})
    regions = pd.DataFrame({})
    departments = pd.DataFrame({})

    return referendum, regions, departments


def merge_regions_and_departments(regions, departments):
    """Merge regions and departments in one DataFrame.

    The columns in the final DataFrame should be:
    ['code_reg', 'name_reg', 'code_dep', 'name_dep']
    """
    regions = regions.rename(
        columns={
            "code": "code_reg",
            "name": "name_reg",
        }
    )
    departments = departments.rename(
        columns={
            "code": "code_dep",
            "name": "name_dep",
            "region_code": "code_reg",
        }
    )

    regions = regions.copy()
    departments = departments.copy()

    regions["code_reg"] = regions["code_reg"].astype(str)
    departments["code_reg"] = departments["code_reg"].astype(str)
    departments["code_dep"] = departments["code_dep"].astype(str)

    merged = departments.merge(
        regions[["code_reg", "name_reg"]],
        on="code_reg",
        how="left",
    )
    return merged[["code_reg", "name_reg", "code_dep", "name_dep"]]


def merge_referendum_and_areas(referendum, regions_and_departments):
    """Merge referendum and regions_and_departments in one DataFrame.

    You can drop the lines relative to DOM-TOM-COM departments, and the
    french living abroad, which all have a code that contains `Z`.

    DOM-TOM-COM departments are departements that are remote from metropolitan
    France, like Guadaloupe, Reunion, or Tahiti.
    """
    referendum = referendum.copy()
    regions_and_departments = regions_and_departments.copy()

    referendum["code_dep"] = (
        referendum["Department code"]
        .astype(str)
        .str.strip()
        .str.zfill(2)
    )
    referendum["name_dep"] = referendum["Department name"].astype(str)

    regions_and_departments["code_dep"] = (
        regions_and_departments["code_dep"]
        .astype(str)
        .str.strip()
        .str.zfill(2)
    )

    # Drop overseas / abroad codes containing 'Z'
    referendum = referendum[~referendum["code_dep"].str.contains("Z", na=False)]

    merged = referendum.merge(
        regions_and_departments,
        on="code_dep",
        how="left",
        suffixes=("", "_area"),
    )

    if "name_dep_area" in merged.columns:
        merged = merged.drop(columns=["name_dep_area"])

    return merged


def compute_referendum_result_by_regions(referendum_and_areas):
    """Return a table with the absolute count for each region.

    The return DataFrame should be indexed by `code_reg` and have columns:
    ['name_reg', 'Registered', 'Abstentions', 'Null', 'Choice A', 'Choice B']
    """
    grouped = (
        referendum_and_areas
        .groupby("code_reg")
        .agg(
            name_reg=("name_reg", "first"),
            Registered=("Registered", "sum"),
            Abstentions=("Abstentions", "sum"),
            Null=("Null", "sum"),
            **{"Choice A": ("Choice A", "sum")},
            **{"Choice B": ("Choice B", "sum")},
        )
    )
    return grouped


def plot_referendum_map(referendum_result_by_regions):
    """Plot a map with the results from the referendum.

    * Load the geographic data with geopandas from `regions.geojson`.
    * Merge these info into `referendum_result_by_regions`.
    * Use the method `GeoDataFrame.plot` to display the result map. The results
      should display the rate of 'Choice A' over all expressed ballots.
    * Return a gpd.GeoDataFrame with a column 'ratio' containing the results.
    """
    geo = gpd.read_file("data/regions.geojson").copy()
    res = referendum_result_by_regions.reset_index().copy()

    geo["code"] = geo["code"].astype(str)
    res["code_reg"] = res["code_reg"].astype(str)

    merged = geo.merge(
        res,
        left_on="code",
        right_on="code_reg",
        how="left",
    )

    denom = merged["Choice A"] + merged["Choice B"]
    merged["ratio"] = merged["Choice A"] / denom.replace(0, pd.NA)

    ax = merged.plot(
        column="ratio",
        legend=True,
        edgecolor="black",
        linewidth=0.5,
    )
    ax.set_axis_off()
    ax.set_title("Referendum: Choice A share among expressed ballots")
    plt.tight_layout()

    return merged


if __name__ == "__main__":

    referendum, df_reg, df_dep = load_data()
    regions_and_departments = merge_regions_and_departments(
        df_reg, df_dep
    )
    referendum_and_areas = merge_referendum_and_areas(
        referendum, regions_and_departments
    )
    referendum_results = compute_referendum_result_by_regions(
        referendum_and_areas
    )
    print(referendum_results)

    plot_referendum_map(referendum_results)
    plt.show()
